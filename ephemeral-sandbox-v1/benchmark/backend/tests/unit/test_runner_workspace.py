from pathlib import Path

from benchmark_lab.runner import TrialContext, _event_family, _operation_evidence
from benchmark_lab.transport import TimedGatewayResponse


def test_workspace_evidence_records_verified_lifecycle_counts() -> None:
    cell = {
        "operation": {
            "operation": "create_workspace",
            "cell": {"workspace_count": 1, "network_profile": "shared"},
        }
    }
    response = TimedGatewayResponse(
        request_id="request-1",
        latency_ns=1,
        response_bytes=1,
        response_sha256="sha256:value",
        value={
            "workspace_session_id": "session-1",
            "network_profile": "shared",
            "finalize_policy": "no_op",
        },
    )
    context = TrialContext(Path("/unused"), "sandbox-1", False)

    evidence = _operation_evidence(cell, [response], context)["evidence"]

    assert evidence == {
        "requested_count": 1,
        "created_count": 1,
        "ready_count": 1,
        "network_profile_matches": 1,
    }


def test_workspace_family_events_use_the_public_family_id() -> None:
    assert _event_family("workspace_lifecycle") == "workspace_lifecycle"
    assert _event_family("layer_stack") == "layerstack"
