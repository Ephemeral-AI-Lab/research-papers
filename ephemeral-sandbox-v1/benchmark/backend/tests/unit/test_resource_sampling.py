import asyncio
import os
import time
from pathlib import Path
from types import MethodType

import pytest

from benchmark_lab import resource_sampling
from benchmark_lab.observability import parse_cgroup, parse_snapshot
from benchmark_lab.resource_sampling import (
    ResourceSamplingError,
    TrialResourceSampler,
    WorkspaceMetricCache,
    _runner_rss,
)

METRIC_IDS = (
    "runner_rss_bytes",
    "daemon_rss_bytes",
    "daemon_cpu_time_ns",
    "sandbox_memory_current_bytes",
    "sandbox_memory_peak_bytes",
    "sandbox_cpu_time_ns",
    "sandbox_block_read_bytes",
    "sandbox_block_write_bytes",
    "workspace_logical_bytes",
    "workspace_allocated_bytes",
    "workspace_file_count",
    "layerstack_bytes",
    "upperdir_bytes",
    "host_free_bytes",
)


def _test_records(index: int) -> list[dict]:
    return [
        {
            "cell_id": "cell-1",
            "trial_id": "trial-1",
            "request_id": None,
            "reading": {
                "metric_id": metric_id,
                "monotonic_offset_ns": index,
                "value": {
                    "availability": "unavailable",
                    "source": "test",
                    "reason": "test collector",
                },
            },
        }
        for metric_id in METRIC_IDS
    ]


class FastProduct:
    def __init__(self) -> None:
        self.cgroup_timestamp = 0
        self.snapshot_timestamp = 0
        self.daemon_calls = 0
        self.timestamp_base_ms = time.time_ns() // 1_000_000 + 10_000

    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        self.cgroup_timestamp += 1
        return parse_cgroup(
            {
                "view": "cgroup",
                "scope": "sandbox",
                "availability": "available",
                "errors": [],
                "topology": {
                    "daemon": {
                        "available": True,
                        "pid": 7,
                        "resident_memory_bytes": 1024,
                        "peak_resident_memory_bytes": 2048,
                        "cpu_time_us": 1,
                    }
                },
                "series": [
                    {
                        "ts": self.timestamp_base_ms + self.cgroup_timestamp,
                        "sample_delta_ms": None,
                        "metrics": {
                            "metrics_source": "docker_engine",
                            "cpu_usec": 1,
                            "mem_cur": 1024,
                            "mem_max": 2048,
                            "io_rbytes": 0,
                            "io_wbytes": 0,
                        },
                        "deltas": {},
                    }
                ],
            }
        )

    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        self.snapshot_timestamp += 1
        return parse_snapshot(
            {
                "sandbox_id": sandbox,
                "lifecycle_state": "ready",
                "availability": "available",
                "sampled_at_unix_ms": (
                    self.timestamp_base_ms + self.snapshot_timestamp
                ),
                "errors": [],
                "daemon": {
                    "daemon_pid": 7,
                    "runtime_dir": "/run/fake",
                    "event_store": {
                        "dropped_storage": 0,
                        "dropped_oversized": 0,
                        "truncated_records": 0,
                    },
                },
                "resources": {"latest": None, "history": []},
                "workspaces": [
                    {
                        "workspace_id": "workspace-1",
                        "lifecycle_state": "active",
                        "finalization_state": "active",
                        "network_profile": "shared",
                        "finalize_policy": "no_op",
                        "layers": {"base_root_hash": None, "layer_count": 1},
                        "namespace_fd_count": 0,
                        "resources": {
                            "latest": {
                                "ts": (
                                    self.timestamp_base_ms + self.snapshot_timestamp
                                ),
                                "sample_delta_ms": None,
                                "metrics": {
                                    "disk_allocated_bytes": 8192,
                                    "disk_truncated": False,
                                },
                                "deltas": {},
                            },
                            "history": [],
                        },
                        "active_namespace_executions": [],
                    }
                ],
                "stack": None,
            },
            sandbox,
        )

    async def observe_daemon(self, sandbox: str, *, request_id: str):
        self.daemon_calls += 1
        raise AssertionError("resource sampling must reuse cgroup.topology.daemon")


class DelayedBoundaryProduct(FastProduct):
    def __init__(self) -> None:
        super().__init__()
        self.cgroup_request_ids: list[str] = []
        self.snapshot_request_ids: list[str] = []

    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        self.cgroup_request_ids.append(request_id)
        view = await super().observe_cgroup(sandbox, request_id=request_id)
        if len(self.cgroup_request_ids) == 1:
            view.availability = "partial"
            view.errors = ["resource ring is not available yet"]
            view.series = []
        return view

    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        self.snapshot_request_ids.append(request_id)
        view = await super().observe_snapshot(sandbox, request_id=request_id)
        if len(self.snapshot_request_ids) == 1:
            view.workspaces[0].resources.latest = None
        return view


class StalePostBoundaryProduct(FastProduct):
    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        view = await super().observe_cgroup(sandbox, request_id=request_id)
        if self.cgroup_timestamp == 2:
            view.series[-1].ts = self.timestamp_base_ms + 1
        return view

    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        view = await super().observe_snapshot(sandbox, request_id=request_id)
        if self.snapshot_timestamp == 2:
            view.workspaces[0].resources.latest.ts = self.timestamp_base_ms + 1
        return view


class PreThresholdPostBoundaryProduct(FastProduct):
    def __init__(self) -> None:
        super().__init__()
        self.timestamp_base_ms = time.time_ns() // 1_000_000 - 10_000
        self.cgroup_emitted_ms: list[int] = []
        self.workspace_emitted_ms: list[int] = []

    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        view = await super().observe_cgroup(sandbox, request_id=request_id)
        if self.cgroup_timestamp >= 3:
            view.series[-1].ts = time.time_ns() // 1_000_000 + 10_000
        self.cgroup_emitted_ms.append(view.series[-1].ts)
        return view

    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        view = await super().observe_snapshot(sandbox, request_id=request_id)
        if self.snapshot_timestamp >= 3:
            timestamp = time.time_ns() // 1_000_000 + 10_000
            view.sampled_at_unix_ms = timestamp
            view.workspaces[0].resources.latest.ts = timestamp
        self.workspace_emitted_ms.append(view.workspaces[0].resources.latest.ts)
        return view


class PendingBoundaryProduct(FastProduct):
    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        view = await super().observe_cgroup(sandbox, request_id=request_id)
        view.availability = "partial"
        view.errors = ["resource ring is not available yet"]
        view.series = []
        return view


class WorkspaceAppearsProduct(FastProduct):
    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        view = await super().observe_snapshot(sandbox, request_id=request_id)
        if self.snapshot_timestamp < 3:
            view.workspaces = []
        return view


class MalformedEmbeddedDaemonProduct(FastProduct):
    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        view = await super().observe_cgroup(sandbox, request_id=request_id)
        view.topology["daemon"]["cpu_time_us"] = "invalid"
        return view


class BlockingPeriodicProduct(FastProduct):
    def __init__(self) -> None:
        super().__init__()
        self.periodic_started = asyncio.Event()
        self.periodic_release = asyncio.Event()
        self.final_boundary_started_ns: int | None = None

    async def observe_cgroup(self, sandbox: str, *, request_id: str):
        if request_id.endswith(".observe.cgroup.1"):
            self.periodic_started.set()
            await self.periodic_release.wait()
        elif request_id.endswith(".observe.cgroup.2.boundary.0"):
            self.final_boundary_started_ns = time.monotonic_ns()
        return await super().observe_cgroup(sandbox, request_id=request_id)

    async def observe_snapshot(self, sandbox: str, *, request_id: str):
        if request_id.endswith(".observe.snapshot.1"):
            self.periodic_started.set()
            await self.periodic_release.wait()
        return await super().observe_snapshot(sandbox, request_id=request_id)


@pytest.mark.asyncio
async def test_mandatory_and_periodic_samples_reuse_exact_cgroup_daemon(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []
    product = FastProduct()
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
    )

    await asyncio.wait_for(sampler.start(), timeout=1)
    async with asyncio.timeout(1):
        while product.cgroup_timestamp < 2:
            await asyncio.sleep(0.01)
    await asyncio.wait_for(sampler.stop(), timeout=1)

    assert product.daemon_calls == 0
    assert product.cgroup_timestamp >= 3
    daemon_readings = [
        item["reading"]
        for batch in batches
        for item in batch
        if item["reading"]["metric_id"] == "daemon_rss_bytes"
    ]
    assert len(daemon_readings) >= 3
    assert all(
        reading["source"]
        == "product_observability.cgroup.topology.daemon.peak_resident_memory_bytes"
        and reading["value"] == {"availability": "available", "value": 2048.0}
        for reading in daemon_readings
    )


@pytest.mark.asyncio
async def test_malformed_embedded_daemon_is_never_used_as_metric_data(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []
    product = MalformedEmbeddedDaemonProduct()
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
    )

    await sampler.start()
    await sampler.stop()

    assert product.daemon_calls == 0
    for batch in batches:
        daemon_values = [
            item["reading"]["value"]
            for item in batch
            if item["reading"]["metric_id"]
            in {"daemon_rss_bytes", "daemon_cpu_time_ns"}
        ]
        assert len(daemon_values) == 2
        assert all(
            value["availability"] == "unavailable"
            and "ObservabilityError" in value["reason"]
            for value in daemon_values
        )


@pytest.mark.asyncio
async def test_sampler_discards_transient_boundary_polls(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []
    product = DelayedBoundaryProduct()
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
    )

    await sampler.start()
    await sampler.stop()

    assert len(batches) == 2
    assert len(product.cgroup_request_ids) == 3
    assert len(product.snapshot_request_ids) == 3
    assert all(".boundary." in item for item in product.cgroup_request_ids)
    for metric_id in (
        "sandbox_cpu_time_ns",
        "sandbox_block_read_bytes",
        "sandbox_block_write_bytes",
        "upperdir_bytes",
    ):
        readings = [
            next(
                item["reading"]
                for item in batch
                if item["reading"]["metric_id"] == metric_id
            )
            for batch in batches
        ]
        assert all(
            reading["value"]["availability"] == "available" for reading in readings
        )


@pytest.mark.asyncio
async def test_sampler_waits_for_post_boundary_newer_than_baseline(
    tmp_path: Path,
) -> None:
    product = StalePostBoundaryProduct()
    batches: list[list[dict]] = []
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
    )

    await sampler.start()
    await sampler.stop()

    assert len(batches) == 2
    assert product.cgroup_timestamp == 3
    assert product.snapshot_timestamp == 3


@pytest.mark.asyncio
async def test_sampler_delays_first_post_response_boundary_poll(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = FastProduct()
    delays: list[tuple[float, int]] = []
    batches: list[list[dict]] = []
    original_sleep = asyncio.sleep

    async def tracked_sleep(delay: float) -> None:
        delays.append((delay, product.cgroup_timestamp))
        await original_sleep(0)

    async def sink(batch: list[dict]) -> None:
        batches.append(batch)

    monkeypatch.setattr(resource_sampling.asyncio, "sleep", tracked_sleep)
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=sink,
    )

    await sampler.start()
    assert delays == []
    await sampler.stop()

    assert delays[0][0] == pytest.approx(
        resource_sampling._POST_BOUNDARY_FIRST_POLL_DELAY_SECONDS,
        abs=0.01,
    )
    assert delays[0][1] == 1
    assert product.cgroup_timestamp == 2
    assert product.snapshot_timestamp == 2
    assert len(batches) == 2


@pytest.mark.asyncio
async def test_sampler_rejects_post_sample_taken_before_response_threshold(
    tmp_path: Path,
) -> None:
    product = PreThresholdPostBoundaryProduct()
    batches: list[list[dict]] = []
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
    )

    await sampler.start()
    await sampler.stop()

    assert len(batches) == 2
    assert product.cgroup_timestamp == 3
    assert product.snapshot_timestamp == 3
    assert sampler._post_response_threshold_ms is not None
    assert (
        product.cgroup_emitted_ms[0]
        < product.cgroup_emitted_ms[1]
        <= sampler._post_response_threshold_ms
        < product.cgroup_emitted_ms[2]
    )
    assert (
        product.workspace_emitted_ms[0]
        < product.workspace_emitted_ms[1]
        <= sampler._post_response_threshold_ms
        < product.workspace_emitted_ms[2]
    )


@pytest.mark.asyncio
async def test_workspace_create_post_boundary_waits_for_created_workspace(
    tmp_path: Path,
) -> None:
    product = WorkspaceAppearsProduct()
    batches: list[list[dict]] = []
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0, result=batches.append(batch)),
        expected_post_workspace_count=1,
    )

    await sampler.start()
    await sampler.stop()

    assert len(batches) == 2
    assert product.cgroup_timestamp == 3
    assert product.snapshot_timestamp == 3
    upperdir = [
        next(
            item["reading"]
            for item in batch
            if item["reading"]["metric_id"] == "upperdir_bytes"
        )
        for batch in batches
    ]
    assert [reading["value"]["value"] for reading in upperdir] == [0.0, 8192.0]


@pytest.mark.asyncio
async def test_sampler_fails_closed_when_boundary_never_becomes_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(resource_sampling, "_BOUNDARY_READINESS_TIMEOUT_SECONDS", 0.0)
    sampler = TrialResourceSampler(
        product=PendingBoundaryProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0),
    )

    with pytest.raises(ResourceSamplingError, match="readiness timed out"):
        await sampler.start()


@pytest.mark.asyncio
async def test_sampler_uses_fixed_deadlines_and_defers_ordered_persistence(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []

    async def sink(batch: list[dict]) -> None:
        batches.append(batch)

    started_ns = time.monotonic_ns()
    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=started_ns,
        sink=sink,
    )
    await sampler.start()
    await asyncio.sleep(0.24)

    # Collection runs independently, but journal persistence is deferred until
    # the explicit trial-boundary stop.
    assert batches == []
    await sampler.stop()

    assert len(batches) >= 4
    assert all(len(batch) == 14 for batch in batches)
    periodic = [
        batch[0]["reading"]["scheduled_monotonic_offset_ns"]
        for batch in batches
        if batch[0]["reading"].get("sampled") is True
    ]
    assert len(periodic) >= 2
    assert 50_000_000 <= periodic[1] - periodic[0] <= 175_000_000
    offsets = [batch[0]["reading"]["monotonic_offset_ns"] for batch in batches]
    assert offsets == sorted(offsets)


@pytest.mark.asyncio
async def test_sampler_records_saturation_as_explicit_unavailability(
    tmp_path: Path,
) -> None:
    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0),
    )
    release = asyncio.Event()

    # Keep the collector implementation tiny while deterministically occupying
    # the single expensive-sample admission slot.
    async def blocked(self, *, index: int, sampled: bool, scheduled_ns: int):
        await release.wait()
        return _test_records(index)

    sampler._sample = MethodType(blocked, sampler)
    for _ in range(2):
        sampler._launch(sampled=True)
    await asyncio.sleep(0)

    saturated = await sampler._samples[1]
    assert len(saturated) == 14
    assert all(
        item["reading"]["value"]["availability"] == "unavailable"
        and "concurrency cap" in item["reading"]["value"]["reason"]
        and item["reading"]["collection_started_monotonic_offset_ns"] is None
        for item in saturated
    )
    release.set()
    await sampler._samples[0]


@pytest.mark.asyncio
async def test_sampler_awaits_baseline_before_start_returns(tmp_path: Path) -> None:
    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0),
    )
    entered = asyncio.Event()
    release = asyncio.Event()

    async def controlled(
        self, *, index: int, sampled: bool, scheduled_ns: int
    ) -> list[dict]:
        if index == 0:
            entered.set()
            await release.wait()
        return _test_records(index)

    sampler._sample = MethodType(controlled, sampler)
    starting = asyncio.create_task(sampler.start())
    await entered.wait()
    assert not starting.done()
    release.set()
    await starting
    await sampler.stop()


@pytest.mark.asyncio
async def test_stop_serializes_boundary_after_active_periodic_collector(
    tmp_path: Path,
) -> None:
    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=10,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0),
    )
    periodic_started = asyncio.Event()
    release_periodic = asyncio.Event()
    active = 0
    maximum_active = 0
    actual_samples: list[tuple[int, bool]] = []

    async def controlled(
        self, *, index: int, sampled: bool, scheduled_ns: int
    ) -> list[dict]:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        actual_samples.append((index, sampled))
        try:
            if sampled:
                periodic_started.set()
                await release_periodic.wait()
            return _test_records(index)
        finally:
            active -= 1

    sampler._sample = MethodType(controlled, sampler)
    await sampler.start()
    await periodic_started.wait()
    stopping = asyncio.create_task(sampler.stop())
    await asyncio.sleep(0)

    assert actual_samples == [(0, False), (1, True)]
    assert not stopping.done()
    release_periodic.set()
    await stopping

    assert maximum_active == 1
    assert len([sample for sample in actual_samples if sample[1] is False]) == 2


@pytest.mark.asyncio
async def test_stop_overlaps_freshness_wait_with_active_periodic_drain(
    tmp_path: Path,
) -> None:
    product = BlockingPeriodicProduct()
    sampler = TrialResourceSampler(
        product=product,
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=10,
        campaign_started_ns=time.monotonic_ns(),
        sink=lambda batch: asyncio.sleep(0),
    )

    await sampler.start()
    await asyncio.wait_for(product.periodic_started.wait(), timeout=1)
    stop_started_ns = time.monotonic_ns()
    stopping = asyncio.create_task(sampler.stop())

    # Keep the admitted periodic collector active beyond the complete
    # post-response freshness wait. The mandatory product query must launch
    # promptly after the collector drains, without starting before 100 ms.
    await asyncio.sleep(0.15)
    periodic_released_ns = time.monotonic_ns()
    product.periodic_release.set()
    await asyncio.wait_for(stopping, timeout=1)

    assert product.final_boundary_started_ns is not None
    assert product.final_boundary_started_ns - stop_started_ns >= int(
        resource_sampling._POST_BOUNDARY_FIRST_POLL_DELAY_SECONDS * 1_000_000_000
    )
    assert product.final_boundary_started_ns - periodic_released_ns < 75_000_000


@pytest.mark.asyncio
async def test_workspace_tree_is_cached_but_dynamic_metrics_are_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    counts = {"workspace": 0, "dynamic": 0}

    def workspace_metrics(path: Path) -> dict:
        counts["workspace"] += 1
        return {
            "workspace_logical_bytes": (1, None),
            "workspace_allocated_bytes": (1, None),
            "workspace_file_count": (1, None),
        }

    def dynamic_metrics(path: Path) -> dict:
        counts["dynamic"] += 1
        return {
            "runner_rss_bytes": (1, None),
            "host_free_bytes": (1, None),
        }

    monkeypatch.setattr(resource_sampling, "_workspace_metrics", workspace_metrics)
    monkeypatch.setattr(resource_sampling, "_dynamic_local_metrics", dynamic_metrics)
    cache = WorkspaceMetricCache()
    for trial in ("trial-1", "trial-2"):
        sampler = TrialResourceSampler(
            product=FastProduct(),
            sandbox="sandbox-1",
            workspace=tmp_path,
            cell_id="cell-1",
            trial_id=trial,
            interval_ms=100,
            campaign_started_ns=time.monotonic_ns(),
            sink=lambda batch: asyncio.sleep(0),
            workspace_cache=cache,
        )
        await sampler.start()
        await sampler.stop()

    assert counts == {"workspace": 1, "dynamic": 4}


@pytest.mark.asyncio
async def test_upperdir_delta_reading_uses_complete_product_workspace_scope(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []

    async def sink(batch: list[dict]) -> None:
        batches.append(batch)

    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=sink,
    )
    await sampler.start()
    await sampler.stop()

    readings = [
        next(
            item["reading"]
            for item in batch
            if item["reading"]["metric_id"] == "upperdir_bytes"
        )
        for batch in batches
    ]
    assert len(readings) == 2
    assert all(
        reading["metric_semantic_revision"] == 2
        and reading["scope"] == "workspace"
        and reading["kind"] == "gauge"
        and reading["aggregation"] == "delta"
        and reading["source"]
        == "product_observability.snapshot.workspaces.disk_allocated_bytes.sum"
        and reading["value"] == {"availability": "available", "value": 8192.0}
        for reading in readings
    )


@pytest.mark.asyncio
async def test_create_sandbox_counter_deltas_are_explicitly_inapplicable(
    tmp_path: Path,
) -> None:
    batches: list[list[dict]] = []

    async def sink(batch: list[dict]) -> None:
        batches.append(batch)

    sampler = TrialResourceSampler(
        product=FastProduct(),
        sandbox="sandbox-1",
        workspace=tmp_path,
        cell_id="cell-1",
        trial_id="trial-1",
        interval_ms=100,
        campaign_started_ns=time.monotonic_ns(),
        sink=sink,
        counter_delta_applicable=False,
    )
    await sampler.start()
    await sampler.stop()

    for batch in batches:
        readings = {item["reading"]["metric_id"]: item["reading"] for item in batch}
        for metric_id in (
            "daemon_cpu_time_ns",
            "sandbox_cpu_time_ns",
            "sandbox_block_read_bytes",
            "sandbox_block_write_bytes",
        ):
            value = readings[metric_id]["value"]
            assert value["availability"] == "unavailable"
            assert "pre-create baseline cannot exist" in value["reason"]
        assert (
            readings["sandbox_memory_current_bytes"]["value"]["availability"]
            == "available"
        )


@pytest.mark.skipif(os.name != "nt", reason="Windows process API")
def test_windows_runner_rss_uses_full_width_process_handle() -> None:
    value, reason = _runner_rss()
    assert reason is None
    assert value is not None and value > 0
