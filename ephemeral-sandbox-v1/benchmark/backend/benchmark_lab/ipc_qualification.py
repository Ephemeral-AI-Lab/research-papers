from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import re
import secrets
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .catalog import _prebuilt_executable
from .paths import BenchmarkRoots, _sync_directory

EXP1_IPC_INVOCATION_COUNT = 25_000
EXP1_IPC_CONCURRENCY = 5
EXP1_IPC_BATCH_COUNT = 5_000
QUALIFICATION_ONLY = True
PERFORMANCE_EVIDENCE = False
TCPIP_EVENT_IDS = (4227, 4231)
MAX_GATEWAY_HANDLE_GROWTH = 32
MAX_GATEWAY_PRIVATE_BYTES_GROWTH = 16 * 1024 * 1024
MAX_GATEWAY_RSS_BYTES_GROWTH = 16 * 1024 * 1024
RESOURCE_GROWTH_POLICY_SOURCE = "EXP1 v1.1 IPC qualification policy preregistration"
PROCESS_SAMPLE_EVERY_BATCHES = 100
BENCHMARK_GIT_EXCLUSIONS = (
    ":(exclude,glob)benchmark/**/.pytest_cache/**",
    ":(exclude,glob)benchmark/**/.venv/**",
    ":(exclude,glob)benchmark/**/__pycache__/**",
    ":(exclude,glob)benchmark/**/dist/**",
    ":(exclude,glob)benchmark/**/node_modules/**",
    ":(exclude,glob)benchmark/**/playwright-report/**",
    ":(exclude,glob)benchmark/**/test-results/**",
    ":(exclude,glob)benchmark/**/*.pyc",
)
PAPER_FROZEN_SCOPE = (
    "benchmark",
    "progress.md",
    "plan/task-packets/exp1-cli-performance-campaign.md",
    "experiment_inventory.md",
    "experiments/exp1-v1.1-protocol-amendment.md",
    "experiments/environment_setup.md",
    "experiments/expected_tables.md",
    "experiments/experiment_log.md",
    "paper_state.json",
    "plan/progress.md",
    "experiments/scripts/archive_exp1_run.py",
    "experiments/scripts/project_exp1_final_runtime.py",
    "experiments/analysis/scripts/generate_exp1_tables.py",
)
PREREGISTERED_PRODUCT_COMMIT = "5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8"
PREREGISTERED_PRODUCT_BRANCH = "main"
PREREGISTERED_PACKAGE_SHA256 = (
    "sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506"
)
PREREGISTERED_ARTIFACT_SHA256 = {
    "gateway": (
        "sha256:42e7642dd025487811abbcd78dcc5513760f2aaa1e6057cfdfa3e74c03748358"
    ),
    "manager_cli": (
        "sha256:e1faa2fe0e9f4909fa2d694166784ac65dde40ba82795b7e0c503eb5fea86513"
    ),
    "runtime_cli": (
        "sha256:e18827cf765945c958e169748575b89645c730b310ee5ffc1b42c382b44a0e26"
    ),
    "observability_cli": (
        "sha256:2b1c13bba36c9486f768824178d1e2ea8d2b1da019bd21cd1f9ea250d5da34c5"
    ),
    "linux_daemon": (
        "sha256:f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a"
    ),
    "windows_config": (
        "sha256:987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a"
    ),
}
EXP1_EXPECTED_HOST = {
    "computer_name": "DESKTOP-OLP1ADS",
    "os_build_number": 26200,
    "architecture": "x64",
    "logical_processors": 48,
    "total_memory_bytes": 137_438_953_472,
}
_INVOCATION_TIMEOUT_SECONDS = 30.0
_GATEWAY_READY_TIMEOUT_SECONDS = 10.0
_GATEWAY_STOP_TIMEOUT_SECONDS = 10.0
_COLLECTOR_TIMEOUT_SECONDS = 30.0
_MAX_CAPTURE_BYTES = 1024 * 1024
_MAX_TCPIP_EVENT_RECORDS = 1024
_IDENTITY = re.compile(r"[a-z0-9][a-z0-9-]{0,127}\Z")
_NPIPE_NAME = re.compile(r"[A-Za-z0-9/_.-]+\Z")
_NPIPE_PREFIX = "npipe://./pipe/"
_BINARY_FLAG = getattr(os, "O_BINARY", 0)


@dataclass(frozen=True, slots=True)
class QualificationWorkload:
    batches: int
    concurrency: int

    @property
    def invocation_count(self) -> int:
        return self.batches * self.concurrency


PRODUCTION_WORKLOAD = QualificationWorkload(
    batches=EXP1_IPC_BATCH_COUNT,
    concurrency=EXP1_IPC_CONCURRENCY,
)


@dataclass(frozen=True, slots=True)
class InvocationCapture:
    request_id: str
    started_monotonic_ns: int
    ended_monotonic_ns: int
    started_utc_ns: int
    ended_utc_ns: int
    return_code: int | None
    stdout: bytes
    stderr: bytes
    execution_error: str | None = None
    credential_exposed: bool = False


@dataclass(frozen=True, slots=True)
class EventLogCursor:
    phase: str
    captured_monotonic_ns: int
    captured_utc_ns: int
    log_name: str
    last_record_id: int
    source: str = "windows_event_log"


@dataclass(frozen=True, slots=True)
class TcpipEvent:
    event_id: int
    record_id: int
    created_at_utc: str
    provider_name: str = "Tcpip"


@dataclass(frozen=True, slots=True)
class GatewayProcessSample:
    phase: str
    captured_monotonic_ns: int
    captured_utc_ns: int
    pid: int
    completed_batches: int
    handle_count: int
    private_bytes: int
    rss_bytes: int
    source: str = "windows_get_process"


@dataclass(frozen=True, slots=True)
class OwnedTcpConnection:
    state: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int


@dataclass(frozen=True, slots=True)
class GatewayTcpSample:
    phase: str
    captured_monotonic_ns: int
    captured_utc_ns: int
    pid: int
    completed_batches: int
    connections: tuple[OwnedTcpConnection, ...]
    source: str = "windows_get_net_tcp_connection"


class IpcQualificationRunner(Protocol):
    endpoint: str

    @property
    def gateway_pid(self) -> int | None: ...

    @property
    def executable_paths(self) -> dict[str, str]: ...

    @property
    def sanitized_commands(self) -> dict[str, Any]: ...

    async def start(self) -> None: ...

    async def invoke(self, request_id: str) -> InvocationCapture: ...

    async def stop(self) -> dict[str, Any]: ...


class IpcQualificationCollector(Protocol):
    async def qualification_identity(
        self,
        roots: BenchmarkRoots,
        runner: IpcQualificationRunner,
    ) -> dict[str, Any]: ...

    async def event_cursor(self, phase: str) -> EventLogCursor: ...

    async def tcpip_events(
        self,
        after_record_id: int,
        through_record_id: int,
    ) -> tuple[TcpipEvent, ...]: ...

    async def gateway_process_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayProcessSample: ...

    async def gateway_tcp_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayTcpSample: ...


class QualificationError(RuntimeError):
    pass


async def qualify_exp1_ipc(roots: BenchmarkRoots) -> dict[str, Any]:
    qualification_id = uuid.uuid4().hex
    evidence_root = _create_evidence_root(roots, qualification_id)
    runner = NativeWindowsIpcRunner(roots, evidence_root, qualification_id)
    return await _execute_qualification(
        roots,
        runner,
        NativeWindowsQualificationCollector(),
        evidence_root,
        qualification_id,
        PRODUCTION_WORKLOAD,
    )


async def _execute_qualification(
    roots: BenchmarkRoots,
    runner: IpcQualificationRunner,
    collector: IpcQualificationCollector,
    evidence_root: Path,
    qualification_id: str,
    workload: QualificationWorkload,
) -> dict[str, Any]:
    roots.validate_state()
    _validate_identity(qualification_id)
    _validate_workload(workload)
    _validate_npipe_endpoint(runner.endpoint)
    evidence_root = evidence_root.resolve(strict=True)
    if (
        evidence_root == roots.results
        or not evidence_root.is_relative_to(roots.results)
        or evidence_root.is_symlink()
        or not evidence_root.is_dir()
    ):
        raise QualificationError("qualification evidence root is unsafe")

    invocations_path = evidence_root / "invocations.ndjson"
    writer = _NdjsonWriter(invocations_path)
    started_monotonic_ns = time.monotonic_ns()
    started_utc_ns = time.time_ns()
    attempted = 0
    succeeded = 0
    failed = 0
    batches_started = 0
    batches_completed = 0
    first_failure: dict[str, Any] | None = None
    failure_kind: str | None = None
    gateway_evidence: dict[str, Any] = {}
    identity_evidence: dict[str, Any] | None = None
    pre_cursor: EventLogCursor | None = None
    post_cursor: EventLogCursor | None = None
    process_samples: list[GatewayProcessSample] = []
    tcp_samples: list[GatewayTcpSample] = []
    tcpip_events: tuple[TcpipEvent, ...] = ()
    collector_errors: list[dict[str, str]] = []
    stop_validation_errors: list[dict[str, str]] = []
    runner_started = False
    gateway_pid: int | None = None

    async def collect_checkpoint(phase: str, completed: int) -> None:
        assert gateway_pid is not None
        try:
            sample = await collector.gateway_process_sample(
                gateway_pid,
                phase,
                completed,
            )
            _validate_process_sample(sample, gateway_pid, phase, completed)
            process_samples.append(sample)
        except Exception as error:
            collector_errors.append(
                _collector_error(f"{phase}_process_sample_{completed}", error)
            )
            raise QualificationError(
                f"gateway {phase} process sample unavailable"
            ) from error
        try:
            tcp_sample = await collector.gateway_tcp_sample(
                gateway_pid,
                phase,
                completed,
            )
            _validate_tcp_sample(tcp_sample, gateway_pid, phase, completed)
            tcp_samples.append(tcp_sample)
        except Exception as error:
            collector_errors.append(
                _collector_error(f"{phase}_tcp_sample_{completed}", error)
            )
            raise QualificationError(
                f"gateway {phase} TCP evidence unavailable"
            ) from error
        if tcp_sample.connections:
            raise QualificationError(f"gateway owns TCP endpoints at {phase}")

    try:
        try:
            identity_evidence = await collector.qualification_identity(roots, runner)
            _validate_qualification_identity(identity_evidence, roots, runner)
        except Exception as error:
            collector_errors.append(_collector_error("qualification_identity", error))
            raise QualificationError(
                "qualification identity evidence unavailable"
            ) from error
        try:
            pre_cursor = await collector.event_cursor("pre_readiness")
            _validate_event_cursor(pre_cursor, "pre_readiness")
        except Exception as error:
            collector_errors.append(_collector_error("pre_readiness_cursor", error))
            raise QualificationError(
                "pre-readiness event cursor unavailable"
            ) from error
        await runner.start()
        runner_started = True
        gateway_pid = runner.gateway_pid
        if gateway_pid is None or gateway_pid <= 0:
            raise QualificationError("qualification gateway PID is unavailable")
        await collect_checkpoint("readiness", 0)
        for batch_index in range(workload.batches):
            batches_started += 1
            request_ids = tuple(
                _request_id(qualification_id, batch_index, slot)
                for slot in range(workload.concurrency)
            )
            captures = await asyncio.gather(
                *(_invoke_once(runner, request_id) for request_id in request_ids)
            )
            records = [
                _invocation_record(
                    capture,
                    batch_index=batch_index,
                    slot=slot,
                    invocation_index=batch_index * workload.concurrency + slot,
                )
                for slot, capture in enumerate(captures)
            ]
            writer.append(records)
            attempted += len(records)
            succeeded += sum(record["result"] == "passed" for record in records)
            failed += sum(record["result"] == "failed" for record in records)
            if failed:
                first_failure = next(
                    record for record in records if record["result"] == "failed"
                )
                failure_kind = str(first_failure["validation"])
                break
            batches_completed += 1
            if batches_completed % PROCESS_SAMPLE_EVERY_BATCHES == 0:
                await collect_checkpoint("cadence", batches_completed)
    except Exception as error:  # noqa: BLE001
        failure_kind = f"qualification_error:{type(error).__name__}"
    finally:
        if runner_started and gateway_pid is not None:
            try:
                await collect_checkpoint("pre_stop", batches_completed)
            except Exception as error:  # noqa: BLE001
                if failure_kind is None:
                    failure_kind = f"qualification_error:{type(error).__name__}"
        try:
            gateway_evidence = await runner.stop()
            if runner_started and gateway_pid is not None:
                _validate_stop_evidence(
                    gateway_evidence,
                    runner,
                    gateway_pid,
                )
        except Exception as error:  # noqa: BLE001
            stop_validation_errors.append(
                _collector_error("gateway_stop_evidence", error)
            )
            if failure_kind is None:
                failure_kind = f"gateway_stop_error:{type(error).__name__}"
        if runner_started and gateway_pid is not None:
            try:
                cleanup_tcp = await collector.gateway_tcp_sample(
                    gateway_pid,
                    "after_cleanup",
                    batches_completed,
                )
                _validate_tcp_sample(
                    cleanup_tcp,
                    gateway_pid,
                    "after_cleanup",
                    batches_completed,
                )
                tcp_samples.append(cleanup_tcp)
            except Exception as error:  # noqa: BLE001
                collector_errors.append(
                    _collector_error("after_cleanup_tcp_sample", error)
                )
        try:
            post_cursor = await collector.event_cursor("post_cleanup")
            _validate_event_cursor(post_cursor, "post_cleanup")
        except Exception as error:  # noqa: BLE001
            collector_errors.append(_collector_error("post_cleanup_cursor", error))
        if pre_cursor is not None and post_cursor is not None:
            try:
                tcpip_events = await collector.tcpip_events(
                    pre_cursor.last_record_id,
                    post_cursor.last_record_id,
                )
                _validate_tcpip_events(tcpip_events, pre_cursor, post_cursor)
            except Exception as error:  # noqa: BLE001
                collector_errors.append(_collector_error("tcpip_event_query", error))
        writer.close()

    ended_monotonic_ns = time.monotonic_ns()
    ended_utc_ns = time.time_ns()
    host_evidence, host_gate_failures = _host_evidence(
        pre_cursor=pre_cursor,
        post_cursor=post_cursor,
        identity_evidence=identity_evidence,
        process_samples=process_samples,
        tcp_samples=tcp_samples,
        completed_batches=batches_completed,
        tcpip_events=tcpip_events,
        collector_errors=collector_errors,
        stop_validation_errors=stop_validation_errors,
        runner_started=runner_started,
    )
    if failure_kind is None and host_gate_failures:
        failure_kind = host_gate_failures[0]
    workload_complete = (
        failed == 0
        and attempted == workload.invocation_count
        and succeeded == workload.invocation_count
        and batches_completed == workload.batches
    )
    if failure_kind is None and not workload_complete:
        failure_kind = "incomplete_qualification"
    gate_failures = list(dict.fromkeys([failure_kind, *host_gate_failures]))
    gate_failures = [failure for failure in gate_failures if failure is not None]
    passed = failure_kind is None and not host_gate_failures and workload_complete
    summary = {
        "schema_version": 1,
        "kind": "exp1_ipc_native_cli_qualification",
        "qualification_id": qualification_id,
        "disposition": "qualification_only",
        "qualification_only": QUALIFICATION_ONLY,
        "performance_evidence": PERFORMANCE_EVIDENCE,
        "status": "passed" if passed else "failed",
        "failure_kind": failure_kind,
        "gate_failures": gate_failures,
        "transport": {
            "kind": "windows_named_pipe",
            "endpoint": runner.endpoint,
            "tcp_used": False,
            "fallback_allowed": False,
            "retry_allowed": False,
            "pacing_allowed": False,
            "gateway_count": 1,
        },
        "workload": {
            "operation": "list_sandboxes",
            "executable_role": "manager",
            "native_process_per_invocation": True,
            "planned_invocations": workload.invocation_count,
            "planned_batches": workload.batches,
            "concurrency": workload.concurrency,
            "attempted_invocations": attempted,
            "successful_invocations": succeeded,
            "failed_invocations": failed,
            "batches_started": batches_started,
            "batches_completed": batches_completed,
        },
        "started_monotonic_ns": started_monotonic_ns,
        "ended_monotonic_ns": ended_monotonic_ns,
        "elapsed_ns": ended_monotonic_ns - started_monotonic_ns,
        "started_utc_ns": started_utc_ns,
        "ended_utc_ns": ended_utc_ns,
        "first_failure": first_failure,
        "gateway": gateway_evidence,
        "host_evidence": host_evidence,
        "evidence": {
            "directory": os.fspath(evidence_root),
            "invocations_ndjson": invocations_path.name,
            "invocations_ndjson_bytes": invocations_path.stat().st_size,
            "invocations_ndjson_sha256": _sha256_file(invocations_path),
            "invocation_records": attempted,
            "host_evidence_json": "host-evidence.json",
            "qualification_manifest_json": "qualification-manifest.json",
            "summary": "summary.json",
        },
    }
    host_evidence_path = evidence_root / "host-evidence.json"
    _write_new_json(host_evidence_path, host_evidence)
    summary["evidence"]["host_evidence_json_bytes"] = host_evidence_path.stat().st_size
    summary["evidence"]["host_evidence_json_sha256"] = _sha256_file(host_evidence_path)
    manifest = {
        "schema_version": 1,
        "kind": "exp1_ipc_qualification_manifest",
        "qualification_id": qualification_id,
        "qualification_only": QUALIFICATION_ONLY,
        "performance_evidence": PERFORMANCE_EVIDENCE,
        "status": "passed" if passed else "failed",
        "gate_failures": gate_failures,
        "transport": summary["transport"],
        "workload": summary["workload"],
        "started_monotonic_ns": started_monotonic_ns,
        "ended_monotonic_ns": ended_monotonic_ns,
        "started_utc_ns": started_utc_ns,
        "ended_utc_ns": ended_utc_ns,
        "gateway_pid": gateway_pid,
        "gateway_stop": gateway_evidence,
        "identity": identity_evidence,
        "policy": host_evidence["policy"],
        "event_log": host_evidence["event_log"],
        "gateway_process": host_evidence["gateway_process"],
        "gateway_tcp": host_evidence["gateway_tcp"],
        "artifacts": {
            "invocations_ndjson": {
                "path": invocations_path.name,
                "bytes": invocations_path.stat().st_size,
                "sha256": _sha256_file(invocations_path),
            },
            "host_evidence_json": {
                "path": host_evidence_path.name,
                "bytes": host_evidence_path.stat().st_size,
                "sha256": _sha256_file(host_evidence_path),
            },
        },
    }
    manifest_path = evidence_root / "qualification-manifest.json"
    _write_new_json(manifest_path, manifest)
    summary["evidence"]["qualification_manifest_json_bytes"] = (
        manifest_path.stat().st_size
    )
    summary["evidence"]["qualification_manifest_json_sha256"] = _sha256_file(
        manifest_path
    )
    summary_path = evidence_root / "summary.json"
    _write_new_json(summary_path, summary)
    return summary


class NativeWindowsIpcRunner:
    def __init__(
        self,
        roots: BenchmarkRoots,
        evidence_root: Path,
        qualification_id: str,
    ) -> None:
        if os.name != "nt":
            raise QualificationError(
                "qualify-exp1-ipc requires native Windows execution"
            )
        self.endpoint = f"{_NPIPE_PREFIX}ephemeral-sandbox-exp1-ipc-{qualification_id}"
        self._roots = roots
        self._evidence_root = evidence_root
        self._gateway = _prebuilt_executable(roots, "sandbox-gateway")
        self._manager = _prebuilt_executable(roots, "sandbox-manager-cli")
        self._runtime = _prebuilt_executable(roots, "sandbox-runtime-cli")
        self._observability = _prebuilt_executable(
            roots,
            "sandbox-observability-cli",
        )
        self._auth_token = secrets.token_urlsafe(48)
        self._pid_path = evidence_root / "gateway.pid"
        self._process: asyncio.subprocess.Process | None = None
        self._stdout_digest: asyncio.Task[dict[str, Any]] | None = None
        self._stderr_digest: asyncio.Task[dict[str, Any]] | None = None

    @property
    def gateway_pid(self) -> int | None:
        return None if self._process is None else self._process.pid

    @property
    def executable_paths(self) -> dict[str, str]:
        return {
            "gateway": os.fspath(self._gateway),
            "manager_cli": os.fspath(self._manager),
            "runtime_cli": os.fspath(self._runtime),
            "observability_cli": os.fspath(self._observability),
        }

    @property
    def sanitized_commands(self) -> dict[str, Any]:
        working_directory = os.fspath(self._roots.product_bin_dir.parent)
        return {
            "gateway_serve": {
                "executable_path": os.fspath(self._gateway),
                "argv": [
                    "serve",
                    "--backend",
                    "none",
                    "--gateway-endpoint",
                    self.endpoint,
                    "--auth-token=<redacted>",
                    "--pid-file",
                    os.fspath(self._pid_path),
                ],
                "working_directory": working_directory,
                "stdin": "null",
                "stdout": "pipe_digest_only",
                "stderr": "pipe_digest_only",
            },
            "manager_list_sandboxes": {
                "executable_path": os.fspath(self._manager),
                "argv_template": [
                    "--gateway-endpoint",
                    self.endpoint,
                    "--gateway-auth-token=<redacted>",
                    "--request-id",
                    "<unique-request-id>",
                    "list_sandboxes",
                ],
                "working_directory": working_directory,
                "stdin": "null",
                "stdout": "strict_single_json_line_hash_only",
                "stderr": "must_be_empty_hash_only",
            },
        }

    async def start(self) -> None:
        if self._process is not None:
            raise QualificationError("qualification gateway was already started")
        self._process = await asyncio.create_subprocess_exec(
            os.fspath(self._gateway),
            "serve",
            "--backend",
            "none",
            "--gateway-endpoint",
            self.endpoint,
            f"--auth-token={self._auth_token}",
            "--pid-file",
            os.fspath(self._pid_path),
            cwd=self._roots.product_bin_dir.parent,
            env=_native_environment(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert self._process.stdout is not None
        assert self._process.stderr is not None
        self._stdout_digest = asyncio.create_task(_digest_stream(self._process.stdout))
        self._stderr_digest = asyncio.create_task(_digest_stream(self._process.stderr))
        try:
            await asyncio.wait_for(
                self._wait_until_ready(),
                timeout=_GATEWAY_READY_TIMEOUT_SECONDS,
            )
        except Exception:
            await self.stop()
            raise

    async def invoke(self, request_id: str) -> InvocationCapture:
        _validate_identity(request_id)
        started_monotonic_ns = time.monotonic_ns()
        started_utc_ns = time.time_ns()
        process: asyncio.subprocess.Process | None = None
        stdout = b""
        stderr = b""
        return_code: int | None = None
        execution_error: str | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                os.fspath(self._manager),
                "--gateway-endpoint",
                self.endpoint,
                f"--gateway-auth-token={self._auth_token}",
                "--request-id",
                request_id,
                "list_sandboxes",
                cwd=self._roots.product_bin_dir.parent,
                env=_native_environment(),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=_INVOCATION_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                process.kill()
                stdout, stderr = await process.communicate()
                execution_error = "timeout"
            return_code = process.returncode
        except OSError:
            execution_error = "process_creation_failed"
        ended_monotonic_ns = time.monotonic_ns()
        ended_utc_ns = time.time_ns()
        credential = self._auth_token.encode()
        return InvocationCapture(
            request_id=request_id,
            started_monotonic_ns=started_monotonic_ns,
            ended_monotonic_ns=ended_monotonic_ns,
            started_utc_ns=started_utc_ns,
            ended_utc_ns=ended_utc_ns,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            execution_error=execution_error,
            credential_exposed=credential in stdout or credential in stderr,
        )

    async def stop(self) -> dict[str, Any]:
        process = self._process
        termination = "not_started"
        if process is not None and process.returncode is None:
            termination = "terminate"
            process.terminate()
            try:
                await asyncio.wait_for(
                    process.wait(),
                    timeout=_GATEWAY_STOP_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                termination = "kill_after_terminate_timeout"
                process.kill()
                await process.wait()
        elif process is not None:
            termination = "already_exited"
        stdout = (
            await self._stdout_digest
            if self._stdout_digest is not None
            else _empty_stream_digest()
        )
        stderr = (
            await self._stderr_digest
            if self._stderr_digest is not None
            else _empty_stream_digest()
        )
        try:
            self._pid_path.unlink()
        except FileNotFoundError:
            pass
        return {
            "schema_version": 1,
            "gateway_pid": None if process is None else process.pid,
            "executable_path": os.fspath(self._gateway),
            "process_exited": process is not None and process.returncode is not None,
            "pid_file_removed": not self._pid_path.exists(),
            "sanitized_command": self.sanitized_commands["gateway_serve"],
            "termination": termination,
            "return_code": None if process is None else process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "auth_token_recorded": False,
        }

    async def _wait_until_ready(self) -> None:
        assert self._process is not None
        while True:
            if self._pid_path.is_file():
                value = self._pid_path.read_text(encoding="utf-8").strip()
                if value == str(self._process.pid):
                    return
                raise QualificationError("qualification gateway PID marker is invalid")
            if self._process.returncode is not None:
                raise QualificationError(
                    "qualification gateway exited before readiness"
                )
            await asyncio.sleep(0.01)


class NativeWindowsQualificationCollector:
    async def qualification_identity(
        self,
        roots: BenchmarkRoots,
        runner: IpcQualificationRunner,
    ) -> dict[str, Any]:
        commit_output = await _run_strict_command(
            ("git", "rev-parse", "HEAD"),
            cwd=roots.product_root,
        )
        try:
            commit = commit_output.decode("ascii").strip()
        except UnicodeDecodeError as error:
            raise QualificationError("product commit identity is invalid") from error
        if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise QualificationError("product commit identity is invalid")
        branch_output = await _run_strict_command(
            ("git", "branch", "--show-current"),
            cwd=roots.product_root,
        )
        try:
            branch = branch_output.decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise QualificationError("product branch identity is invalid") from error
        if not branch:
            raise QualificationError("product branch identity is invalid")
        status = await _run_strict_command(
            ("git", "status", "--porcelain=v1", "-z"),
            cwd=roots.product_root,
        )
        paper_commit_output = await _run_strict_command(
            ("git", "rev-parse", "HEAD"),
            cwd=roots.test_repository_root,
        )
        try:
            paper_commit = paper_commit_output.decode("ascii").strip()
        except UnicodeDecodeError as error:
            raise QualificationError("paper commit identity is invalid") from error
        if re.fullmatch(r"[0-9a-f]{40}", paper_commit) is None:
            raise QualificationError("paper commit identity is invalid")
        paper_status = await _run_strict_command(
            (
                "git",
                "status",
                "--porcelain=v1",
                "-z",
                "--",
                *PAPER_FROZEN_SCOPE,
                *BENCHMARK_GIT_EXCLUSIONS,
            ),
            cwd=roots.test_repository_root,
        )

        package_directory = roots.product_bin_dir.parent.resolve(strict=True)
        package_zip = package_directory.with_suffix(".zip")
        _require_safe_directory(package_directory)
        _require_safe_file(package_zip)
        expected_package_name = f"windows-exp1-{commit[:8]}"
        executable_paths = runner.executable_paths
        if set(executable_paths) != {
            "gateway",
            "manager_cli",
            "runtime_cli",
            "observability_cli",
        }:
            raise QualificationError("qualification executable identities are invalid")
        executables = {
            role: _file_identity(Path(path), roots.product_bin_dir)
            for role, path in executable_paths.items()
        }
        packaged_support = {
            "linux_daemon": _file_identity(
                package_directory / "dist" / "sandbox-daemon-linux-amd64",
                package_directory,
            ),
            "windows_config": _file_identity(
                package_directory / "config" / "windows-amd64.yml",
                package_directory,
            ),
        }

        qualifier_path = Path(__file__).resolve(strict=True)
        cli_path = qualifier_path.with_name("cli.py").resolve(strict=True)
        launcher_path = (
            roots.product_bin_dir / "start-sandbox-windows-docker-gateway.ps1"
        )
        qualifier_test_path = (
            roots.benchmark_source_root
            / "backend"
            / "tests"
            / "unit"
            / "test_ipc_qualification.py"
        )
        amendment_path = (
            roots.test_repository_root
            / "experiments"
            / "exp1-v1.1-protocol-amendment.md"
        )
        sources = {
            "ipc_qualification": _file_identity(
                qualifier_path,
                roots.test_repository_root,
            ),
            "benchmark_cli": _file_identity(cli_path, roots.test_repository_root),
            "packaged_gateway_launcher": _file_identity(
                launcher_path,
                roots.product_bin_dir,
            ),
            "ipc_qualification_test": _file_identity(
                qualifier_test_path,
                roots.test_repository_root,
            ),
            "protocol_amendment": _file_identity(
                amendment_path,
                roots.test_repository_root,
            ),
        }
        host = await self._host_identity()
        commands = _expected_sanitized_commands(roots, runner)
        return {
            "schema_version": 1,
            "captured_monotonic_ns": time.monotonic_ns(),
            "captured_utc_ns": time.time_ns(),
            "product": {
                "commit": commit,
                "branch": branch,
                "status_clean": not status,
                "status_bytes": len(status),
                "status_sha256": _sha256_bytes(status),
                "package_directory": os.fspath(package_directory),
                "package_directory_name": package_directory.name,
                "expected_package_directory_name": expected_package_name,
                "package_name_matches_commit": (
                    package_directory.name == expected_package_name
                ),
                "package_zip_path": os.fspath(package_zip),
                "package_zip_bytes": package_zip.stat().st_size,
                "package_zip_sha256": _sha256_file(package_zip),
            },
            "paper": {
                "commit": paper_commit,
                "scoped_status_clean": not paper_status,
                "scoped_status_bytes": len(paper_status),
                "scoped_status_sha256": _sha256_bytes(paper_status),
                "paper_root": os.fspath(roots.test_repository_root),
                "frozen_scope": list(PAPER_FROZEN_SCOPE),
                "generated_exclusions": list(BENCHMARK_GIT_EXCLUSIONS),
                "policy_source": (
                    "experiments/scripts/archive_exp1_run.py:"
                    "PAPER_FROZEN_SCOPE+BENCHMARK_GIT_EXCLUSIONS"
                ),
            },
            "executables": executables,
            "packaged_support": packaged_support,
            "qualifier_sources": sources,
            "host": host,
            "build": {
                "package_identity": package_directory.name,
                "product_commit": commit,
                "python_executable": os.fspath(
                    Path(sys.executable).resolve(strict=True)
                ),
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "python_architecture": platform.machine().lower(),
                "package_build_command": [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    ".\\bin\\package-windows-amd64-release.ps1",
                    "-PackageName",
                    package_directory.name,
                    "-OutDir",
                    "target",
                    "-Profile",
                    "release",
                ],
            },
            "sanitized_commands": commands,
        }

    async def _host_identity(self) -> dict[str, Any]:
        value = await _run_powershell_json(
            """
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
[pscustomobject]@{
    computer_name = [string]$computer.Name
    os_caption = [string]$os.Caption
    os_version = [string]$os.Version
    os_build_number = [long]$os.BuildNumber
    architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    logical_processors = [long]$computer.NumberOfLogicalProcessors
    total_memory_bytes = [long]$computer.TotalPhysicalMemory
} | ConvertTo-Json -Compress
""".strip()
        )
        keys = {
            "computer_name",
            "os_caption",
            "os_version",
            "os_build_number",
            "architecture",
            "logical_processors",
            "total_memory_bytes",
        }
        _require_exact_keys(value, keys)
        if (
            any(
                not isinstance(value[name], str) or not value[name].strip()
                for name in (
                    "computer_name",
                    "os_caption",
                    "os_version",
                    "architecture",
                )
            )
            or not _is_positive_int(value["os_build_number"])
            or not _is_positive_int(value["logical_processors"])
            or not _is_positive_int(value["total_memory_bytes"])
        ):
            raise QualificationError("Windows host/build identity is invalid")
        return value

    async def event_cursor(self, phase: str) -> EventLogCursor:
        _validate_phase(phase, {"pre_readiness", "post_cleanup"})
        value = await _run_powershell_json(
            """
$ErrorActionPreference = 'Stop'
$event = Get-WinEvent -LogName System -MaxEvents 1 -ErrorAction Stop
[pscustomobject]@{
    log_name = 'System'
    last_record_id = [long]$event.RecordId
} | ConvertTo-Json -Compress
""".strip()
        )
        _require_exact_keys(value, {"log_name", "last_record_id"})
        if value["log_name"] != "System" or not _is_nonnegative_int(
            value["last_record_id"]
        ):
            raise QualificationError("Windows event cursor response is invalid")
        return EventLogCursor(
            phase=phase,
            captured_monotonic_ns=time.monotonic_ns(),
            captured_utc_ns=time.time_ns(),
            log_name="System",
            last_record_id=value["last_record_id"],
        )

    async def tcpip_events(
        self,
        after_record_id: int,
        through_record_id: int,
    ) -> tuple[TcpipEvent, ...]:
        if (
            not _is_nonnegative_int(after_record_id)
            or not _is_nonnegative_int(through_record_id)
            or through_record_id < after_record_id
        ):
            raise QualificationError("Windows event query bounds are invalid")
        xpath = (
            "*[System[Provider[@Name='Tcpip'] and "
            "(EventID=4227 or EventID=4231) and "
            f"EventRecordID > {after_record_id} and "
            f"EventRecordID <= {through_record_id}]]"
        )
        value = await _run_powershell_json(
            f"""
$ErrorActionPreference = 'Stop'
$query = [System.Diagnostics.Eventing.Reader.EventLogQuery]::new(
    'System',
    [System.Diagnostics.Eventing.Reader.PathType]::LogName,
    "{xpath}"
)
$reader = [System.Diagnostics.Eventing.Reader.EventLogReader]::new($query)
$records = [System.Collections.Generic.List[object]]::new()
try {{
    while ($record = $reader.ReadEvent()) {{
        try {{
            if ($records.Count -ge {_MAX_TCPIP_EVENT_RECORDS}) {{
                throw 'TCP/IP qualification event limit exceeded'
            }}
            $records.Add([pscustomobject]@{{
                event_id = [long]$record.Id
                record_id = [long]$record.RecordId
                created_at_utc = $record.TimeCreated.ToUniversalTime().ToString('O')
                provider_name = $record.ProviderName
            }})
        }} finally {{
            $record.Dispose()
        }}
    }}
}} finally {{
    $reader.Dispose()
}}
ConvertTo-Json -InputObject $records.ToArray() -Compress
""".strip()
        )
        if not isinstance(value, list):
            raise QualificationError("Windows TCP/IP event response is invalid")
        records: list[TcpipEvent] = []
        for item in value:
            _require_exact_keys(
                item,
                {"event_id", "record_id", "created_at_utc", "provider_name"},
            )
            if (
                not _is_nonnegative_int(item["event_id"])
                or not _is_nonnegative_int(item["record_id"])
                or not isinstance(item["created_at_utc"], str)
                or not item["created_at_utc"]
                or item["provider_name"] != "Tcpip"
            ):
                raise QualificationError("Windows TCP/IP event record is invalid")
            records.append(
                TcpipEvent(
                    event_id=item["event_id"],
                    record_id=item["record_id"],
                    created_at_utc=item["created_at_utc"],
                )
            )
        return tuple(sorted(records, key=lambda record: record.record_id))

    async def gateway_process_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayProcessSample:
        _validate_checkpoint(phase, completed_batches, include_cleanup=False)
        if not _is_positive_int(pid):
            raise QualificationError("gateway process PID is invalid")
        value = await _run_powershell_json(
            f"""
$ErrorActionPreference = 'Stop'
$process = Get-Process -Id {pid} -ErrorAction Stop
[pscustomobject]@{{
    pid = [long]$process.Id
    handle_count = [long]$process.HandleCount
    private_bytes = [long]$process.PrivateMemorySize64
    rss_bytes = [long]$process.WorkingSet64
}} | ConvertTo-Json -Compress
""".strip()
        )
        _require_exact_keys(
            value,
            {"pid", "handle_count", "private_bytes", "rss_bytes"},
        )
        if (
            value["pid"] != pid
            or not _is_nonnegative_int(value["handle_count"])
            or not _is_nonnegative_int(value["private_bytes"])
            or not _is_nonnegative_int(value["rss_bytes"])
        ):
            raise QualificationError("Windows gateway process sample is invalid")
        return GatewayProcessSample(
            phase=phase,
            captured_monotonic_ns=time.monotonic_ns(),
            captured_utc_ns=time.time_ns(),
            pid=pid,
            completed_batches=completed_batches,
            handle_count=value["handle_count"],
            private_bytes=value["private_bytes"],
            rss_bytes=value["rss_bytes"],
        )

    async def gateway_tcp_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayTcpSample:
        _validate_checkpoint(phase, completed_batches, include_cleanup=True)
        if not _is_positive_int(pid):
            raise QualificationError("gateway TCP owner PID is invalid")
        value = await _run_powershell_json(
            f"""
$ErrorActionPreference = 'Stop'
$connections = @(
    Get-NetTCPConnection -ErrorAction Stop |
    Where-Object {{ $_.OwningProcess -eq {pid} }} |
    ForEach-Object {{
        [pscustomobject]@{{
            state = [string]$_.State
            local_address = [string]$_.LocalAddress
            local_port = [long]$_.LocalPort
            remote_address = [string]$_.RemoteAddress
            remote_port = [long]$_.RemotePort
        }}
    }}
)
if ($connections.Count -gt {_MAX_TCPIP_EVENT_RECORDS}) {{
    throw 'Gateway TCP ownership record limit exceeded'
}}
ConvertTo-Json -InputObject $connections -Compress
""".strip()
        )
        if not isinstance(value, list):
            raise QualificationError("Windows gateway TCP response is invalid")
        connections: list[OwnedTcpConnection] = []
        keys = {
            "state",
            "local_address",
            "local_port",
            "remote_address",
            "remote_port",
        }
        for item in value:
            _require_exact_keys(item, keys)
            if (
                not isinstance(item["state"], str)
                or not item["state"]
                or not isinstance(item["local_address"], str)
                or not item["local_address"]
                or not _is_nonnegative_int(item["local_port"])
                or item["local_port"] > 65_535
                or not isinstance(item["remote_address"], str)
                or not item["remote_address"]
                or not _is_nonnegative_int(item["remote_port"])
                or item["remote_port"] > 65_535
            ):
                raise QualificationError(
                    "Windows gateway TCP ownership record is invalid"
                )
            connections.append(
                OwnedTcpConnection(
                    state=item["state"],
                    local_address=item["local_address"],
                    local_port=item["local_port"],
                    remote_address=item["remote_address"],
                    remote_port=item["remote_port"],
                )
            )
        return GatewayTcpSample(
            phase=phase,
            captured_monotonic_ns=time.monotonic_ns(),
            captured_utc_ns=time.time_ns(),
            pid=pid,
            completed_batches=completed_batches,
            connections=tuple(connections),
        )


async def _invoke_once(
    runner: IpcQualificationRunner,
    request_id: str,
) -> InvocationCapture:
    started_monotonic_ns = time.monotonic_ns()
    started_utc_ns = time.time_ns()
    try:
        capture = await runner.invoke(request_id)
    except Exception as error:  # noqa: BLE001
        ended_monotonic_ns = time.monotonic_ns()
        ended_utc_ns = time.time_ns()
        return InvocationCapture(
            request_id=request_id,
            started_monotonic_ns=started_monotonic_ns,
            ended_monotonic_ns=ended_monotonic_ns,
            started_utc_ns=started_utc_ns,
            ended_utc_ns=ended_utc_ns,
            return_code=None,
            stdout=b"",
            stderr=b"",
            execution_error=f"runner_error:{type(error).__name__}",
        )
    if capture.request_id != request_id:
        return InvocationCapture(
            request_id=request_id,
            started_monotonic_ns=capture.started_monotonic_ns,
            ended_monotonic_ns=capture.ended_monotonic_ns,
            started_utc_ns=capture.started_utc_ns,
            ended_utc_ns=capture.ended_utc_ns,
            return_code=capture.return_code,
            stdout=capture.stdout,
            stderr=capture.stderr,
            execution_error="request_id_mismatch",
            credential_exposed=capture.credential_exposed,
        )
    return capture


def _host_evidence(
    *,
    pre_cursor: EventLogCursor | None,
    post_cursor: EventLogCursor | None,
    identity_evidence: dict[str, Any] | None,
    process_samples: list[GatewayProcessSample],
    tcp_samples: list[GatewayTcpSample],
    completed_batches: int,
    tcpip_events: tuple[TcpipEvent, ...],
    collector_errors: list[dict[str, str]],
    stop_validation_errors: list[dict[str, str]],
    runner_started: bool,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    if collector_errors:
        failures.append("host_evidence_collection_error")
    if identity_evidence is None or any(
        error["phase"] == "qualification_identity" for error in collector_errors
    ):
        failures.append("qualification_identity_invalid")
    if runner_started and stop_validation_errors:
        failures.append("gateway_stop_evidence_invalid")

    event_query_completed = (
        pre_cursor is not None
        and post_cursor is not None
        and not any(error["phase"] == "tcpip_event_query" for error in collector_errors)
    )
    if not event_query_completed:
        failures.append("tcpip_event_evidence_incomplete")
    elif tcpip_events:
        failures.append("tcpip_event_detected")

    expected_checkpoints = _expected_checkpoint_keys(completed_batches)
    actual_process_checkpoints = [
        (sample.phase, sample.completed_batches) for sample in process_samples
    ]
    process_growth: dict[str, Any] | None = None
    if actual_process_checkpoints != expected_checkpoints:
        failures.append("gateway_process_evidence_incomplete")
    else:
        readiness_sample = process_samples[0]
        final_sample = process_samples[-1]
        limits = {
            "handle_count": MAX_GATEWAY_HANDLE_GROWTH,
            "private_bytes": MAX_GATEWAY_PRIVATE_BYTES_GROWTH,
            "rss_bytes": MAX_GATEWAY_RSS_BYTES_GROWTH,
        }
        peak_decisions = {}
        final_decisions = {}
        for name, limit in limits.items():
            readiness_value = getattr(readiness_sample, name)
            peak_value = max(getattr(sample, name) for sample in process_samples)
            final_value = getattr(final_sample, name)
            peak_decisions[name] = {
                "readiness": readiness_value,
                "peak": peak_value,
                "growth": peak_value - readiness_value,
                "maximum_allowed_growth": limit,
                "within_bound": peak_value - readiness_value <= limit,
            }
            final_decisions[name] = {
                "readiness": readiness_value,
                "final": final_value,
                "growth": final_value - readiness_value,
                "maximum_allowed_growth": limit,
                "within_bound": final_value - readiness_value <= limit,
            }
        process_growth = {
            "peak_over_readiness": {
                "decisions": peak_decisions,
                "passed": all(
                    decision["within_bound"] for decision in peak_decisions.values()
                ),
            },
            "final_pre_stop_over_readiness": {
                "decisions": final_decisions,
                "passed": all(
                    decision["within_bound"] for decision in final_decisions.values()
                ),
            },
        }
        for metric, label in (
            ("handle_count", "handle"),
            ("private_bytes", "private_bytes"),
            ("rss_bytes", "rss"),
        ):
            if not peak_decisions[metric]["within_bound"]:
                failures.append(f"gateway_{label}_peak_growth_exceeded")
            if not final_decisions[metric]["within_bound"]:
                failures.append(f"gateway_{label}_final_growth_exceeded")

    expected_tcp_checkpoints = [
        *expected_checkpoints,
        ("after_cleanup", completed_batches),
    ]
    actual_tcp_checkpoints = [
        (sample.phase, sample.completed_batches) for sample in tcp_samples
    ]
    tcp_complete = actual_tcp_checkpoints == expected_tcp_checkpoints
    if not tcp_complete:
        failures.append("gateway_tcp_evidence_incomplete")
    owned_tcp_count = sum(len(sample.connections) for sample in tcp_samples)
    if owned_tcp_count:
        failures.append("gateway_owned_tcp_detected")

    failures = list(dict.fromkeys(failures))
    evidence = {
        "schema_version": 1,
        "kind": "exp1_ipc_host_qualification_evidence",
        "qualification_only": QUALIFICATION_ONLY,
        "performance_evidence": PERFORMANCE_EVIDENCE,
        "status": "passed" if not failures else "failed",
        "gate_failures": failures,
        "policy": {
            "source": RESOURCE_GROWTH_POLICY_SOURCE,
            "source_requirement": (
                "zero new qualifier-attributable System/Tcpip 4227/4231 "
                "events, zero gateway-owned TCP endpoints, bounded gateway "
                "process handle/private/RSS growth, and complete cleanup evidence"
            ),
            "threshold_origin": (
                "fixed preregistered fail-closed qualification policy; not a "
                "performance result"
            ),
            "handle_threshold_basis": (
                "one handle per maximum pending named-pipe instance; product "
                "listener cap is 32"
            ),
            "memory_threshold_basis": (
                "fixed 16 MiB post-readiness allowance for both private and "
                "resident bytes; any larger retained growth blocks freeze"
            ),
            "event_ids": list(TCPIP_EVENT_IDS),
            "process_sample_every_completed_batches": PROCESS_SAMPLE_EVERY_BATCHES,
            "process_growth_gates": [
                "peak_over_readiness",
                "final_pre_stop_over_readiness",
            ],
            "maximum_post_readiness_growth": {
                "handle_count": MAX_GATEWAY_HANDLE_GROWTH,
                "private_bytes": MAX_GATEWAY_PRIVATE_BYTES_GROWTH,
                "rss_bytes": MAX_GATEWAY_RSS_BYTES_GROWTH,
            },
            "missing_or_invalid_evidence_fails": True,
        },
        "event_log": {
            "log_name": "System",
            "provider_name": "Tcpip",
            "attribution_policy": (
                "every new matching event in the qualification cursor interval "
                "is conservatively treated as qualifier-attributable"
            ),
            "pre_readiness_cursor": _event_cursor_record(pre_cursor),
            "post_cleanup_cursor": _event_cursor_record(post_cursor),
            "query_interval": "(pre_readiness_record_id, post_cleanup_record_id]",
            "query_completed": event_query_completed,
            "new_event_count": len(tcpip_events),
            "events": [_tcpip_event_record(event) for event in tcpip_events],
            "passed": event_query_completed and not tcpip_events,
        },
        "gateway_process": {
            "expected_checkpoints": [
                {"phase": phase, "completed_batches": batches}
                for phase, batches in expected_checkpoints
            ],
            "samples": [_process_sample_record(sample) for sample in process_samples],
            "growth": process_growth,
            "passed": (
                process_growth is not None
                and process_growth["peak_over_readiness"]["passed"]
                and process_growth["final_pre_stop_over_readiness"]["passed"]
            ),
        },
        "gateway_tcp": {
            "expected_checkpoints": [
                {"phase": phase, "completed_batches": batches}
                for phase, batches in expected_tcp_checkpoints
            ],
            "samples": [_tcp_sample_record(sample) for sample in tcp_samples],
            "owned_connection_count": owned_tcp_count,
            "passed": tcp_complete and owned_tcp_count == 0,
        },
        "gateway_stop": {
            "required": runner_started,
            "validation_passed": runner_started and not stop_validation_errors,
            "validation_errors": stop_validation_errors,
        },
        "identity": identity_evidence,
        "collector_errors": collector_errors,
    }
    return evidence, failures


def _expected_checkpoint_keys(completed_batches: int) -> list[tuple[str, int]]:
    return [
        ("readiness", 0),
        *[
            ("cadence", batch)
            for batch in range(
                PROCESS_SAMPLE_EVERY_BATCHES,
                completed_batches + 1,
                PROCESS_SAMPLE_EVERY_BATCHES,
            )
        ],
        ("pre_stop", completed_batches),
    ]


def _event_cursor_record(cursor: EventLogCursor | None) -> dict[str, Any] | None:
    if cursor is None:
        return None
    return {
        "phase": cursor.phase,
        "captured_monotonic_ns": cursor.captured_monotonic_ns,
        "captured_utc_ns": cursor.captured_utc_ns,
        "log_name": cursor.log_name,
        "last_record_id": cursor.last_record_id,
        "source": cursor.source,
    }


def _tcpip_event_record(event: TcpipEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "record_id": event.record_id,
        "created_at_utc": event.created_at_utc,
        "provider_name": event.provider_name,
    }


def _process_sample_record(
    sample: GatewayProcessSample | None,
) -> dict[str, Any] | None:
    if sample is None:
        return None
    return {
        "phase": sample.phase,
        "captured_monotonic_ns": sample.captured_monotonic_ns,
        "captured_utc_ns": sample.captured_utc_ns,
        "pid": sample.pid,
        "completed_batches": sample.completed_batches,
        "handle_count": sample.handle_count,
        "private_bytes": sample.private_bytes,
        "rss_bytes": sample.rss_bytes,
        "source": sample.source,
    }


def _tcp_sample_record(sample: GatewayTcpSample) -> dict[str, Any]:
    return {
        "phase": sample.phase,
        "captured_monotonic_ns": sample.captured_monotonic_ns,
        "captured_utc_ns": sample.captured_utc_ns,
        "pid": sample.pid,
        "completed_batches": sample.completed_batches,
        "source": sample.source,
        "connection_count": len(sample.connections),
        "connections": [
            {
                "state": connection.state,
                "local_address": connection.local_address,
                "local_port": connection.local_port,
                "remote_address": connection.remote_address,
                "remote_port": connection.remote_port,
            }
            for connection in sample.connections
        ],
    }


def _validate_event_cursor(cursor: EventLogCursor, phase: str) -> None:
    if (
        cursor.phase != phase
        or cursor.log_name != "System"
        or cursor.source != "windows_event_log"
        or not _is_positive_int(cursor.captured_monotonic_ns)
        or not _is_positive_int(cursor.captured_utc_ns)
        or not _is_nonnegative_int(cursor.last_record_id)
    ):
        raise QualificationError("Windows event cursor evidence is invalid")


def _validate_process_sample(
    sample: GatewayProcessSample,
    pid: int,
    phase: str,
    completed_batches: int,
) -> None:
    if (
        sample.phase != phase
        or sample.pid != pid
        or sample.completed_batches != completed_batches
        or sample.source != "windows_get_process"
        or not _is_positive_int(sample.captured_monotonic_ns)
        or not _is_positive_int(sample.captured_utc_ns)
        or not _is_nonnegative_int(sample.handle_count)
        or not _is_nonnegative_int(sample.private_bytes)
        or not _is_nonnegative_int(sample.rss_bytes)
    ):
        raise QualificationError("Windows gateway process evidence is invalid")


def _validate_tcp_sample(
    sample: GatewayTcpSample,
    pid: int,
    phase: str,
    completed_batches: int,
) -> None:
    if (
        sample.phase != phase
        or sample.pid != pid
        or sample.completed_batches != completed_batches
        or sample.source != "windows_get_net_tcp_connection"
        or not _is_positive_int(sample.captured_monotonic_ns)
        or not _is_positive_int(sample.captured_utc_ns)
        or not isinstance(sample.connections, tuple)
    ):
        raise QualificationError("Windows gateway TCP evidence is invalid")
    for connection in sample.connections:
        if (
            not isinstance(connection, OwnedTcpConnection)
            or not connection.state
            or not connection.local_address
            or not _is_nonnegative_int(connection.local_port)
            or connection.local_port > 65_535
            or not connection.remote_address
            or not _is_nonnegative_int(connection.remote_port)
            or connection.remote_port > 65_535
        ):
            raise QualificationError("Windows gateway TCP evidence is invalid")


def _validate_stop_evidence(
    evidence: dict[str, Any],
    runner: IpcQualificationRunner,
    gateway_pid: int,
) -> None:
    _require_exact_keys(
        evidence,
        {
            "schema_version",
            "gateway_pid",
            "executable_path",
            "process_exited",
            "pid_file_removed",
            "sanitized_command",
            "termination",
            "return_code",
            "stdout",
            "stderr",
            "auth_token_recorded",
        },
    )
    if (
        evidence["schema_version"] != 1
        or evidence["gateway_pid"] != gateway_pid
        or evidence["executable_path"] != runner.executable_paths["gateway"]
        or evidence["process_exited"] is not True
        or evidence["pid_file_removed"] is not True
        or evidence["sanitized_command"] != runner.sanitized_commands["gateway_serve"]
        or evidence["termination"]
        not in {
            "terminate",
            "already_exited",
        }
        or type(evidence["return_code"]) is not int
        or evidence["auth_token_recorded"] is not False
    ):
        raise QualificationError("gateway stop evidence is invalid")
    _validate_stream_digest(evidence["stdout"])
    _validate_stream_digest(evidence["stderr"])


def _validate_stream_digest(value: Any) -> None:
    _require_exact_keys(value, {"bytes", "sha256"})
    if (
        not _is_nonnegative_int(value["bytes"])
        or not isinstance(value["sha256"], str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", value["sha256"]) is None
    ):
        raise QualificationError("gateway stream digest evidence is invalid")


def _validate_qualification_identity(
    value: dict[str, Any],
    roots: BenchmarkRoots,
    runner: IpcQualificationRunner,
) -> None:
    _require_exact_keys(
        value,
        {
            "schema_version",
            "captured_monotonic_ns",
            "captured_utc_ns",
            "product",
            "paper",
            "executables",
            "packaged_support",
            "qualifier_sources",
            "host",
            "build",
            "sanitized_commands",
        },
    )
    if (
        value["schema_version"] != 1
        or not _is_positive_int(value["captured_monotonic_ns"])
        or not _is_positive_int(value["captured_utc_ns"])
    ):
        raise QualificationError("qualification identity evidence is invalid")

    product = value["product"]
    _require_exact_keys(
        product,
        {
            "commit",
            "branch",
            "status_clean",
            "status_bytes",
            "status_sha256",
            "package_directory",
            "package_directory_name",
            "expected_package_directory_name",
            "package_name_matches_commit",
            "package_zip_path",
            "package_zip_bytes",
            "package_zip_sha256",
        },
    )
    commit = product["commit"]
    expected_package = f"windows-exp1-{commit[:8]}" if isinstance(commit, str) else ""
    package_directory = os.fspath(roots.product_bin_dir.parent)
    if (
        not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
        or commit != PREREGISTERED_PRODUCT_COMMIT
        or product["branch"] != PREREGISTERED_PRODUCT_BRANCH
        or product["status_clean"] is not True
        or product["status_bytes"] != 0
        or product["status_sha256"] != _sha256_bytes(b"")
        or product["package_directory"] != package_directory
        or product["package_directory_name"] != expected_package
        or product["expected_package_directory_name"] != expected_package
        or product["package_name_matches_commit"] is not True
        or product["package_zip_path"] != f"{package_directory}.zip"
        or not _is_positive_int(product["package_zip_bytes"])
        or not _is_sha256(product["package_zip_sha256"])
        or product["package_zip_sha256"] != PREREGISTERED_PACKAGE_SHA256
    ):
        raise QualificationError("product/package identity evidence is invalid")

    paper = value["paper"]
    _require_exact_keys(
        paper,
        {
            "commit",
            "scoped_status_clean",
            "scoped_status_bytes",
            "scoped_status_sha256",
            "paper_root",
            "frozen_scope",
            "generated_exclusions",
            "policy_source",
        },
    )
    if (
        not isinstance(paper["commit"], str)
        or re.fullmatch(r"[0-9a-f]{40}", paper["commit"]) is None
        or paper["scoped_status_clean"] is not True
        or paper["scoped_status_bytes"] != 0
        or paper["scoped_status_sha256"] != _sha256_bytes(b"")
        or paper["paper_root"] != os.fspath(roots.test_repository_root)
        or paper["frozen_scope"] != list(PAPER_FROZEN_SCOPE)
        or paper["generated_exclusions"] != list(BENCHMARK_GIT_EXCLUSIONS)
        or paper["policy_source"]
        != (
            "experiments/scripts/archive_exp1_run.py:"
            "PAPER_FROZEN_SCOPE+BENCHMARK_GIT_EXCLUSIONS"
        )
    ):
        raise QualificationError("paper scoped identity evidence is invalid")

    executables = value["executables"]
    if not isinstance(executables, dict) or set(executables) != set(
        runner.executable_paths
    ):
        raise QualificationError("executable identity evidence is invalid")
    for role, expected_path in runner.executable_paths.items():
        _validate_file_identity(executables[role], expected_path)
        if executables[role]["sha256"] != PREREGISTERED_ARTIFACT_SHA256[role]:
            raise QualificationError("preregistered executable identity drifted")

    packaged_support = value["packaged_support"]
    if not isinstance(packaged_support, dict) or set(packaged_support) != {
        "linux_daemon",
        "windows_config",
    }:
        raise QualificationError("packaged support identity evidence is invalid")
    package_directory_path = Path(package_directory)
    for role, relative in (
        ("linux_daemon", Path("dist/sandbox-daemon-linux-amd64")),
        ("windows_config", Path("config/windows-amd64.yml")),
    ):
        _validate_file_identity(
            packaged_support[role],
            os.fspath(package_directory_path / relative),
        )
        if packaged_support[role]["sha256"] != PREREGISTERED_ARTIFACT_SHA256[role]:
            raise QualificationError("preregistered support identity drifted")

    qualifier_path = os.fspath(Path(__file__).resolve(strict=True))
    sources = value["qualifier_sources"]
    if not isinstance(sources, dict) or set(sources) != {
        "ipc_qualification",
        "benchmark_cli",
        "packaged_gateway_launcher",
        "ipc_qualification_test",
        "protocol_amendment",
    }:
        raise QualificationError("qualifier source identity evidence is invalid")
    _validate_file_identity(sources["ipc_qualification"], qualifier_path)
    _validate_file_identity(
        sources["benchmark_cli"],
        os.fspath(Path(qualifier_path).with_name("cli.py")),
    )
    _validate_file_identity(
        sources["packaged_gateway_launcher"],
        os.fspath(roots.product_bin_dir / "start-sandbox-windows-docker-gateway.ps1"),
    )
    _validate_file_identity(
        sources["ipc_qualification_test"],
        os.fspath(
            roots.benchmark_source_root
            / "backend"
            / "tests"
            / "unit"
            / "test_ipc_qualification.py"
        ),
    )
    _validate_file_identity(
        sources["protocol_amendment"],
        os.fspath(
            roots.test_repository_root
            / "experiments"
            / "exp1-v1.1-protocol-amendment.md"
        ),
    )

    host = value["host"]
    _require_exact_keys(
        host,
        {
            "computer_name",
            "os_caption",
            "os_version",
            "os_build_number",
            "architecture",
            "logical_processors",
            "total_memory_bytes",
        },
    )
    if (
        any(
            not isinstance(host[name], str) or not host[name].strip()
            for name in (
                "computer_name",
                "os_caption",
                "os_version",
                "architecture",
            )
        )
        or not _is_positive_int(host["os_build_number"])
        or not _is_positive_int(host["logical_processors"])
        or not _is_positive_int(host["total_memory_bytes"])
        or any(host[key] != expected for key, expected in EXP1_EXPECTED_HOST.items())
    ):
        raise QualificationError("host identity evidence is invalid")

    build = value["build"]
    _require_exact_keys(
        build,
        {
            "package_identity",
            "product_commit",
            "python_executable",
            "python_implementation",
            "python_version",
            "python_architecture",
            "package_build_command",
        },
    )
    if (
        build["package_identity"] != expected_package
        or build["product_commit"] != commit
        or not all(
            isinstance(build[field], str) and build[field]
            for field in (
                "python_executable",
                "python_implementation",
                "python_version",
                "python_architecture",
            )
        )
        or build["package_build_command"]
        != [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ".\\bin\\package-windows-amd64-release.ps1",
            "-PackageName",
            expected_package,
            "-OutDir",
            "target",
            "-Profile",
            "release",
        ]
    ):
        raise QualificationError("build identity evidence is invalid")
    if value["sanitized_commands"] != _expected_sanitized_commands(roots, runner):
        raise QualificationError("sanitized command evidence is invalid")


def _validate_file_identity(value: Any, expected_path: str) -> None:
    _require_exact_keys(value, {"path", "bytes", "sha256"})
    if (
        value["path"] != expected_path
        or not _is_positive_int(value["bytes"])
        or not _is_sha256(value["sha256"])
    ):
        raise QualificationError("file identity evidence is invalid")


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    )


def _validate_tcpip_events(
    events: tuple[TcpipEvent, ...],
    pre_cursor: EventLogCursor,
    post_cursor: EventLogCursor,
) -> None:
    if (
        pre_cursor.log_name != post_cursor.log_name
        or post_cursor.last_record_id < pre_cursor.last_record_id
        or len(events) > _MAX_TCPIP_EVENT_RECORDS
    ):
        raise QualificationError("Windows TCP/IP event evidence is invalid")
    record_ids: set[int] = set()
    for event in events:
        if (
            event.event_id not in TCPIP_EVENT_IDS
            or event.provider_name != "Tcpip"
            or not isinstance(event.created_at_utc, str)
            or not event.created_at_utc
            or event.record_id <= pre_cursor.last_record_id
            or event.record_id > post_cursor.last_record_id
            or event.record_id in record_ids
        ):
            raise QualificationError("Windows TCP/IP event evidence is invalid")
        record_ids.add(event.record_id)


async def _run_powershell_json(script: str) -> Any:
    process = await asyncio.create_subprocess_exec(
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
        env=_native_environment(),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=_COLLECTOR_TIMEOUT_SECONDS,
        )
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise QualificationError("Windows evidence collector timed out") from error
    if len(stdout) > _MAX_CAPTURE_BYTES or len(stderr) > _MAX_CAPTURE_BYTES:
        raise QualificationError("Windows evidence collector output is oversized")
    if process.returncode != 0:
        raise QualificationError("Windows evidence collector exited nonzero")
    if stderr:
        raise QualificationError("Windows evidence collector emitted stderr")
    if not stdout.endswith(b"\n") or stdout.count(b"\n") != 1:
        raise QualificationError("Windows evidence collector output framing is invalid")
    try:
        return json.loads(stdout.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(
            "Windows evidence collector output is invalid"
        ) from error


async def _run_strict_command(
    arguments: tuple[str, ...],
    *,
    cwd: Path,
) -> bytes:
    process = await asyncio.create_subprocess_exec(
        *arguments,
        cwd=cwd,
        env=_native_environment(),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=_COLLECTOR_TIMEOUT_SECONDS,
        )
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise QualificationError("identity command timed out") from error
    if len(stdout) > _MAX_CAPTURE_BYTES or len(stderr) > _MAX_CAPTURE_BYTES:
        raise QualificationError("identity command output is oversized")
    if process.returncode != 0:
        raise QualificationError("identity command exited nonzero")
    if stderr:
        raise QualificationError("identity command emitted stderr")
    return stdout


def _expected_sanitized_commands(
    roots: BenchmarkRoots,
    runner: IpcQualificationRunner,
) -> dict[str, Any]:
    return {
        **runner.sanitized_commands,
        "product_commit": {
            "executable": "git",
            "argv": ["rev-parse", "HEAD"],
            "working_directory": os.fspath(roots.product_root),
        },
        "product_status": {
            "executable": "git",
            "argv": ["status", "--porcelain=v1", "-z"],
            "working_directory": os.fspath(roots.product_root),
        },
        "paper_commit": {
            "executable": "git",
            "argv": ["rev-parse", "HEAD"],
            "working_directory": os.fspath(roots.test_repository_root),
        },
        "paper_scoped_status": {
            "executable": "git",
            "argv": [
                "status",
                "--porcelain=v1",
                "-z",
                "--",
                *PAPER_FROZEN_SCOPE,
                *BENCHMARK_GIT_EXCLUSIONS,
            ],
            "working_directory": os.fspath(roots.test_repository_root),
        },
        "host_identity": {
            "executable": "powershell.exe",
            "script_id": "windows_cim_host_build_identity_v1",
        },
        "event_cursor": {
            "executable": "powershell.exe",
            "script_id": "windows_system_event_log_cursor_v1",
        },
        "tcpip_event_query": {
            "executable": "powershell.exe",
            "script_id": "windows_system_tcpip_4227_4231_cursor_query_v1",
        },
        "gateway_process_sample": {
            "executable": "powershell.exe",
            "script_id": "windows_get_process_handle_private_rss_v1",
        },
        "gateway_tcp_sample": {
            "executable": "powershell.exe",
            "script_id": "windows_get_net_tcp_connection_owner_pid_v1",
        },
    }


def _file_identity(path: Path, parent: Path) -> dict[str, Any]:
    _require_safe_file(path)
    canonical = path.resolve(strict=True)
    if not canonical.is_relative_to(parent):
        raise QualificationError("qualification identity file escaped its root")
    return {
        "path": os.fspath(canonical),
        "bytes": canonical.stat().st_size,
        "sha256": _sha256_file(canonical),
    }


def _require_safe_file(path: Path) -> None:
    try:
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise QualificationError("qualification identity file is missing") from error
    if path.is_symlink() or not path.is_file() or canonical != path:
        raise QualificationError("qualification identity file is unsafe")


def _require_safe_directory(path: Path) -> None:
    try:
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise QualificationError(
            "qualification identity directory is missing"
        ) from error
    if path.is_symlink() or not path.is_dir() or canonical != path:
        raise QualificationError("qualification identity directory is unsafe")


def _collector_error(phase: str, error: Exception) -> dict[str, str]:
    return {
        "phase": phase,
        "error_type": type(error).__name__,
    }


def _require_exact_keys(value: Any, keys: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise QualificationError("Windows evidence collector shape is invalid")


def _validate_phase(phase: str, allowed: set[str]) -> None:
    if phase not in allowed:
        raise QualificationError("qualification evidence phase is invalid")


def _validate_checkpoint(
    phase: str,
    completed_batches: int,
    *,
    include_cleanup: bool,
) -> None:
    if not _is_nonnegative_int(completed_batches):
        raise QualificationError("qualification checkpoint batch is invalid")
    if phase == "readiness" and completed_batches == 0:
        return
    if (
        phase == "cadence"
        and completed_batches > 0
        and completed_batches % PROCESS_SAMPLE_EVERY_BATCHES == 0
    ):
        return
    if phase == "pre_stop":
        return
    if include_cleanup and phase == "after_cleanup":
        return
    raise QualificationError("qualification evidence checkpoint is invalid")


def _is_positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _invocation_record(
    capture: InvocationCapture,
    *,
    batch_index: int,
    slot: int,
    invocation_index: int,
) -> dict[str, Any]:
    validation = _validate_capture(capture)
    return {
        "schema_version": 1,
        "qualification_only": QUALIFICATION_ONLY,
        "performance_evidence": PERFORMANCE_EVIDENCE,
        "invocation_index": invocation_index,
        "batch_index": batch_index,
        "slot": slot,
        "request_id": capture.request_id,
        "operation": "list_sandboxes",
        "executable_role": "manager",
        "started_monotonic_ns": capture.started_monotonic_ns,
        "ended_monotonic_ns": capture.ended_monotonic_ns,
        "elapsed_ns": max(
            0,
            capture.ended_monotonic_ns - capture.started_monotonic_ns,
        ),
        "started_utc_ns": capture.started_utc_ns,
        "ended_utc_ns": capture.ended_utc_ns,
        "return_code": capture.return_code,
        "stdout_bytes": len(capture.stdout),
        "stderr_bytes": len(capture.stderr),
        "stdout_sha256": _sha256_bytes(capture.stdout),
        "stderr_sha256": _sha256_bytes(capture.stderr),
        "result": "passed" if validation == "passed" else "failed",
        "validation": validation,
        "auth_token_recorded": False,
    }


def _validate_capture(capture: InvocationCapture) -> str:
    if capture.credential_exposed:
        return "credential_echo"
    if capture.execution_error is not None:
        return capture.execution_error
    if len(capture.stdout) > _MAX_CAPTURE_BYTES:
        return "stdout_oversize"
    if len(capture.stderr) > _MAX_CAPTURE_BYTES:
        return "stderr_oversize"
    if capture.return_code != 0:
        return "nonzero_exit"
    if capture.stderr:
        return "unexpected_stderr"
    if not capture.stdout.endswith(b"\n") or capture.stdout.count(b"\n") != 1:
        return "stdout_framing"
    try:
        value = json.loads(capture.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid_json"
    if (
        not isinstance(value, dict)
        or set(value) != {"sandboxes"}
        or value["sandboxes"] != []
    ):
        return "response_shape"
    return "passed"


class _NdjsonWriter:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG,
            0o600,
        )
        self._closed = False

    def append(self, records: list[dict[str, Any]]) -> None:
        payload = b"".join(
            json.dumps(
                record,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
            + b"\n"
            for record in records
        )
        _write_all(self._descriptor, payload)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            os.fsync(self._descriptor)
        finally:
            os.close(self._descriptor)
        _sync_directory(self._path.parent)


def _create_evidence_root(
    roots: BenchmarkRoots,
    qualification_id: str,
) -> Path:
    roots.validate_state()
    _validate_identity(qualification_id)
    parent = roots.results / "qualification-only"
    parent.mkdir(mode=0o700, exist_ok=True)
    evidence_root = parent / f"exp1-ipc-{qualification_id}"
    evidence_root.mkdir(mode=0o700)
    return evidence_root.resolve(strict=True)


def _request_id(qualification_id: str, batch_index: int, slot: int) -> str:
    return f"exp1-ipc-{qualification_id}-batch-{batch_index:04d}-slot-{slot}"


def _validate_identity(value: str) -> None:
    if _IDENTITY.fullmatch(value) is None:
        raise QualificationError("qualification identity is invalid")


def _validate_workload(workload: QualificationWorkload) -> None:
    if workload.batches < 1 or workload.concurrency < 1:
        raise QualificationError("qualification workload must be positive")


def _validate_npipe_endpoint(endpoint: str) -> None:
    name = endpoint.removeprefix(_NPIPE_PREFIX)
    native_path = rf"\\.\pipe\{name.replace('/', '\\')}"
    if (
        not endpoint.startswith(_NPIPE_PREFIX)
        or not name
        or _NPIPE_NAME.fullmatch(name) is None
        or "\\" in endpoint
        or "tcp://" in endpoint.lower()
        or any(segment in {"", ".", ".."} for segment in name.split("/"))
        or len(native_path.encode("utf-16-le")) // 2 > 256
    ):
        raise QualificationError("qualification endpoint must be one safe npipe URI")


def _native_environment() -> dict[str, str]:
    return {
        name: os.environ[name]
        for name in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP")
        if name in os.environ
    }


async def _digest_stream(
    stream: asyncio.StreamReader,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    while chunk := await stream.read(64 * 1024):
        byte_count += len(chunk)
        digest.update(chunk)
    return {
        "bytes": byte_count,
        "sha256": f"sha256:{digest.hexdigest()}",
    }


def _empty_stream_digest() -> dict[str, Any]:
    return {
        "bytes": 0,
        "sha256": _sha256_bytes(b""),
    }


def _sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    payload = (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
        + b"\n"
    )
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG,
        0o600,
    )
    try:
        _write_all(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _sync_directory(path.parent)


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("short qualification evidence write")
        view = view[written:]
