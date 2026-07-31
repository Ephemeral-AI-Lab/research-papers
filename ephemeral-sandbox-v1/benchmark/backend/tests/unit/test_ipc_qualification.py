import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest
from benchmark_lab import cli
from benchmark_lab import ipc_qualification as ipc_module
from benchmark_lab.ipc_qualification import (
    BENCHMARK_GIT_EXCLUSIONS,
    EXP1_IPC_BATCH_COUNT,
    EXP1_IPC_CONCURRENCY,
    EXP1_IPC_INVOCATION_COUNT,
    MAX_GATEWAY_HANDLE_GROWTH,
    MAX_GATEWAY_PRIVATE_BYTES_GROWTH,
    MAX_GATEWAY_RSS_BYTES_GROWTH,
    PAPER_FROZEN_SCOPE,
    PERFORMANCE_EVIDENCE,
    PREREGISTERED_ARTIFACT_SHA256,
    PREREGISTERED_PACKAGE_SHA256,
    PREREGISTERED_PRODUCT_BRANCH,
    PREREGISTERED_PRODUCT_COMMIT,
    PROCESS_SAMPLE_EVERY_BATCHES,
    PRODUCTION_WORKLOAD,
    QUALIFICATION_ONLY,
    RESOURCE_GROWTH_POLICY_SOURCE,
    TCPIP_EVENT_IDS,
    EventLogCursor,
    GatewayProcessSample,
    GatewayTcpSample,
    InvocationCapture,
    OwnedTcpConnection,
    QualificationError,
    QualificationWorkload,
    TcpipEvent,
    _create_evidence_root,
    _execute_qualification,
    _expected_sanitized_commands,
    _validate_capture,
    _validate_npipe_endpoint,
)
from benchmark_lab.paths import BenchmarkRoots


class FakeRunner:
    endpoint = "npipe://./pipe/ephemeral-sandbox-test-qualification"

    def __init__(
        self,
        *,
        failure_index: int | None = None,
        raise_index: int | None = None,
        stop_override: dict[str, Any] | None = None,
    ) -> None:
        self.failure_index = failure_index
        self.raise_index = raise_index
        self.stop_override = stop_override
        self.started = 0
        self.stopped = 0
        self.active = 0
        self.peak_active = 0
        self.request_ids: list[str] = []

    @property
    def gateway_pid(self) -> int:
        return 4242

    @property
    def executable_paths(self) -> dict[str, str]:
        return {
            "gateway": "C:\\fake-package\\bin\\sandbox-gateway.exe",
            "manager_cli": "C:\\fake-package\\bin\\sandbox-manager-cli.exe",
            "runtime_cli": "C:\\fake-package\\bin\\sandbox-runtime-cli.exe",
            "observability_cli": (
                "C:\\fake-package\\bin\\sandbox-observability-cli.exe"
            ),
        }

    @property
    def sanitized_commands(self) -> dict[str, Any]:
        return {
            "gateway_serve": {
                "executable_path": self.executable_paths["gateway"],
                "argv": [
                    "serve",
                    "--backend",
                    "none",
                    "--gateway-endpoint",
                    self.endpoint,
                    "--auth-token=<redacted>",
                    "--pid-file",
                    "C:\\fake-evidence\\gateway.pid",
                ],
                "working_directory": "C:\\fake-package",
                "stdin": "null",
                "stdout": "pipe_digest_only",
                "stderr": "pipe_digest_only",
            },
            "manager_list_sandboxes": {
                "executable_path": self.executable_paths["manager_cli"],
                "argv_template": [
                    "--gateway-endpoint",
                    self.endpoint,
                    "--gateway-auth-token=<redacted>",
                    "--request-id",
                    "<unique-request-id>",
                    "list_sandboxes",
                ],
                "working_directory": "C:\\fake-package",
                "stdin": "null",
                "stdout": "strict_single_json_line_hash_only",
                "stderr": "must_be_empty_hash_only",
            },
        }

    async def start(self) -> None:
        self.started += 1

    async def invoke(self, request_id: str) -> InvocationCapture:
        index = len(self.request_ids)
        self.request_ids.append(request_id)
        self.active += 1
        self.peak_active = max(self.peak_active, self.active)
        try:
            await asyncio.sleep(0)
            if index == self.raise_index:
                raise OSError("injected invocation failure")
            failed = index == self.failure_index
            return InvocationCapture(
                request_id=request_id,
                started_monotonic_ns=1000 + index * 10,
                ended_monotonic_ns=1005 + index * 10,
                started_utc_ns=2000 + index * 10,
                ended_utc_ns=2005 + index * 10,
                return_code=0,
                stdout=(
                    b'{"sandboxes":[],"secret":"test-secret-token"}\n'
                    if failed
                    else b'{"sandboxes":[]}\n'
                ),
                stderr=b"",
                credential_exposed=failed,
            )
        finally:
            self.active -= 1

    async def stop(self) -> dict[str, Any]:
        self.stopped += 1
        evidence = {
            "schema_version": 1,
            "gateway_pid": self.gateway_pid,
            "executable_path": self.executable_paths["gateway"],
            "process_exited": True,
            "pid_file_removed": True,
            "sanitized_command": self.sanitized_commands["gateway_serve"],
            "termination": "terminate",
            "return_code": 0,
            "stdout": {
                "bytes": 0,
                "sha256": (
                    "sha256:e3b0c44298fc1c149afbf4c8996fb924"
                    "27ae41e4649b934ca495991b7852b855"
                ),
            },
            "stderr": {
                "bytes": 0,
                "sha256": (
                    "sha256:e3b0c44298fc1c149afbf4c8996fb924"
                    "27ae41e4649b934ca495991b7852b855"
                ),
            },
            "auth_token_recorded": False,
        }
        if self.stop_override:
            evidence.update(self.stop_override)
        return evidence


class FakeCollector:
    def __init__(
        self,
        *,
        events: tuple[TcpipEvent, ...] = (),
        readiness_handles: int = 100,
        post_handles: int = 100,
        readiness_private_bytes: int = 8 * 1024 * 1024,
        post_private_bytes: int = 8 * 1024 * 1024,
        readiness_rss_bytes: int = 12 * 1024 * 1024,
        post_rss_bytes: int = 12 * 1024 * 1024,
        fail_phase: str | None = None,
        process_overrides: dict[tuple[str, int], tuple[int, int, int]] | None = None,
        tcp_connections: (
            dict[tuple[str, int], tuple[OwnedTcpConnection, ...]] | None
        ) = None,
        identity_case: str | None = None,
    ) -> None:
        self.events = events
        self.readiness_handles = readiness_handles
        self.post_handles = post_handles
        self.readiness_private_bytes = readiness_private_bytes
        self.post_private_bytes = post_private_bytes
        self.readiness_rss_bytes = readiness_rss_bytes
        self.post_rss_bytes = post_rss_bytes
        self.fail_phase = fail_phase
        self.process_overrides = process_overrides or {}
        self.tcp_connections = tcp_connections or {}
        self.identity_case = identity_case
        self.calls: list[str] = []

    async def qualification_identity(
        self,
        roots: BenchmarkRoots,
        runner: FakeRunner,
    ) -> dict[str, Any]:
        self.calls.append("identity")
        if self.fail_phase == "identity":
            raise OSError("injected identity failure")
        commit = PREREGISTERED_PRODUCT_COMMIT
        package = os.fspath(roots.product_bin_dir.parent)
        digest = "sha256:" + "0" * 64

        def file_identity(path: str, sha256: str = digest) -> dict[str, Any]:
            return {"path": path, "bytes": 1, "sha256": sha256}

        value = {
            "schema_version": 1,
            "captured_monotonic_ns": 10,
            "captured_utc_ns": 20,
            "product": {
                "commit": commit,
                "branch": PREREGISTERED_PRODUCT_BRANCH,
                "status_clean": True,
                "status_bytes": 0,
                "status_sha256": (
                    "sha256:e3b0c44298fc1c149afbf4c8996fb924"
                    "27ae41e4649b934ca495991b7852b855"
                ),
                "package_directory": package,
                "package_directory_name": f"windows-exp1-{commit[:8]}",
                "expected_package_directory_name": f"windows-exp1-{commit[:8]}",
                "package_name_matches_commit": True,
                "package_zip_path": f"{package}.zip",
                "package_zip_bytes": 1,
                "package_zip_sha256": PREREGISTERED_PACKAGE_SHA256,
            },
            "paper": {
                "commit": "b" * 40,
                "scoped_status_clean": True,
                "scoped_status_bytes": 0,
                "scoped_status_sha256": (
                    "sha256:e3b0c44298fc1c149afbf4c8996fb924"
                    "27ae41e4649b934ca495991b7852b855"
                ),
                "paper_root": os.fspath(roots.test_repository_root),
                "frozen_scope": list(PAPER_FROZEN_SCOPE),
                "generated_exclusions": list(BENCHMARK_GIT_EXCLUSIONS),
                "policy_source": (
                    "experiments/scripts/archive_exp1_run.py:"
                    "PAPER_FROZEN_SCOPE+BENCHMARK_GIT_EXCLUSIONS"
                ),
            },
            "executables": {
                role: file_identity(path, PREREGISTERED_ARTIFACT_SHA256[role])
                for role, path in runner.executable_paths.items()
            },
            "packaged_support": {
                "linux_daemon": file_identity(
                    os.fspath(
                        roots.product_bin_dir.parent
                        / "dist"
                        / "sandbox-daemon-linux-amd64"
                    ),
                    PREREGISTERED_ARTIFACT_SHA256["linux_daemon"],
                ),
                "windows_config": file_identity(
                    os.fspath(
                        roots.product_bin_dir.parent / "config" / "windows-amd64.yml"
                    ),
                    PREREGISTERED_ARTIFACT_SHA256["windows_config"],
                ),
            },
            "qualifier_sources": {
                "ipc_qualification": file_identity(
                    os.fspath(Path(ipc_module.__file__).resolve())
                ),
                "benchmark_cli": file_identity(
                    os.fspath(Path(ipc_module.__file__).with_name("cli.py").resolve())
                ),
                "packaged_gateway_launcher": file_identity(
                    os.fspath(
                        roots.product_bin_dir
                        / "start-sandbox-windows-docker-gateway.ps1"
                    )
                ),
                "ipc_qualification_test": file_identity(
                    os.fspath(
                        roots.benchmark_source_root
                        / "backend"
                        / "tests"
                        / "unit"
                        / "test_ipc_qualification.py"
                    )
                ),
                "protocol_amendment": file_identity(
                    os.fspath(
                        roots.test_repository_root
                        / "experiments"
                        / "exp1-v1.1-protocol-amendment.md"
                    )
                ),
            },
            "host": {
                "computer_name": "DESKTOP-OLP1ADS",
                "os_caption": "Windows",
                "os_version": "10.0.26200",
                "os_build_number": 26200,
                "architecture": "x64",
                "logical_processors": 48,
                "total_memory_bytes": 137_438_953_472,
            },
            "build": {
                "package_identity": f"windows-exp1-{commit[:8]}",
                "product_commit": commit,
                "python_executable": "C:\\Python313\\python.exe",
                "python_implementation": "CPython",
                "python_version": "3.13.0",
                "python_architecture": "amd64",
                "package_build_command": [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    ".\\bin\\package-windows-amd64-release.ps1",
                    "-PackageName",
                    f"windows-exp1-{commit[:8]}",
                    "-OutDir",
                    "target",
                    "-Profile",
                    "release",
                ],
            },
            "sanitized_commands": _expected_sanitized_commands(roots, runner),
        }
        if self.identity_case == "dirty":
            value["product"]["status_clean"] = False
            value["product"]["status_bytes"] = 1
        elif self.identity_case == "package_mismatch":
            value["product"]["package_name_matches_commit"] = False
        elif self.identity_case == "command_shape":
            value["sanitized_commands"]["gateway_serve"]["argv"].append("--secret")
        elif self.identity_case == "paper_dirty":
            value["paper"]["scoped_status_clean"] = False
            value["paper"]["scoped_status_bytes"] = 1
        elif self.identity_case == "branch":
            value["product"]["branch"] = "feature"
        elif self.identity_case == "artifact_hash":
            value["executables"]["gateway"]["sha256"] = digest
        elif self.identity_case == "host":
            value["host"]["computer_name"] = "OTHER-HOST"
        return value

    async def event_cursor(self, phase: str) -> EventLogCursor:
        self.calls.append(f"cursor:{phase}")
        if self.fail_phase == f"cursor:{phase}":
            raise OSError("injected cursor failure")
        is_pre = phase == "pre_readiness"
        return EventLogCursor(
            phase=phase,
            captured_monotonic_ns=100 if is_pre else 400,
            captured_utc_ns=200 if is_pre else 500,
            log_name="System",
            last_record_id=1000 if is_pre else 1100,
        )

    async def tcpip_events(
        self,
        after_record_id: int,
        through_record_id: int,
    ) -> tuple[TcpipEvent, ...]:
        self.calls.append(f"events:{after_record_id}:{through_record_id}")
        if self.fail_phase == "events":
            raise OSError("injected event query failure")
        return self.events

    async def gateway_process_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayProcessSample:
        call = f"process:{phase}:{completed_batches}"
        self.calls.append(call)
        if self.fail_phase == call:
            raise OSError("injected process sample failure")
        readiness = phase == "readiness"
        default = (
            (
                self.readiness_handles,
                self.readiness_private_bytes,
                self.readiness_rss_bytes,
            )
            if readiness
            else (
                self.post_handles,
                self.post_private_bytes,
                self.post_rss_bytes,
            )
        )
        handles, private_bytes, rss_bytes = self.process_overrides.get(
            (phase, completed_batches),
            default,
        )
        return GatewayProcessSample(
            phase=phase,
            captured_monotonic_ns=250 + completed_batches,
            captured_utc_ns=300 + completed_batches,
            pid=pid,
            completed_batches=completed_batches,
            handle_count=handles,
            private_bytes=private_bytes,
            rss_bytes=rss_bytes,
        )

    async def gateway_tcp_sample(
        self,
        pid: int,
        phase: str,
        completed_batches: int,
    ) -> GatewayTcpSample:
        call = f"tcp:{phase}:{completed_batches}"
        self.calls.append(call)
        if self.fail_phase == call:
            raise OSError("injected TCP sample failure")
        return GatewayTcpSample(
            phase=phase,
            captured_monotonic_ns=260 + completed_batches,
            captured_utc_ns=310 + completed_batches,
            pid=pid,
            completed_batches=completed_batches,
            connections=self.tcp_connections.get((phase, completed_batches), ()),
        )


def _roots(tmp_path: Path) -> BenchmarkRoots:
    test_root = tmp_path / "paper"
    product_root = tmp_path / "product"
    product_bin = (
        product_root
        / "target"
        / f"windows-exp1-{PREREGISTERED_PRODUCT_COMMIT[:8]}"
        / "bin"
    )
    (test_root / "benchmark").mkdir(parents=True)
    product_bin.mkdir(parents=True)
    return BenchmarkRoots.resolve(
        test_root,
        product_root,
        product_bin,
        initialize=True,
    )


@pytest.mark.asyncio
async def test_fixed_workload_runs_concurrency_five_without_retry_or_pacing(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-success"
    evidence_root = _create_evidence_root(roots, qualification_id)
    runner = FakeRunner()
    collector = FakeCollector()

    summary = await _execute_qualification(
        roots,
        runner,
        collector,
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=2, concurrency=5),
    )

    assert summary["status"] == "passed"
    assert summary["qualification_only"] is True
    assert summary["performance_evidence"] is False
    assert summary["transport"] == {
        "kind": "windows_named_pipe",
        "endpoint": runner.endpoint,
        "tcp_used": False,
        "fallback_allowed": False,
        "retry_allowed": False,
        "pacing_allowed": False,
        "gateway_count": 1,
    }
    assert summary["workload"]["attempted_invocations"] == 10
    assert summary["workload"]["successful_invocations"] == 10
    assert summary["workload"]["planned_batches"] == 2
    assert summary["workload"]["concurrency"] == 5
    assert runner.started == 1
    assert runner.stopped == 1
    assert runner.peak_active == 5
    assert len(runner.request_ids) == len(set(runner.request_ids)) == 10
    assert collector.calls == [
        "identity",
        "cursor:pre_readiness",
        "process:readiness:0",
        "tcp:readiness:0",
        "process:pre_stop:2",
        "tcp:pre_stop:2",
        "tcp:after_cleanup:2",
        "cursor:post_cleanup",
        "events:1000:1100",
    ]
    assert summary["host_evidence"]["status"] == "passed"
    assert summary["host_evidence"]["event_log"]["new_event_count"] == 0
    growth = summary["host_evidence"]["gateway_process"]["growth"]
    assert growth["peak_over_readiness"]["passed"] is True
    assert growth["final_pre_stop_over_readiness"]["passed"] is True
    assert summary["host_evidence"]["gateway_tcp"]["passed"] is True
    assert summary["host_evidence"]["gateway_stop"]["validation_passed"] is True
    assert summary["host_evidence"]["policy"]["maximum_post_readiness_growth"] == {
        "handle_count": 32,
        "private_bytes": 16 * 1024 * 1024,
        "rss_bytes": 16 * 1024 * 1024,
    }
    assert summary["host_evidence"]["policy"]["source"] == (
        RESOURCE_GROWTH_POLICY_SOURCE
    )

    records = [
        json.loads(line)
        for line in (evidence_root / "invocations.ndjson")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(records) == 10
    assert all(record["result"] == "passed" for record in records)
    assert all(record["qualification_only"] is True for record in records)
    assert all(record["performance_evidence"] is False for record in records)
    assert all(record["stdout_bytes"] == 17 for record in records)
    assert all(record["stderr_bytes"] == 0 for record in records)
    assert len({record["request_id"] for record in records}) == 10
    persisted_summary = json.loads(
        (evidence_root / "summary.json").read_text(encoding="utf-8")
    )
    assert persisted_summary == summary
    persisted_host_evidence = json.loads(
        (evidence_root / "host-evidence.json").read_text(encoding="utf-8")
    )
    assert persisted_host_evidence == summary["host_evidence"]
    manifest = json.loads(
        (evidence_root / "qualification-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["qualification_only"] is True
    assert manifest["performance_evidence"] is False
    assert manifest["identity"] == summary["host_evidence"]["identity"]
    assert manifest["gateway_stop"] == summary["gateway"]
    assert summary["evidence"]["qualification_manifest_json_sha256"].startswith(
        "sha256:"
    )


@pytest.mark.asyncio
async def test_failure_retains_complete_batch_evidence_and_stops(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-failure"
    evidence_root = _create_evidence_root(roots, qualification_id)
    runner = FakeRunner(failure_index=2)

    summary = await _execute_qualification(
        roots,
        runner,
        FakeCollector(),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=3, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == "credential_echo"
    assert summary["workload"]["attempted_invocations"] == 5
    assert summary["workload"]["successful_invocations"] == 4
    assert summary["workload"]["failed_invocations"] == 1
    assert summary["workload"]["batches_started"] == 1
    assert summary["workload"]["batches_completed"] == 0
    assert summary["first_failure"]["invocation_index"] == 2
    assert runner.stopped == 1
    evidence = b"".join(path.read_bytes() for path in sorted(evidence_root.iterdir()))
    assert b"test-secret-token" not in evidence
    assert (
        len(
            (evidence_root / "invocations.ndjson")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        == 5
    )


@pytest.mark.asyncio
async def test_runner_exception_becomes_partial_failure_record(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-runner-error"
    evidence_root = _create_evidence_root(roots, qualification_id)
    runner = FakeRunner(raise_index=1)

    summary = await _execute_qualification(
        roots,
        runner,
        FakeCollector(),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=2, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == "runner_error:OSError"
    assert summary["workload"]["attempted_invocations"] == 5
    assert summary["first_failure"]["request_id"] == runner.request_ids[1]


@pytest.mark.asyncio
@pytest.mark.parametrize("event_id", TCPIP_EVENT_IDS)
async def test_new_tcpip_event_fails_qualification_with_cursor_evidence(
    tmp_path: Path,
    event_id: int,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = f"qualification-tcpip-event-{event_id}"
    evidence_root = _create_evidence_root(roots, qualification_id)
    event = TcpipEvent(
        event_id=event_id,
        record_id=1050,
        created_at_utc="2026-07-31T08:00:00.0000000Z",
    )

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(events=(event,)),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == "tcpip_event_detected"
    assert summary["gate_failures"] == ["tcpip_event_detected"]
    assert summary["workload"]["successful_invocations"] == 5
    event_evidence = summary["host_evidence"]["event_log"]
    assert event_evidence["pre_readiness_cursor"]["last_record_id"] == 1000
    assert event_evidence["post_cleanup_cursor"]["last_record_id"] == 1100
    assert event_evidence["query_interval"] == (
        "(pre_readiness_record_id, post_cleanup_record_id]"
    )
    assert event_evidence["new_event_count"] == 1
    assert event_evidence["events"] == [
        {
            "event_id": event_id,
            "record_id": 1050,
            "created_at_utc": "2026-07-31T08:00:00.0000000Z",
            "provider_name": "Tcpip",
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("collector_kwargs", "failure", "metric"),
    [
        (
            {"post_handles": 100 + MAX_GATEWAY_HANDLE_GROWTH + 1},
            "gateway_handle_peak_growth_exceeded",
            "handle_count",
        ),
        (
            {
                "post_private_bytes": (
                    8 * 1024 * 1024 + MAX_GATEWAY_PRIVATE_BYTES_GROWTH + 1
                )
            },
            "gateway_private_bytes_peak_growth_exceeded",
            "private_bytes",
        ),
        (
            {"post_rss_bytes": (12 * 1024 * 1024 + MAX_GATEWAY_RSS_BYTES_GROWTH + 1)},
            "gateway_rss_peak_growth_exceeded",
            "rss_bytes",
        ),
    ],
)
async def test_gateway_process_growth_policy_is_fail_closed(
    tmp_path: Path,
    collector_kwargs: dict[str, int],
    failure: str,
    metric: str,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = f"qualification-{metric.replace('_', '-')}"
    evidence_root = _create_evidence_root(roots, qualification_id)

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(**collector_kwargs),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == failure
    decision = summary["host_evidence"]["gateway_process"]["growth"][
        "peak_over_readiness"
    ]["decisions"][metric]
    assert decision["within_bound"] is False
    assert decision["growth"] == decision["maximum_allowed_growth"] + 1
    assert summary["workload"]["successful_invocations"] == 5


@pytest.mark.asyncio
async def test_gateway_process_growth_at_exact_bounds_passes(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-exact-growth-bounds"
    evidence_root = _create_evidence_root(roots, qualification_id)

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(
            post_handles=100 + MAX_GATEWAY_HANDLE_GROWTH,
            post_private_bytes=(8 * 1024 * 1024 + MAX_GATEWAY_PRIVATE_BYTES_GROWTH),
            post_rss_bytes=12 * 1024 * 1024 + MAX_GATEWAY_RSS_BYTES_GROWTH,
        ),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "passed"
    growth = summary["host_evidence"]["gateway_process"]["growth"]
    for gate in ("peak_over_readiness", "final_pre_stop_over_readiness"):
        decisions = growth[gate]["decisions"]
        assert all(decision["within_bound"] for decision in decisions.values())
        assert all(
            decision["growth"] == decision["maximum_allowed_growth"]
            for decision in decisions.values()
        )


@pytest.mark.asyncio
async def test_cadence_peak_growth_fails_even_when_final_returns_to_baseline(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-cadence-peak"
    evidence_root = _create_evidence_root(roots, qualification_id)
    collector = FakeCollector(
        process_overrides={
            ("cadence", 100): (
                100 + MAX_GATEWAY_HANDLE_GROWTH + 1,
                8 * 1024 * 1024,
                12 * 1024 * 1024,
            ),
            ("pre_stop", 100): (
                100,
                8 * 1024 * 1024,
                12 * 1024 * 1024,
            ),
        }
    )

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        collector,
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=100, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == "gateway_handle_peak_growth_exceeded"
    growth = summary["host_evidence"]["gateway_process"]["growth"]
    assert growth["peak_over_readiness"]["passed"] is False
    assert growth["final_pre_stop_over_readiness"]["passed"] is True
    assert "process:cadence:100" in collector.calls
    assert "tcp:cadence:100" in collector.calls
    assert summary["workload"]["successful_invocations"] == 500


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("phase", "completed_batches", "workload_batches"),
    [
        ("readiness", 0, 1),
        ("cadence", 100, 100),
        ("pre_stop", 1, 1),
        ("after_cleanup", 1, 1),
    ],
)
async def test_owned_tcp_at_any_required_checkpoint_fails(
    tmp_path: Path,
    phase: str,
    completed_batches: int,
    workload_batches: int,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = f"qualification-tcp-{phase.replace('_', '-')}"
    evidence_root = _create_evidence_root(roots, qualification_id)
    connection = OwnedTcpConnection(
        state="Listen",
        local_address="127.0.0.1",
        local_port=7878,
        remote_address="0.0.0.0",
        remote_port=0,
    )

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(
            tcp_connections={(phase, completed_batches): (connection,)},
        ),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=workload_batches, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert "gateway_owned_tcp_detected" in summary["gate_failures"]
    tcp = summary["host_evidence"]["gateway_tcp"]
    assert tcp["owned_connection_count"] == 1
    matching = [
        sample
        for sample in tcp["samples"]
        if sample["phase"] == phase and sample["completed_batches"] == completed_batches
    ]
    assert matching[0]["connections"][0]["local_port"] == 7878


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fail_phase", "workload_batches"),
    [
        ("tcp:readiness:0", 1),
        ("process:cadence:100", 100),
        ("tcp:cadence:100", 100),
        ("tcp:pre_stop:1", 1),
        ("tcp:after_cleanup:1", 1),
    ],
)
async def test_missing_checkpoint_evidence_fails_closed(
    tmp_path: Path,
    fail_phase: str,
    workload_batches: int,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-missing-" + fail_phase.replace(":", "-").replace(
        "_", "-"
    )
    evidence_root = _create_evidence_root(roots, qualification_id)

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(fail_phase=fail_phase),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=workload_batches, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert "host_evidence_collection_error" in summary["gate_failures"]
    assert any(
        failure in summary["gate_failures"]
        for failure in (
            "gateway_process_evidence_incomplete",
            "gateway_tcp_evidence_incomplete",
        )
    )
    assert summary["host_evidence"]["collector_errors"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("override", "field"),
    [
        ({"gateway_pid": 9999}, "gateway_pid"),
        ({"executable_path": "C:\\wrong.exe"}, "executable_path"),
        ({"process_exited": False}, "process_exited"),
        ({"pid_file_removed": False}, "pid_file_removed"),
        ({"sanitized_command": {"redacted": False}}, "sanitized_command"),
        ({"termination": "kill_after_terminate_timeout"}, "termination"),
        ({"return_code": None}, "return_code"),
        ({"stdout": {"bytes": 0, "sha256": "invalid"}}, "stdout"),
        ({"auth_token_recorded": True}, "auth_token_recorded"),
    ],
)
async def test_stop_evidence_fields_are_fail_closed(
    tmp_path: Path,
    override: dict[str, Any],
    field: str,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = f"qualification-stop-{field.replace('_', '-')}"
    evidence_root = _create_evidence_root(roots, qualification_id)

    summary = await _execute_qualification(
        roots,
        FakeRunner(stop_override=override),
        FakeCollector(),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert "gateway_stop_evidence_invalid" in summary["gate_failures"]
    assert summary["host_evidence"]["gateway_stop"]["validation_passed"] is False
    assert summary["host_evidence"]["gateway_stop"]["validation_errors"] == [
        {"phase": "gateway_stop_evidence", "error_type": "QualificationError"}
    ]
    assert summary["host_evidence"]["event_log"]["query_completed"] is True
    assert summary["host_evidence"]["gateway_tcp"]["samples"][-1]["phase"] == (
        "after_cleanup"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "identity_case",
    [
        "dirty",
        "package_mismatch",
        "command_shape",
        "paper_dirty",
        "branch",
        "artifact_hash",
        "host",
    ],
)
async def test_identity_drift_blocks_gateway_start_and_preserves_manifest(
    tmp_path: Path,
    identity_case: str,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = f"qualification-identity-{identity_case.replace('_', '-')}"
    evidence_root = _create_evidence_root(roots, qualification_id)
    runner = FakeRunner()

    summary = await _execute_qualification(
        roots,
        runner,
        FakeCollector(identity_case=identity_case),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert runner.started == 0
    assert "qualification_identity_invalid" in summary["gate_failures"]
    assert summary["workload"]["attempted_invocations"] == 0
    manifest = json.loads(
        (evidence_root / "qualification-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "failed"
    assert manifest["identity"] is not None


@pytest.mark.asyncio
async def test_collector_failure_preserves_partial_host_evidence(
    tmp_path: Path,
) -> None:
    roots = _roots(tmp_path)
    qualification_id = "qualification-collector-failure"
    evidence_root = _create_evidence_root(roots, qualification_id)

    summary = await _execute_qualification(
        roots,
        FakeRunner(),
        FakeCollector(fail_phase="cursor:post_cleanup"),
        evidence_root,
        qualification_id,
        QualificationWorkload(batches=1, concurrency=5),
    )

    assert summary["status"] == "failed"
    assert summary["failure_kind"] == "host_evidence_collection_error"
    assert summary["gate_failures"] == [
        "host_evidence_collection_error",
        "tcpip_event_evidence_incomplete",
    ]
    host = summary["host_evidence"]
    assert host["event_log"]["pre_readiness_cursor"] is not None
    assert host["event_log"]["post_cleanup_cursor"] is None
    assert host["event_log"]["query_completed"] is False
    assert host["gateway_process"]["passed"] is True
    assert host["collector_errors"] == [
        {"phase": "post_cleanup_cursor", "error_type": "OSError"}
    ]
    assert (evidence_root / "host-evidence.json").is_file()


@pytest.mark.parametrize(
    ("capture", "expected"),
    [
        (
            InvocationCapture(
                "request-1",
                1,
                2,
                3,
                4,
                1,
                b"",
                b"",
            ),
            "nonzero_exit",
        ),
        (
            InvocationCapture(
                "request-1",
                1,
                2,
                3,
                4,
                0,
                b'{"sandboxes":[]}\n',
                b"warning\n",
            ),
            "unexpected_stderr",
        ),
        (
            InvocationCapture(
                "request-1",
                1,
                2,
                3,
                4,
                0,
                b'{"sandboxes":[]}\nextra\n',
                b"",
            ),
            "stdout_framing",
        ),
        (
            InvocationCapture(
                "request-1",
                1,
                2,
                3,
                4,
                0,
                b"not-json\n",
                b"",
            ),
            "invalid_json",
        ),
        (
            InvocationCapture(
                "request-1",
                1,
                2,
                3,
                4,
                0,
                b'{"sandboxes":[],"extra":true}\n',
                b"",
            ),
            "response_shape",
        ),
    ],
)
def test_invocation_validation_is_strict(
    capture: InvocationCapture,
    expected: str,
) -> None:
    assert _validate_capture(capture) == expected


def test_production_workload_is_fixed() -> None:
    assert EXP1_IPC_INVOCATION_COUNT == 25_000
    assert EXP1_IPC_CONCURRENCY == 5
    assert EXP1_IPC_BATCH_COUNT == 5_000
    assert PRODUCTION_WORKLOAD == QualificationWorkload(
        batches=5_000,
        concurrency=5,
    )
    assert PRODUCTION_WORKLOAD.invocation_count == 25_000
    assert QUALIFICATION_ONLY is True
    assert PERFORMANCE_EVIDENCE is False
    assert TCPIP_EVENT_IDS == (4227, 4231)
    assert MAX_GATEWAY_HANDLE_GROWTH == 32
    assert MAX_GATEWAY_PRIVATE_BYTES_GROWTH == 16 * 1024 * 1024
    assert MAX_GATEWAY_RSS_BYTES_GROWTH == 16 * 1024 * 1024
    assert RESOURCE_GROWTH_POLICY_SOURCE == (
        "EXP1 v1.1 IPC qualification policy preregistration"
    )
    assert PROCESS_SAMPLE_EVERY_BATCHES == 100


def test_paper_scope_matches_archive_contract() -> None:
    assert PAPER_FROZEN_SCOPE == (
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
    assert BENCHMARK_GIT_EXCLUSIONS == (
        ":(exclude,glob)benchmark/**/.pytest_cache/**",
        ":(exclude,glob)benchmark/**/.venv/**",
        ":(exclude,glob)benchmark/**/__pycache__/**",
        ":(exclude,glob)benchmark/**/dist/**",
        ":(exclude,glob)benchmark/**/node_modules/**",
        ":(exclude,glob)benchmark/**/playwright-report/**",
        ":(exclude,glob)benchmark/**/test-results/**",
        ":(exclude,glob)benchmark/**/*.pyc",
    )


def test_only_safe_npipe_endpoint_is_accepted() -> None:
    _validate_npipe_endpoint("npipe://./pipe/ephemeral-sandbox-exp1-ipc-1234")
    for endpoint in (
        "127.0.0.1:7878",
        "tcp://127.0.0.1:7878",
        "unix:///tmp/gateway.sock",
        "npipe://./pipe/../escape",
        "npipe://server/pipe/gateway",
        "npipe://./pipe/name with spaces",
        "npipe://./pipe/name?query",
        f"npipe://./pipe/{'x' * 249}",
    ):
        with pytest.raises(QualificationError):
            _validate_npipe_endpoint(endpoint)


def test_cli_command_has_no_workload_override_flags(tmp_path: Path) -> None:
    roots = _roots(tmp_path)
    arguments = cli.parser().parse_args(
        [
            "qualify-exp1-ipc",
            "--test-repository-root",
            str(roots.test_repository_root),
            "--product-root",
            str(roots.product_root),
            "--product-bin-dir",
            str(roots.product_bin_dir),
        ]
    )

    assert arguments.command == "qualify-exp1-ipc"
    assert not hasattr(arguments, "batches")
    assert not hasattr(arguments, "concurrency")
    assert not hasattr(arguments, "invocations")


def test_cli_returns_two_for_failed_qualification(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def failed(_roots: object) -> dict[str, str]:
        return {"status": "failed"}

    monkeypatch.setattr(cli, "qualify_exp1_ipc", failed)
    service = argparse.Namespace(roots=object())
    arguments = argparse.Namespace(command="qualify-exp1-ipc")

    assert cli._dispatch(arguments, service) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "failed"}
