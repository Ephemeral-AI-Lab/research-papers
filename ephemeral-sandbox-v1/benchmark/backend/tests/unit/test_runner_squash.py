import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmark_lab.artifacts import ArtifactId, ArtifactStore
from benchmark_lab.observability import parse_layerstack
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.runner import (
    CampaignError,
    CampaignRunner,
    TrialContext,
    _layerstack_evidence,
    _operation_evidence,
    _sampled_peak,
    _trace_layerstack_evidence,
)
from benchmark_lab.transport import TimedGatewayResponse


ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "tests/fixtures/golden/rust/quick-smoke-completed"


def _roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def _view(version: int, root: str, layers: list[tuple[str, int, int]], leases: int = 0):
    return parse_layerstack(
        {
            "view": "layerstack",
            "manifest_version": version,
            "root_hash": root,
            "active_lease_count": leases,
            "total_bytes": sum(item[1] for item in layers),
            "total_allocated_bytes": sum(item[2] for item in layers),
            "storage_logical_bytes": sum(item[1] for item in layers) + 100,
            "storage_allocated_bytes": sum(item[2] for item in layers) + 200,
            "staging_entry_count": 0,
            "layers": [
                {
                    "layer_id": identity,
                    "bytes": logical,
                    "allocated_bytes": allocated,
                    "leased_by_workspaces": 0,
                    "booked_by": [],
                }
                for identity, logical, allocated in layers
            ],
        }
    )


@pytest.mark.asyncio
async def test_squash_uses_the_frozen_public_request_identity() -> None:
    class Product:
        async def squash_layerstacks(self, sandbox, *, timeout_ms, request_id):
            assert sandbox == "sandbox"
            assert timeout_ms == 123
            assert request_id == "squash-layerstack-0"
            return TimedGatewayResponse(request_id, 1, 1, "sha256:response", {})

    runner = CampaignRunner.__new__(CampaignRunner)
    responses = await runner._operate(
        Product(),
        SimpleNamespace(),
        {
            "operation": {"operation": "squash_layerstack", "cell": {}},
            "protocol": {"timeout_ms": 123},
        },
        TrialContext(Path("/tmp/work"), "sandbox", True),
        "trial-id",
    )
    assert responses[0].request_id == "squash-layerstack-0"


def test_squash_evidence_preserves_the_frozen_public_shape() -> None:
    baseline_view = _view(2, "before", [("L1", 4, 8), ("L2", 5, 16)], leases=1)
    settled_view = _view(3, "after", [("S1", 9, 12)], leases=1)
    baseline = _layerstack_evidence(baseline_view, 10, sampled=False)
    post_commit = _trace_layerstack_evidence(
        {
            "manifest_version": 3,
            "s2_root_hash": "after",
            "s2_layer_count": 1,
            "s2_active_logical_bytes": 9,
            "s2_active_allocated_bytes": 12,
            "s2_storage_logical_bytes": 109,
            "s2_storage_allocated_bytes": 212,
            "s2_staging_entry_count": 0,
        },
        20,
        sampled=False,
    )
    context = TrialContext(Path("/tmp/work"), "sandbox", True)
    context.data = {
        "source_layer_ids": ["L1", "L2"],
        "s0_view": baseline_view,
        "s3_view": settled_view,
        "s0_baseline": baseline,
        "s1_sampled_peak": _sampled_peak(baseline, post_commit),
        "s2_post_commit": post_commit,
        "s3_settled": _layerstack_evidence(settled_view, 30, sampled=False),
        "dispositions": {
            "migrated": 1,
            "identity": 0,
            "leased": 0,
            "faulty": 0,
            "session_gone": 0,
        },
        "observed_squashed_block_count": 1,
        "content_equivalent": True,
    }
    context.sessions = [SimpleNamespace(session_id="session-1")]
    cell = {
        "operation": {
            "operation": "squash_layerstack",
            "cell": {"live_sessions": 1, "remount_parallelism": 4},
        }
    }

    evidence = _operation_evidence(cell, [], context)["evidence"]
    golden_file = next(
        path
        for path in (GOLDEN / "cells").rglob("operation-evidence-*.json")
        if json.loads(path.read_text())["data"]["operation"] == "squash_layerstack"
    )
    frozen = json.loads(golden_file.read_text())["data"]["evidence"]

    assert set(evidence) == set(frozen)
    assert evidence["observed_replaced_layer_count"] == 2
    assert evidence["reclaimed_bytes"] == {"availability": "available", "value": 24}
    assert evidence["manifest_reduced"] is True
    assert evidence["content_equivalent"] is True
    assert evidence["s1_sampled_peak"]["sampled"] is True


class _SessionRegistry:
    def __init__(self) -> None:
        self.retired: list[object] = []

    def retire_product_destroyed(self, session) -> None:
        self.retired.append(session)


def _squash_context() -> TrialContext:
    context = TrialContext(Path("/tmp/work"), "sandbox", True)
    context.sessions = [SimpleNamespace(session_id="session-1")]
    context.data = {
        "squash_cell": {
            "squashable_blocks": 1,
            "layers_per_block": 2,
        },
        "eligible_sessions": 1,
    }
    return context


def _squash_response() -> dict:
    return {
        "manifest_version": 3,
        "squashed_blocks": [{
            "squashed_layer_id": "squashed",
            "replaced_layer_ids": ["layer-1", "layer-2"],
            "replaced_layers": "reclaimed",
            "blocked_reasons": None,
        }],
        "swept_sessions": [{
            "session_id": "session-1",
            "disposition": "migrated",
            "reason": None,
            "class_detail": None,
        }],
        "faulty_sessions": None,
    }


def test_squash_response_requires_strict_nested_schema_and_exact_block_width() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    valid = _squash_response()
    runner._verify_squash_response(valid, _squash_context(), _SessionRegistry())

    extra = _squash_response()
    extra["unexpected"] = True
    with pytest.raises(CampaignError, match="response schema"):
        runner._verify_squash_response(extra, _squash_context(), _SessionRegistry())

    short = _squash_response()
    short["squashed_blocks"][0]["replaced_layer_ids"] = ["layer-1"]
    with pytest.raises(CampaignError, match="reduction shape"):
        runner._verify_squash_response(short, _squash_context(), _SessionRegistry())


def test_squash_faulty_summary_must_match_strict_disposition_fields() -> None:
    runner = CampaignRunner.__new__(CampaignRunner)
    response = _squash_response()
    response["swept_sessions"][0].update(
        disposition="faulty", class_detail="remount failed"
    )
    response["faulty_sessions"] = [{
        "session_id": "session-1",
        "class_detail": "different",
        "lease_errors": [],
    }]
    with pytest.raises(CampaignError, match="summary disagrees"):
        runner._verify_squash_response(
            response, _squash_context(), _SessionRegistry()
        )


def test_squash_trace_rejects_present_malformed_optional_counters() -> None:
    attrs = {
        "manifest_version": 3,
        "s2_root_hash": "after",
        "s2_layer_count": 1,
        "s2_storage_allocated_bytes": "not-an-integer",
    }
    with pytest.raises(CampaignError, match="attribute s2_storage_allocated_bytes"):
        _trace_layerstack_evidence(attrs, 1, sampled=False)


def _node(name: str, *, attrs=None, children=None, offset=0.0, duration=1.0):
    return SimpleNamespace(
        offset_ms=offset,
        span=SimpleNamespace(
            name=name,
            status="completed",
            dur_ms=duration,
            attrs=attrs or {},
        ),
        children=children or [],
    )


class _TraceProduct:
    def __init__(self, trace, settled) -> None:
        self.trace = trace
        self.settled = settled

    async def observe_trace(self, *args, **kwargs):
        return self.trace

    async def observe_layerstack(self, *args, **kwargs):
        return self.settled


@pytest.mark.asyncio
async def test_squash_trace_requires_exact_phase_and_remount_cardinality(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    store = ArtifactStore(roots)
    store.create_run("run-trace")
    runner = CampaignRunner(roots)
    runner._started_ns = time.monotonic_ns()
    runner._definitions = json.loads(
        (GOLDEN / "definition-snapshot.json").read_text()
    )["data"]
    cell = next(
        item
        for item in json.loads((GOLDEN / "expanded-plan.json").read_text())["data"][
            "cells"
        ]
        if item["operation_id"] == "squash_layerstack"
        and item["operation"]["cell"]["live_sessions"] == 1
    )
    attrs = {
        "manifest_version": 3,
        "blocks": 1,
        "swept": 1,
        "sweep_width": 4,
        "s2_root_hash": "after",
        "s2_layer_count": 1,
        "s2_storage_logical_bytes": 109,
        "s2_storage_allocated_bytes": 212,
        "s2_staging_entry_count": 0,
    }
    children = [
        _node("layerstack.squash.plan"),
        _node("layerstack.squash.flatten"),
        _node("layerstack.squash.commit", offset=2),
        _node("layerstack.squash.remount_sweep"),
        _node("workspace_session.remount"),
    ]
    trace = SimpleNamespace(spans=[_node("layerstack.squash", attrs=attrs, children=children)])
    baseline = _view(2, "before", [("L1", 4, 8), ("L2", 5, 16)], leases=1)
    settled = _view(3, "after", [("S1", 9, 12)], leases=1)
    context = TrialContext(Path("/tmp/work"), "sandbox", True)
    context.data = {
        "expected_remount_spans": 1,
        "s0_baseline": _layerstack_evidence(baseline, 1, sampled=False),
    }
    response = TimedGatewayResponse(
        "trial.request.0",
        10,
        1,
        "sha256:response",
        {
            "manifest_version": 3,
            "squashed_blocks": [{}],
            "swept_sessions": [{}],
        },
        started_ns=runner._started_ns,
    )

    await runner._phase_observations(
        "run-trace",
        cell,
        "trial-1",
        response,
        _TraceProduct(trace, settled),
        context,
    )
    phases = [
        item["record"]["data"]
        for item in store.read_records("run-trace", ArtifactId.OBSERVATIONS).records
        if item["record"]["record"] == "phase"
    ]
    assert len(phases) == 6
    assert context.data["s3_settled"]["root_hash"]["value"] == "after"

    trace.spans[0].children.append(_node("workspace_session.remount"))
    with pytest.raises(CampaignError, match="phase cardinality mismatch"):
        await runner._phase_observations(
            "run-trace",
            cell,
            "trial-2",
            response,
            _TraceProduct(trace, settled),
            context,
        )
