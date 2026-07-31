from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .catalog import _prebuilt_executable
from .fixtures import same_native_path
from .paths import BenchmarkRoots, _sync_directory
from .product import (
    ProductAccess,
    ProductAccessError,
    SandboxRecord,
    _identity,
    _product_path,
    _sandbox_record,
)
from .transport import (
    MAX_WIRE_BYTES,
    GatewayEndpoint,
    GatewayProductError,
    GatewayTransportError,
    TimedGatewayResponse,
)

_EXECUTABLES = {
    "manager": "sandbox-manager-cli",
    "runtime": "sandbox-runtime-cli",
    "observability": "sandbox-observability-cli",
}
_TRANSPORT_ERROR_KINDS = {
    "config_error",
    "connection_error",
    "protocol_error",
}
_BINARY_FLAG = getattr(os, "O_BINARY", 0)
# A parseable schema-v2 metadata file is the sole commit marker. It embeds both
# redacted byte streams losslessly, then is written and flushed after the two
# closed projection files. Trial calls retain these complete marker bytes until
# their durability boundary; non-trial calls commit immediately. A crash can
# therefore leave immutable projections without a marker, or a self-contained
# marker from which projections can be reconstructed.
_EVIDENCE_COMMIT_PROTOCOL = "metadata-packed-payload-fsync-v1"
_EVIDENCE_FLUSH_CONCURRENCY = 8


@dataclass
class _TrialEvidenceBuffer:
    trial_id: str
    pending: dict[Path, bytes] = field(default_factory=dict)
    flushing: bool = False


class ProductCliAccess(ProductAccess):
    """Closed product access implemented exclusively by released CLI subprocesses."""

    def __init__(
        self,
        endpoint: GatewayEndpoint,
        auth_token: str,
        roots: BenchmarkRoots,
        evidence_root: Path,
    ) -> None:
        self._runs_root = roots.runs.resolve(strict=True)
        self._sandboxes: set[str] = set()
        self._endpoint = endpoint
        self._auth_token = auth_token
        self._package_root = roots.product_bin_dir.parent.resolve(strict=True)
        self._executables = {
            role: _prebuilt_executable(roots, name)
            for role, name in _EXECUTABLES.items()
        }
        self._executable_sha256 = {
            role: _sha256_file(executable)
            for role, executable in self._executables.items()
        }
        resolved_evidence_root = evidence_root.resolve(strict=True)
        self._evidence_root = resolved_evidence_root / "cli-subprocesses"
        self._evidence_root.mkdir(mode=0o700, exist_ok=True)
        if self._evidence_root.is_symlink() or not self._evidence_root.is_dir():
            raise ProductAccessError("CLI evidence directory is unsafe")
        self._evidence_root = self._evidence_root.resolve(strict=True)
        if not self._evidence_root.is_relative_to(resolved_evidence_root):
            raise ProductAccessError("CLI evidence directory escaped the run directory")
        self._content_root = resolved_evidence_root / "cli-content"
        self._content_root.mkdir(mode=0o700, exist_ok=True)
        if self._content_root.is_symlink() or not self._content_root.is_dir():
            raise ProductAccessError("CLI content directory is unsafe")
        self._content_root = self._content_root.resolve(strict=True)
        if not self._content_root.is_relative_to(resolved_evidence_root):
            raise ProductAccessError("CLI content directory escaped the run directory")
        self._staged_file_writes: dict[str, str] = {}
        self._evidence_buffer_lock = threading.Lock()
        self._trial_evidence_buffer: _TrialEvidenceBuffer | None = None

    def begin_trial_evidence(self, trial_id: str) -> None:
        trial_id = _identity(trial_id)
        with self._evidence_buffer_lock:
            if self._trial_evidence_buffer is not None:
                raise ProductAccessError(
                    "CLI trial evidence transaction is already active"
                )
            self._trial_evidence_buffer = _TrialEvidenceBuffer(trial_id)

    async def flush_trial_evidence(self, trial_id: str) -> None:
        trial_id = _identity(trial_id)
        with self._evidence_buffer_lock:
            buffer = self._require_trial_evidence_buffer(trial_id)
            if buffer.flushing:
                raise ProductAccessError(
                    "CLI trial evidence transaction is already flushing"
                )
            buffer.flushing = True
            pending = tuple(
                sorted(buffer.pending.items(), key=lambda item: item[0].name)
            )

        committed: list[Path] = []
        failures: list[BaseException] = []
        try:
            semaphore = asyncio.Semaphore(_EVIDENCE_FLUSH_CONCURRENCY)

            async def commit(path: Path, content: bytes) -> Path:
                async with semaphore:
                    await asyncio.to_thread(
                        _write_new,
                        path,
                        content,
                        discard_on_error=True,
                    )
                return path

            results = await asyncio.gather(
                *(commit(path, content) for path, content in pending),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, BaseException):
                    failures.append(result)
                else:
                    committed.append(result)
            if committed:
                try:
                    await asyncio.to_thread(_sync_directory, self._evidence_root)
                except Exception as error:
                    failures.append(error)
        finally:
            with self._evidence_buffer_lock:
                active = self._require_trial_evidence_buffer(trial_id)
                for path in committed:
                    active.pending.pop(path, None)
                active.flushing = False

        if failures:
            raise BaseExceptionGroup("CLI trial evidence commit failed", failures)

    def end_trial_evidence(self, trial_id: str) -> None:
        trial_id = _identity(trial_id)
        with self._evidence_buffer_lock:
            buffer = self._require_trial_evidence_buffer(trial_id)
            if buffer.flushing:
                raise ProductAccessError(
                    "cannot end a flushing CLI trial evidence transaction"
                )
            pending = len(buffer.pending)
            self._trial_evidence_buffer = None
        if pending:
            raise ProductAccessError(
                "cannot end a CLI trial evidence transaction with "
                f"{pending} pending commit marker(s)"
            )

    def _require_trial_evidence_buffer(self, trial_id: str) -> _TrialEvidenceBuffer:
        buffer = self._trial_evidence_buffer
        if buffer is None:
            raise ProductAccessError("CLI trial evidence transaction is not active")
        if buffer.trial_id != trial_id:
            raise ProductAccessError(
                "CLI trial evidence transaction identity does not match"
            )
        return buffer

    async def stage_file_write_content(self, content: str, *, request_id: str) -> None:
        request_id = _identity(request_id)
        encoded = content.encode()
        if len(encoded) > 4 * 1024 * 1024:
            raise ProductAccessError("file content exceeds fixed bound")
        if request_id in self._staged_file_writes:
            raise ProductAccessError("file content was already staged")
        path = self._content_path(request_id)
        await asyncio.to_thread(_write_new, path, encoded)
        self._staged_file_writes[request_id] = content

    def discard_file_write_content(self, request_id: str) -> None:
        request_id = _identity(request_id)
        self._staged_file_writes.pop(request_id, None)
        self._remove_content_file(request_id)

    async def create_sandbox(
        self, image: str, workspace_root: Path, *, request_id: str
    ) -> tuple[SandboxRecord, TimedGatewayResponse]:
        workspace = workspace_root.resolve(strict=True)
        if workspace == self._runs_root or not workspace.is_relative_to(
            self._runs_root
        ):
            raise ProductAccessError("sandbox workspace is not benchmark-owned")
        response = await self._invoke(
            "manager",
            "create_sandbox",
            [
                "--image",
                image,
                "--workspace-bind-root",
                os.fspath(workspace),
                "--count",
                "1",
            ],
            timeout_seconds=600,
            request_id=request_id,
        )
        record = _sandbox_record(response.value)
        if (
            record.state != "ready"
            or not same_native_path(record.workspace_root, workspace)
            or record.id in self._sandboxes
        ):
            raise ProductAccessError(
                "create_sandbox response violated ownership or readiness"
            )
        self._sandboxes.add(record.id)
        return record, response

    async def inspect_sandbox(
        self, sandbox_id: str, *, request_id: str
    ) -> SandboxRecord:
        self._require_owned(sandbox_id)
        response = await self._invoke(
            "manager",
            "inspect_sandbox",
            ["--sandbox-id", sandbox_id],
            timeout_seconds=30,
            request_id=request_id,
        )
        record = _sandbox_record(response.value)
        if record.id != sandbox_id or record.state != "ready":
            raise ProductAccessError(
                "inspect_sandbox response violated identity or readiness"
            )
        return record

    async def destroy_sandbox(
        self, sandbox_id: str, *, request_id: str
    ) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        response = await self._invoke(
            "manager",
            "destroy_sandbox",
            ["--sandbox-id", sandbox_id],
            timeout_seconds=600,
            request_id=request_id,
        )
        self._sandboxes.remove(sandbox_id)
        return response

    async def squash_layerstacks(
        self,
        sandbox_id: str,
        *,
        timeout_ms: int,
        request_id: str,
    ) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        return await self._invoke(
            "manager",
            "squash_layerstacks",
            ["--sandbox-id", sandbox_id],
            timeout_seconds=timeout_ms / 1000,
            request_id=request_id,
        )

    async def cleanup_owned(self, *, request_prefix: str) -> None:
        issues: list[BaseException] = []
        for index, sandbox_id in enumerate(sorted(self._sandboxes)):
            try:
                await self.destroy_sandbox(
                    sandbox_id,
                    request_id=f"{request_prefix}.destroy.{index}",
                )
            except BaseException as error:
                issues.append(error)
        try:
            await self.assert_no_sandboxes(request_id=f"{request_prefix}.list")
        except BaseException as error:
            issues.append(error)
        if issues:
            raise BaseExceptionGroup("product CLI cleanup failed", issues)

    async def assert_no_sandboxes(self, *, request_id: str) -> None:
        response = await self._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=30,
            request_id=request_id,
        )
        if (
            not isinstance(response.value, dict)
            or response.value.get("sandboxes") != []
        ):
            raise ProductAccessError(
                "isolated gateway retained sandbox records after CLI cleanup"
            )

    async def _observe(
        self,
        operation: str,
        sandbox_id: str,
        args: dict[str, Any],
        request_id: str,
    ) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        operation_args = ["--sandbox-id", sandbox_id]
        if operation == "cgroup":
            operation_args.extend(
                ["--scope", str(args["scope"]), "--window-ms", str(args["window_ms"])]
            )
        elif operation == "trace":
            operation_args.extend(["--trace-id", str(args["trace_id"])])
        elif args:
            raise ProductAccessError("observability CLI arguments are not implemented")
        return await self._invoke(
            "observability",
            operation,
            operation_args,
            timeout_seconds=30,
            request_id=request_id,
        )

    async def _sandbox_request(
        self,
        operation: str,
        sandbox_id: str,
        session_id: str | None,
        args: dict[str, Any],
        timeout_ms: int,
        request_id: str,
    ) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        operation_args: list[str]
        if operation == "exec_command":
            operation_args = [
                "--timeout-ms",
                str(args["timeout_ms"]),
                "--yield-time-ms",
                str(args["yield_time_ms"]),
            ]
            if session_id is not None:
                operation_args.extend(["--workspace-session-id", _identity(session_id)])
            operation_args.append(str(args["cmd"]))
        elif operation == "create_workspace_session":
            operation_args = ["--network-profile", str(args["network_profile"])]
        elif operation == "destroy_workspace_session":
            operation_args = [
                "--workspace-session-id",
                _identity(str(args["workspace_session_id"])),
            ]
        elif operation == "file_read":
            operation_args = [
                "--path",
                _product_path(str(args["path"])),
                "--offset",
                str(args["offset"]),
                "--limit",
                str(args["limit"]),
            ]
            if session_id is not None:
                operation_args.extend(["--workspace-session-id", _identity(session_id)])
        elif operation == "file_write":
            operation_args = await self._file_write_arguments(
                args, session_id, request_id
            )
        elif operation == "file_edit":
            operation_args = [
                "--path",
                _product_path(str(args["path"])),
                "--edits",
                json.dumps(
                    args["edits"],
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ),
            ]
            if session_id is not None:
                operation_args.extend(["--workspace-session-id", _identity(session_id)])
        elif operation == "file_blame":
            operation_args = ["--path", _product_path(str(args["path"]))]
        else:
            raise ProductAccessError(
                f"runtime CLI operation is not implemented: {operation}"
            )
        try:
            return await self._invoke(
                "runtime",
                operation,
                operation_args,
                timeout_seconds=timeout_ms / 1000,
                request_id=request_id,
                sandbox_id=sandbox_id,
            )
        finally:
            if operation == "file_write":
                self._remove_content_file(request_id)

    async def _file_write_arguments(
        self,
        args: dict[str, Any],
        session_id: str | None,
        request_id: str,
    ) -> list[str]:
        content = args["content"]
        if not isinstance(content, str):
            raise ProductAccessError("file content exceeds fixed bound")
        path = self._content_path(request_id)
        if request_id not in self._staged_file_writes:
            if len(content.encode()) > 4 * 1024 * 1024:
                raise ProductAccessError("file content exceeds fixed bound")
            await self.stage_file_write_content(content, request_id=request_id)
        elif self._staged_file_writes[request_id] != content:
            raise ProductAccessError("staged file content does not match request")
        if path.is_symlink() or not path.is_file():
            raise ProductAccessError("staged file content is unsafe")
        operation_args = [
            "--path",
            _product_path(str(args["path"])),
            "--content-file",
            os.fspath(path),
        ]
        if session_id is not None:
            operation_args.extend(["--workspace-session-id", _identity(session_id)])
        return operation_args

    def _content_path(self, request_id: str) -> Path:
        digest = hashlib.sha256(_identity(request_id).encode()).hexdigest()
        return self._content_root / f"{digest}.txt"

    def _remove_content_file(self, request_id: str) -> None:
        path = self._content_path(request_id)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        self._staged_file_writes.pop(request_id, None)

    async def _invoke(
        self,
        executable_role: str,
        operation: str,
        operation_args: list[str],
        *,
        timeout_seconds: float,
        request_id: str,
        sandbox_id: str | None = None,
    ) -> TimedGatewayResponse:
        request_id = _identity(request_id)
        executable = self._executables[executable_role]
        socket = f"{self._endpoint.host}:{self._endpoint.port}"
        argv = [
            os.fspath(executable),
            "--gateway-socket",
            socket,
            f"--gateway-auth-token={self._auth_token}",
            "--request-id",
            request_id,
        ]
        if sandbox_id is not None:
            argv.extend(["--sandbox-id", _identity(sandbox_id)])
        argv.extend([operation, *operation_args])
        sanitized_argv = _sanitized_argv(argv, operation, self._auth_token)
        started_ns = time.monotonic_ns()
        process: asyncio.subprocess.Process | None = None
        stdout = b""
        stderr = b""
        return_code: int | None = None
        validation = "process_creation_failed"
        try:
            process = await asyncio.create_subprocess_exec(
                *argv,
                cwd=self._package_root,
                env={
                    name: os.environ[name]
                    for name in (
                        "PATH",
                        "SystemRoot",
                        "WINDIR",
                        "TEMP",
                        "TMP",
                    )
                    if name in os.environ
                },
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
            except TimeoutError as error:
                process.kill()
                stdout, stderr = await process.communicate()
                return_code = process.returncode
                validation = "timeout"
                raise GatewayTransportError("cli_timeout") from error
            except asyncio.CancelledError:
                process.kill()
                stdout, stderr = await process.communicate()
                return_code = process.returncode
                validation = "cancelled"
                raise
            return_code = process.returncode
            validation = "response_validation_failed"
            value = _validate_response(
                operation,
                return_code,
                stdout,
                stderr,
                self._auth_token,
            )
            validation = "passed"
        except BaseException as error:
            ended_ns = time.monotonic_ns()
            if validation == "response_validation_failed":
                validation = _validation_failure(error)
            try:
                await asyncio.to_thread(
                    self._persist_invocation,
                    executable_role,
                    operation,
                    request_id,
                    sanitized_argv,
                    started_ns,
                    ended_ns,
                    return_code,
                    stdout,
                    stderr,
                    validation,
                )
            except BaseException as persistence_error:
                raise BaseExceptionGroup(
                    "CLI invocation and evidence persistence both failed",
                    [error, persistence_error],
                )
            raise
        ended_ns = time.monotonic_ns()
        evidence = await asyncio.to_thread(
            self._persist_invocation,
            executable_role,
            operation,
            request_id,
            sanitized_argv,
            started_ns,
            ended_ns,
            return_code,
            stdout,
            stderr,
            validation,
        )
        return TimedGatewayResponse(
            request_id=request_id,
            latency_ns=ended_ns - started_ns,
            response_bytes=len(stdout),
            response_sha256=f"sha256:{hashlib.sha256(stdout).hexdigest()}",
            value=value,
            started_ns=started_ns,
            transport_evidence=evidence,
        )

    def _persist_invocation(
        self,
        executable_role: str,
        operation: str,
        request_id: str,
        sanitized_argv: list[str],
        started_ns: int,
        ended_ns: int,
        return_code: int | None,
        stdout: bytes,
        stderr: bytes,
        validation: str,
    ) -> dict[str, Any]:
        invocation_id = hashlib.sha256(
            f"{executable_role}:{operation}:{request_id}".encode()
        ).hexdigest()
        stdout_path = self._evidence_root / f"{invocation_id}.stdout"
        stderr_path = self._evidence_root / f"{invocation_id}.stderr"
        metadata_path = self._evidence_root / f"{invocation_id}.json"
        stdout = _redact_bytes(stdout, self._auth_token)
        stderr = _redact_bytes(stderr, self._auth_token)
        _write_new(stdout_path, stdout, durable=False)
        _write_new(stderr_path, stderr, durable=False)
        metadata = {
            "schema_version": 2,
            "invocation_id": invocation_id,
            "request_id": request_id,
            "operation": operation,
            "executable_role": executable_role,
            "executable_path": os.fspath(self._executables[executable_role]),
            "executable_sha256": self._executable_sha256[executable_role],
            "sanitized_argv": sanitized_argv,
            "started_monotonic_ns": started_ns,
            "ended_monotonic_ns": ended_ns,
            "elapsed_ns": ended_ns - started_ns,
            "return_code": return_code,
            "stdout_path": stdout_path.relative_to(
                self._evidence_root.parent
            ).as_posix(),
            "stderr_path": stderr_path.relative_to(
                self._evidence_root.parent
            ).as_posix(),
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_sha256": f"sha256:{hashlib.sha256(stdout).hexdigest()}",
            "stderr_sha256": f"sha256:{hashlib.sha256(stderr).hexdigest()}",
            "stdout_base64": base64.b64encode(stdout).decode("ascii"),
            "stderr_base64": base64.b64encode(stderr).decode("ascii"),
            "response_validation": validation,
            "evidence_commit": _EVIDENCE_COMMIT_PROTOCOL,
        }
        metadata_bytes = (
            json.dumps(
                metadata,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
            + b"\n"
        )
        with self._evidence_buffer_lock:
            buffer = self._trial_evidence_buffer
            if buffer is not None:
                if buffer.flushing:
                    raise ProductAccessError(
                        "cannot persist CLI evidence while its transaction is flushing"
                    )
                if metadata_path in buffer.pending:
                    raise ProductAccessError(
                        "CLI invocation evidence commit marker is duplicated"
                    )
                buffer.pending[metadata_path] = metadata_bytes
        if buffer is None:
            _write_new(
                metadata_path,
                metadata_bytes,
                discard_on_error=True,
            )
            _sync_directory(self._evidence_root)
        transport_metadata = {
            key: value
            for key, value in metadata.items()
            if key not in {"stdout_base64", "stderr_base64"}
        }
        return {
            "kind": "product_cli_subprocess",
            "metadata_path": metadata_path.relative_to(
                self._evidence_root.parent
            ).as_posix(),
            **transport_metadata,
        }


def _validate_response(
    operation: str,
    return_code: int | None,
    stdout: bytes,
    stderr: bytes,
    auth_token: str,
) -> dict[str, Any]:
    if auth_token.encode() in stdout or auth_token.encode() in stderr:
        raise GatewayTransportError("credential_echo")
    if len(stdout) > MAX_WIRE_BYTES or len(stderr) > MAX_WIRE_BYTES:
        raise GatewayTransportError("cli_output_oversize")
    if return_code != 0:
        kind, message = _error_envelope(stderr)
        if kind in _TRANSPORT_ERROR_KINDS:
            raise GatewayTransportError(kind)
        raise GatewayProductError(kind, message)
    if stderr:
        raise GatewayTransportError("cli_unexpected_stderr")
    if not stdout.endswith(b"\n") or stdout.count(b"\n") != 1:
        raise GatewayTransportError("cli_response_framing")
    try:
        value = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GatewayTransportError("invalid_json") from error
    if not isinstance(value, dict):
        raise GatewayTransportError("response_schema")
    _validate_operation_shape(operation, value)
    return value


def _validation_failure(error: BaseException) -> str:
    if isinstance(error, GatewayTransportError):
        return f"transport_error:{error}"
    if isinstance(error, GatewayProductError):
        return f"product_error:{error.kind}"
    return f"validation_error:{type(error).__name__}"


def _validate_operation_shape(operation: str, value: dict[str, Any]) -> None:
    required = {
        "create_sandbox": {"id", "workspace_root", "state"},
        "inspect_sandbox": {"id", "workspace_root", "state"},
        "list_sandboxes": {"sandboxes"},
        "exec_command": {"status"},
        "create_workspace_session": {"workspace_session_id"},
        "destroy_workspace_session": {"workspace_session_id", "destroyed"},
        "file_read": {"path", "content", "bytes_read"},
        "file_write": {"path", "bytes_written"},
        "file_edit": {"path", "edits_applied"},
        "file_blame": {"path", "ranges"},
        "cgroup": {"view"},
        "daemon": {"view"},
        "layerstack": {"view"},
        "snapshot": {"sandbox_id", "lifecycle_state", "availability"},
        "trace": {"view"},
    }.get(operation, set())
    if not required.issubset(value):
        raise GatewayTransportError("response_schema")


def _error_envelope(stderr: bytes) -> tuple[str, str]:
    try:
        value = json.loads(stderr)
        error = value["error"]
        kind = error["kind"]
        message = error["message"]
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as error:
        raise GatewayTransportError("cli_error_schema") from error
    if not isinstance(kind, str) or not kind or not isinstance(message, str):
        raise GatewayTransportError("cli_error_schema")
    return kind[:256], " ".join(message.split())[:1024]


def _sanitized_argv(argv: list[str], operation: str, auth_token: str) -> list[str]:
    result: list[str] = []
    redact_next = False
    for index, value in enumerate(argv):
        if redact_next:
            result.append("[REDACTED]")
            redact_next = False
            continue
        if value == "--gateway-auth-token":
            result.append(value)
            redact_next = True
            continue
        if value.startswith("--gateway-auth-token="):
            result.append("--gateway-auth-token=[REDACTED]")
            continue
        if index and argv[index - 1] == "--edits":
            digest = hashlib.sha256(value.encode()).hexdigest()
            result.append(f"[JSON sha256:{digest}]")
            continue
        if operation == "exec_command" and index == len(argv) - 1:
            digest = hashlib.sha256(value.encode()).hexdigest()
            result.append(f"[COMMAND sha256:{digest}]")
            continue
        result.append("[REDACTED]" if value == auth_token else value)
    return result


def _redact_bytes(value: bytes, auth_token: str) -> bytes:
    return value.replace(auth_token.encode(), b"[REDACTED]")


def _write_new(
    path: Path,
    content: bytes,
    *,
    durable: bool = True,
    discard_on_error: bool = False,
) -> None:
    created = False
    try:
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG, 0o600
        )
        created = True
        try:
            view = memoryview(content)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short artifact write")
                view = view[written:]
            if durable:
                os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except BaseException:
        if discard_on_error and created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"
