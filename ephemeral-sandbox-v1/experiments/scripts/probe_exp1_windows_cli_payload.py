from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


async def _probe(executable: Path, payload_bytes: int) -> dict[str, Any]:
    payload = "x" * payload_bytes
    arguments = [
        str(executable),
        "--gateway-socket",
        "127.0.0.1:1",
        "--gateway-auth-token",
        "exp1-diagnostic-token",
        "--sandbox-id",
        "exp1-diagnostic",
        "--request-id",
        f"exp1-python-subprocess-{payload_bytes}",
        "file_write",
        "--path",
        "diagnostic.bin",
        "--content",
        payload,
    ]
    started_ns = time.monotonic_ns()
    process: asyncio.subprocess.Process | None = None
    try:
        process = await asyncio.create_subprocess_exec(
            *arguments,
            cwd=executable.parent.parent,
            env={
                name: os.environ[name]
                for name in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP")
                if name in os.environ
            },
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        ended_ns = time.monotonic_ns()
        return {
            "payload_bytes": payload_bytes,
            "process_started": True,
            "pid_was_assigned": process.pid is not None,
            "return_code": process.returncode,
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_sha256": f"sha256:{hashlib.sha256(stdout).hexdigest()}",
            "stderr_sha256": f"sha256:{hashlib.sha256(stderr).hexdigest()}",
            "elapsed_ns": ended_ns - started_ns,
            "expected_gateway_connection": "deliberately unavailable",
        }
    except OSError as error:
        ended_ns = time.monotonic_ns()
        return {
            "payload_bytes": payload_bytes,
            "process_started": False,
            "return_code": None,
            "error_type": type(error).__name__,
            "errno": error.errno,
            "winerror": getattr(error, "winerror", None),
            "error": str(error),
            "elapsed_ns": ended_ns - started_ns,
            "expected_gateway_connection": "not attempted",
        }
    except TimeoutError:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        ended_ns = time.monotonic_ns()
        return {
            "payload_bytes": payload_bytes,
            "process_started": process is not None,
            "return_code": None if process is None else process.returncode,
            "error_type": "TimeoutError",
            "error": "diagnostic child did not terminate within 10 seconds",
            "elapsed_ns": ended_ns - started_ns,
        }


async def _run(executable: Path) -> dict[str, Any]:
    probes = [
        await _probe(executable, 4096),
        await _probe(executable, 262144),
    ]
    return {
        "schema_version": 1,
        "kind": "native_windows_asyncio_cli_payload_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {
            "computer_name": platform.node(),
            "operating_system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "subprocess_api": "asyncio.create_subprocess_exec",
        },
        "runtime_cli": {
            "path": str(executable),
            "sha256": _sha256(executable),
        },
        "sanitized_argument_shape": [
            str(executable),
            "--gateway-socket",
            "127.0.0.1:1",
            "--gateway-auth-token",
            "[REDACTED]",
            "--sandbox-id",
            "exp1-diagnostic",
            "--request-id",
            "PAYLOAD-SPECIFIC-ID",
            "file_write",
            "--path",
            "diagnostic.bin",
            "--content",
            "PAYLOAD",
        ],
        "probes": probes,
        "acceptance": {
            "small_payload_process_started": probes[0]["process_started"] is True,
            "required_payload_process_started": probes[1]["process_started"] is True,
            "required_payload_failed_before_gateway": (
                probes[1]["process_started"] is False
                and probes[1].get("winerror") == 206
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-cli", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    executable = arguments.runtime_cli.resolve(strict=True)
    output = arguments.output.resolve()
    if output.exists():
        raise SystemExit("diagnostic output already exists")
    result = asyncio.run(_run(executable))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    accepted = result["acceptance"]
    return (
        0
        if accepted["small_payload_process_started"]
        and accepted["required_payload_failed_before_gateway"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
