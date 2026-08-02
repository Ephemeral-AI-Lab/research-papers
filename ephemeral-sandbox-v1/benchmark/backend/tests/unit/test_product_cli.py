import asyncio
import base64
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import pytest

import benchmark_lab.product_cli as product_cli_module
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.product import ProductAccessError
from benchmark_lab.product_cli import ProductCliAccess, _validate_operation_shape
from benchmark_lab.transport import (
    GatewayEndpoint,
    GatewayProductError,
    GatewayTransportError,
)


class FakeProcess:
    def __init__(
        self,
        stdout: bytes,
        stderr: bytes = b"",
        returncode: int = 0,
        *,
        block_until_killed: bool = False,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.block_until_killed = block_until_killed
        self.killed = False
        self.started = asyncio.Event()
        self._released = asyncio.Event()

    async def communicate(self) -> tuple[bytes, bytes]:
        self.started.set()
        if self.block_until_killed and not self.killed:
            await self._released.wait()
        return self.stdout, self.stderr

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
        self._released.set()


def test_snapshot_cli_shape_matches_released_top_level_response() -> None:
    _validate_operation_shape(
        "snapshot",
        {
            "sandbox_id": "sandbox-1",
            "lifecycle_state": "ready",
            "availability": "available",
            "daemon": {},
            "resources": {},
            "workspaces": [],
            "stack": {},
        },
    )


def _roots(tmp_path: Path) -> BenchmarkRoots:
    test_root = tmp_path / "paper"
    product_root = tmp_path / "product"
    bin_root = product_root / "bin"
    (test_root / "benchmark").mkdir(parents=True)
    bin_root.mkdir(parents=True)
    return BenchmarkRoots.resolve(
        test_root,
        product_root,
        bin_root,
        initialize=True,
    )


def _access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    process_factory: Any,
    endpoint: GatewayEndpoint | None = None,
) -> tuple[ProductCliAccess, Path, list[str]]:
    roots = _roots(tmp_path)
    selected: list[str] = []

    def executable(_roots: BenchmarkRoots, name: str) -> Path:
        selected.append(name)
        path = roots.product_bin_dir / f"{name}.exe"
        path.write_bytes(name.encode())
        return path.resolve(strict=True)

    monkeypatch.setattr("benchmark_lab.product_cli._prebuilt_executable", executable)
    monkeypatch.setattr(
        "benchmark_lab.product_cli.asyncio.create_subprocess_exec",
        process_factory,
    )
    run_root = roots.runs / "run-1"
    run_root.mkdir()
    return (
        ProductCliAccess(
            endpoint or GatewayEndpoint("127.0.0.1", 47621),
            "-secret-token",
            roots,
            run_root,
        ),
        run_root,
        selected,
    )


@pytest.mark.asyncio
async def test_invocation_uses_exact_cli_and_persists_redacted_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[tuple[str, ...], dict[str, Any]]] = []

    async def create_process(*argv: str, **kwargs: Any) -> FakeProcess:
        calls.append((argv, kwargs))
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, selected = _access(tmp_path, monkeypatch, create_process)
    response = await access._invoke(
        "manager",
        "list_sandboxes",
        [],
        timeout_seconds=1,
        request_id="run-1.ready.0",
    )

    assert selected == [
        "sandbox-manager-cli",
        "sandbox-runtime-cli",
        "sandbox-observability-cli",
    ]
    argv, kwargs = calls[0]
    assert Path(argv[0]).name == "sandbox-manager-cli.exe"
    assert argv[1:] == (
        "--gateway-endpoint",
        "127.0.0.1:47621",
        "--gateway-auth-token=-secret-token",
        "--request-id",
        "run-1.ready.0",
        "list_sandboxes",
    )
    assert kwargs["cwd"] == access._package_root
    assert response.request_id == "run-1.ready.0"
    assert response.value == {"sandboxes": []}
    assert response.latency_ns > 0
    metadata_files = list((run_root / "cli-subprocesses").glob("*.json"))
    assert len(metadata_files) == 1
    metadata_text = metadata_files[0].read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert "-secret-token" not in metadata_text
    assert metadata["sanitized_argv"][3] == "--gateway-auth-token=[REDACTED]"
    assert metadata["response_validation"] == "passed"
    assert metadata["request_id"] == response.request_id
    assert metadata["schema_version"] == 2
    assert metadata["evidence_commit"] == "metadata-packed-payload-fsync-v1"
    assert response.transport_evidence["metadata_path"].endswith(".json")
    assert "stdout_base64" not in response.transport_evidence
    assert "stderr_base64" not in response.transport_evidence


@pytest.mark.asyncio
async def test_named_pipe_uri_is_passed_exactly_and_token_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, ...]] = []
    uri = "npipe://./pipe/ephemeral-sandbox-benchmark-exact-uri"

    async def create_process(*argv: str, **_kwargs: Any) -> FakeProcess:
        calls.append(argv)
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(
        tmp_path,
        monkeypatch,
        create_process,
        GatewayEndpoint.windows_named_pipe(uri),
    )
    await access._invoke(
        "manager",
        "list_sandboxes",
        [],
        timeout_seconds=1,
        request_id="run-1.named-pipe",
    )

    assert calls[0][1:4] == (
        "--gateway-endpoint",
        uri,
        "--gateway-auth-token=-secret-token",
    )
    metadata_text = next(
        (run_root / "cli-subprocesses").glob("*.json")
    ).read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    assert "-secret-token" not in metadata_text
    assert metadata["sanitized_argv"][2] == uri
    assert metadata["sanitized_argv"][3] == (
        "--gateway-auth-token=[REDACTED]"
    )


@pytest.mark.asyncio
async def test_executable_digests_are_cached_once_per_access_instance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    digest_calls: list[Path] = []
    real_sha256_file = product_cli_module._sha256_file

    def observed_sha256_file(path: Path) -> str:
        digest_calls.append(path)
        return real_sha256_file(path)

    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(b'{"sandboxes":[]}\n')

    monkeypatch.setattr(product_cli_module, "_sha256_file", observed_sha256_file)
    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)

    for index in range(2):
        await access._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=1,
            request_id=f"run-1.digest.{index}",
        )

    assert sorted(path.name for path in digest_calls) == [
        "sandbox-manager-cli.exe",
        "sandbox-observability-cli.exe",
        "sandbox-runtime-cli.exe",
    ]
    manager_digests = {
        json.loads(path.read_text(encoding="utf-8"))["executable_sha256"]
        for path in (run_root / "cli-subprocesses").glob("*.json")
    }
    assert manager_digests == {real_sha256_file(access._executables["manager"])}


@pytest.mark.asyncio
async def test_invocation_evidence_uses_metadata_as_the_only_durable_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    fsync_calls: list[int] = []
    monkeypatch.setattr(
        product_cli_module.os,
        "fsync",
        lambda descriptor: fsync_calls.append(descriptor),
    )

    await access._invoke(
        "manager",
        "list_sandboxes",
        [],
        timeout_seconds=1,
        request_id="run-1.commit",
    )

    evidence = run_root / "cli-subprocesses"
    assert len(fsync_calls) == 1 + (os.name != "nt")
    assert sorted(path.suffix for path in evidence.iterdir()) == [
        ".json",
        ".stderr",
        ".stdout",
    ]
    metadata = json.loads(next(evidence.glob("*.json")).read_text(encoding="utf-8"))
    assert metadata["evidence_commit"] == "metadata-packed-payload-fsync-v1"
    for stream in ("stdout", "stderr"):
        payload = (run_root / metadata[f"{stream}_path"]).read_bytes()
        assert base64.b64decode(metadata[f"{stream}_base64"], validate=True) == payload
        assert metadata[f"{stream}_bytes"] == len(payload)
        assert metadata[f"{stream}_sha256"] == (
            f"sha256:{hashlib.sha256(payload).hexdigest()}"
        )


@pytest.mark.asyncio
async def test_trial_evidence_defers_markers_until_one_bounded_flush(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    fsync_calls: list[int] = []
    monkeypatch.setattr(
        product_cli_module.os,
        "fsync",
        lambda descriptor: fsync_calls.append(descriptor),
    )
    access.begin_trial_evidence("trial-1")

    responses = await asyncio.gather(
        *(
            access._invoke(
                "manager",
                "list_sandboxes",
                [],
                timeout_seconds=1,
                request_id=f"trial-1.request.{index}",
            )
            for index in range(3)
        )
    )

    evidence = run_root / "cli-subprocesses"
    assert not list(evidence.glob("*.json"))
    assert len(list(evidence.glob("*.stdout"))) == 3
    assert len(list(evidence.glob("*.stderr"))) == 3
    assert fsync_calls == []
    assert all(
        response.transport_evidence is not None
        and response.transport_evidence["metadata_path"].endswith(".json")
        for response in responses
    )

    await access.flush_trial_evidence("trial-1")
    access.end_trial_evidence("trial-1")

    metadata_paths = sorted(evidence.glob("*.json"))
    assert len(metadata_paths) == 3
    assert len(fsync_calls) == 3 + (os.name != "nt")
    for path in metadata_paths:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        assert metadata["schema_version"] == 2
        assert metadata["evidence_commit"] == "metadata-packed-payload-fsync-v1"
        for stream in ("stdout", "stderr"):
            payload = (run_root / metadata[f"{stream}_path"]).read_bytes()
            assert (
                base64.b64decode(metadata[f"{stream}_base64"], validate=True) == payload
            )


@pytest.mark.asyncio
async def test_concurrent_trial_evidence_preserves_every_unique_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*argv: str, **_kwargs: Any) -> FakeProcess:
        request_id = argv[argv.index("--request-id") + 1]
        index = int(request_id.rsplit(".", 1)[1])
        await asyncio.sleep((7 - index) * 0.001)
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    access.begin_trial_evidence("trial-concurrent")
    request_ids = [f"trial-concurrent.request.{index}" for index in range(8)]

    responses = await asyncio.gather(
        *(
            access._invoke(
                "manager",
                "list_sandboxes",
                [],
                timeout_seconds=1,
                request_id=request_id,
            )
            for request_id in request_ids
        )
    )
    real_write_new = product_cli_module._write_new
    write_lock = threading.Lock()
    active_writes = 0
    peak_active_writes = 0

    def observe_parallel_writes(
        path: Path,
        content: bytes,
        *,
        durable: bool = True,
        discard_on_error: bool = False,
    ) -> None:
        nonlocal active_writes, peak_active_writes
        with write_lock:
            active_writes += 1
            peak_active_writes = max(peak_active_writes, active_writes)
        try:
            time.sleep(0.01)
            real_write_new(
                path,
                content,
                durable=durable,
                discard_on_error=discard_on_error,
            )
        finally:
            with write_lock:
                active_writes -= 1

    monkeypatch.setattr(product_cli_module, "_EVIDENCE_FLUSH_CONCURRENCY", 2)
    monkeypatch.setattr(product_cli_module, "_write_new", observe_parallel_writes)
    await access.flush_trial_evidence("trial-concurrent")
    access.end_trial_evidence("trial-concurrent")

    metadata = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (run_root / "cli-subprocesses").glob("*.json")
    ]
    assert sorted(item["request_id"] for item in metadata) == request_ids
    assert len({item["invocation_id"] for item in metadata}) == len(request_ids)
    assert len(
        {
            response.transport_evidence["metadata_path"]
            for response in responses
            if response.transport_evidence is not None
        }
    ) == len(request_ids)
    assert peak_active_writes == 2


@pytest.mark.asyncio
async def test_trial_evidence_lifecycle_rejects_nested_and_mismatched_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        raise AssertionError("lifecycle test must not launch a process")

    access, _, _ = _access(tmp_path, monkeypatch, create_process)
    with pytest.raises(ProductAccessError, match="not active"):
        await access.flush_trial_evidence("trial-1")
    with pytest.raises(ProductAccessError, match="not active"):
        access.end_trial_evidence("trial-1")

    access.begin_trial_evidence("trial-1")
    with pytest.raises(ProductAccessError, match="already active"):
        access.begin_trial_evidence("trial-1")
    with pytest.raises(ProductAccessError, match="does not match"):
        await access.flush_trial_evidence("trial-2")
    with pytest.raises(ProductAccessError, match="does not match"):
        access.end_trial_evidence("trial-2")

    await access.flush_trial_evidence("trial-1")
    access.end_trial_evidence("trial-1")


@pytest.mark.asyncio
async def test_failed_trial_flush_commits_other_markers_and_closes_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    access.begin_trial_evidence("trial-failed-flush")
    await asyncio.gather(
        *(
            access._invoke(
                "manager",
                "list_sandboxes",
                [],
                timeout_seconds=1,
                request_id=f"trial-failed-flush.request.{index}",
            )
            for index in range(3)
        )
    )

    real_write_new = product_cli_module._write_new
    failed = False
    failure_lock = threading.Lock()

    def fail_one_marker(
        path: Path,
        content: bytes,
        *,
        durable: bool = True,
        discard_on_error: bool = False,
    ) -> None:
        nonlocal failed
        with failure_lock:
            inject_failure = path.suffix == ".json" and not failed
            failed = failed or inject_failure
        if inject_failure:
            raise OSError("injected grouped marker failure")
        real_write_new(
            path,
            content,
            durable=durable,
            discard_on_error=discard_on_error,
        )

    monkeypatch.setattr(product_cli_module, "_write_new", fail_one_marker)
    with pytest.raises(
        BaseExceptionGroup, match="CLI trial evidence commit failed"
    ) as captured:
        await access.flush_trial_evidence("trial-failed-flush")
    assert any(
        isinstance(error, OSError) and "injected grouped marker failure" in str(error)
        for error in captured.value.exceptions
    )
    assert len(list((run_root / "cli-subprocesses").glob("*.json"))) == 2
    with pytest.raises(ProductAccessError, match="1 pending commit marker"):
        access.end_trial_evidence("trial-failed-flush")

    monkeypatch.setattr(product_cli_module, "_write_new", real_write_new)
    await access._invoke(
        "manager",
        "list_sandboxes",
        [],
        timeout_seconds=1,
        request_id="outside-after-failed-flush",
    )
    assert len(list((run_root / "cli-subprocesses").glob("*.json"))) == 3


@pytest.mark.asyncio
async def test_end_trial_evidence_rejects_and_discards_unflushed_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(b'{"sandboxes":[]}\n')

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    access.begin_trial_evidence("trial-unflushed")
    await access._invoke(
        "manager",
        "list_sandboxes",
        [],
        timeout_seconds=1,
        request_id="trial-unflushed.request.0",
    )

    with pytest.raises(ProductAccessError, match="1 pending commit marker"):
        access.end_trial_evidence("trial-unflushed")
    assert not list((run_root / "cli-subprocesses").glob("*.json"))

    access.begin_trial_evidence("trial-next")
    await access.flush_trial_evidence("trial-next")
    access.end_trial_evidence("trial-next")


def test_failed_metadata_flush_leaves_redacted_uncommitted_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        raise AssertionError("direct persistence test must not launch a process")

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    real_fsync = product_cli_module.os.fsync

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("injected metadata flush failure")

    monkeypatch.setattr(product_cli_module.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="injected metadata flush failure"):
        access._persist_invocation(
            "manager",
            "list_sandboxes",
            "run-1.flush-failure",
            ["sandbox-manager-cli.exe", "--gateway-auth-token=[REDACTED]"],
            10,
            20,
            0,
            b'{"token":"-secret-token"}\n',
            b"-secret-token warning\n",
            "transport_error:credential_echo",
        )

    evidence = run_root / "cli-subprocesses"
    assert not list(evidence.glob("*.json"))
    payloads = sorted(evidence.iterdir())
    assert [path.suffix for path in payloads] == [".stderr", ".stdout"]
    assert all(b"-secret-token" not in path.read_bytes() for path in payloads)
    before_retry = {path.name: path.read_bytes() for path in payloads}

    monkeypatch.setattr(product_cli_module.os, "fsync", real_fsync)
    with pytest.raises(FileExistsError):
        access._persist_invocation(
            "manager",
            "list_sandboxes",
            "run-1.flush-failure",
            ["sandbox-manager-cli.exe", "--gateway-auth-token=[REDACTED]"],
            10,
            20,
            0,
            b"different stdout\n",
            b"",
            "passed",
        )
    assert {path.name: path.read_bytes() for path in payloads} == before_retry
    assert not list(evidence.glob("*.json"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stdout", "stderr", "returncode", "exception"),
    [
        (b"not-json\n", b"", 0, GatewayTransportError),
        (b'{"sandboxes":[]}\n', b"warning\n", 0, GatewayTransportError),
        (
            b"",
            b'{"error":{"kind":"invalid_request","message":"bad"}}\n',
            2,
            GatewayProductError,
        ),
    ],
)
async def test_invalid_cli_results_fail_closed_and_are_retained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: bytes,
    stderr: bytes,
    returncode: int,
    exception: type[BaseException],
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return FakeProcess(stdout, stderr, returncode)

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    with pytest.raises(exception):
        await access._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=1,
            request_id="run-1.invalid",
        )
    metadata = json.loads(
        next((run_root / "cli-subprocesses").glob("*.json")).read_text(encoding="utf-8")
    )
    assert metadata["response_validation"] != "passed"
    assert metadata["return_code"] == returncode


@pytest.mark.asyncio
async def test_timeout_kills_reaps_and_records_cli_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = FakeProcess(b"", block_until_killed=True)

    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return process

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    with pytest.raises(GatewayTransportError, match="cli_timeout"):
        await access._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=0.001,
            request_id="run-1.timeout",
        )
    assert process.killed
    metadata = json.loads(
        next((run_root / "cli-subprocesses").glob("*.json")).read_text(encoding="utf-8")
    )
    assert metadata["response_validation"] == "timeout"
    assert metadata["return_code"] == -9


@pytest.mark.asyncio
async def test_cancellation_kills_reaps_and_records_cli_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = FakeProcess(b"", block_until_killed=True)

    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return process

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    task = asyncio.create_task(
        access._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=10,
            request_id="run-1.cancelled",
        )
    )
    await process.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert process.killed
    metadata = json.loads(
        next((run_root / "cli-subprocesses").glob("*.json")).read_text(encoding="utf-8")
    )
    assert metadata["response_validation"] == "cancelled"
    assert metadata["return_code"] == -9


@pytest.mark.asyncio
async def test_cancelled_trial_invocation_is_buffered_and_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = FakeProcess(b"", block_until_killed=True)

    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        return process

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    access.begin_trial_evidence("trial-cancelled")
    task = asyncio.create_task(
        access._invoke(
            "manager",
            "list_sandboxes",
            [],
            timeout_seconds=10,
            request_id="trial-cancelled.request.0",
        )
    )
    await process.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    evidence = run_root / "cli-subprocesses"
    assert process.killed
    assert not list(evidence.glob("*.json"))
    await access.flush_trial_evidence("trial-cancelled")
    access.end_trial_evidence("trial-cancelled")

    metadata = json.loads(next(evidence.glob("*.json")).read_text(encoding="utf-8"))
    assert metadata["response_validation"] == "cancelled"
    assert metadata["return_code"] == -9


@pytest.mark.asyncio
async def test_file_write_uses_exact_bounded_content_file_and_removes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed_content: bytes | None = None
    observed_path: Path | None = None
    captured_argv: tuple[str, ...] = ()

    async def create_process(*argv: str, **_kwargs: Any) -> FakeProcess:
        nonlocal observed_content, observed_path, captured_argv
        captured_argv = argv
        content_index = argv.index("--content-file") + 1
        observed_path = Path(argv[content_index])
        observed_content = observed_path.read_bytes()
        return FakeProcess(b'{"path":"payload.txt","bytes_written":262144}\n')

    access, _, _ = _access(tmp_path, monkeypatch, create_process)
    access._sandboxes.add("sandbox-1")
    content = ("x\n" * 131_072)[:262_144]
    await access.stage_file_write_content(content, request_id="run-1.write.0")
    staged_path = access._content_path("run-1.write.0")
    assert staged_path.read_bytes() == content.encode()
    response = await access.file_write(
        "sandbox-1",
        session_id="session-1",
        path="payload.txt",
        content=content,
        timeout_ms=1000,
        request_id="run-1.write.0",
    )

    assert observed_content == content.encode()
    assert observed_path is not None and not observed_path.exists()
    assert "--content-file" in captured_argv
    assert "--content" not in captured_argv
    assert response.value["bytes_written"] == 262_144


@pytest.mark.asyncio
async def test_staged_file_write_rejects_content_mismatch_and_can_be_discarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        raise AssertionError("mismatched staged content must not launch a process")

    access, _, _ = _access(tmp_path, monkeypatch, create_process)
    access._sandboxes.add("sandbox-1")
    await access.stage_file_write_content("expected", request_id="run-1.write.mismatch")

    with pytest.raises(ProductAccessError, match="does not match"):
        await access.file_write(
            "sandbox-1",
            session_id=None,
            path="payload.txt",
            content="different",
            timeout_ms=1000,
            request_id="run-1.write.mismatch",
        )

    access.discard_file_write_content("run-1.write.mismatch")
    assert not access._content_path("run-1.write.mismatch").exists()


@pytest.mark.asyncio
@pytest.mark.skipif(os.name != "nt", reason="Windows extended-path identity regression")
async def test_create_accepts_equivalent_windows_extended_workspace_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_holder: dict[str, Path] = {}

    async def create_process(*_argv: str, **_kwargs: Any) -> FakeProcess:
        workspace = workspace_holder["workspace"].resolve(strict=True)
        extended = f"\\\\?\\{workspace}"
        payload = {
            "id": "sandbox-1",
            "workspace_root": extended,
            "state": "ready",
            "activity_revision": 0,
            "daemon": {"host": "127.0.0.1", "port": 32768},
            "daemon_http": {"host": "127.0.0.1", "port": 32769},
            "shared_base": {
                "source": "C:\\cache\\base",
                "target": "/eos/layer-stack/base",
                "root_hash": "abc",
                "readonly": True,
            },
            "resource_profile": {
                "name": "standard",
                "nano_cpus": 1_000_000_000,
                "memory_high_bytes": 402_653_184,
                "memory_max_bytes": 536_870_912,
                "pids_max": 256,
                "workload_memory_high_bytes": 402_653_184,
                "workload_memory_max_bytes": 402_653_184,
                "workload_pids_max": 224,
                "control_plane_pids_reserve": 32,
                "daemon_runtime_profile": "standard",
                "separate_workload_cgroup": True,
            },
        }
        return FakeProcess((json.dumps(payload) + "\n").encode())

    access, run_root, _ = _access(tmp_path, monkeypatch, create_process)
    workspace = run_root / "workspace"
    workspace.mkdir()
    workspace_holder["workspace"] = workspace

    record, response = await access.create_sandbox(
        "image@sha256:digest",
        workspace,
        request_id="run-1.create",
    )

    assert record.id == "sandbox-1"
    assert response.value["workspace_root"].startswith("\\\\?\\")
    assert access.owned_sandboxes == {"sandbox-1"}
