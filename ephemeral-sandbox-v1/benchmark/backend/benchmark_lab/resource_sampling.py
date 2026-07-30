from __future__ import annotations

import asyncio
import os
import shutil
import stat
import subprocess
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .observability import CgroupView, SnapshotView
from .product import ProductAccess


ResourceSink = Callable[[dict[str, Any]], Awaitable[None]]

_METRICS = {
    "runner_rss_bytes": ("bytes", "runner", "gauge", "maximum", "macos.ps"),
    "daemon_rss_bytes": (
        "bytes", "daemon", "gauge", "maximum",
        "product_observability.snapshot.daemon.daemon_pid",
    ),
    "daemon_cpu_time_ns": (
        "nanoseconds", "daemon", "monotonic_counter", "delta",
        "product_observability.snapshot.daemon.daemon_pid",
    ),
    "sandbox_memory_current_bytes": (
        "bytes", "sandbox", "gauge", "maximum",
        "product_observability.cgroup.docker_engine.memory.current",
    ),
    "sandbox_memory_peak_bytes": (
        "bytes", "sandbox", "gauge", "maximum",
        "product_observability.cgroup.docker_engine.memory.current.sampled_peak",
    ),
    "sandbox_cpu_time_ns": (
        "nanoseconds", "sandbox", "monotonic_counter", "delta",
        "product_observability.cgroup.docker_engine.cpu.usage_usec",
    ),
    "sandbox_block_read_bytes": (
        "bytes", "sandbox", "monotonic_counter", "delta",
        "product_observability.cgroup.docker_engine.io.read_bytes",
    ),
    "sandbox_block_write_bytes": (
        "bytes", "sandbox", "monotonic_counter", "delta",
        "product_observability.cgroup.docker_engine.io.write_bytes",
    ),
    "workspace_logical_bytes": (
        "bytes", "workspace", "gauge", "maximum", "filesystem.metadata",
    ),
    "workspace_allocated_bytes": (
        "bytes", "workspace", "gauge", "maximum", "filesystem.metadata",
    ),
    "workspace_file_count": (
        "count", "workspace", "gauge", "maximum", "filesystem.metadata",
    ),
    "layerstack_bytes": (
        "bytes", "layerstack", "gauge", "maximum",
        "product_observability.snapshot.stack.storage_allocated_bytes",
    ),
    "upperdir_bytes": (
        "bytes", "layerstack", "gauge", "maximum",
        "product_observability.snapshot.workspaces.disk_allocated_bytes.sum",
    ),
    "host_free_bytes": (
        "bytes", "host_volume", "gauge", "minimum", "host_volume.df_posix",
    ),
}


def resource_metric_source(metric_id: str) -> str:
    return _METRICS[metric_id][4]


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
    ) -> None:
        if not 10 <= interval_ms <= 60_000:
            raise ValueError("resource sample interval is invalid")
        self._product = product
        self._sandbox = sandbox
        self._workspace = workspace
        self._cell_id = cell_id
        self._trial_id = trial_id
        self._interval = interval_ms / 1000
        self._campaign_started_ns = campaign_started_ns
        self._sink = sink
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._sample_index = 0

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("resource sampler was already started")
        await self._sample(sampled=False)
        self._task = asyncio.create_task(self._loop(), name=f"resources:{self._trial_id}")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop.set()
        await self._task
        self._task = None
        await self._sample(sampled=False)

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except TimeoutError:
                await self._sample(sampled=True)
                continue
            return

    async def _sample(self, *, sampled: bool) -> None:
        index = self._sample_index
        self._sample_index += 1
        local, cgroup, snapshot = await asyncio.gather(
            asyncio.to_thread(_local_metrics, self._workspace),
            self._product.observe_cgroup(
                self._sandbox, request_id=f"{self._trial_id}.observe.cgroup.{index}"
            ),
            self._product.observe_snapshot(
                self._sandbox, request_id=f"{self._trial_id}.observe.snapshot.{index}"
            ),
        )
        offset = max(0, time.monotonic_ns() - self._campaign_started_ns)
        values = _resource_values(local, cgroup, snapshot)
        for metric_id in _METRICS:
            value, reason = values[metric_id]
            await self._sink(
                {
                    "cell_id": self._cell_id,
                    "trial_id": self._trial_id,
                    "request_id": None,
                    "reading": _reading(
                        metric_id, offset, value=value, reason=reason, sampled=sampled
                    ),
                }
            )


def _resource_values(
    local: dict[str, tuple[int | None, str | None]],
    cgroup: CgroupView,
    snapshot: SnapshotView,
) -> dict[str, tuple[int | None, str | None]]:
    latest = cgroup.series[-1].metrics
    daemon_reason = (
        f"product snapshot exposed container PID {snapshot.daemon.daemon_pid} "
        "without a host PID namespace and process start identity"
    )
    stack_value = snapshot.stack.storage_allocated_bytes if snapshot.stack else None
    stack_reason = (
        None if stack_value is not None else "LayerStack allocated storage was not reported by the product"
    )
    upperdir: int | None = 0
    upperdir_reason: str | None = None
    if snapshot.availability == "partial":
        upperdir = None
        upperdir_reason = "product snapshot was partial"
    for workspace in snapshot.workspaces:
        sample = workspace.resources.latest
        if (
            sample is None
            or sample.metrics.disk_allocated_bytes is None
            or sample.metrics.disk_truncated is True
            or sample.metrics.record_truncated_bytes is not None
        ):
            upperdir = None
            upperdir_reason = "workspace upperdir allocation was not completely reported"
            break
        if upperdir is not None:
            upperdir += sample.metrics.disk_allocated_bytes
    return {
        **local,
        "daemon_rss_bytes": (None, daemon_reason),
        "daemon_cpu_time_ns": (None, daemon_reason),
        "sandbox_memory_current_bytes": (latest.mem_cur, _missing("sandbox memory", latest.mem_cur)),
        "sandbox_memory_peak_bytes": (latest.mem_cur, _missing("sandbox memory", latest.mem_cur)),
        "sandbox_cpu_time_ns": (
            None if latest.cpu_usec is None else latest.cpu_usec * 1_000,
            _missing("sandbox CPU counter", latest.cpu_usec),
        ),
        "sandbox_block_read_bytes": (
            latest.io_rbytes, _missing("sandbox block-read counter", latest.io_rbytes)
        ),
        "sandbox_block_write_bytes": (
            latest.io_wbytes, _missing("sandbox block-write counter", latest.io_wbytes)
        ),
        "layerstack_bytes": (stack_value, stack_reason),
        "upperdir_bytes": (upperdir, upperdir_reason),
    }


def _local_metrics(workspace: Path) -> dict[str, tuple[int | None, str | None]]:
    rss, rss_reason = _runner_rss()
    logical = allocated = files = 0
    pending = [workspace]
    seen = 0
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                seen += 1
                if seen > 1_000_000:
                    raise RuntimeError("workspace resource walk exceeded its fixed entry cap")
                metadata = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(metadata.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(metadata.st_mode):
                    files += 1
                    logical += metadata.st_size
                    allocated += getattr(metadata, "st_blocks", 0) * 512
    return {
        "runner_rss_bytes": (rss, rss_reason),
        "workspace_logical_bytes": (logical, None),
        "workspace_allocated_bytes": (allocated, None),
        "workspace_file_count": (files, None),
        "host_free_bytes": (shutil.disk_usage(workspace).free, None),
    }


def _runner_rss() -> tuple[int | None, str | None]:
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
    value: int | None,
    reason: str | None,
    sampled: bool,
) -> dict[str, Any]:
    unit, scope, kind, aggregation, source = _METRICS[metric_id]
    reading: dict[str, Any] = {
        "schema_version": 1,
        "metric_id": metric_id,
        "metric_semantic_revision": 1,
        "unit": unit,
        "scope": scope,
        "kind": kind,
        "aggregation": aggregation,
        "source": source,
        "monotonic_offset_ns": offset,
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
