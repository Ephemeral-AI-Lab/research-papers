import json
from pathlib import Path

import pytest

from benchmark_lab.artifacts import (
    ArtifactError,
    ArtifactId,
    ArtifactStore,
    read_envelope_path,
    read_journal_path,
)
from benchmark_lab.paths import BenchmarkRoots


GOLDEN = Path(__file__).parents[3] / "tests/fixtures/golden"


def roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


@pytest.mark.parametrize("case", ["quick-smoke-completed", "quick-smoke-cancelled"])
def test_reads_frozen_legacy_envelopes(case: str) -> None:
    run = GOLDEN / "rust" / case
    expected = {
        ArtifactId.RUN_MANIFEST: "run-manifest.json",
        ArtifactId.INTENT_PLAN: "intent-plan.json",
        ArtifactId.EXPANDED_PLAN: "expanded-plan.json",
        ArtifactId.DEFINITION_SNAPSHOT: "definition-snapshot.json",
        ArtifactId.ENVIRONMENT_METADATA: "environment-metadata.json",
        ArtifactId.SUMMARY: "summary.json",
        ArtifactId.REPORT: "report.json",
        ArtifactId.JSON_EXPORT: "export.json",
    }
    for artifact_id, file_name in expected.items():
        assert read_envelope_path(run / file_name, artifact_id)


def test_migrates_all_historical_observation_versions_in_memory() -> None:
    observations = GOLDEN / "observations"
    v1 = read_journal_path(observations / "observations-v1.ndjson", ArtifactId.OBSERVATIONS)
    v2 = read_journal_path(observations / "observations-v2.ndjson", ArtifactId.OBSERVATIONS)
    v3 = read_journal_path(observations / "observations-v3.ndjson", ArtifactId.OBSERVATIONS)
    assert v1.records == v2.records == v3.records
    trial = read_journal_path(
        observations / "observations-v2-trial.ndjson", ArtifactId.OBSERVATIONS
    ).records[0]
    assert trial["record"]["data"]["artifacts"] == []


def test_schema_v5_trial_lifecycle_round_trips_and_rejects_v4_shape(
    tmp_path: Path,
) -> None:
    benchmark_roots = roots(tmp_path)
    store = ArtifactStore(benchmark_roots)
    run = store.create_run("run-v5")
    trial = {
        "operation_id": "file_read",
        "cell_id": "sha256:" + "1" * 64,
        "trial_id": "trial-1",
        "warmup": False,
        "kind": "measured",
        "sequence_in_cell": 0,
        "reportable": True,
        "latency_ns": 11,
        "request_count": 1,
        "status": "success",
        "product_succeeded": True,
        "infrastructure_failed": False,
        "cleanup_baseline_restored": True,
        "checks_passed": True,
        "setup_ns": 1,
        "operation_ns": 11,
        "verify_ns": 2,
        "teardown_ns": 3,
        "artifacts": [],
    }
    record = {"sequence": 1, "record": {"record": "trial", "data": trial}}
    store.append_record("run-v5", ArtifactId.OBSERVATIONS, record)
    assert store.read_records("run-v5", ArtifactId.OBSERVATIONS).records == [record]

    envelope = json.loads((run / "observations.ndjson").read_text())
    del envelope["data"]["record"]["data"]["verify_ns"]
    (run / "observations.ndjson").write_text(json.dumps(envelope) + "\n")
    with pytest.raises(ArtifactError, match="schema version 5 trial fields"):
        store.read_records("run-v5", ArtifactId.OBSERVATIONS)


def test_recovery_accepts_only_a_partial_final_record() -> None:
    recovery = GOLDEN / "recovery"
    partial = recovery / "complete-plus-partial-tail.ndjson"
    with pytest.raises(ArtifactError, match="partial trailing"):
        read_journal_path(partial, ArtifactId.EVENTS)
    recovered = read_journal_path(partial, ArtifactId.EVENTS, recover_partial_tail=True)
    assert len(recovered.records) == 1
    assert recovered.partial_tail_line == 2

    with pytest.raises(ArtifactError, match="line 2"):
        read_journal_path(
            recovery / "interior-corruption.ndjson",
            ArtifactId.EVENTS,
            recover_partial_tail=True,
        )


def test_schema_mismatch_and_unknown_version_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"schema_name":"wrong","schema_version":1,"data":{}}')
    with pytest.raises(ArtifactError, match="schema mismatch"):
        read_envelope_path(path, ArtifactId.RUN_MANIFEST)
    path.write_text(
        '{"schema_name":"eos_benchmark_run_manifest","schema_version":3,"data":{}}'
    )
    with pytest.raises(ArtifactError, match="unsupported"):
        read_envelope_path(path, ArtifactId.RUN_MANIFEST)


def test_store_writes_atomically_and_quarantines_partial_tail(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    store = ArtifactStore(benchmark_roots)
    run = store.create_run("run-1")
    manifest = {"schema_version": 1, "run_id": "run-1"}
    store.write_immutable("run-1", ArtifactId.RUN_MANIFEST, manifest)
    assert store.read_envelope("run-1", ArtifactId.RUN_MANIFEST) == manifest
    with pytest.raises(ArtifactError, match="already exists"):
        store.write_immutable("run-1", ArtifactId.RUN_MANIFEST, manifest)

    store.replace_snapshot("run-1", ArtifactId.REPORT, {"revision": 1})
    store.replace_snapshot("run-1", ArtifactId.REPORT, {"revision": 2})
    assert store.read_envelope("run-1", ArtifactId.REPORT) == {"revision": 2}
    assert list(run.glob(".*.tmp-*")) == []
    assert list(benchmark_roots.tmp.iterdir()) == []

    event = {
        "sequence": 1,
        "run_id": "run-1",
        "monotonic_offset_ns": 0,
        "data": {"kind": "run_state", "state": "planned"},
    }
    store.append_record("run-1", ArtifactId.EVENTS, event)
    with (run / "events.ndjson").open("ab") as stream:
        stream.write(b'{"partial":')
    recovered = store.read_records("run-1", ArtifactId.EVENTS, recover_partial_tail=True)
    assert recovered.partial_tail_line == 2
    quarantined = store.quarantine_partial_tail("run-1", ArtifactId.EVENTS)
    assert quarantined is not None
    assert quarantined.line == 2
    assert store.read_records("run-1", ArtifactId.EVENTS).records == [event]
    quarantine = run / ".recovery-quarantine" / quarantined.file_name
    assert quarantine.read_bytes() == b'{"partial":'


def test_bounded_evidence_is_content_addressed_and_paths_are_closed(tmp_path: Path) -> None:
    store = ArtifactStore(roots(tmp_path))
    store.create_run("run-1")
    first = store.write_trial_evidence("run-1", "cell:1", "trial-1", {"ok": True})
    second = store.write_trial_evidence("run-1", "cell:1", "trial-1", {"ok": True})
    assert first == second
    with pytest.raises(ArtifactError, match="path component"):
        store.write_trial_evidence("run-1", "../escape", "trial-1", {})
    with pytest.raises(ArtifactError, match="runtime secret"):
        store.write_trial_evidence(
            "run-1", "cell:2", "trial-2", {"token": "do-not-store"},
            forbidden_secrets=("do-not-store",),
        )


def test_artifact_index_and_download_use_only_opaque_ids(tmp_path: Path) -> None:
    store = ArtifactStore(roots(tmp_path))
    run = store.create_run("run-1")
    store.write_immutable("run-1", ArtifactId.RUN_MANIFEST, {"run_id": "run-1"})
    evidence = store.write_trial_evidence("run-1", "cell:1", "trial-1", {"ok": True})
    index = store.list_artifacts("run-1")
    assert [item.artifact_id for item in index] == [
        evidence.artifact_id,
        ArtifactId.RUN_MANIFEST.value,
    ]
    assert store.download_artifact("run-1", evidence.artifact_id).reference == evidence
    assert json.loads(
        store.download_artifact("run-1", ArtifactId.RUN_MANIFEST.value).content
    )["data"] == {"run_id": "run-1"}
    for unsafe in ("../run-manifest.json", "cells/cell:1", "bounded_evidence_unknown"):
        with pytest.raises(ArtifactError, match="unknown artifact id"):
            store.download_artifact("run-1", unsafe)

    evidence_path = next((run / "cells").rglob("operation-evidence-*.json"))
    evidence_path.rename(evidence_path.with_name("operation-evidence-" + "0" * 64 + ".json"))
    with pytest.raises(ArtifactError, match="digest mismatch"):
        store.list_artifacts("run-1")


def test_frozen_bounded_evidence_is_indexable_without_product_access(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    destination = benchmark_roots.results / "run-1"
    source = GOLDEN / "rust" / "quick-smoke-completed"
    import shutil

    shutil.copytree(source, destination)
    index = ArtifactStore(benchmark_roots).list_artifacts("run-1")
    evidence = [item for item in index if item.artifact_id.startswith("bounded_evidence_")]
    assert len(evidence) == 48
    assert all(item.size_bytes <= 1024 * 1024 for item in evidence)


def test_safe_incomplete_removal_refuses_unknown_entries(tmp_path: Path) -> None:
    store = ArtifactStore(roots(tmp_path))
    run = store.create_run("run-1")
    (run / "unknown").write_text("keep")
    with pytest.raises(ArtifactError, match="prevents safe removal"):
        store.remove_incomplete_run("run-1")
    assert (run / "unknown").read_text() == "keep"
