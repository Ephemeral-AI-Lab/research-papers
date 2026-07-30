import asyncio
import os
import signal
from pathlib import Path
from typing import Any

import pytest
import yaml

from benchmark_lab.gateway import (
    GatewayLauncher,
    GatewayLifecycleError,
    recover_stale_gateway,
)
from benchmark_lab.models import OwnedPathMarker
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.safety import OwnershipLedger
from benchmark_lab.transport import TimedGatewayResponse


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


async def no_orphans(_: str) -> None:
    pass


def roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    source = test / "benchmark"
    source.mkdir(parents=True)
    defaults = Path(__file__).parents[3] / "defaults/gateway.yml"
    (source / "defaults").mkdir()
    (source / "defaults/gateway.yml").write_bytes(defaults.read_bytes())
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    for name in ("sandbox-gateway", "sandbox-daemon"):
        path = binaries / name
        path.write_text("prebuilt executable")
        path.chmod(0o700)
    tools = product / "dist/git"
    tools.mkdir(parents=True)
    for name in ("linux-arm64.tar", "linux-amd64.tar"):
        (tools / name).write_bytes(b"archive")
    daemon = product / "dist" / "sandbox-daemon-linux-arm64"
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


async def test_launches_prebuilt_gateway_with_private_state_and_cleans_up(tmp_path: Path) -> None:
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
    assert launch["start_new_session"] is True
    assert launch["cwd"] == benchmark_roots.product_root
    token = (runtime / "gateway.token").read_text().strip()
    assert token and oct((runtime / "gateway.token").stat().st_mode & 0o777) == "0o600"
    assert token not in repr(gateway.client)
    assert "must-redact" not in (runtime / "gateway.log.jsonl").read_text()
    assert fake_client.calls == [("list_sandboxes", {})]
    await gateway.close()
    assert fake_client.calls == [("list_sandboxes", {}), ("list_sandboxes", {})]
    assert not runtime.exists()
    assert all("must-redact" not in record.text for record in gateway.logs)


async def test_shutdown_sweeps_every_sandbox_before_process_exit(tmp_path: Path) -> None:
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


async def test_readiness_failure_terminates_and_removes_private_runtime(tmp_path: Path) -> None:
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


async def test_stale_recovery_proves_process_identity_before_signalling(tmp_path: Path) -> None:
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

    async def cleanup(identity: str) -> None:
        cleaned.append(identity)

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
    await recover_stale_gateway(
        benchmark_roots,
        "run-1",
        client_factory=lambda _endpoint, _token: fake_client,
        kill_group=kill_group,
        process_identity=lambda _: current_identity[0],
        orphan_cleanup=cleanup,
    )
    assert cleaned
    assert not (benchmark_roots.runtime / "run-1").exists()


async def test_stale_recovery_refuses_reused_pid_and_preserves_evidence(tmp_path: Path) -> None:
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


async def test_stale_recovery_aggregates_orphan_cleanup_and_deletes_token(tmp_path: Path) -> None:
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

    async def fails(_: str) -> None:
        raise RuntimeError("injected cleanup failure")

    with pytest.raises(GatewayLifecycleError, match="Docker resource cleanup"):
        await recover_stale_gateway(
            benchmark_roots,
            "run-1",
            process_identity=lambda _: None,
            orphan_cleanup=fails,
        )
    runtime = benchmark_roots.runtime / "run-1"
    assert runtime.exists()
    assert not (runtime / "gateway.token").exists()


def test_unowned_run_and_binary_symlink_fail_before_launch(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    (benchmark_roots.runs / "run-1" / ".ownership.json").write_text("{}")
    with pytest.raises(GatewayLifecycleError, match="ownership"):
        asyncio.run(GatewayLauncher(benchmark_roots).start("run-1"))

    benchmark_roots = roots(tmp_path / "second")
    gateway_binary = benchmark_roots.product_bin_dir / "sandbox-gateway"
    gateway_binary.unlink()
    gateway_binary.symlink_to("/bin/true")
    with pytest.raises(GatewayLifecycleError, match="preflight"):
        asyncio.run(GatewayLauncher(benchmark_roots).start("run-1"))
