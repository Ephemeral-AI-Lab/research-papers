import asyncio
import json
import os
import signal
from pathlib import Path
from typing import Any

import benchmark_lab.gateway as gateway_module
import pytest
import yaml
from benchmark_lab.gateway import (
    GatewayLauncher,
    GatewayLifecycleError,
    _cleanup_docker_resources,
    _cli_readiness_request_id,
    _wait_until_ready,
    cleanup_gateway_docker_resources,
    recover_stale_gateway,
)
from benchmark_lab.models import OwnedPathMarker
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.safety import OwnershipLedger
from benchmark_lab.transport import GatewayProductError, TimedGatewayResponse


class FakeProcess:
    def __init__(self, pid: int = 43210) -> None:
        self.pid = pid
        self.returncode: int | None = None
        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdout.feed_data(b"safe output\n")
        self.stderr.feed_data(b"SANDBOX_GATEWAY_AUTH_TOKEN=must-redact\n")
        self._stopped = asyncio.Event()

    async def wait(self) -> int:
        await self._stopped.wait()
        assert self.returncode is not None
        return self.returncode

    def stop(self) -> None:
        self.returncode = 0
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self._stopped.set()


class FakeClient:
    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses = responses or [{"sandboxes": []}, {"sandboxes": []}]

    async def request(
        self, operation: str, scope: dict[str, Any], args: dict[str, Any], **_: Any
    ) -> TimedGatewayResponse:
        self.calls.append((operation, args))
        value = self.responses.pop(0)
        return TimedGatewayResponse("request-1", 1, 3, "sha256:abc", value)


async def no_orphans(_: str, __: bool) -> None:
    pass


def test_cli_readiness_request_id_is_unique_per_gateway_instance() -> None:
    first = _cli_readiness_request_id("run-1", "benchmark-gateway-first", 0)
    second = _cli_readiness_request_id("run-1", "benchmark-gateway-second", 0)

    assert first != second
    assert first == "run-1.benchmark-gateway-first.ready.0"


async def test_cli_readiness_product_rejection_fails_without_retry(
    tmp_path: Path,
) -> None:
    process = FakeProcess()
    pid_path = tmp_path / "gateway.pid"
    pid_path.write_text(str(process.pid))
    attempts = 0

    async def rejected() -> None:
        nonlocal attempts
        attempts += 1
        raise GatewayProductError("invalid_request", "safe rejection")

    with pytest.raises(
        GatewayLifecycleError, match="readiness CLI request was rejected"
    ):
        await _wait_until_ready(
            process,
            pid_path,
            FakeClient(),
            readiness_timeout_seconds=1,
            readiness_probe=rejected,
        )

    assert attempts == 1


def roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    source = test / "benchmark"
    source.mkdir(parents=True)
    defaults = Path(__file__).parents[3] / "defaults/gateway.yml"
    (source / "defaults").mkdir()
    (source / "defaults/gateway.yml").write_bytes(defaults.read_bytes())
    if os.name == "nt":
        (product / "config").mkdir(parents=True)
        (product / "config/windows-amd64.yml").write_bytes(defaults.read_bytes())
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    suffix = ".exe" if os.name == "nt" else ""
    for name in ("sandbox-gateway", "sandbox-daemon"):
        path = binaries / f"{name}{suffix}"
        path.write_text("prebuilt executable")
        path.chmod(0o700)
    daemon = product / "dist" / "sandbox-daemon-linux-arm64"
    daemon.parent.mkdir(parents=True)
    daemon.write_bytes(b"\x7fELFfake container executable")
    daemon.chmod(0o700)
    amd64_daemon = product / "dist" / "sandbox-daemon-linux-amd64"
    amd64_daemon.write_bytes(b"\x7fELFfake container executable")
    amd64_daemon.chmod(0o700)
    benchmark_roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    run_path = benchmark_roots.runs / "run-1"
    run_path.mkdir()
    OwnershipLedger(benchmark_roots).register(
        run_path, OwnedPathMarker(role="runs", identity={"run_id": "run-1"})
    )
    return benchmark_roots


async def test_launches_prebuilt_gateway_with_private_state_and_cleans_up(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()
    fake_client = FakeClient()
    launch: dict[str, Any] = {}

    async def process_factory(*args: str, **kwargs: Any) -> FakeProcess:
        launch.update({"args": args, **kwargs})
        config_path = Path(args[-1])
        config = yaml.safe_load(config_path.read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    def kill_group(pid: int, sent_signal: signal.Signals) -> None:
        assert pid == process.pid
        assert sent_signal == signal.SIGTERM
        process.stop()

    gateway = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: "process-identity-1",
        orphan_cleanup=no_orphans,
    ).start("run-1", readiness_timeout_seconds=1)
    runtime = benchmark_roots.runtime / "run-1"
    assert launch["args"][1:5] == ("serve", "--backend", "docker", "--config-yaml")
    if os.name == "nt":
        assert launch["creationflags"] != 0
        assert "start_new_session" not in launch
        assert launch["cwd"] == benchmark_roots.product_bin_dir.parent
    else:
        assert launch["start_new_session"] is True
        assert "creationflags" not in launch
        assert launch["cwd"] == benchmark_roots.product_root
    token_path = runtime / "gateway.token"
    token = token_path.read_text().strip()
    assert token and token_path.is_file() and not token_path.is_symlink()
    if os.name != "nt":
        assert oct(token_path.stat().st_mode & 0o777) == "0o600"
    assert token not in repr(gateway.client)
    assert "must-redact" not in (runtime / "gateway.log.jsonl").read_text()
    shared_cache = benchmark_roots.runs / "run-1" / "shared-base-cache"
    assert Path(launch["env"]["EOS_SHARED_BASE_CACHE"]) == shared_cache.resolve()
    assert fake_client.calls == [("list_sandboxes", {})]
    await gateway.close()
    assert fake_client.calls == [("list_sandboxes", {}), ("list_sandboxes", {})]
    assert not runtime.exists()
    assert shared_cache.is_dir()
    assert all("must-redact" not in record.text for record in gateway.logs)


async def test_successive_gateways_reuse_the_run_scoped_shared_base_cache(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    processes = [FakeProcess(43210), FakeProcess(43211)]
    launch_environments: list[dict[str, str]] = []
    launch_index = 0

    async def process_factory(*args: str, **kwargs: Any) -> FakeProcess:
        nonlocal launch_index
        process = processes[launch_index]
        launch_index += 1
        launch_environments.append(kwargs["env"])
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    def kill_group(pid: int, _: signal.Signals) -> None:
        next(process for process in processes if process.pid == pid).stop()

    launcher = GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: FakeClient(),
        kill_group=kill_group,
        process_identity=lambda pid: f"process-identity-{pid}",
        orphan_cleanup=no_orphans,
    )
    first = await launcher.start("run-1", readiness_timeout_seconds=1)
    await first.close(retain_shared_base_volumes=True)
    second = await launcher.start("run-1", readiness_timeout_seconds=1)
    await second.close(retain_shared_base_volumes=True)

    expected = (benchmark_roots.runs / "run-1" / "shared-base-cache").resolve()
    assert [Path(item["EOS_SHARED_BASE_CACHE"]) for item in launch_environments] == [
        expected,
        expected,
    ]
    assert first.identity.gateway_instance_id != second.identity.gateway_instance_id
    assert expected.is_dir()


async def test_shutdown_sweeps_every_sandbox_before_process_exit(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()
    fake_client = FakeClient(
        [
            {"sandboxes": []},
            {"sandboxes": [{"id": "sandbox-1"}, {"id": "sandbox-2"}]},
            {},
            {},
        ]
    )

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    def kill_group(_: int, __: signal.Signals) -> None:
        process.stop()

    gateway = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: "process-identity-1",
        orphan_cleanup=no_orphans,
    ).start("run-1", readiness_timeout_seconds=1)
    await gateway.close()
    assert fake_client.calls[-2:] == [
        ("destroy_sandbox", {"sandbox_id": "sandbox-1"}),
        ("destroy_sandbox", {"sandbox_id": "sandbox-2"}),
    ]


async def test_readiness_failure_terminates_and_removes_private_runtime(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text("wrong-pid")
        return process

    def kill_group(_: int, __: signal.Signals) -> None:
        process.stop()

    with pytest.raises(GatewayLifecycleError, match="startup failed"):
        await GatewayLauncher(
            benchmark_roots,
            process_factory=process_factory,
            client_factory=lambda _endpoint, _token: FakeClient(),
            kill_group=kill_group,
            process_identity=lambda _: "process-identity-1",
            orphan_cleanup=no_orphans,
        ).start("run-1", readiness_timeout_seconds=0.01)
    assert not (benchmark_roots.runtime / "run-1").exists()


async def test_cleanup_failure_preserves_owned_runtime_evidence(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()
    fake_client = FakeClient([{"sandboxes": []}, {"sandboxes": [{"id": "../escape"}]}])

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    def kill_group(_: int, __: signal.Signals) -> None:
        process.stop()

    gateway = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: "process-identity-1",
        orphan_cleanup=no_orphans,
    ).start("run-1", readiness_timeout_seconds=1)
    with pytest.raises(GatewayLifecycleError, match="sandbox cleanup"):
        await gateway.close()
    runtime = benchmark_roots.runtime / "run-1"
    assert runtime.exists()
    assert (runtime / ".ownership.json").exists()
    assert not (runtime / "gateway.token").exists()


async def test_cross_gateway_final_cleanup_removes_first_owner_shared_base_volume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_gateway_id = "benchmark-gateway-first"
    second_gateway_id = "benchmark-gateway-second"
    root_hash = "a" * 64
    shared = f"eos-shared-base-{root_hash}"
    ordinary = "eos-sandbox-layer-stack"
    calls: list[tuple[str, ...]] = []
    finalizing = False

    async def docker_output(*arguments: str) -> bytes:
        calls.append(arguments)
        owner = arguments[-1].removeprefix("label=eos.gateway_instance_id=")
        if arguments[:2] == ("ps", "-aq"):
            return (
                b"0123456789ab\n"
                if owner == first_gateway_id and not finalizing
                else b""
            )
        if arguments[:3] == ("volume", "ls", "--quiet"):
            if owner != first_gateway_id:
                return b""
            if finalizing:
                return f"{shared}\n".encode()
            return f"{shared}\n{ordinary}\n".encode()
        if arguments[:2] == ("volume", "inspect"):
            name = arguments[2]
            labels = {
                "eos.gateway_instance_id": first_gateway_id,
            }
            if name == shared:
                labels.update(
                    {
                        "eos.shared_base.root_hash": root_hash,
                        "eos.shared_base.target": "/eos/layer-stack/base",
                        "eos.shared_base.readonly": "true",
                    }
                )
            else:
                labels.update(
                    {
                        "eos.sandbox_id": "sandbox-1",
                        "eos.cleanup_policy": "remove-on-destroy",
                    }
                )
            return json.dumps([{"Name": name, "Labels": labels}]).encode()
        if arguments[:2] in {("rm", "--force"), ("volume", "rm")}:
            return b""
        raise AssertionError(arguments)

    monkeypatch.setattr(gateway_module, "_docker_output", docker_output)

    await _cleanup_docker_resources(first_gateway_id, retain_shared_base_volumes=True)
    assert ("rm", "--force", "0123456789ab") in calls
    assert ("volume", "rm", ordinary) in calls
    assert ("volume", "rm", shared) not in calls

    finalizing = True
    await cleanup_gateway_docker_resources((second_gateway_id, first_gateway_id))
    assert (
        "volume",
        "ls",
        "--quiet",
        "--filter",
        f"label=eos.gateway_instance_id={second_gateway_id}",
    ) in calls
    assert ("volume", "rm", shared) in calls


async def test_cleanup_preserves_ambiguous_shared_base_volume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway_instance_id = "benchmark-gateway-owned"
    root_hash = "b" * 64
    shared = f"eos-shared-base-{root_hash}"
    calls: list[tuple[str, ...]] = []

    async def docker_output(*arguments: str) -> bytes:
        calls.append(arguments)
        if arguments[:2] == ("ps", "-aq"):
            return b""
        if arguments[:3] == ("volume", "ls", "--quiet"):
            return f"{shared}\n".encode()
        if arguments[:2] == ("volume", "inspect"):
            return json.dumps(
                [
                    {
                        "Name": shared,
                        "Labels": {
                            "eos.gateway_instance_id": gateway_instance_id,
                            "eos.shared_base.root_hash": "c" * 64,
                            "eos.shared_base.target": "/eos/layer-stack/base",
                            "eos.shared_base.readonly": "true",
                        },
                    }
                ]
            ).encode()
        raise AssertionError(arguments)

    monkeypatch.setattr(gateway_module, "_docker_output", docker_output)

    with pytest.raises(GatewayLifecycleError, match="cleanup was incomplete"):
        await _cleanup_docker_resources(
            gateway_instance_id, retain_shared_base_volumes=False
        )
    assert ("volume", "rm", shared) not in calls


async def test_stale_recovery_proves_process_identity_before_signalling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()
    fake_client = FakeClient([{"sandboxes": []}, {"sandboxes": []}])
    current_identity: list[str | None] = ["process-identity-1"]
    cleaned: list[str] = []

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    def kill_group(_: int, __: signal.Signals) -> None:
        current_identity[0] = None
        process.stop()

    async def cleanup(identity: str, retain_shared_base_volumes: bool) -> None:
        cleaned.append(f"{identity}:{retain_shared_base_volumes}")

    abandoned = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: current_identity[0],
        orphan_cleanup=cleanup,
    ).start("run-1", readiness_timeout_seconds=1)
    await asyncio.sleep(0.01)
    os.close(abandoned._log_descriptor)
    abandoned._log_descriptor = None

    original_lstat = Path.lstat

    def private_token_lstat(path: Path) -> os.stat_result:
        metadata = original_lstat(path)
        if path.name != "gateway.token":
            return metadata
        values = list(metadata)
        values[0] &= ~0o077
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", private_token_lstat)
    await recover_stale_gateway(
        benchmark_roots,
        "run-1",
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: current_identity[0],
        orphan_cleanup=cleanup,
    )
    assert cleaned and cleaned[-1].endswith(":False")
    assert not (benchmark_roots.runtime / "run-1").exists()


async def test_stale_recovery_refuses_reused_pid_and_preserves_evidence(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    gateway = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: FakeClient(),
        kill_group=lambda _pid, _signal: process.stop(),
        process_identity=lambda _: "original-process",
        orphan_cleanup=no_orphans,
    ).start("run-1", readiness_timeout_seconds=1)
    with pytest.raises(GatewayLifecycleError, match="refusing to signal"):
        await recover_stale_gateway(
            benchmark_roots,
            "run-1",
            process_identity=lambda _: "different-process",
            orphan_cleanup=no_orphans,
        )
    assert (benchmark_roots.runtime / "run-1" / "gateway.token").exists()
    await gateway.close()


async def test_stale_recovery_aggregates_orphan_cleanup_and_deletes_token(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    process = FakeProcess()

    async def process_factory(*args: str, **_: Any) -> FakeProcess:
        config = yaml.safe_load(Path(args[-1]).read_bytes())
        Path(config["gateway"]["pid_path"]).write_text(str(process.pid))
        return process

    abandoned = await GatewayLauncher(
        benchmark_roots,
        process_factory=process_factory,
        client_factory=lambda _endpoint, _token: FakeClient(),
        kill_group=lambda _pid, _signal: process.stop(),
        process_identity=lambda _: "original-process",
        orphan_cleanup=no_orphans,
    ).start("run-1", readiness_timeout_seconds=1)
    await asyncio.sleep(0.01)
    process.stop()
    os.close(abandoned._log_descriptor)
    abandoned._log_descriptor = None
    retention_modes: list[bool] = []

    async def fails(_: str, retain_shared_base_volumes: bool) -> None:
        retention_modes.append(retain_shared_base_volumes)
        raise RuntimeError("injected cleanup failure")

    with pytest.raises(GatewayLifecycleError, match="Docker resource cleanup"):
        await recover_stale_gateway(
            benchmark_roots,
            "run-1",
            process_identity=lambda _: None,
            orphan_cleanup=fails,
        )
    runtime = benchmark_roots.runtime / "run-1"
    assert retention_modes == [False]
    assert runtime.exists()
    assert not (runtime / "gateway.token").exists()


def test_unowned_run_fails_before_launch(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    (benchmark_roots.runs / "run-1" / ".ownership.json").write_text("{}")
    with pytest.raises(GatewayLifecycleError, match="ownership"):
        asyncio.run(GatewayLauncher(benchmark_roots).start("run-1"))


def test_binary_symlink_fails_before_launch(tmp_path: Path, symlink_or_skip) -> None:
    benchmark_roots = roots(tmp_path)
    suffix = ".exe" if os.name == "nt" else ""
    gateway_binary = benchmark_roots.product_bin_dir / f"sandbox-gateway{suffix}"
    gateway_binary.unlink()
    target = benchmark_roots.product_root / "outside-gateway"
    target.write_bytes(b"outside")
    target.chmod(0o700)
    symlink_or_skip(gateway_binary, target)
    with pytest.raises(GatewayLifecycleError, match="preflight"):
        asyncio.run(GatewayLauncher(benchmark_roots).start("run-1"))
