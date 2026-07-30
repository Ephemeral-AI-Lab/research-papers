import asyncio
import copy
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import benchmark_lab.runner as runner_module
from benchmark_lab.artifacts import ArtifactId, ArtifactStore
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.observability import parse_cgroup, parse_snapshot
from benchmark_lab.reports import RunCorpus
from benchmark_lab.runner import CampaignError, CampaignRunner, TrialContext
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


class FakeProduct:
    def __init__(self, *, fail_destroy: bool = False) -> None:
        self.files: dict[str, str] = {}
        self.fail_destroy = fail_destroy

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
        return parse_cgroup({
            "view": "cgroup",
            "scope": "sandbox",
            "series": [{
                "ts": 1,
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
            }],
        })

    async def observe_snapshot(self, sandbox, *, request_id):
        return parse_snapshot({
            "sandbox_id": sandbox,
            "lifecycle_state": "ready",
            "availability": "available",
            "sampled_at_unix_ms": 1,
            "errors": [],
            "daemon": {"daemon_pid": 7, "runtime_dir": "/run/fake"},
            "resources": {"latest": None, "history": []},
            "workspaces": [],
            "stack": None,
        }, sandbox)

    @staticmethod
    def _response(request_id: str, value: dict) -> TimedGatewayResponse:
        return TimedGatewayResponse(request_id, 123, 17, "sha256:response", value)


class FakeGateway:
    client = object()

    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def _install_fakes(monkeypatch, fake: FakeProduct, gateway: FakeGateway) -> None:
    class Launcher:
        async def start(self, run_id, *, remount_sweep_width):
            return gateway

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

    monkeypatch.setattr(runner_module, "GatewayLauncher", lambda roots: Launcher())
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
    definition_reference = ArtifactStore(roots).download_artifact(
        "run-success", ArtifactId.DEFINITION_SNAPSHOT.value
    ).reference
    assert corpus.manifest["definition_snapshot"]["sha256"] == definition_reference.sha256
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
    assert (roots.runs / "run-cleanup-failed").exists()
    store = ArtifactStore(roots)
    assert store.read_envelope("run-cleanup-failed", ArtifactId.RUN_MANIFEST)["state"] == "failed"
    corpus = RunCorpus.open(store.run_path("run-cleanup-failed"))
    assert corpus.report is not None
    assert corpus.report.state == "failed"
    assert corpus.report.correctness_verdict == "fail"


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
