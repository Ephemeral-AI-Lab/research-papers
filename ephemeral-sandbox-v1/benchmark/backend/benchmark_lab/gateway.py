import asyncio
import hashlib
import json
import os
import platform
import re
import secrets
import signal
import socket
import subprocess
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, ValidationError

from .catalog import CatalogError, _prebuilt_executable
from .models import OwnedPathMarker, StrictModel
from .paths import MARKER_NAME, BenchmarkRoots, _sync_directory
from .product import ProductAccessError
from .redaction import BoundedLogCapture, LogRecord, SecretRedactor
from .safety import OwnershipError, OwnershipLedger
from .transport import (
    GatewayClient,
    GatewayEndpoint,
    GatewayError,
    GatewayProductError,
)

GATEWAY_EXECUTABLE = "sandbox-gateway"
AUTH_ENV = "SANDBOX_GATEWAY_AUTH_TOKEN"
SHARED_CACHE_ENV = "EOS_SHARED_BASE_CACHE"
_BINARY_FLAG = getattr(os, "O_BINARY", 0)
ALLOWED_ENV = (
    "PATH",
    "HOME",
    "USERPROFILE",
    "SystemRoot",
    "WINDIR",
    "TEMP",
    "TMP",
    "TMPDIR",
    "XDG_RUNTIME_DIR",
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "DOCKER_CONFIG",
    "DOCKER_TLS_VERIFY",
    "DOCKER_CERT_PATH",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
_DOCKER_CONTAINER_ID = re.compile(r"^[0-9a-f]{12,64}$")
_DOCKER_VOLUME_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$")
_SHARED_BASE_VOLUME_NAME = re.compile(r"^eos-shared-base-([0-9a-f]{64})$")
_GATEWAY_INSTANCE_LABEL = "eos.gateway_instance_id"
_SHARED_BASE_ROOT_HASH_LABEL = "eos.shared_base.root_hash"
_SHARED_BASE_TARGET_LABEL = "eos.shared_base.target"
_SHARED_BASE_READONLY_LABEL = "eos.shared_base.readonly"
_SHARED_BASE_TARGET = "/eos/layer-stack/base"


class GatewayLifecycleError(RuntimeError):
    pass


class SandboxList(StrictModel):
    sandboxes: list[dict[str, Any]]


class OwnerProcess(StrictModel):
    schema_version: int = Field(ge=1, le=1)
    pid: int = Field(gt=0)
    process_group: int = Field(gt=0)
    process_identity: str = Field(min_length=1, max_length=4096)
    gateway_executable: str = Field(min_length=1)
    gateway_binary_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    gateway_instance_id: str = Field(min_length=1, max_length=256)
    endpoint_host: str
    endpoint_port: int = Field(ge=1, le=65535)


@dataclass(frozen=True, slots=True)
class GatewayIdentity:
    run_id: str
    gateway_instance_id: str
    endpoint: GatewayEndpoint
    gateway_binary_sha256: str
    daemon_binary_sha256: str
    effective_config_sha256: str


ProcessFactory = Callable[..., Awaitable[Any]]
ClientFactory = Callable[[GatewayEndpoint, str], GatewayClient]
KillGroup = Callable[[int, int], None]
ProcessIdentity = Callable[[int], str | None]
OrphanCleanup = Callable[[str, bool], Awaitable[None]]


class GatewayLauncher:
    def __init__(
        self,
        roots: BenchmarkRoots,
        *,
        process_factory: ProcessFactory = asyncio.create_subprocess_exec,
        client_factory: ClientFactory = GatewayClient,
        kill_group: KillGroup | None = None,
        process_identity: ProcessIdentity | None = None,
        orphan_cleanup: OrphanCleanup | None = None,
    ) -> None:
        self._roots = roots
        self._process_factory = process_factory
        self._client_factory = client_factory
        self._kill_group = kill_group or _default_kill_group
        self._process_identity = process_identity or _process_identity
        self._orphan_cleanup = orphan_cleanup or _cleanup_docker_resources

    async def start(
        self,
        run_id: str,
        *,
        remount_sweep_width: int = 1,
        readiness_timeout_seconds: float = 60,
        readiness_via_cli: bool = False,
    ) -> "IsolatedGateway":
        _validate_identity(run_id)
        if not 1 <= remount_sweep_width <= 1024:
            raise GatewayLifecycleError("remount sweep width is invalid")
        self._roots.validate_state()
        _require_owned_run(self._roots, run_id)
        try:
            gateway_binary = _prebuilt_executable(self._roots, GATEWAY_EXECUTABLE)
            daemon_binary = _container_daemon_executable(self._roots)
        except CatalogError as error:
            raise GatewayLifecycleError(
                "gateway preflight rejected a product binary"
            ) from error

        ledger = OwnershipLedger(self._roots)
        runtime_path = self._roots.runtime / run_id
        runtime_marker = OwnedPathMarker(role="runtime", identity={"run_id": run_id})
        try:
            runtime_path.mkdir(mode=0o700)
            ledger.register(runtime_path, runtime_marker)
        except (OSError, OwnershipError) as error:
            _cleanup_failed_registration(runtime_path, ledger, runtime_marker)
            raise GatewayLifecycleError(
                "isolated runtime ownership setup failed"
            ) from error

        process: Any | None = None
        log_tasks: tuple[asyncio.Task[None], asyncio.Task[None]] | None = None
        token = secrets.token_urlsafe(48)
        redactor = SecretRedactor({token})
        log_descriptor: int | None = None
        capture: BoundedLogCapture | None = None
        gateway_instance_id: str | None = None
        try:
            shared_cache = _run_shared_cache(self._roots, run_id)
            endpoint = _reserve_loopback_endpoint()
            gateway_instance_id = f"benchmark-gateway-{secrets.token_hex(16)}"
            config_path = runtime_path / "effective-config.yml"
            pid_path = runtime_path / "gateway.pid"
            token_path = runtime_path / "gateway.token"
            log_path = runtime_path / "gateway.log.jsonl"
            registry_path = runtime_path / "registry.json"
            config = _effective_config(
                self._roots,
                daemon_binary,
                endpoint,
                config_path,
                pid_path,
                registry_path,
                gateway_instance_id,
                remount_sweep_width,
            )
            config_bytes = yaml.safe_dump(config, sort_keys=True).encode()
            _write_new_private(config_path, config_bytes)
            _write_new_private(token_path, token.encode() + b"\n")
            log_descriptor = os.open(
                log_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG,
                0o600,
            )

            def persist_log(record: LogRecord) -> None:
                assert log_descriptor is not None
                payload = (
                    json.dumps(
                        {"stream": record.stream, "text": record.text},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode()
                    + b"\n"
                )
                os.write(log_descriptor, payload)

            capture = BoundedLogCapture(
                redactor, max_total_bytes=128 * 1024, sink=persist_log
            )
            environment = {
                name: os.environ[name] for name in ALLOWED_ENV if name in os.environ
            }
            environment.update(
                {
                    AUTH_ENV: token,
                    SHARED_CACHE_ENV: os.fspath(shared_cache),
                }
            )
            process_options: dict[str, Any] = {}
            if os.name == "nt":
                process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                process_options["start_new_session"] = True
            process = await self._process_factory(
                os.fspath(gateway_binary),
                "serve",
                "--backend",
                "docker",
                "--config-yaml",
                os.fspath(config_path),
                cwd=(
                    self._roots.product_bin_dir.parent
                    if os.name == "nt"
                    else self._roots.product_root
                ),
                env=environment,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **process_options,
            )
            if process.pid is None or process.stdout is None or process.stderr is None:
                raise GatewayLifecycleError(
                    "gateway process streams or identity are unavailable"
                )
            process_identity = self._process_identity(process.pid)
            if process_identity is None:
                raise GatewayLifecycleError("gateway process identity is unavailable")
            gateway_binary_sha256 = _sha256(gateway_binary)
            _write_new_private(
                runtime_path / "owner-process.json",
                OwnerProcess(
                    schema_version=1,
                    pid=process.pid,
                    process_group=process.pid,
                    process_identity=process_identity,
                    gateway_executable=os.fspath(gateway_binary),
                    gateway_binary_sha256=gateway_binary_sha256,
                    gateway_instance_id=gateway_instance_id,
                    endpoint_host=endpoint.host,
                    endpoint_port=endpoint.port,
                )
                .model_dump_json()
                .encode()
                + b"\n",
            )
            assert capture is not None
            log_tasks = (
                asyncio.create_task(capture.drain(process.stdout, "stdout")),
                asyncio.create_task(capture.drain(process.stderr, "stderr")),
            )
            client = self._client_factory(endpoint, token)
            readiness_probe = None
            if readiness_via_cli:
                from .product_cli import ProductCliAccess

                cli = ProductCliAccess(
                    endpoint,
                    token,
                    self._roots,
                    self._roots.results / run_id,
                )
                readiness_attempt = 0

                async def probe_cli_readiness() -> None:
                    nonlocal readiness_attempt
                    attempt = readiness_attempt
                    readiness_attempt += 1
                    await cli.assert_no_sandboxes(
                        request_id=_cli_readiness_request_id(
                            run_id, gateway_instance_id, attempt
                        )
                    )

                readiness_probe = probe_cli_readiness
            await _wait_until_ready(
                process,
                pid_path,
                client,
                readiness_timeout_seconds=readiness_timeout_seconds,
                readiness_probe=readiness_probe,
            )
            identity = GatewayIdentity(
                run_id=run_id,
                gateway_instance_id=gateway_instance_id,
                endpoint=endpoint,
                gateway_binary_sha256=gateway_binary_sha256,
                daemon_binary_sha256=_sha256(daemon_binary),
                effective_config_sha256=f"sha256:{hashlib.sha256(config_bytes).hexdigest()}",
            )
            return IsolatedGateway(
                identity=identity,
                client=client,
                process=process,
                runtime_path=runtime_path,
                token_path=token_path,
                runtime_marker=runtime_marker,
                ledger=ledger,
                capture=capture,
                log_tasks=log_tasks,
                kill_group=self._kill_group,
                log_descriptor=log_descriptor,
                orphan_cleanup=self._orphan_cleanup,
                auth_token=token,
            )
        except BaseException as error:
            issues: list[str] = []
            if process is not None:
                try:
                    await _terminate_process(process, self._kill_group)
                except Exception:
                    issues.append("process termination")
            if log_tasks is not None:
                await _join_log_tasks(log_tasks)
            if log_descriptor is not None:
                try:
                    _close_log(log_descriptor)
                except OSError:
                    issues.append("log persistence")
            if process is not None and gateway_instance_id is not None:
                try:
                    await self._orphan_cleanup(gateway_instance_id, False)
                except Exception:
                    issues.append("Docker resource cleanup")
            token_path = runtime_path / "gateway.token"
            try:
                token_path.unlink(missing_ok=True)
            except OSError:
                issues.append("credential deletion")
            if not issues:
                try:
                    ledger.remove(runtime_path, runtime_marker)
                except (OSError, OwnershipError):
                    issues.append("runtime cleanup")
            if isinstance(error, asyncio.CancelledError) and not issues:
                raise
            suffix = f"; incomplete cleanup: {', '.join(issues)}" if issues else ""
            raise GatewayLifecycleError(
                f"isolated gateway startup failed{suffix}"
            ) from error


class IsolatedGateway:
    def __init__(
        self,
        *,
        identity: GatewayIdentity,
        client: GatewayClient,
        process: Any,
        runtime_path: Path,
        token_path: Path,
        runtime_marker: OwnedPathMarker,
        ledger: OwnershipLedger,
        capture: BoundedLogCapture,
        log_tasks: tuple[asyncio.Task[None], asyncio.Task[None]],
        kill_group: KillGroup,
        log_descriptor: int,
        orphan_cleanup: OrphanCleanup,
        auth_token: str,
    ) -> None:
        self.identity = identity
        self.client = client
        self._process = process
        self._runtime_path = runtime_path
        self._token_path = token_path
        self._runtime_marker = runtime_marker
        self._ledger = ledger
        self._capture = capture
        self._log_tasks = log_tasks
        self._kill_group = kill_group
        self._log_descriptor = log_descriptor
        self._orphan_cleanup = orphan_cleanup
        self._auth_token = auth_token
        self._closed = False

    @property
    def logs(self) -> tuple[Any, ...]:
        return self._capture.records

    @property
    def auth_token(self) -> str:
        if self._closed:
            raise GatewayLifecycleError("gateway credential is unavailable after close")
        return self._auth_token

    async def close(
        self,
        *,
        destroy_sandboxes_via_gateway: bool = True,
        retain_shared_base_volumes: bool = False,
    ) -> None:
        if self._closed:
            return
        issues: list[str] = []
        if destroy_sandboxes_via_gateway:
            try:
                await _destroy_all_sandboxes(self.client)
            except Exception:
                issues.append("sandbox cleanup")
        try:
            await _terminate_process(self._process, self._kill_group)
        except Exception:
            issues.append("process termination")
        try:
            await self._orphan_cleanup(
                self.identity.gateway_instance_id, retain_shared_base_volumes
            )
        except Exception:
            issues.append("Docker resource cleanup")
        await _join_log_tasks(self._log_tasks)
        if self._log_descriptor is not None:
            try:
                _close_log(self._log_descriptor)
            except OSError:
                issues.append("log persistence")
            self._log_descriptor = None
        try:
            self._token_path.unlink(missing_ok=True)
            _sync_directory(self._runtime_path)
        except OSError:
            issues.append("credential deletion")
        if not issues:
            try:
                self._ledger.remove(self._runtime_path, self._runtime_marker)
            except (OSError, OwnershipError):
                issues.append("runtime cleanup")
        if issues:
            raise GatewayLifecycleError(
                f"isolated gateway cleanup was incomplete: {', '.join(issues)}"
            )
        self._closed = True
        self._auth_token = ""


async def _wait_until_ready(
    process: Any,
    pid_path: Path,
    client: GatewayClient,
    *,
    readiness_timeout_seconds: float,
    readiness_probe: Callable[[], Awaitable[None]] | None = None,
) -> None:
    deadline = asyncio.get_running_loop().time() + readiness_timeout_seconds
    while True:
        if process.returncode is not None:
            raise GatewayLifecycleError("gateway process exited before readiness")
        try:
            pid_matches = pid_path.read_text().strip() == str(process.pid)
        except OSError:
            pid_matches = False
        if pid_matches:
            try:
                if readiness_probe is None:
                    response = await client.request(
                        "list_sandboxes", {"kind": "system"}, {}, timeout_seconds=2
                    )
                    SandboxList.model_validate(response.value)
                else:
                    await readiness_probe()
                return
            except GatewayProductError as error:
                raise GatewayLifecycleError(
                    "gateway readiness CLI request was rejected"
                ) from error
            except (GatewayError, ProductAccessError, ValidationError):
                pass
        if asyncio.get_running_loop().time() >= deadline:
            raise GatewayLifecycleError("gateway readiness timed out")
        await asyncio.sleep(0.05)


async def _destroy_all_sandboxes(client: GatewayClient) -> None:
    response = await client.request(
        "list_sandboxes", {"kind": "system"}, {}, timeout_seconds=10
    )
    try:
        listing = SandboxList.model_validate(response.value)
    except ValidationError as error:
        raise GatewayLifecycleError(
            "gateway sandbox listing schema is invalid"
        ) from error
    failed = False
    for record in listing.sandboxes:
        sandbox_id = record.get("id")
        if not isinstance(sandbox_id, str) or _SAFE_ID.fullmatch(sandbox_id) is None:
            failed = True
            continue
        try:
            await client.request(
                "destroy_sandbox",
                {"kind": "system"},
                {"sandbox_id": sandbox_id},
                timeout_seconds=10 * 60,
            )
        except GatewayError:
            failed = True
    if failed:
        raise GatewayLifecycleError(
            "one or more isolated sandboxes could not be removed"
        )


async def _terminate_process(process: Any, kill_group: KillGroup) -> None:
    if process.returncode is None:
        try:
            kill_group(process.pid, int(signal.SIGTERM))
        except ProcessLookupError:
            pass
        try:
            await asyncio.wait_for(process.wait(), 10)
        except TimeoutError:
            try:
                kill_group(process.pid, _force_kill_signal())
            except ProcessLookupError:
                pass
            await asyncio.wait_for(process.wait(), 10)


async def _join_log_tasks(tasks: tuple[asyncio.Task[None], asyncio.Task[None]]) -> None:
    done, pending = await asyncio.wait(tasks, timeout=2)
    for task in pending:
        task.cancel()
    await asyncio.gather(*done, *pending, return_exceptions=True)


def _effective_config(
    roots: BenchmarkRoots,
    daemon_binary: Path,
    endpoint: GatewayEndpoint,
    config_path: Path,
    pid_path: Path,
    registry_path: Path,
    gateway_instance_id: str,
    remount_sweep_width: int,
) -> dict[str, Any]:
    template = (
        roots.product_bin_dir.parent / "config/windows-amd64.yml"
        if os.name == "nt"
        else roots.benchmark_source_root / "defaults/gateway.yml"
    )
    if template.is_symlink() or not template.is_file():
        raise GatewayLifecycleError(
            "gateway configuration template is missing or unsafe"
        )
    config = yaml.safe_load(template.read_bytes())
    if not isinstance(config, dict):
        raise GatewayLifecycleError("gateway configuration template is invalid")
    try:
        gateway_config = config.setdefault("gateway", {})
        manager_config = config["manager"]
        if not isinstance(gateway_config, dict) or not isinstance(manager_config, dict):
            raise TypeError
        gateway_config.update(
            {
                "bind_addr": f"{endpoint.host}:{endpoint.port}",
                "pid_path": os.fspath(pid_path),
                "max_concurrent_connections": 256,
            }
        )
        manager_config.update(
            {
                "registry_path": os.fspath(registry_path),
                "workspace_roots": [os.fspath(roots.runs)],
            }
        )
        manager_config["docker"].update(
            {
                "daemon_binary_path": os.fspath(daemon_binary),
                "daemon_config_yaml_path": os.fspath(
                    template if os.name == "nt" else config_path
                ),
                "gateway_instance_id": gateway_instance_id,
            }
        )
        config["runtime"]["layerstack"]["remount_sweep_width"] = remount_sweep_width
    except (KeyError, TypeError, AttributeError) as error:
        raise GatewayLifecycleError(
            "gateway configuration template shape is invalid"
        ) from error
    return config


def _require_owned_run(roots: BenchmarkRoots, run_id: str) -> None:
    run_path = roots.runs / run_id
    expected = OwnedPathMarker(role="runs", identity={"run_id": run_id})
    try:
        OwnershipLedger(roots).adopt(run_path, expected)
    except OwnershipError as error:
        raise GatewayLifecycleError("run workspace ownership is invalid") from error


def _run_shared_cache(roots: BenchmarkRoots, run_id: str) -> Path:
    run_path = roots.runs / run_id
    shared_cache = run_path / "shared-base-cache"
    try:
        run_root = run_path.resolve(strict=True)
        shared_cache.mkdir(mode=0o700, exist_ok=True)
        resolved = shared_cache.resolve(strict=True)
    except OSError as error:
        raise GatewayLifecycleError(
            "run-scoped shared-base cache is unavailable"
        ) from error
    if (
        shared_cache.is_symlink()
        or not shared_cache.is_dir()
        or resolved == run_root
        or not resolved.is_relative_to(run_root)
    ):
        raise GatewayLifecycleError("run-scoped shared-base cache is unsafe")
    return resolved


async def recover_stale_gateway(
    roots: BenchmarkRoots,
    run_id: str,
    *,
    client_factory: ClientFactory = GatewayClient,
    kill_group: KillGroup | None = None,
    process_identity: ProcessIdentity | None = None,
    orphan_cleanup: OrphanCleanup | None = None,
) -> None:
    _validate_identity(run_id)
    kill_group = kill_group or _default_kill_group
    process_identity = process_identity or _process_identity
    roots.validate_state()
    runtime_path = roots.runtime / run_id
    runtime_marker = OwnedPathMarker(role="runtime", identity={"run_id": run_id})
    ledger = OwnershipLedger(roots)
    try:
        ledger.adopt(runtime_path, runtime_marker)
        metadata_path = runtime_path / "owner-process.json"
        if metadata_path.is_symlink() or metadata_path.stat().st_size > 16 * 1024:
            raise GatewayLifecycleError("stale process metadata is unsafe")
        metadata = OwnerProcess.model_validate_json(metadata_path.read_bytes())
    except (OSError, OwnershipError, ValidationError) as error:
        raise GatewayLifecycleError("stale process ownership proof failed") from error
    expected_binary = _prebuilt_executable(roots, GATEWAY_EXECUTABLE)
    if (
        Path(metadata.gateway_executable) != expected_binary
        or metadata.gateway_binary_sha256 != _sha256(expected_binary)
        or metadata.process_group != metadata.pid
    ):
        raise GatewayLifecycleError("stale process executable proof failed")

    current_identity = process_identity(metadata.pid)
    if current_identity is not None and current_identity != metadata.process_identity:
        raise GatewayLifecycleError("stale PID identity changed; refusing to signal it")
    issues: list[str] = []
    if current_identity is not None:
        token_path = runtime_path / "gateway.token"
        try:
            token_metadata = token_path.lstat()
            token = token_path.read_text().strip()
        except OSError:
            issues.append("credential recovery")
        else:
            if token_path.is_symlink() or token_metadata.st_mode & 0o077 or not token:
                issues.append("credential recovery")
            else:
                client = client_factory(
                    GatewayEndpoint(metadata.endpoint_host, metadata.endpoint_port),
                    token,
                )
                try:
                    await _destroy_all_sandboxes(client)
                except Exception:
                    issues.append("sandbox cleanup")
        try:
            kill_group(metadata.process_group, int(signal.SIGTERM))
        except ProcessLookupError:
            pass
        except Exception:
            issues.append("process termination")
        else:
            deadline = asyncio.get_running_loop().time() + 10
            while process_identity(metadata.pid) is not None:
                if asyncio.get_running_loop().time() >= deadline:
                    try:
                        kill_group(metadata.process_group, _force_kill_signal())
                    except ProcessLookupError:
                        pass
                    except Exception:
                        issues.append("process termination")
                    await asyncio.sleep(0.05)
                    if process_identity(metadata.pid) is not None:
                        issues.append("process termination")
                    break
                await asyncio.sleep(0.05)

    cleanup = orphan_cleanup or _cleanup_docker_resources
    try:
        await cleanup(metadata.gateway_instance_id, False)
    except Exception:
        issues.append("Docker resource cleanup")
    try:
        (runtime_path / "gateway.token").unlink(missing_ok=True)
    except OSError:
        issues.append("credential deletion")
    if not issues:
        try:
            ledger.remove(runtime_path, runtime_marker)
        except (OSError, OwnershipError):
            issues.append("runtime cleanup")
    if issues:
        raise GatewayLifecycleError(
            f"stale gateway cleanup was incomplete: {', '.join(issues)}"
        )


def _container_daemon_executable(roots: BenchmarkRoots) -> Path:
    architecture = platform.machine().lower()
    package = {
        "arm64": "sandbox-daemon-linux-arm64",
        "aarch64": "sandbox-daemon-linux-arm64",
        "x86_64": "sandbox-daemon-linux-amd64",
        "amd64": "sandbox-daemon-linux-amd64",
    }.get(architecture)
    if package is None:
        raise GatewayLifecycleError(
            "host architecture has no fixed container daemon package"
        )
    package_candidate = roots.product_bin_dir.parent / "dist" / package
    candidate = (
        package_candidate
        if package_candidate.is_file()
        else roots.product_root / "dist" / package
    )
    try:
        metadata = candidate.lstat()
        canonical = candidate.resolve(strict=True)
        with canonical.open("rb") as stream:
            magic = stream.read(4)
    except OSError as error:
        raise GatewayLifecycleError(
            "container daemon package is unavailable"
        ) from error
    if (
        candidate.is_symlink()
        or not candidate.is_file()
        or canonical != candidate
        or not os.access(canonical, os.X_OK)
        or metadata.st_size <= 4
        or magic != b"\x7fELF"
    ):
        raise GatewayLifecycleError(
            "container daemon package is unsafe or is not Linux ELF"
        )
    return canonical


def _reserve_loopback_endpoint() -> GatewayEndpoint:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        host, port = reservation.getsockname()
    return GatewayEndpoint(host, port)


def _write_new_private(path: Path, content: bytes) -> None:
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG, 0o600
    )
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _sync_directory(path.parent)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _validate_identity(value: str) -> None:
    if _SAFE_ID.fullmatch(value) is None:
        raise GatewayLifecycleError("run identity is invalid")


def _cli_readiness_request_id(
    run_id: str, gateway_instance_id: str, attempt: int
) -> str:
    return f"{run_id}.{gateway_instance_id}.ready.{attempt}"


def _process_identity(pid: int) -> str | None:
    if os.name == "nt":
        command = (
            "$p=Get-Process -Id "
            + str(pid)
            + " -ErrorAction SilentlyContinue;"
            + "if($null -eq $p){exit 1};"
            + "$v=$p.Path+'|'+$p.StartTime.ToUniversalTime().Ticks;"
            + "[Console]::Out.Write($v)"
        )
        try:
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise GatewayLifecycleError("process identity could not be read") from error
        if completed.returncode == 1 or not completed.stdout:
            return None
        if completed.returncode != 0 or len(completed.stdout) > 16 * 1024:
            raise GatewayLifecycleError("process identity could not be read")
        return f"sha256:{hashlib.sha256(completed.stdout).hexdigest()}"
    proc = Path("/proc") / str(pid)
    if proc.exists():
        try:
            stat_fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            executable = os.readlink(proc / "exe")
            source = f"{executable}\0{stat_fields[19]}".encode()
        except (OSError, IndexError) as error:
            raise GatewayLifecycleError("process identity could not be read") from error
        return f"sha256:{hashlib.sha256(source).hexdigest()}"
    try:
        completed = subprocess.run(
            ["/bin/ps", "-o", "lstart=", "-o", "command=", "-p", str(pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GatewayLifecycleError("process identity could not be read") from error
    if completed.returncode == 1 or not completed.stdout.strip():
        return None
    if completed.returncode != 0 or len(completed.stdout) > 16 * 1024:
        raise GatewayLifecycleError("process identity could not be read")
    return f"sha256:{hashlib.sha256(completed.stdout).hexdigest()}"


def _default_kill_group(pid: int, selected_signal: int) -> None:
    if os.name == "nt":
        os.kill(pid, signal.SIGTERM)
        return
    os.killpg(pid, selected_signal)


def _force_kill_signal() -> int:
    return int(getattr(signal, "SIGKILL", signal.SIGTERM))


async def cleanup_gateway_docker_resources(
    gateway_instance_ids: tuple[str, ...],
) -> None:
    failures = 0
    for gateway_instance_id in dict.fromkeys(gateway_instance_ids):
        try:
            await _cleanup_docker_resources(
                gateway_instance_id, retain_shared_base_volumes=False
            )
        except GatewayLifecycleError:
            failures += 1
    if failures:
        raise GatewayLifecycleError(
            "retained shared-base Docker cleanup was incomplete"
        )


async def _cleanup_docker_resources(
    gateway_instance_id: str,
    retain_shared_base_volumes: bool = False,
) -> None:
    _validate_identity(gateway_instance_id)
    label = f"label={_GATEWAY_INSTANCE_LABEL}={gateway_instance_id}"
    container_output = await _docker_output("ps", "-aq", "--filter", label)
    containers = _validated_lines(container_output, _DOCKER_CONTAINER_ID)
    volume_output = await _docker_output("volume", "ls", "--quiet", "--filter", label)
    volumes = _validated_lines(volume_output, _DOCKER_VOLUME_NAME)
    removable_volumes: list[str] = []
    failures = 0
    for volume in volumes:
        try:
            shared_base = await _validated_owned_volume(gateway_instance_id, volume)
        except GatewayLifecycleError:
            failures += 1
            continue
        if not shared_base or not retain_shared_base_volumes:
            removable_volumes.append(volume)
    for container in containers:
        try:
            await _docker_output("rm", "--force", container)
        except GatewayLifecycleError:
            failures += 1
    for volume in removable_volumes:
        try:
            await _docker_output("volume", "rm", volume)
        except GatewayLifecycleError:
            failures += 1
    if failures:
        raise GatewayLifecycleError("Docker cleanup was incomplete")


async def _validated_owned_volume(gateway_instance_id: str, volume: str) -> bool:
    content = await _docker_output("volume", "inspect", volume)
    try:
        records = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GatewayLifecycleError(
            "Docker volume ownership output is invalid"
        ) from error
    if (
        not isinstance(records, list)
        or len(records) != 1
        or not isinstance(records[0], dict)
        or records[0].get("Name") != volume
        or not isinstance(records[0].get("Labels"), dict)
    ):
        raise GatewayLifecycleError("Docker volume ownership output is invalid")
    labels = records[0]["Labels"]
    if (
        any(
            not isinstance(name, str) or not isinstance(value, str)
            for name, value in labels.items()
        )
        or labels.get(_GATEWAY_INSTANCE_LABEL) != gateway_instance_id
    ):
        raise GatewayLifecycleError("Docker volume ownership proof is invalid")
    match = _SHARED_BASE_VOLUME_NAME.fullmatch(volume)
    shared_labels = {
        _SHARED_BASE_ROOT_HASH_LABEL,
        _SHARED_BASE_TARGET_LABEL,
        _SHARED_BASE_READONLY_LABEL,
    }
    has_shared_labels = bool(shared_labels.intersection(labels))
    if match is None:
        if has_shared_labels:
            raise GatewayLifecycleError(
                "Docker shared-base volume identity is ambiguous"
            )
        return False
    root_hash = match.group(1)
    if (
        labels.get(_SHARED_BASE_ROOT_HASH_LABEL) != root_hash
        or labels.get(_SHARED_BASE_TARGET_LABEL) != _SHARED_BASE_TARGET
        or labels.get(_SHARED_BASE_READONLY_LABEL) != "true"
    ):
        raise GatewayLifecycleError("Docker shared-base volume identity is ambiguous")
    return True


async def _docker_output(*arguments: str) -> bytes:
    environment = {name: os.environ[name] for name in ALLOWED_ENV if name in os.environ}
    try:
        process = await asyncio.create_subprocess_exec(
            "docker",
            *arguments,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=environment,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), 30)
    except (OSError, TimeoutError) as error:
        raise GatewayLifecycleError("Docker cleanup command failed") from error
    if process.returncode != 0 or len(stdout) > 64 * 1024 or len(stderr) > 64 * 1024:
        raise GatewayLifecycleError("Docker cleanup command failed")
    return stdout


def _validated_lines(content: bytes, pattern: re.Pattern[str]) -> tuple[str, ...]:
    try:
        lines = tuple(line for line in content.decode("ascii").splitlines() if line)
    except UnicodeDecodeError as error:
        raise GatewayLifecycleError(
            "Docker cleanup identity output is invalid"
        ) from error
    if len(lines) > 64 or any(pattern.fullmatch(line) is None for line in lines):
        raise GatewayLifecycleError("Docker cleanup identity output is invalid")
    return lines


def _close_log(descriptor: int) -> None:
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _cleanup_failed_registration(
    runtime_path: Path,
    ledger: OwnershipLedger,
    marker: OwnedPathMarker | None,
) -> None:
    if not runtime_path.exists() or runtime_path.is_symlink():
        return
    if marker is not None and (runtime_path / MARKER_NAME).is_file():
        try:
            ledger.adopt(runtime_path, marker)
            ledger.remove(runtime_path, marker)
        except (OSError, OwnershipError):
            pass
    else:
        try:
            runtime_path.rmdir()
        except OSError:
            pass
