from __future__ import annotations

import asyncio
import os
import shutil
import stat
import subprocess
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fixtures import native_filesystem_path
from .observability import (
    CgroupView,
    DaemonProcessMetrics,
    ObservabilityError,
    SnapshotView,
    daemon_from_cgroup,
)
from .product import ProductAccess

ResourceSink = Callable[[list[dict[str, Any]]], Awaitable[None]]
_MAX_IN_FLIGHT_SAMPLES = 1
# The qualified Windows product samples its resource rings every 100 ms. A
# retry faster than that cadence can only launch duplicate CLI observations
# against the same ring generation.
_BOUNDARY_POLL_INTERVAL_SECONDS = 0.1
_POST_BOUNDARY_FIRST_POLL_DELAY_SECONDS = 0.1
_BOUNDARY_READINESS_TIMEOUT_SECONDS = 5.0
_RESOURCE_RING_PENDING = "resource ring is not available yet"
_INAPPLICABLE_CREATE_COUNTERS = frozenset(
    {
        "daemon_cpu_time_ns",
        "sandbox_cpu_time_ns",
        "sandbox_block_read_bytes",
        "sandbox_block_write_bytes",
    }
)


class ResourceSamplingError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _ProductBoundary:
    cgroup_timestamp_ms: int
    snapshot_timestamp_ms: int
    workspace_timestamps_ms: tuple[tuple[str, int], ...]


_METRICS = {
    "runner_rss_bytes": ("bytes", "runner", "gauge", "maximum", "host_process_api"),
    "daemon_rss_bytes": (
        "bytes",
        "daemon",
        "gauge",
        "maximum",
        "product_observability.cgroup.topology.daemon.peak_resident_memory_bytes",
    ),
    "daemon_cpu_time_ns": (
        "nanoseconds",
        "daemon",
        "monotonic_counter",
        "delta",
        "product_observability.cgroup.topology.daemon.cpu_time_us",
    ),
    "sandbox_memory_current_bytes": (
        "bytes",
        "sandbox",
        "gauge",
        "maximum",
        "product_observability.cgroup.docker_engine.memory.current",
    ),
    "sandbox_memory_peak_bytes": (
        "bytes",
        "sandbox",
        "gauge",
        "maximum",
        "product_observability.cgroup.docker_engine.memory.current.sampled_peak",
    ),
    "sandbox_cpu_time_ns": (
        "nanoseconds",
        "sandbox",
        "monotonic_counter",
        "delta",
        "product_observability.cgroup.docker_engine.cpu.usage_usec",
    ),
    "sandbox_block_read_bytes": (
        "bytes",
        "sandbox",
        "monotonic_counter",
        "delta",
        "product_observability.cgroup.docker_engine.io.read_bytes",
    ),
    "sandbox_block_write_bytes": (
        "bytes",
        "sandbox",
        "monotonic_counter",
        "delta",
        "product_observability.cgroup.docker_engine.io.write_bytes",
    ),
    "workspace_logical_bytes": (
        "bytes",
        "workspace",
        "gauge",
        "maximum",
        "filesystem.metadata",
    ),
    "workspace_allocated_bytes": (
        "bytes",
        "workspace",
        "gauge",
        "maximum",
        "filesystem.metadata",
    ),
    "workspace_file_count": (
        "count",
        "workspace",
        "gauge",
        "maximum",
        "filesystem.metadata",
    ),
    "layerstack_bytes": (
        "bytes",
        "layerstack",
        "gauge",
        "maximum",
        "product_observability.snapshot.stack.storage_allocated_bytes",
    ),
    "upperdir_bytes": (
        "bytes",
        "workspace",
        "gauge",
        "delta",
        "product_observability.snapshot.workspaces.disk_allocated_bytes.sum",
    ),
    "host_free_bytes": (
        "bytes",
        "host_volume",
        "gauge",
        "minimum",
        "filesystem.disk_usage",
    ),
}
_METRIC_SEMANTIC_REVISIONS = {
    "upperdir_bytes": 2,
}


def resource_metric_source(metric_id: str) -> str:
    return _METRICS[metric_id][4]


class WorkspaceMetricCache:
    """Cache immutable host-workspace tree metrics for one campaign runner."""

    def __init__(self) -> None:
        self._values: dict[str, dict[str, tuple[int | None, str | None]]] = {}
        self._pending: dict[
            str, asyncio.Task[dict[str, tuple[int | None, str | None]]]
        ] = {}
        self._lock = asyncio.Lock()

    async def get(self, workspace: Path) -> dict[str, tuple[int | None, str | None]]:
        resolved = workspace.resolve(strict=True)
        key = os.path.normcase(os.fspath(resolved))
        async with self._lock:
            cached = self._values.get(key)
            if cached is not None:
                return dict(cached)
            task = self._pending.get(key)
            if task is None:
                task = asyncio.create_task(
                    asyncio.to_thread(_workspace_metrics, resolved),
                    name=f"workspace-metrics:{resolved.name}",
                )
                self._pending[key] = task
        try:
            values = await asyncio.shield(task)
        except BaseException:
            async with self._lock:
                if self._pending.get(key) is task:
                    del self._pending[key]
            raise
        async with self._lock:
            self._values[key] = dict(values)
            if self._pending.get(key) is task:
                del self._pending[key]
        return dict(values)

    async def invalidate(self, workspace: Path) -> None:
        """Discard a path after an explicit host-workspace mutation."""
        resolved = workspace.resolve(strict=True)
        key = os.path.normcase(os.fspath(resolved))
        async with self._lock:
            self._values.pop(key, None)


class TrialResourceSampler:
    def __init__(
        self,
        *,
        product: ProductAccess,
        sandbox: str,
        workspace: Path,
        cell_id: str,
        trial_id: str,
        interval_ms: int,
        campaign_started_ns: int,
        sink: ResourceSink,
        workspace_cache: WorkspaceMetricCache | None = None,
        counter_delta_applicable: bool = True,
        expected_post_workspace_count: int | None = None,
    ) -> None:
        if not 10 <= interval_ms <= 60_000:
            raise ValueError("resource sample interval is invalid")
        if (
            expected_post_workspace_count is not None
            and expected_post_workspace_count < 1
        ):
            raise ValueError("expected post-operation workspace count is invalid")
        self._product = product
        self._sandbox = sandbox
        self._workspace = workspace
        self._cell_id = cell_id
        self._trial_id = trial_id
        self._interval = interval_ms / 1000
        self._campaign_started_ns = campaign_started_ns
        self._sink = sink
        self._workspace_cache = workspace_cache or WorkspaceMetricCache()
        self._counter_delta_applicable = counter_delta_applicable
        self._expected_post_workspace_count = expected_post_workspace_count
        self._workspace_values: (
            dict[str, tuple[int | None, str | None]] | BaseException | None
        ) = None
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._sample_index = 0
        self._samples: dict[int, asyncio.Task[list[dict[str, Any]]]] = {}
        self._baseline_boundary: _ProductBoundary | None = None
        self._post_response_threshold_ms: int | None = None
        self._post_boundary_not_before_ns: int | None = None

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("resource sampler was already started")
        if self._workspace_values is None:
            try:
                self._workspace_values = await self._workspace_cache.get(
                    self._workspace
                )
            except asyncio.CancelledError:
                raise
            except BaseException as error:
                self._workspace_values = error
        baseline = self._launch(
            sampled=False,
            scheduled_ns=time.monotonic_ns(),
            force=True,
        )
        # The operation barrier cannot be released until the counter baseline
        # is an actual completed collection.
        await baseline
        self._task = asyncio.create_task(
            self._loop(), name=f"resources:{self._trial_id}"
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        # Start the qualified product-ring wait at the post-response boundary.
        # An already-admitted periodic collection must still drain before the
        # mandatory boundary can launch, but its drain is independent of the
        # ring's 100-ms freshness interval and can safely overlap that wait.
        self._post_response_threshold_ms = time.time_ns() // 1_000_000
        self._post_boundary_not_before_ns = time.monotonic_ns() + int(
            _POST_BOUNDARY_FIRST_POLL_DELAY_SECONDS * 1_000_000_000
        )
        self._stop.set()
        await self._task
        self._task = None
        active = [task for task in self._samples.values() if not task.done()]
        if active:
            # A periodic collector admitted during the primary window keeps its
            # evidence, but the mandatory boundary must not overlap it and
            # exceed the one-expensive-collector perturbation cap.
            await asyncio.gather(*active, return_exceptions=True)
        # This boundary collection is mandatory even when a periodic collector
        # was still completing at stop. It begins only after all measured
        # responses have validated and gives counter metrics a real endpoint.
        self._launch(
            sampled=False,
            scheduled_ns=time.monotonic_ns(),
            force=True,
        )
        results = await asyncio.gather(
            *(self._samples[index] for index in sorted(self._samples)),
            return_exceptions=True,
        )
        errors: list[BaseException] = []
        for result in results:
            if isinstance(result, BaseException):
                errors.append(result)
                continue
            try:
                # Samples may collect concurrently, but their complete record
                # batches are persisted in scheduled order. The sink fsyncs
                # each batch before stop returns, making the trial boundary
                # the durability boundary.
                await self._sink(result)
            except BaseException as error:
                errors.append(error)
        self._samples.clear()
        if errors:
            raise BaseExceptionGroup("resource sampling failed", errors)

    async def _loop(self) -> None:
        deadline = time.monotonic() + self._interval
        while True:
            remaining = max(0.0, deadline - time.monotonic())
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=remaining)
            except TimeoutError:
                self._launch(
                    sampled=True,
                    scheduled_ns=int(deadline * 1_000_000_000),
                )
                deadline += self._interval
                continue
            return

    def _launch(
        self,
        *,
        sampled: bool,
        scheduled_ns: int | None = None,
        force: bool = False,
    ) -> asyncio.Task[list[dict[str, Any]]]:
        index = self._sample_index
        self._sample_index += 1
        scheduled_ns = scheduled_ns or time.monotonic_ns()
        active = sum(not task.done() for task in self._samples.values())
        if not force and active >= _MAX_IN_FLIGHT_SAMPLES:
            task = asyncio.create_task(
                self._unavailable_sample(
                    sampled=sampled,
                    scheduled_ns=scheduled_ns,
                    reason=(
                        "resource collector saturated at its fixed "
                        f"{_MAX_IN_FLIGHT_SAMPLES}-sample concurrency cap"
                    ),
                ),
                name=f"resources:{self._trial_id}:{index}:unavailable",
            )
        else:
            task = asyncio.create_task(
                self._sample(
                    index=index,
                    sampled=sampled,
                    scheduled_ns=scheduled_ns,
                ),
                name=f"resources:{self._trial_id}:{index}",
            )
        self._samples[index] = task
        return task

    async def _sample(
        self, *, index: int, sampled: bool, scheduled_ns: int
    ) -> list[dict[str, Any]]:
        started_ns = time.monotonic_ns()
        boundary: _ProductBoundary | None = None
        if not sampled and self._counter_delta_applicable:
            boundary_result, dynamic = await asyncio.gather(
                self._await_product_boundary(
                    index=index,
                    after=self._baseline_boundary,
                    post_response_threshold_ms=(
                        self._post_response_threshold_ms
                        if self._baseline_boundary is not None
                        else None
                    ),
                ),
                asyncio.to_thread(_dynamic_local_metrics, self._workspace),
                return_exceptions=True,
            )
            if isinstance(boundary_result, BaseException):
                raise boundary_result
            cgroup, snapshot, boundary = boundary_result
        else:
            dynamic, cgroup, snapshot = await asyncio.gather(
                asyncio.to_thread(_dynamic_local_metrics, self._workspace),
                self._product.observe_cgroup(
                    self._sandbox,
                    request_id=f"{self._trial_id}.observe.cgroup.{index}",
                ),
                self._product.observe_snapshot(
                    self._sandbox,
                    request_id=f"{self._trial_id}.observe.snapshot.{index}",
                ),
                return_exceptions=True,
            )
        daemon = _daemon_metrics_from_cgroup(cgroup)
        completed_ns = time.monotonic_ns()
        observed_offset = max(0, started_ns - self._campaign_started_ns)
        completed_offset = max(0, completed_ns - self._campaign_started_ns)
        scheduled_offset = max(0, scheduled_ns - self._campaign_started_ns)
        local = _combine_local_metrics(dynamic, self._workspace_values)
        values = _resource_values(local, cgroup, snapshot, daemon)
        if not self._counter_delta_applicable:
            reason = (
                "counter delta is inapplicable because a sandbox-scoped "
                "pre-create baseline cannot exist"
            )
            for metric_id in _INAPPLICABLE_CREATE_COUNTERS:
                values[metric_id] = (None, reason)
        elif not sampled and self._baseline_boundary is None:
            if boundary is None:
                raise ResourceSamplingError(
                    "resource baseline boundary was not captured"
                )
            if (
                self._expected_post_workspace_count is not None
                and boundary.workspace_timestamps_ms
            ):
                raise ResourceSamplingError(
                    "workspace-create baseline unexpectedly had live workspaces"
                )
            self._baseline_boundary = boundary
        return self._records(
            values,
            offset=observed_offset,
            scheduled_offset=scheduled_offset,
            collection_started_offset=observed_offset,
            collection_completed_offset=completed_offset,
            sampled=sampled,
        )

    async def _await_product_boundary(
        self,
        *,
        index: int,
        after: _ProductBoundary | None,
        post_response_threshold_ms: int | None,
    ) -> tuple[CgroupView, SnapshotView, _ProductBoundary]:
        post_boundary_not_before_ns = self._post_boundary_not_before_ns
        if (
            after is None
            and (
                post_response_threshold_ms is not None
                or post_boundary_not_before_ns is not None
            )
        ) or (
            after is not None
            and (
                post_response_threshold_ms is None
                or post_boundary_not_before_ns is None
            )
        ):
            raise ResourceSamplingError(
                "post-response resource threshold does not match boundary phase"
            )
        deadline = time.monotonic() + _BOUNDARY_READINESS_TIMEOUT_SECONDS
        attempt = 0
        pending_reason = "product resource boundary was not ready"
        if after is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ResourceSamplingError(
                    f"product resource boundary readiness timed out: {pending_reason}"
                )
            freshness_wait = max(
                0.0,
                (post_boundary_not_before_ns - time.monotonic_ns()) / 1_000_000_000,
            )
            if freshness_wait:
                await asyncio.sleep(min(freshness_wait, remaining))
        while True:
            cgroup, snapshot = await asyncio.gather(
                self._product.observe_cgroup(
                    self._sandbox,
                    request_id=(
                        f"{self._trial_id}.observe.cgroup.{index}.boundary.{attempt}"
                    ),
                ),
                self._product.observe_snapshot(
                    self._sandbox,
                    request_id=(
                        f"{self._trial_id}.observe.snapshot.{index}.boundary.{attempt}"
                    ),
                ),
            )
            boundary, pending_reason = _complete_product_boundary(cgroup, snapshot)
            if boundary is not None:
                if after is None or _boundary_is_fresh(
                    boundary,
                    after,
                    post_response_threshold_ms=post_response_threshold_ms,
                    expected_workspace_count=self._expected_post_workspace_count,
                ):
                    return cgroup, snapshot, boundary
                pending_reason = "product resource boundary was not newer than baseline"
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ResourceSamplingError(
                    f"product resource boundary readiness timed out: {pending_reason}"
                )
            attempt += 1
            await asyncio.sleep(min(_BOUNDARY_POLL_INTERVAL_SECONDS, remaining))

    async def _unavailable_sample(
        self, *, sampled: bool, scheduled_ns: int, reason: str
    ) -> list[dict[str, Any]]:
        values = {metric_id: (None, reason) for metric_id in _METRICS}
        offset = max(0, scheduled_ns - self._campaign_started_ns)
        return self._records(
            values,
            offset=offset,
            scheduled_offset=offset,
            collection_started_offset=None,
            collection_completed_offset=None,
            sampled=sampled,
        )

    def _records(
        self,
        values: dict[str, tuple[int | None, str | None]],
        *,
        offset: int,
        scheduled_offset: int,
        collection_started_offset: int | None,
        collection_completed_offset: int | None,
        sampled: bool,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for metric_id in _METRICS:
            value, reason = values[metric_id]
            records.append(
                {
                    "cell_id": self._cell_id,
                    "trial_id": self._trial_id,
                    "request_id": None,
                    "reading": _reading(
                        metric_id,
                        offset,
                        scheduled_offset=scheduled_offset,
                        collection_started_offset=collection_started_offset,
                        collection_completed_offset=collection_completed_offset,
                        value=value,
                        reason=reason,
                        sampled=sampled,
                    ),
                }
            )
        return records


def _complete_product_boundary(
    cgroup: CgroupView,
    snapshot: SnapshotView,
) -> tuple[_ProductBoundary | None, str]:
    if cgroup.availability != "available":
        if not cgroup.series and cgroup.errors == [_RESOURCE_RING_PENDING]:
            return None, _RESOURCE_RING_PENDING
        raise ResourceSamplingError(
            "product cgroup boundary was partial: "
            + ("; ".join(cgroup.errors) or "no error was reported")
        )
    latest_cgroup = cgroup.series[-1]
    missing_cgroup = [
        name
        for name in ("cpu_usec", "mem_cur", "io_rbytes", "io_wbytes")
        if getattr(latest_cgroup.metrics, name) is None
    ]
    if missing_cgroup:
        raise ResourceSamplingError(
            "product cgroup boundary omitted required metrics: "
            + ", ".join(missing_cgroup)
        )
    if snapshot.availability != "available":
        raise ResourceSamplingError(
            "product snapshot boundary was partial: "
            + ("; ".join(snapshot.errors) or "no error was reported")
        )
    workspace_timestamps: list[tuple[str, int]] = []
    for workspace in snapshot.workspaces:
        latest_workspace = workspace.resources.latest
        if latest_workspace is None:
            return (
                None,
                f"workspace {workspace.workspace_id} resource sample is not available yet",
            )
        metrics = latest_workspace.metrics
        if (
            metrics.disk_allocated_bytes is None
            or metrics.disk_truncated is True
            or metrics.record_truncated_bytes is not None
        ):
            raise ResourceSamplingError(
                f"workspace {workspace.workspace_id} upperdir allocation "
                "was not completely reported"
            )
        workspace_timestamps.append((workspace.workspace_id, latest_workspace.ts))
    return (
        _ProductBoundary(
            cgroup_timestamp_ms=latest_cgroup.ts,
            snapshot_timestamp_ms=snapshot.sampled_at_unix_ms,
            workspace_timestamps_ms=tuple(sorted(workspace_timestamps)),
        ),
        "",
    )


def _boundary_is_fresh(
    boundary: _ProductBoundary,
    baseline: _ProductBoundary,
    *,
    post_response_threshold_ms: int,
    expected_workspace_count: int | None,
) -> bool:
    if boundary.cgroup_timestamp_ms <= max(
        baseline.cgroup_timestamp_ms,
        post_response_threshold_ms,
    ):
        return False
    current_workspaces = dict(boundary.workspace_timestamps_ms)
    baseline_workspaces = dict(baseline.workspace_timestamps_ms)
    if (
        expected_workspace_count is not None
        and len(current_workspaces) != expected_workspace_count
    ):
        return False
    if not baseline_workspaces:
        return not current_workspaces or all(
            timestamp > max(baseline.snapshot_timestamp_ms, post_response_threshold_ms)
            for timestamp in current_workspaces.values()
        )
    if not baseline_workspaces.keys() <= current_workspaces.keys():
        return False
    if any(
        current_workspaces[workspace_id] <= max(timestamp, post_response_threshold_ms)
        for workspace_id, timestamp in baseline_workspaces.items()
    ):
        return False
    return all(
        workspace_id in baseline_workspaces
        or timestamp > max(baseline.snapshot_timestamp_ms, post_response_threshold_ms)
        for workspace_id, timestamp in current_workspaces.items()
    )


def _daemon_metrics_from_cgroup(
    cgroup: CgroupView | BaseException,
) -> DaemonProcessMetrics | BaseException:
    if isinstance(cgroup, BaseException):
        return cgroup
    try:
        return daemon_from_cgroup(cgroup)
    except ObservabilityError as error:
        return error


def _resource_values(
    local: dict[str, tuple[int | None, str | None]] | BaseException,
    cgroup: CgroupView | BaseException,
    snapshot: SnapshotView | BaseException,
    daemon: DaemonProcessMetrics | BaseException,
) -> dict[str, tuple[int | None, str | None]]:
    if isinstance(local, BaseException):
        reason = _collector_failure("host/workspace", local)
        local = {
            metric_id: (None, reason)
            for metric_id in (
                "runner_rss_bytes",
                "workspace_logical_bytes",
                "workspace_allocated_bytes",
                "workspace_file_count",
                "host_free_bytes",
            )
        }
    latest = (
        None
        if isinstance(cgroup, BaseException) or not cgroup.series
        else cgroup.series[-1].metrics
    )
    cgroup_reason = (
        None
        if latest is not None
        else (
            _collector_failure("product cgroup", cgroup)
            if isinstance(cgroup, BaseException)
            else "; ".join(cgroup.errors) or "product cgroup sample was unavailable"
        )
    )
    daemon_available = False if isinstance(daemon, BaseException) else daemon.available
    daemon_reason = None
    if not daemon_available:
        if isinstance(daemon, BaseException):
            daemon_reason = _collector_failure("product cgroup topology daemon", daemon)
        else:
            raw_reason = (daemon.model_extra or {}).get("error")
            daemon_reason = (
                str(raw_reason)
                if raw_reason
                else "product daemon self metrics were unavailable"
            )
    daemon_rss = (
        daemon.peak_resident_memory_bytes
        if daemon_available and not isinstance(daemon, BaseException)
        else None
    )
    daemon_cpu = (
        daemon.cpu_time_us
        if daemon_available and not isinstance(daemon, BaseException)
        else None
    )
    stack_value = (
        snapshot.stack.storage_allocated_bytes
        if not isinstance(snapshot, BaseException) and snapshot.stack
        else None
    )
    stack_reason = (
        None
        if stack_value is not None
        else (
            _collector_failure("product snapshot", snapshot)
            if isinstance(snapshot, BaseException)
            else "LayerStack allocated storage was not reported by the product"
        )
    )
    upperdir: int | None = 0
    upperdir_reason: str | None = None
    if isinstance(snapshot, BaseException):
        upperdir = None
        upperdir_reason = _collector_failure("product snapshot", snapshot)
    elif snapshot.availability == "partial":
        upperdir = None
        upperdir_reason = "product snapshot was partial"
    for workspace in () if isinstance(snapshot, BaseException) else snapshot.workspaces:
        sample = workspace.resources.latest
        if (
            sample is None
            or sample.metrics.disk_allocated_bytes is None
            or sample.metrics.disk_truncated is True
            or sample.metrics.record_truncated_bytes is not None
        ):
            upperdir = None
            upperdir_reason = (
                "workspace upperdir allocation was not completely reported"
            )
            break
        if upperdir is not None:
            upperdir += sample.metrics.disk_allocated_bytes
    return {
        **local,
        "daemon_rss_bytes": (
            daemon_rss,
            daemon_reason or _missing("daemon peak resident memory", daemon_rss),
        ),
        "daemon_cpu_time_ns": (
            None if daemon_cpu is None else daemon_cpu * 1_000,
            daemon_reason or _missing("daemon CPU counter", daemon_cpu),
        ),
        "sandbox_memory_current_bytes": (
            None if latest is None else latest.mem_cur,
            cgroup_reason
            if latest is None
            else _missing("sandbox memory", latest.mem_cur),
        ),
        "sandbox_memory_peak_bytes": (
            None if latest is None else latest.mem_cur,
            cgroup_reason
            if latest is None
            else _missing("sandbox memory", latest.mem_cur),
        ),
        "sandbox_cpu_time_ns": (
            None
            if latest is None or latest.cpu_usec is None
            else latest.cpu_usec * 1_000,
            cgroup_reason
            if latest is None
            else _missing("sandbox CPU counter", latest.cpu_usec),
        ),
        "sandbox_block_read_bytes": (
            None if latest is None else latest.io_rbytes,
            cgroup_reason
            if latest is None
            else _missing("sandbox block-read counter", latest.io_rbytes),
        ),
        "sandbox_block_write_bytes": (
            None if latest is None else latest.io_wbytes,
            cgroup_reason
            if latest is None
            else _missing("sandbox block-write counter", latest.io_wbytes),
        ),
        "layerstack_bytes": (stack_value, stack_reason),
        "upperdir_bytes": (upperdir, upperdir_reason),
    }


def _workspace_metrics(
    workspace: Path,
) -> dict[str, tuple[int | None, str | None]]:
    logical = allocated = files = 0
    allocated_available = True
    pending = [native_filesystem_path(workspace)]
    seen = 0
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                seen += 1
                if seen > 1_000_000:
                    raise RuntimeError(
                        "workspace resource walk exceeded its fixed entry cap"
                    )
                metadata = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(metadata.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(metadata.st_mode):
                    files += 1
                    logical += metadata.st_size
                    blocks = getattr(metadata, "st_blocks", None)
                    if blocks is None:
                        allocated_available = False
                    elif allocated_available:
                        allocated += blocks * 512
    return {
        "workspace_logical_bytes": (logical, None),
        "workspace_allocated_bytes": (
            allocated if allocated_available else None,
            (
                None
                if allocated_available
                else "host filesystem metadata does not expose allocated block counts"
            ),
        ),
        "workspace_file_count": (files, None),
    }


def _dynamic_local_metrics(
    workspace: Path,
) -> dict[str, tuple[int | None, str | None]]:
    rss, rss_reason = _runner_rss()
    return {
        "runner_rss_bytes": (rss, rss_reason),
        "host_free_bytes": (
            shutil.disk_usage(native_filesystem_path(workspace)).free,
            None,
        ),
    }


def _combine_local_metrics(
    dynamic: dict[str, tuple[int | None, str | None]] | BaseException,
    workspace: (dict[str, tuple[int | None, str | None]] | BaseException | None),
) -> dict[str, tuple[int | None, str | None]]:
    if isinstance(dynamic, BaseException):
        reason = _collector_failure("host dynamic", dynamic)
        values = {
            metric_id: (None, reason)
            for metric_id in ("runner_rss_bytes", "host_free_bytes")
        }
    else:
        values = dict(dynamic)
    if workspace is None:
        workspace = RuntimeError("workspace metrics were not initialized")
    if isinstance(workspace, BaseException):
        reason = _collector_failure("host workspace", workspace)
        values.update(
            {
                metric_id: (None, reason)
                for metric_id in (
                    "workspace_logical_bytes",
                    "workspace_allocated_bytes",
                    "workspace_file_count",
                )
            }
        )
    else:
        values.update(workspace)
    return values


def _runner_rss() -> tuple[int | None, str | None]:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(ProcessMemoryCounters),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            handle = kernel32.GetCurrentProcess()
            succeeded = psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            )
            if succeeded and counters.WorkingSetSize > 0:
                return int(counters.WorkingSetSize), None
        except (AttributeError, OSError, ValueError):
            pass
        return None, "Windows process resident memory observation was unavailable"
    try:
        completed = subprocess.run(
            ["/bin/ps", "-o", "rss=", "-p", str(os.getpid())],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
            text=True,
        )
        value = int(completed.stdout.strip()) if completed.returncode == 0 else 0
        if value > 0:
            return value * 1024, None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None, "runner resident memory observation was unavailable"


def _reading(
    metric_id: str,
    offset: int,
    *,
    scheduled_offset: int,
    collection_started_offset: int | None,
    collection_completed_offset: int | None,
    value: int | None,
    reason: str | None,
    sampled: bool,
) -> dict[str, Any]:
    unit, scope, kind, aggregation, source = _METRICS[metric_id]
    reading: dict[str, Any] = {
        "schema_version": 1,
        "metric_id": metric_id,
        "metric_semantic_revision": _METRIC_SEMANTIC_REVISIONS.get(metric_id, 1),
        "unit": unit,
        "scope": scope,
        "kind": kind,
        "aggregation": aggregation,
        "source": source,
        "monotonic_offset_ns": offset,
        "scheduled_monotonic_offset_ns": scheduled_offset,
        "collection_started_monotonic_offset_ns": collection_started_offset,
        "collection_completed_monotonic_offset_ns": collection_completed_offset,
        "value": (
            {"availability": "available", "value": float(value)}
            if value is not None
            else {
                "availability": "unavailable",
                "source": source,
                "reason": reason or "product did not report the metric",
            }
        ),
    }
    if sampled:
        reading["sampled"] = True
    return reading


def _missing(label: str, value: int | None) -> str | None:
    return None if value is not None else f"{label} was not reported by the product"


def _collector_failure(label: str, error: BaseException) -> str:
    return f"{label} resource collection failed: {type(error).__name__}"
