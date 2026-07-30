import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark_lab.artifacts import ArtifactId, ArtifactStore
from benchmark_lab.models import OwnedPathMarker
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.recovery import RecoveryScanner
from benchmark_lab.safety import OwnershipLedger


def roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def interrupted_run(
    benchmark_roots: BenchmarkRoots,
    run_id: str = "run-1",
    *,
    state: str = "running",
    owned_roles: tuple[str, ...] = ("runs", "runtime"),
) -> ArtifactStore:
    store = ArtifactStore(benchmark_roots)
    store.create_run(run_id)
    store.write_immutable(
        run_id,
        ArtifactId.RUN_MANIFEST,
        {
            "schema_version": 2,
            "run_id": run_id,
            "name": "interrupted",
            "state": state,
            "plan_hash": "sha256:plan",
            "failure": None,
            "ended_at": None,
        },
    )
    store.append_record(
        run_id,
        ArtifactId.EVENTS,
        {
            "sequence": 1,
            "run_id": run_id,
            "monotonic_offset_ns": 10,
            "data": {"kind": "run_state", "state": state},
        },
    )
    ledger = OwnershipLedger(benchmark_roots)
    for role in owned_roles:
        target = getattr(benchmark_roots, role) / run_id
        target.mkdir()
        ledger.register(target, OwnedPathMarker(role=role, identity={"run_id": run_id}))
    return store


@pytest.mark.parametrize(
    ("state", "owned_roles"),
    [
        ("planned", ()),
        ("queued", ("runs",)),
        ("preparing", ("runtime",)),
        ("running", ("runs", "runtime")),
        ("verifying", ("runs",)),
        ("tearing_down", ()),
        ("cancelling", ("runtime",)),
    ],
)
def test_recovers_every_nonterminal_transition_with_only_present_owned_resources(
    tmp_path: Path, state: str, owned_roles: tuple[str, ...]
) -> None:
    benchmark_roots = roots(tmp_path)
    store = interrupted_run(
        benchmark_roots, state=state, owned_roles=owned_roles
    )
    cleaned: list[str] = []

    result = RecoveryScanner(benchmark_roots, cleaned.append).scan()

    assert result.execution_available
    assert result.recovered_run_ids == ("run-1",)
    assert cleaned == ["run-1"]
    assert store.read_envelope("run-1", ArtifactId.RUN_MANIFEST)["state"] == "failed"
    assert not (benchmark_roots.runs / "run-1").exists()
    assert not (benchmark_roots.runtime / "run-1").exists()


def test_recovers_partial_tail_only_after_proved_cleanup(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    store = interrupted_run(benchmark_roots)
    with (store.run_path("run-1") / "events.ndjson").open("ab") as stream:
        stream.write(b'{"partial":')
    cleaned: list[str] = []
    result = RecoveryScanner(
        benchmark_roots,
        cleaned.append,
        now=lambda: datetime(2026, 7, 13, tzinfo=UTC),
    ).scan()

    assert result.execution_available
    assert result.recovered_run_ids == ("run-1",)
    assert cleaned == ["run-1"]
    assert not (benchmark_roots.runs / "run-1").exists()
    assert not (benchmark_roots.runtime / "run-1").exists()
    manifest = store.read_envelope("run-1", ArtifactId.RUN_MANIFEST)
    assert manifest["state"] == "failed"
    assert manifest["failure"]["code"] == "recovered_interrupted_run"
    assert manifest["ended_at"] == "2026-07-13T00:00:00Z"
    assert store.read_records("run-1", ArtifactId.EVENTS).records[-1]["data"]["state"] == "failed"
    assert len(list((store.run_path("run-1") / ".recovery-quarantine").iterdir())) == 1


def test_recovery_preserves_historical_manifest_envelope_version(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    store = interrupted_run(benchmark_roots)
    path = store.run_path("run-1") / "run-manifest.json"
    envelope = json.loads(path.read_text())
    envelope["schema_version"] = 1
    envelope["data"]["schema_version"] = 1
    path.write_text(json.dumps(envelope) + "\n")

    result = RecoveryScanner(benchmark_roots, lambda _run_id: None).scan()

    assert result.execution_available
    recovered = json.loads(path.read_text())
    assert recovered["schema_version"] == 1
    assert recovered["data"]["schema_version"] == 1
    assert recovered["data"]["state"] == "failed"


@pytest.mark.parametrize("failure", ["ownership", "cleanup"])
def test_failed_proof_or_cleanup_blocks_execution_without_manifest_mutation(
    tmp_path: Path, failure: str
) -> None:
    benchmark_roots = roots(tmp_path)
    store = interrupted_run(benchmark_roots)
    cleaned: list[str] = []
    if failure == "ownership":
        marker = benchmark_roots.runtime / "run-1" / ".ownership.json"
        marker.write_text(marker.read_text().replace('"run-1"', '"other"'))

    def cleanup(run_id: str) -> None:
        cleaned.append(run_id)
        if failure == "cleanup":
            raise RuntimeError("injected cleanup failure")

    result = RecoveryScanner(benchmark_roots, cleanup).scan()
    assert not result.execution_available
    assert len(result.issues) == 1
    assert store.read_envelope("run-1", ArtifactId.RUN_MANIFEST)["state"] == "running"
    assert cleaned == ([] if failure == "ownership" else ["run-1"])


def test_interior_corruption_is_fatal_read_only_and_other_runs_are_scanned(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    first = interrupted_run(benchmark_roots, "run-1")
    interrupted_run(benchmark_roots, "run-2")
    journal = first.run_path("run-1") / "events.ndjson"
    original = journal.read_bytes()
    journal.write_bytes(original + b"broken\n" + original)
    cleaned: list[str] = []

    result = RecoveryScanner(benchmark_roots, cleaned.append).scan()
    assert not result.execution_available
    assert result.recovered_run_ids == ("run-2",)
    assert [issue.run_id for issue in result.issues] == ["run-1"]
    assert journal.read_bytes() == original + b"broken\n" + original
    assert not (first.run_path("run-1") / ".recovery-quarantine").exists()
    assert first.read_envelope("run-1", ArtifactId.RUN_MANIFEST)["state"] == "running"
    assert cleaned == ["run-2"]


def test_terminal_runs_are_never_recovered(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    store = interrupted_run(benchmark_roots)
    manifest = store.read_envelope("run-1", ArtifactId.RUN_MANIFEST)
    manifest["state"] = "failed"
    store.replace_snapshot("run-1", ArtifactId.RUN_MANIFEST, manifest)
    called: list[str] = []
    result = RecoveryScanner(benchmark_roots, called.append).scan()
    assert result.execution_available
    assert result.recovered_run_ids == ()
    assert called == []
