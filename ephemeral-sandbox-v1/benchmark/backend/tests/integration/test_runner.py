import asyncio
import copy
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import benchmark_lab.runner as runner_module
from benchmark_lab.artifacts import ArtifactId, ArtifactStore
from benchmark_lab.observability import parse_cgroup, parse_daemon, parse_snapshot
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.reports import RunCorpus
from benchmark_lab.runner import (
    BatchTiming,
    CampaignError,
    CampaignRunner,
    TrialContext,
)
from benchmark_lab.transport import GatewayTransportError, TimedGatewayResponse

ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "tests/fixtures/golden/rust/quick-smoke-completed"


def _roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def _artifact(name: str) -> dict:
    return json.loads((GOLDEN / name).read_text())["data"]


def test_cell_workspaces_are_materialized_in_one_distinct_bounded_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    runner._profiles = {"paper": {"id": "paper"}}
    runner._seed = 7
    run_path = roots.runs / "run-batch-workspaces"
    run_path.mkdir()
    cells = [
        {
            "cell_id": f"sha256:{index:064x}",
            "operation": {
                "operation": "create_sandbox",
                "cell": {"workspace_profile": "paper"},
            },
        }
        for index in range(3)
    ]
    calls: list[tuple[list[Path], int]] = []

    def materialize(
        fixtures_root: Path,
        workspaces: list[Path],
        profile: dict,
        seed: int,
        *,
        max_workers: int,
    ) -> dict:
        assert fixtures_root == roots.fixtures
        assert profile == runner._profiles["paper"]
        assert seed == runner._seed
        calls.append((list(workspaces), max_workers))
        for workspace in workspaces:
            (workspace / "fixture-manifest.json").write_text("{}")
        return {}

    monkeypatch.setattr(runner_module, "materialize_workspaces", materialize)

    runner._prepare_cell_workspaces(run_path, cells)

    assert len(calls) == 1
    workspaces, max_workers = calls[0]
    assert max_workers == 4
    assert len(workspaces) == len(cells)
    assert len({workspace.resolve() for workspace in workspaces}) == len(cells)
    assert runner._prepared_cell_workspaces == {
        cell["cell_id"]: run_path / f"cell-{cell['cell_id'][-16:]}" for cell in cells
    }
    assert all(
        not (workspace / "fixture-manifest.json").exists() for workspace in workspaces
    )


def _single_file_read_plan() -> dict:
    plan = copy.deepcopy(_artifact("expanded-plan.json"))
    cell = next(item for item in plan["cells"] if item["operation_id"] == "file_read")
    cell["protocol"]["warmups"] = 0
    cell["protocol"]["measured_trials"] = 1
    plan["cells"] = [cell]
    block = next(
        item for item in plan["execution_blocks"] if cell["cell_id"] in item["cell_ids"]
    )
    block["cell_ids"] = [cell["cell_id"]]
    plan["execution_blocks"] = [block]
    plan["estimates"] = {
        "cell_count": 1,
        "trial_batch_count": 1,
        "issued_operation_request_count": 1,
    }
    return plan


def _two_block_file_read_plan() -> dict:
    plan = _single_file_read_plan()
    first = plan["cells"][0]
    second = copy.deepcopy(first)
    second["cell_id"] = f"sha256:{'f' * 64}"
    second_block = copy.deepcopy(plan["execution_blocks"][0])
    second_block["block_id"] = f"sha256:{'e' * 64}"
    second_block["cell_ids"] = [second["cell_id"]]
    plan["cells"] = [first, second]
    plan["execution_blocks"] = [plan["execution_blocks"][0], second_block]
    plan["estimates"] = {
        "cell_count": 2,
        "trial_batch_count": 2,
        "issued_operation_request_count": 2,
    }
    return plan


class FakeProduct:
    def __init__(self, *, fail_destroy: bool = False) -> None:
        self.files: dict[str, str] = {}
        self.fail_destroy = fail_destroy
        self.cgroup_timestamp = 0
        self.snapshot_timestamp = 0
        self.resource_timestamp_base_ms = time.time_ns() // 1_000_000 + 10_000

    async def create_sandbox(self, image, workspace, *, request_id):
        return SimpleNamespace(id="sandbox-1"), self._response(request_id, {})

    async def destroy_sandbox(self, sandbox, *, request_id):
        if self.fail_destroy:
            raise RuntimeError("simulated destroy failure")
        return self._response(request_id, {"destroyed": True})

    async def file_write(
        self, sandbox, *, session_id, path, content, timeout_ms, request_id
    ):
        self.files[path] = content
        return self._response(
            request_id,
            {"path": path, "bytes_written": len(content.encode())},
        )

    async def file_read(
        self, sandbox, *, session_id, path, offset, limit, timeout_ms, request_id
    ):
        content = self.files[path]
        return self._response(
            request_id,
            {
                "path": path,
                "content": content,
                "bytes_read": len(content.encode()),
            },
        )

    async def observe_cgroup(self, sandbox, *, request_id):
        self.cgroup_timestamp += 1
        return parse_cgroup(
            {
                "view": "cgroup",
                "scope": "sandbox",
                "availability": "available",
                "errors": [],
                "topology": {},
                "series": [
                    {
                        "ts": self.resource_timestamp_base_ms + self.cgroup_timestamp,
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

    async def observe_snapshot(self, sandbox, *, request_id):
        self.snapshot_timestamp += 1
        return parse_snapshot(
            {
                "sandbox_id": sandbox,
                "lifecycle_state": "ready",
                "availability": "available",
                "sampled_at_unix_ms": (
                    self.resource_timestamp_base_ms + self.snapshot_timestamp
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
                "workspaces": [],
                "stack": None,
            },
            sandbox,
        )

    async def observe_daemon(self, sandbox, *, request_id):
        return parse_daemon(
            {
                "view": "daemon",
                "scope": "sandbox",
                "daemon": {
                    "available": True,
                    "pid": 7,
                    "resident_memory_bytes": 1024,
                    "peak_resident_memory_bytes": 2048,
                    "cpu_time_us": 1,
                },
            }
        )

    @staticmethod
    def _response(request_id: str, value: dict) -> TimedGatewayResponse:
        return TimedGatewayResponse(request_id, 123, 17, "sha256:response", value)


class FakeGateway:
    client = object()

    def __init__(self, gateway_instance_id: str = "benchmark-gateway-fake") -> None:
        self.closed = False
        self.retained_shared_base_volumes = False
        self.finalized = False
        self.identity = SimpleNamespace(gateway_instance_id=gateway_instance_id)

    async def close(
        self,
        *,
        destroy_sandboxes_via_gateway: bool,
        retain_shared_base_volumes: bool,
    ) -> None:
        assert destroy_sandboxes_via_gateway is True
        self.retained_shared_base_volumes = retain_shared_base_volumes
        self.closed = True


def _install_fakes(
    monkeypatch, fake: FakeProduct, gateway: FakeGateway | list[FakeGateway]
) -> None:
    gateways = gateway if isinstance(gateway, list) else [gateway]
    launched = 0

    class Launcher:
        async def start(
            self,
            run_id,
            *,
            remount_sweep_width,
            readiness_via_cli,
        ):
            nonlocal launched
            assert readiness_via_cli is False
            selected = gateways[launched]
            launched += 1
            return selected

    async def environment(roots, plan):
        return {
            "schema_version": 1,
            "treatment": {
                "source_commit": "fake",
                "source_dirty": False,
                "source_diff_hash": None,
                "daemon_binary_hash": None,
                "gateway_binary_hash": None,
            },
            "host": {"monotonic_clock": "time.monotonic_ns"},
            "image_reference": "ubuntu:24.04",
            "image_digest": None,
            "workspace_root_identity": None,
            "client_cohort": "direct_client",
            "gateway_endpoint_identity": "fake",
        }

    async def cleanup_gateway_docker_resources(
        gateway_instance_ids: tuple[str, ...],
    ) -> None:
        assert gateway_instance_ids == tuple(
            item.identity.gateway_instance_id for item in gateways
        )
        for item in gateways:
            item.finalized = True

    monkeypatch.setattr(runner_module, "GatewayLauncher", lambda roots: Launcher())
    monkeypatch.setattr(
        runner_module,
        "cleanup_gateway_docker_resources",
        cleanup_gateway_docker_resources,
    )
    monkeypatch.setattr(runner_module, "ProductAccess", lambda client, runs: fake)
    monkeypatch.setattr(runner_module, "collect_environment", environment)


def test_runner_persists_verified_terminal_corpus_and_removes_workspace(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    fake = FakeProduct()
    gateway = FakeGateway()
    _install_fakes(monkeypatch, fake, gateway)
    plan = _single_file_read_plan()

    result = asyncio.run(
        CampaignRunner(roots).run(
            "run-success",
            plan,
            intent=_artifact("intent-plan.json"),
            definition_snapshot=_artifact("definition-snapshot.json"),
        )
    )

    assert result.state == "completed"
    assert result.trial_batches == 1
    assert result.issued_requests == 1
    assert gateway.closed
    assert gateway.retained_shared_base_volumes
    assert gateway.finalized
    assert not (roots.runs / "run-success").exists()
    corpus = RunCorpus.open(ArtifactStore(roots).run_path("run-success"))
    manifest_envelope = json.loads(
        (ArtifactStore(roots).run_path("run-success") / "run-manifest.json").read_text()
    )
    assert manifest_envelope["schema_version"] == 2
    assert corpus.manifest["schema_version"] == 2
    assert corpus.manifest["producer"] == {
        "implementation": "python",
        "implementation_version": "0.1.0",
        "source_commit": "fake",
    }
    assert corpus.manifest["treatment"] == corpus.environment["treatment"]
    assert corpus.manifest["correctness"] == "pass"
    definition_reference = (
        ArtifactStore(roots)
        .download_artifact("run-success", ArtifactId.DEFINITION_SNAPSHOT.value)
        .reference
    )
    assert (
        corpus.manifest["definition_snapshot"]["sha256"] == definition_reference.sha256
    )
    assert corpus.report is not None
    assert corpus.report.definition_snapshot_sha256 == definition_reference.sha256
    assert set(corpus.manifest["artifact_schemas"]) == {
        "run_manifest",
        "intent_plan",
        "expanded_plan",
        "definition_snapshot",
        "environment_metadata",
        "events",
        "observations",
        "bounded_evidence",
    }
    assert corpus.report.correctness_verdict == "pass"
    event_kinds = {event["data"]["kind"] for event in corpus.events.records}
    assert {
        "request_state",
        "resource_window",
        "correctness",
        "log",
    } <= event_kinds
    request_states = [
        event["data"]
        for event in corpus.events.records
        if event["data"]["kind"] == "request_state"
    ]
    assert [event["state"] for event in request_states] == [
        "waiting_at_barrier",
        "ready_at_barrier",
        "in_flight",
        "succeeded",
    ]
    assert len({event["request_id"] for event in request_states}) == 1
    resource_windows = [
        event["data"]
        for event in corpus.events.records
        if event["data"]["kind"] == "resource_window"
    ]
    assert len(resource_windows) == 28
    assert {event["metric_id"] for event in resource_windows} == {
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
    }
    correctness = [
        event["data"]
        for event in corpus.events.records
        if event["data"]["kind"] == "correctness"
    ]
    assert correctness and all(event["passed"] is True for event in correctness)
    log = next(
        event["data"]
        for event in corpus.events.records
        if event["data"]["kind"] == "log"
    )
    assert log["level"] == "info"
    assert "stdout_sha256=sha256:" in log["message"]
    trial_states = [
        event["data"]
        for event in corpus.events.records
        if event["data"]["kind"] == "trial_state"
    ]
    assert [event["state"] for event in trial_states] == ["preparing", "completed"]
    assert trial_states[0]["trial_id"] == trial_states[1]["trial_id"]
    assert trial_states[0]["warmup"] is False
    trials = [
        item["record"]["data"]
        for item in corpus.observations.records
        if item["record"]["record"] == "trial"
    ]
    assert trials[0]["latency_ns"] >= 0
    assert trials[0]["artifacts"][0]["artifact_id"].startswith("bounded_evidence_")


def test_runner_finalizes_retained_volumes_from_every_execution_block(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    fake = FakeProduct()
    gateways = [
        FakeGateway("benchmark-gateway-first"),
        FakeGateway("benchmark-gateway-second"),
    ]
    _install_fakes(monkeypatch, fake, gateways)

    result = asyncio.run(
        CampaignRunner(roots).run(
            "run-two-blocks",
            _two_block_file_read_plan(),
            intent=_artifact("intent-plan.json"),
            definition_snapshot=_artifact("definition-snapshot.json"),
        )
    )

    assert result.state == "completed"
    assert result.trial_batches == 2
    assert all(gateway.closed for gateway in gateways)
    assert all(gateway.retained_shared_base_volumes for gateway in gateways)
    assert all(gateway.finalized for gateway in gateways)
    assert not (roots.runs / "run-two-blocks").exists()


def test_runner_cleanup_failure_forces_failed_retained_run(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    fake = FakeProduct(fail_destroy=True)
    gateway = FakeGateway()
    _install_fakes(monkeypatch, fake, gateway)

    with pytest.raises(CampaignError, match="cell cleanup failed"):
        asyncio.run(
            CampaignRunner(roots).run(
                "run-cleanup-failed",
                _single_file_read_plan(),
                intent=_artifact("intent-plan.json"),
                definition_snapshot=_artifact("definition-snapshot.json"),
            )
        )

    assert gateway.closed
    assert gateway.finalized
    assert (roots.runs / "run-cleanup-failed").exists()
    store = ArtifactStore(roots)
    assert (
        store.read_envelope("run-cleanup-failed", ArtifactId.RUN_MANIFEST)["state"]
        == "failed"
    )
    corpus = RunCorpus.open(store.run_path("run-cleanup-failed"))
    assert corpus.report is not None
    assert corpus.report.state == "failed"
    assert corpus.report.correctness_verdict == "fail"


def test_retained_volume_cleanup_failure_forces_failed_retained_run(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    fake = FakeProduct()
    gateway = FakeGateway()
    _install_fakes(monkeypatch, fake, gateway)
    cleanup_calls: list[tuple[str, ...]] = []

    async def fails(gateway_instance_ids: tuple[str, ...]) -> None:
        cleanup_calls.append(gateway_instance_ids)
        raise RuntimeError("simulated retained volume cleanup failure")

    monkeypatch.setattr(runner_module, "cleanup_gateway_docker_resources", fails)

    with pytest.raises(
        CampaignError, match="retained shared-base Docker cleanup failed"
    ):
        asyncio.run(
            CampaignRunner(roots).run(
                "run-retained-cleanup-failed",
                _single_file_read_plan(),
                intent=_artifact("intent-plan.json"),
                definition_snapshot=_artifact("definition-snapshot.json"),
            )
        )

    assert cleanup_calls == [(gateway.identity.gateway_instance_id,)]
    assert gateway.closed
    assert (roots.runs / "run-retained-cleanup-failed").exists()
    manifest = ArtifactStore(roots).read_envelope(
        "run-retained-cleanup-failed", ArtifactId.RUN_MANIFEST
    )
    assert manifest["state"] == "failed"


def test_runner_clean_cancellation_removes_owned_workspace(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    fake = FakeProduct()
    gateway = FakeGateway()
    _install_fakes(monkeypatch, fake, gateway)
    runner: CampaignRunner

    async def cancel_during_operation(record: dict) -> None:
        data = record["data"]
        if (
            data["kind"] == "trial_phase"
            and data["phase"] == "operation"
            and data["state"] == "running"
        ):
            runner.cancel()

    runner = CampaignRunner(roots, event_sink=cancel_during_operation)
    result = asyncio.run(
        runner.run(
            "run-cancelled",
            _single_file_read_plan(),
            intent=_artifact("intent-plan.json"),
            definition_snapshot=_artifact("definition-snapshot.json"),
        )
    )

    assert result.state == "cancelled"
    assert gateway.closed
    assert gateway.finalized
    assert not (roots.runs / "run-cancelled").exists()
    corpus = RunCorpus.open(ArtifactStore(roots).run_path("run-cancelled"))
    assert corpus.report is not None
    assert corpus.report.state == "cancelled"
    assert corpus.manifest["state"] == "cancelled"


@pytest.mark.asyncio
async def test_request_batch_cancellation_has_bounded_grace() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._cancel = asyncio.Event()
    runner._CANCELLATION_GRACE_SECONDS = 0.01
    admitted = 0
    all_admitted = asyncio.Event()
    cancelled = 0

    async def operation() -> None:
        nonlocal admitted, cancelled
        admitted += 1
        if admitted == 3:
            all_admitted.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled += 1

    task = asyncio.create_task(runner._run_batch([operation, operation, operation]))
    await asyncio.wait_for(all_admitted.wait(), timeout=1)
    runner.cancel()

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=1)
    assert admitted == 3
    assert cancelled == 3


@pytest.mark.asyncio
async def test_request_batch_rejects_admission_after_cancellation() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._cancel = asyncio.Event()
    runner.cancel()
    admitted = False

    async def operation() -> None:
        nonlocal admitted
        admitted = True

    with pytest.raises(asyncio.CancelledError):
        await runner._run_batch([operation])
    assert admitted is False


@pytest.mark.asyncio
async def test_request_batch_records_release_after_every_task_reaches_barrier() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._cancel = asyncio.Event()
    timing = BatchTiming()
    started: list[int] = []

    async def operation() -> str:
        started.append(time.monotonic_ns())
        await asyncio.sleep(0)
        return "ok"

    result = await runner._run_batch(
        [operation, operation, operation], batch_timing=timing
    )

    assert result == ["ok", "ok", "ok"]
    assert timing.barrier_released_ns is not None
    assert timing.batch_completed_ns is not None
    assert all(value >= timing.barrier_released_ns for value in started)
    assert timing.batch_completed_ns >= max(started)


@pytest.mark.asyncio
async def test_in_flight_event_fsync_is_deferred_until_after_batch_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    store = runner._store
    store.create_run("run-deferred-states")
    runner._started_ns = time.monotonic_ns()
    append_sizes: list[int] = []
    real_append = store.append_records

    def observed_append(run_id, artifact_id, records):
        append_sizes.append(len(records))
        real_append(run_id, artifact_id, records)

    monkeypatch.setattr(store, "append_records", observed_append)
    launch_append_counts: list[int] = []

    async def operation() -> TimedGatewayResponse:
        launch_append_counts.append(len(append_sizes))
        started_ns = time.monotonic_ns()
        return TimedGatewayResponse(
            "request",
            1,
            1,
            "sha256:response",
            {},
            started_ns=started_ns,
        )

    request_ids = [f"request-{index}" for index in range(3)]
    await runner._run_request_batch(
        "run-deferred-states",
        "cell-1",
        "trial-1",
        request_ids,
        [operation, operation, operation],
        batch_timing=BatchTiming(),
    )

    # Waiting intent and the all-tasks-ready barrier share one ordered durable
    # commit before release. No in-flight fsync occurs before any operation
    # begins; six in-flight/terminal records append after all operations return.
    assert launch_append_counts == [1, 1, 1]
    assert append_sizes == [6, 6]


@pytest.mark.asyncio
async def test_pre_release_event_commit_failure_keeps_operations_behind_barrier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    store = runner._store
    store.create_run("run-pre-release-failure")
    runner._started_ns = time.monotonic_ns()
    runner._begin_trial_journal()
    await runner._event(
        "run-pre-release-failure",
        {
            "kind": "trial_phase",
            "cell_id": "cell-1",
            "trial_id": "trial-1",
            "warmup": False,
            "phase": "operation",
            "state": "running",
        },
    )
    launched = False

    async def operation() -> str:
        nonlocal launched
        launched = True
        return "unexpected"

    def fail_append(*_args, **_kwargs) -> None:
        raise OSError("simulated pre-release durability failure")

    monkeypatch.setattr(store, "append_records", fail_append)
    with pytest.raises(BaseExceptionGroup) as captured:
        await runner._run_request_batch(
            "run-pre-release-failure",
            "cell-1",
            "trial-1",
            ["request-1"],
            [operation],
            batch_timing=BatchTiming(),
        )

    durability_failures = captured.value.subgroup(OSError)
    assert durability_failures is not None
    assert any(
        str(error) == "simulated pre-release durability failure"
        for error in durability_failures.exceptions
    )
    assert launched is False
    assert [
        record["data"]["state"]
        for record in runner._trial_event_buffer
        if record["data"]["kind"] == "request_state"
    ] == ["waiting_at_barrier", "ready_at_barrier"]
    runner._end_trial_journal()


@pytest.mark.asyncio
async def test_trial_journal_groups_non_barrier_records_by_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    delivered: list[dict] = []

    async def event_sink(record: dict) -> None:
        delivered.append(record)

    runner = CampaignRunner(roots, event_sink=event_sink)
    store = runner._store
    store.create_run("run-grouped-journal")
    runner._started_ns = time.monotonic_ns()
    appends: list[tuple[ArtifactId, int]] = []
    real_append = store.append_records

    def observed_append(run_id, artifact_id, records):
        appends.append((artifact_id, len(records)))
        real_append(run_id, artifact_id, records)

    monkeypatch.setattr(store, "append_records", observed_append)
    runner._begin_trial_journal()
    await runner._event(
        "run-grouped-journal",
        {
            "kind": "trial_phase",
            "cell_id": "cell-1",
            "trial_id": "trial-1",
            "warmup": False,
            "phase": "verify",
            "state": "completed",
        },
    )
    runner._observation(
        "run-grouped-journal",
        {
            "record": "operation",
            "data": {
                "operation_id": "file_read",
                "cell_id": "cell-1",
                "trial_id": "trial-1",
                "request_id": None,
                "evidence": {},
            },
        },
    )
    await runner._resource_observations(
        "run-grouped-journal",
        [
            {
                "cell_id": "cell-1",
                "trial_id": "trial-1",
                "request_id": None,
                "reading": {
                    "metric_id": "sandbox_cpu_time_us",
                    "monotonic_offset_ns": 1,
                    "value": {"availability": "available", "value": 1},
                },
            }
        ],
    )

    assert appends == []
    assert delivered == []
    await runner._flush_trial_journal("run-grouped-journal")
    runner._end_trial_journal()

    assert appends == [
        (ArtifactId.OBSERVATIONS, 2),
        (ArtifactId.EVENTS, 2),
    ]
    assert [record["data"]["kind"] for record in delivered] == [
        "trial_phase",
        "resource_window",
    ]
    assert (
        len(store.read_records("run-grouped-journal", ArtifactId.OBSERVATIONS).records)
        == 2
    )


@pytest.mark.asyncio
async def test_request_barriers_flush_prior_trial_records_in_sequence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    store = runner._store
    store.create_run("run-grouped-barrier")
    runner._started_ns = time.monotonic_ns()
    event_batches: list[list[str]] = []
    real_append = store.append_records

    def observed_append(run_id, artifact_id, records):
        if artifact_id is ArtifactId.EVENTS:
            event_batches.append([record["data"]["state"] for record in records])
        real_append(run_id, artifact_id, records)

    monkeypatch.setattr(store, "append_records", observed_append)
    runner._begin_trial_journal()
    await runner._event(
        "run-grouped-barrier",
        {
            "kind": "trial_phase",
            "cell_id": "cell-1",
            "trial_id": "trial-1",
            "warmup": False,
            "phase": "setup",
            "state": "completed",
        },
    )

    async def operation() -> str:
        return "ok"

    result = await runner._run_request_batch(
        "run-grouped-barrier",
        "cell-1",
        "trial-1",
        ["request-1", "request-2"],
        [operation, operation],
        batch_timing=BatchTiming(),
    )
    runner._end_trial_journal()

    assert result == ["ok", "ok"]
    assert event_batches == [
        [
            "completed",
            "waiting_at_barrier",
            "waiting_at_barrier",
            "ready_at_barrier",
            "ready_at_barrier",
        ],
        ["in_flight", "succeeded", "in_flight", "succeeded"],
    ]


@pytest.mark.asyncio
async def test_failed_trial_commits_buffer_before_propagating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    store = runner._store
    store.create_run("run-failed-grouped-journal")
    runner._started_ns = time.monotonic_ns()

    async def failed_trial(*_args, **_kwargs):
        await runner._event(
            "run-failed-grouped-journal",
            {
                "kind": "trial_phase",
                "cell_id": "cell-1",
                "trial_id": "trial-1",
                "warmup": False,
                "phase": "setup",
                "state": "running",
            },
        )
        raise RuntimeError("simulated trial failure")

    monkeypatch.setattr(runner, "_run_trial", failed_trial)
    with pytest.raises(RuntimeError, match="simulated trial failure"):
        await runner._run_trial_with_journal(
            "run-failed-grouped-journal",
            tmp_path,
            object(),
            object(),
            {},
            None,
            "trial-1",
            False,
            0,
        )

    assert (
        len(store.read_records("run-failed-grouped-journal", ArtifactId.EVENTS).records)
        == 1
    )
    assert runner._trial_event_buffer is None
    assert runner._trial_observation_buffer is None


@pytest.mark.asyncio
async def test_cli_evidence_commits_before_trial_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    runner._store.create_run("run-cli-evidence-order")
    runner._started_ns = time.monotonic_ns()
    order: list[str] = []

    class FakeCli(runner_module.ProductCliAccess):
        def __init__(self) -> None:
            pass

        def begin_trial_evidence(self, trial_id: str) -> None:
            assert trial_id == "trial-1"
            order.append("evidence-begin")

        async def flush_trial_evidence(self, trial_id: str) -> None:
            assert trial_id == "trial-1"
            order.append("evidence-flush")

        def end_trial_evidence(self, trial_id: str) -> None:
            assert trial_id == "trial-1"
            order.append("evidence-end")

    async def trial(*_args, **_kwargs):
        order.append("trial")
        await runner._event(
            "run-cli-evidence-order",
            {
                "kind": "trial_phase",
                "cell_id": "cell-1",
                "trial_id": "trial-1",
                "warmup": False,
                "phase": "teardown",
                "state": "completed",
            },
        )
        return object()

    real_flush = runner._flush_trial_journal

    async def flush_journal(run_id: str) -> None:
        order.append("journal-flush")
        await real_flush(run_id)

    monkeypatch.setattr(runner, "_run_trial", trial)
    monkeypatch.setattr(runner, "_flush_trial_journal", flush_journal)

    await runner._run_trial_with_journal(
        "run-cli-evidence-order",
        tmp_path,
        FakeCli(),
        object(),
        {},
        None,
        "trial-1",
        False,
        0,
    )

    assert order == [
        "evidence-begin",
        "trial",
        "evidence-flush",
        "journal-flush",
        "evidence-end",
    ]
    assert runner._trial_event_buffer is None
    assert (
        len(
            runner._store.read_records(
                "run-cli-evidence-order", ArtifactId.EVENTS
            ).records
        )
        == 1
    )


@pytest.mark.asyncio
async def test_file_write_content_is_staged_before_batch_release() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._cancel = asyncio.Event()
    staged: set[str] = set()
    launch_stage_counts: list[int] = []

    class FakeCli(runner_module.ProductCliAccess):
        def __init__(self) -> None:
            pass

        async def stage_file_write_content(
            self, content: str, *, request_id: str
        ) -> None:
            assert content
            staged.add(request_id)

        def discard_file_write_content(self, request_id: str) -> None:
            staged.discard(request_id)

        async def file_write(self, *args, request_id: str, **kwargs):
            launch_stage_counts.append(len(staged))
            assert request_id in staged
            started_ns = time.monotonic_ns()
            return TimedGatewayResponse(
                request_id,
                1,
                1,
                "sha256:response",
                {"path": kwargs["path"], "bytes_written": 4},
                started_ns=started_ns,
            )

    cell = {
        "cell_id": "sha256:" + "4" * 64,
        "protocol": {"timeout_ms": 1000},
        "operation": {
            "operation": "file_write",
            "cell": {
                "concurrent_requests": 5,
                "content_bytes": 4,
                "target_mode": "independent",
            },
        },
    }
    context = TrialContext(
        Path("workspace"),
        "sandbox",
        False,
        data={"paths": [f"file-{index}.txt" for index in range(5)]},
    )

    responses = await runner._operate(
        FakeCli(),
        object(),
        cell,
        context,
        "trial-1",
        batch_timing=BatchTiming(),
    )

    assert len(responses) == 5
    assert launch_stage_counts == [5] * 5
    assert staged == set()


@pytest.mark.asyncio
async def test_trial_makespan_uses_validated_response_end_not_persistence_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    runner._started_ns = 1
    runner._definitions = {"operations": [{"id": "file_read", "checks": []}]}
    ordering: list[str] = []

    class Sampler:
        def __init__(self, **kwargs) -> None:
            pass

        async def start(self) -> None:
            ordering.append("resource-start")

        async def stop(self) -> None:
            ordering.append("resource-stop")

    async def no_op(*args, **kwargs) -> None:
        pass

    async def setup(*args, **kwargs):
        return TrialContext(tmp_path / "workspace", "sandbox", True)

    async def operate(*args, **kwargs):
        ordering.append("operate")
        timing = kwargs["batch_timing"]
        timing.barrier_released_ns = 100
        # This models request-state/evidence persistence completing long after
        # the validated responses. It must not enter the primary makespan.
        timing.batch_completed_ns = 10_000
        return [
            TimedGatewayResponse(
                "request-1",
                50,
                1,
                "sha256:response-1",
                {},
                started_ns=150,
            ),
            TimedGatewayResponse(
                "request-2",
                100,
                1,
                "sha256:response-2",
                {},
                started_ns=200,
            ),
        ]

    async def observe_request(*args, **kwargs) -> None:
        ordering.append("request-observation")

    async def verify(*args, **kwargs) -> None:
        ordering.append("verify")

    async def teardown(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(runner_module, "TrialResourceSampler", Sampler)
    monkeypatch.setattr(runner_module, "_operation_evidence", lambda *args: {})
    monkeypatch.setattr(runner, "_trial_phase", no_op)
    monkeypatch.setattr(runner, "_setup_trial", setup)
    monkeypatch.setattr(runner, "_operate", operate)
    monkeypatch.setattr(runner, "_verify", verify)
    monkeypatch.setattr(runner, "_teardown_trial", teardown)
    monkeypatch.setattr(runner, "_request_observation", observe_request)
    monkeypatch.setattr(runner, "_registered_check_observations", no_op)
    monkeypatch.setattr(runner, "_trial_observation", no_op)
    monkeypatch.setattr(
        runner,
        "_persist_operation_evidence",
        lambda *args, **kwargs: {"artifact_id": "bounded"},
    )
    cell = {
        "cell_id": "sha256:" + "3" * 64,
        "protocol": {"timeout_ms": 1},
        "operation": {
            "operation": "file_read",
            "cell": {
                "concurrent_requests": 2,
                "target_mode": "independent",
            },
        },
    }

    outcome = await runner._run_trial(
        "run-timing",
        tmp_path,
        object(),
        object(),
        cell,
        None,
        "trial-1",
        False,
        0,
    )

    assert outcome.batch_makespan_ns == 200
    assert outcome.operation_ns == 200
    assert ordering == [
        "resource-start",
        "operate",
        "resource-stop",
        "request-observation",
        "request-observation",
        "verify",
    ]


@pytest.mark.asyncio
async def test_create_workspace_sampler_requires_planned_post_workspace_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    runner._started_ns = 1
    runner._definitions = {"operations": [{"id": "create_workspace", "checks": []}]}
    sampler_arguments: list[dict] = []

    class Sampler:
        def __init__(self, **kwargs) -> None:
            sampler_arguments.append(kwargs)

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

    async def no_op(*args, **kwargs) -> None:
        pass

    async def setup(*args, **kwargs):
        return TrialContext(tmp_path / "workspace", "sandbox", True)

    async def operate(*args, **kwargs):
        timing = kwargs["batch_timing"]
        timing.barrier_released_ns = 100
        timing.batch_completed_ns = 200
        return [
            TimedGatewayResponse(
                f"request-{index}",
                100,
                1,
                f"sha256:response-{index}",
                {},
                started_ns=100,
            )
            for index in range(5)
        ]

    monkeypatch.setattr(runner_module, "TrialResourceSampler", Sampler)
    monkeypatch.setattr(
        runner_module,
        "_operation_evidence",
        lambda *args: {"evidence": {}},
    )
    monkeypatch.setattr(runner, "_trial_phase", no_op)
    monkeypatch.setattr(runner, "_setup_trial", setup)
    monkeypatch.setattr(runner, "_operate", operate)
    monkeypatch.setattr(runner, "_verify", no_op)
    monkeypatch.setattr(runner, "_teardown_trial", no_op)
    monkeypatch.setattr(runner, "_request_observation", no_op)
    monkeypatch.setattr(runner, "_registered_check_observations", no_op)
    monkeypatch.setattr(runner, "_trial_observation", no_op)
    monkeypatch.setattr(
        runner,
        "_persist_operation_evidence",
        lambda *args, **kwargs: {"artifact_id": "bounded"},
    )
    cell = {
        "cell_id": "sha256:" + "4" * 64,
        "protocol": {"timeout_ms": 1},
        "operation": {
            "operation": "create_workspace",
            "cell": {
                "workspace_count": 5,
                "network_profile": "shared",
            },
        },
    }

    outcome = await runner._run_trial(
        "run-create-workspace-boundary",
        tmp_path,
        object(),
        object(),
        cell,
        None,
        "trial-1",
        False,
        0,
    )

    assert outcome.status == "success"
    assert len(sampler_arguments) == 1
    assert sampler_arguments[0]["expected_post_workspace_count"] == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["file_write", "file_edit"])
@pytest.mark.parametrize("target_mode", ["independent", "same_target"])
async def test_session_mutation_publishes_one_cell_baseline_and_reuses_it(
    tmp_path: Path,
    operation: str,
    target_mode: str,
) -> None:
    roots = _roots(tmp_path)
    runner = CampaignRunner(roots)
    run_path = roots.runs / "run-session-baseline"
    run_path.mkdir()
    concurrent_requests = 3
    baseline_writes: list[tuple[str, str]] = []

    class Product:
        def __init__(self) -> None:
            self.published: dict[str, str] = {}
            self.session_views: dict[str, dict[str, str]] = {}

        async def create_sandbox(self, *args, **kwargs):
            return SimpleNamespace(id="sandbox-cell"), object()

        async def destroy_sandbox(self, *args, **kwargs):
            return object()

        async def file_write(
            self,
            sandbox,
            *,
            session_id,
            path,
            content,
            request_id,
            **kwargs,
        ):
            target = (
                self.published if session_id is None else self.session_views[session_id]
            )
            target[path] = content
            if session_id is None:
                baseline_writes.append((path, request_id))
            return TimedGatewayResponse(
                request_id,
                1,
                1,
                "sha256:write",
                {
                    "type": "update",
                    "path": path,
                    "bytes_written": len(content.encode()),
                },
            )

        async def file_edit(
            self,
            sandbox,
            *,
            session_id,
            path,
            edits,
            request_id,
            **kwargs,
        ):
            assert session_id is not None
            content = self.session_views[session_id][path]
            replacements = 0
            for edit in edits:
                count = content.count(edit["old_string"])
                replacements += count
                content = content.replace(
                    edit["old_string"],
                    edit["new_string"],
                    -1 if edit["replace_all"] else 1,
                )
            self.session_views[session_id][path] = content
            return TimedGatewayResponse(
                request_id,
                1,
                1,
                "sha256:edit",
                {
                    "type": "edit",
                    "path": path,
                    "edits_applied": len(edits),
                    "replacements": replacements,
                    "bytes_written": len(content.encode()),
                },
            )

    product = Product()

    class Sessions:
        def __init__(self) -> None:
            self.created: list[str] = []
            self.destroyed: list[str] = []

        async def create_no_op(self, sandbox, network_profile, *, request_id, **kwargs):
            assert network_profile == "shared"
            session_id = f"session-{len(self.created)}"
            self.created.append(session_id)
            product.session_views[session_id] = dict(product.published)
            return (
                SimpleNamespace(
                    sandbox_id=sandbox,
                    session_id=session_id,
                    network_profile=network_profile,
                ),
                object(),
            )

        async def destroy(self, session, *, request_id, **kwargs):
            self.destroyed.append(session.session_id)
            del product.session_views[session.session_id]
            return object()

    sessions = Sessions()
    body: dict[str, object] = {
        "destination": "session",
        "target_mode": target_mode,
        "concurrent_requests": concurrent_requests,
        "resolved_isolation": "fresh_sessions_per_trial",
    }
    if operation == "file_write":
        body["content_bytes"] = 4096
    else:
        body.update(
            file_bytes=4096,
            replacement_count=1,
            match_density=1.0,
        )
    cell = {
        "cell_id": "sha256:" + "7" * 64,
        "comparison_key": {"isolation": "fresh_sessions_per_trial"},
        "protocol": {"timeout_ms": 1000},
        "operation": {"operation": operation, "cell": body},
    }

    cell_context = await runner._setup_cell(run_path, product, sessions, cell)
    assert cell_context is not None
    published_baseline = dict(product.published)
    expected_paths = concurrent_requests if target_mode == "independent" else 1
    assert len(baseline_writes) == expected_paths
    assert all(
        request_id.startswith("cell-7777777777777777.prepare.")
        for _, request_id in baseline_writes
    )

    for index in range(2):
        trial_id = f"trial-{index}"
        context = await runner._setup_trial(
            run_path, product, sessions, cell, cell_context, trial_id
        )
        assert context.data["paths"] == cell_context.data["paths"]
        assert len(context.sessions) == 1
        session_id = context.sessions[0].session_id
        assert product.session_views[session_id] == published_baseline

        await runner._operate(product, sessions, cell, context, trial_id)

        assert product.published == published_baseline
        assert product.session_views[session_id] != published_baseline
        assert len(baseline_writes) == expected_paths
        await runner._teardown_trial(product, sessions, context, trial_id)

    assert sessions.created == ["session-0", "session-1"]
    assert sessions.destroyed == sessions.created
    await runner._teardown_cell(product, sessions, cell_context, cell["cell_id"])


@pytest.mark.asyncio
async def test_independent_verification_reads_run_concurrently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    active = 0
    maximum_active = 0
    all_started = asyncio.Event()
    attribution_started = asyncio.Event()
    release = asyncio.Event()
    paths = [f"file-{index}.txt" for index in range(5)]

    async def read_exact(*args, path: str, **kwargs) -> str:
        nonlocal active, maximum_active
        active += 1
        maximum_active = max(maximum_active, active)
        if active == len(paths):
            all_started.set()
        await release.wait()
        active -= 1
        return f"content:{path}"

    async def verify_attribution(*args, **kwargs) -> None:
        attribution_started.set()
        await release.wait()

    monkeypatch.setattr(runner, "_read_exact", read_exact)
    monkeypatch.setattr(runner, "_verify_mutation_attribution", verify_attribution)
    body = {
        "destination": "session",
        "target_mode": "independent",
        "concurrent_requests": 5,
        "content_bytes": 16,
    }
    cell = {
        "operation": {"operation": "file_write", "cell": body},
        "protocol": {"timeout_ms": 1000},
    }
    responses = [
        TimedGatewayResponse(
            f"request-{index}",
            1,
            1,
            f"sha256:{index}",
            {
                "type": "update",
                "path": path,
                "bytes_written": body["content_bytes"],
            },
        )
        for index, path in enumerate(paths)
    ]
    context = TrialContext(
        tmp_path,
        "sandbox",
        False,
        data={
            "paths": paths,
            "request_contents": [f"content:{path}" for path in paths],
            "operation_session": SimpleNamespace(session_id="session"),
        },
    )

    verifying = asyncio.create_task(
        runner._verify(
            object(), object(), cell, responses, context, "trial-independent"
        )
    )
    await asyncio.wait_for(all_started.wait(), timeout=1)
    await asyncio.wait_for(attribution_started.wait(), timeout=1)
    release.set()
    await verifying

    assert maximum_active == 5


@pytest.mark.asyncio
async def test_mutation_verification_preserves_both_branch_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    both_started = asyncio.Event()
    started = 0

    async def fail_after_both(message: str) -> None:
        nonlocal started
        started += 1
        if started == 2:
            both_started.set()
        await both_started.wait()
        raise CampaignError(message)

    async def verify_contents(*args, **kwargs) -> None:
        await fail_after_both("content branch failed")

    async def verify_attribution(*args, **kwargs) -> None:
        await fail_after_both("attribution branch failed")

    monkeypatch.setattr(runner, "_verify_mutation_contents", verify_contents)
    monkeypatch.setattr(runner, "_verify_mutation_attribution", verify_attribution)
    body = {
        "destination": "session",
        "target_mode": "independent",
        "concurrent_requests": 1,
        "content_bytes": 16,
    }
    cell = {
        "operation": {"operation": "file_write", "cell": body},
        "protocol": {"timeout_ms": 1000},
    }
    response = TimedGatewayResponse(
        "request-0",
        1,
        1,
        "sha256:0",
        {
            "type": "update",
            "path": "file.txt",
            "bytes_written": body["content_bytes"],
        },
    )
    context = TrialContext(
        tmp_path,
        "sandbox",
        False,
        data={
            "paths": ["file.txt"],
            "request_contents": ["content"],
            "operation_session": SimpleNamespace(session_id="session"),
        },
    )

    with pytest.raises(BaseExceptionGroup) as captured:
        await runner._verify(
            object(), object(), cell, [response], context, "trial-both-fail"
        )

    messages = {str(error) for error in captured.value.exceptions}
    assert messages == {"content branch failed", "attribution branch failed"}


@pytest.mark.asyncio
async def test_verification_read_fetches_remaining_pages_concurrently(
    tmp_path: Path,
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    lines = [f"{index:04d}" for index in range(4500)]
    content = "\n".join(lines)
    active = 0
    maximum_active = 0
    remaining_started = asyncio.Event()
    release = asyncio.Event()
    calls: list[tuple[int, int, str]] = []

    class Product:
        async def file_read(
            self,
            *args,
            offset: int,
            limit: int,
            request_id: str,
            **kwargs,
        ):
            nonlocal active, maximum_active
            calls.append((offset, limit, request_id))
            if offset > 1:
                active += 1
                maximum_active = max(maximum_active, active)
                if active == 2:
                    remaining_started.set()
                await release.wait()
                active -= 1
            selected = lines[offset - 1 : offset - 1 + limit]
            next_offset = (
                offset + len(selected)
                if offset - 1 + len(selected) < len(lines)
                else None
            )
            page_content = "\n".join(selected)
            return SimpleNamespace(
                value={
                    "path": "fixture.txt",
                    "content": page_content,
                    "start_line": offset,
                    "num_lines": len(selected),
                    "total_lines": len(lines),
                    "bytes_read": len(page_content.encode()),
                    "total_bytes": len(content.encode()),
                    "next_offset": next_offset,
                    "truncated": next_offset is not None,
                }
            )

    reading = asyncio.create_task(
        runner._read_exact(
            Product(),
            "sandbox",
            session_id=None,
            path="fixture.txt",
            expected_bytes=len(content.encode()),
            timeout_ms=1000,
            request_id="trial.verify",
        )
    )
    await asyncio.wait_for(remaining_started.wait(), timeout=1)
    assert maximum_active == 2
    release.set()

    assert await reading == content
    assert calls == [
        (1, 2000, "trial.verify.0"),
        (2001, 2000, "trial.verify.1"),
        (4001, 2000, "trial.verify.2"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["file_read", "file_write", "file_edit"])
async def test_independent_fixture_writes_run_concurrently(
    tmp_path: Path,
    operation: str,
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    active = 0
    maximum_active = 0
    all_started = asyncio.Event()
    release = asyncio.Event()
    request_ids: list[str] = []

    class Product:
        async def file_write(self, *args, request_id: str, **kwargs):
            nonlocal active, maximum_active
            request_ids.append(request_id)
            active += 1
            maximum_active = max(maximum_active, active)
            if active == 5:
                all_started.set()
            await release.wait()
            active -= 1
            return object()

    body: dict[str, object] = {
        "target_mode": "independent",
        "concurrent_requests": 5,
    }
    if operation == "file_read":
        body["returned_bytes"] = 4096
    elif operation == "file_write":
        body["content_bytes"] = 4096
    else:
        body.update(
            file_bytes=4096,
            replacement_count=1,
            match_density=1.0,
        )
    cell = {
        "operation": {"operation": operation, "cell": body},
        "protocol": {"timeout_ms": 1000},
    }
    context = TrialContext(tmp_path, "sandbox", False)

    if operation == "file_read":
        preparing = asyncio.create_task(
            runner._prepare_reads(Product(), cell, context, "trial-independent")
        )
    else:
        preparing = asyncio.create_task(
            runner._prepare_mutation(Product(), cell, context, "trial-independent")
        )
    await asyncio.wait_for(all_started.wait(), timeout=1)
    assert maximum_active == 5
    release.set()
    await preparing

    assert len(context.data["paths"]) == 5
    assert len(request_ids) == 5
    assert len(set(request_ids)) == 5


@pytest.mark.asyncio
async def test_create_workspace_teardown_destroys_sessions_in_parallel_first(
    tmp_path: Path,
) -> None:
    runner = CampaignRunner(_roots(tmp_path))
    sessions_to_destroy = [
        SimpleNamespace(session_id=f"session-{index}", sandbox_id="sandbox")
        for index in range(5)
    ]
    all_started = asyncio.Event()
    release = asyncio.Event()
    started: list[str] = []
    sandbox_destroyed = False

    class Lifecycle:
        async def destroy(self, session, *, request_id: str):
            started.append(session.session_id)
            if len(started) == len(sessions_to_destroy):
                all_started.set()
            await release.wait()

    class Product:
        async def destroy_sandbox(self, sandbox: str, *, request_id: str):
            nonlocal sandbox_destroyed
            assert len(started) == len(sessions_to_destroy)
            sandbox_destroyed = True

    context = TrialContext(
        tmp_path,
        "sandbox",
        True,
        sessions=sessions_to_destroy,
        data={"operation_id": "create_workspace"},
    )
    teardown = asyncio.create_task(
        runner._teardown_trial(
            Product(), Lifecycle(), context, "trial-create-workspace"
        )
    )
    await asyncio.wait_for(all_started.wait(), timeout=1)
    assert not sandbox_destroyed
    release.set()
    await teardown

    assert sandbox_destroyed
    assert set(started) == {session.session_id for session in sessions_to_destroy}


@pytest.mark.asyncio
async def test_cancellation_request_persists_exactly_one_public_transition(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    store = ArtifactStore(roots)
    store.create_run("run-cancel")
    runner = CampaignRunner(roots)
    runner._started_ns = time.monotonic_ns()

    assert await runner.request_cancel("run-cancel") is True
    assert await runner.request_cancel("run-cancel") is False

    events = store.read_records("run-cancel", ArtifactId.EVENTS).records
    assert [event["data"] for event in events] == [
        {"kind": "run_state", "state": "cancelling"}
    ]


@pytest.mark.parametrize(
    ("cancel_phase", "expected_teardowns"),
    [("setup", 0), ("operation", 1), ("verify", 1), ("teardown", 1)],
)
@pytest.mark.asyncio
async def test_trial_cancellation_is_attributed_at_every_lifecycle_phase(
    tmp_path: Path,
    monkeypatch,
    cancel_phase: str,
    expected_teardowns: int,
) -> None:
    roots = _roots(tmp_path)
    ArtifactStore(roots).create_run("run-cancel-phase")
    runner = CampaignRunner(roots)
    runner._started_ns = time.monotonic_ns()
    runner._definitions = {"operations": [{"id": "create_workspace", "checks": []}]}
    teardowns = 0

    class Sampler:
        def __init__(self, **kwargs) -> None:
            pass

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

    async def phase(*args) -> None:
        phase_name, state = args[-2:]
        if phase_name == cancel_phase and state == "running":
            runner.cancel()

    async def setup(*args, **kwargs):
        return TrialContext(tmp_path / "workspace", "sandbox", True)

    async def operate(*args, **kwargs):
        timing = kwargs["batch_timing"]
        timing.barrier_released_ns = time.monotonic_ns()
        timing.batch_completed_ns = time.monotonic_ns()
        return [TimedGatewayResponse("request-1", 1, 1, "sha256:response", {})]

    async def verify(*args, **kwargs) -> None:
        pass

    async def teardown(*args, **kwargs) -> None:
        nonlocal teardowns
        teardowns += 1

    async def no_op(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(runner_module, "TrialResourceSampler", Sampler)
    monkeypatch.setattr(runner, "_trial_phase", phase)
    monkeypatch.setattr(runner, "_setup_trial", setup)
    monkeypatch.setattr(runner, "_operate", operate)
    monkeypatch.setattr(runner, "_verify", verify)
    monkeypatch.setattr(runner, "_teardown_trial", teardown)
    monkeypatch.setattr(runner, "_request_observation", no_op)
    monkeypatch.setattr(runner, "_registered_check_observations", no_op)
    monkeypatch.setattr(runner, "_trial_observation", no_op)
    cell = {
        "cell_id": "sha256:" + "2" * 64,
        "protocol": {"timeout_ms": 1},
        "operation": {
            "operation": "create_workspace",
            "cell": {"workspace_count": 1, "network_profile": "shared"},
        },
    }

    with pytest.raises(asyncio.CancelledError):
        await runner._run_trial(
            "run-cancel-phase",
            roots.runs / "run-cancel-phase",
            object(),
            object(),
            cell,
            None,
            "trial-1",
            False,
            0,
        )
    assert teardowns == expected_teardowns


@pytest.mark.asyncio
async def test_shielded_cleanup_finishes_after_outer_cancellation() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._CLEANUP_TIMEOUT_SECONDS = 1
    started = asyncio.Event()
    release = asyncio.Event()
    finished = False

    async def cleanup() -> None:
        nonlocal finished
        started.set()
        await release.wait()
        finished = True

    task = asyncio.create_task(runner._shielded_cleanup(cleanup()))
    await started.wait()
    task.cancel()
    release.set()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished


@pytest.mark.asyncio
async def test_trial_retains_infrastructure_attribution_when_cleanup_also_fails(
    tmp_path: Path, monkeypatch
) -> None:
    roots = _roots(tmp_path)
    store = ArtifactStore(roots)
    store.create_run("run-combined-failure")
    runner = CampaignRunner(roots)
    runner._started_ns = 1
    runner._definitions = {
        "operations": [{"id": "file_read", "checks": []}],
    }

    class Sampler:
        def __init__(self, **kwargs) -> None:
            pass

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

    async def setup(*args, **kwargs):
        return TrialContext(tmp_path / "workspace", "sandbox", True)

    async def operate(*args, **kwargs):
        raise GatewayTransportError("simulated_disconnect")

    async def teardown(*args, **kwargs):
        raise RuntimeError("simulated cleanup failure")

    monkeypatch.setattr(runner_module, "TrialResourceSampler", Sampler)
    monkeypatch.setattr(CampaignRunner, "_setup_trial", setup)
    monkeypatch.setattr(CampaignRunner, "_operate", operate)
    monkeypatch.setattr(CampaignRunner, "_teardown_trial", teardown)
    cell = {
        "cell_id": "sha256:" + "1" * 64,
        "operation": {"operation": "file_read", "cell": {}},
    }

    with pytest.raises(CampaignError, match="both failed"):
        await runner._run_trial(
            "run-combined-failure",
            roots.runs / "run-combined-failure",
            object(),
            object(),
            cell,
            None,
            "trial-1",
            False,
            0,
        )

    trial = next(
        item["record"]["data"]
        for item in store.read_records(
            "run-combined-failure", ArtifactId.OBSERVATIONS
        ).records
        if item["record"]["record"] == "trial"
    )
    assert trial["status"] == "cleanup_invalid"
    assert trial["infrastructure_failed"] is True
    assert trial["cleanup_baseline_restored"] is False
