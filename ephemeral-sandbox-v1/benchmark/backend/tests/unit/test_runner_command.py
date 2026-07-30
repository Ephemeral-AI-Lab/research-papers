from pathlib import Path

from benchmark_lab.runner import TrialContext, _operation_evidence
from benchmark_lab.transport import TimedGatewayResponse


def test_command_evidence_preserves_stdout_and_empty_stderr_contract() -> None:
    command = ":"
    cell = {
        "operation": {
            "operation": "exec_command",
            "cell": {
                "command_case": "noop",
                "command": command,
            },
        }
    }
    response = TimedGatewayResponse(
        request_id="request-1",
        latency_ns=1,
        response_bytes=1,
        response_sha256="sha256:value",
        value={"exit_code": 0, "output": ""},
    )

    context = TrialContext(Path("/unused"), "sandbox-1", False)
    evidence = _operation_evidence(cell, [response], context)["evidence"]

    empty = {
        "byte_count": 0,
        "truncated": False,
        "sha256": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }
    assert evidence == {
        "command_case": "noop",
        "template_revision": 1,
        "command_sha256": "sha256:e7ac0786668e0ff0f02b62bd04f45ff636fd82db63b1104601c975dc005f3a67",
        "exit_code": 0,
        "stdout": empty,
        "stderr": empty,
    }
