from dataclasses import replace
from pathlib import Path

import pytest

from benchmark_lab.comparison import ComparisonError, compare_runs, read_comparison
from benchmark_lab.reports import RunCorpus, derive_summary


GOLDEN = Path(__file__).parents[3] / "tests/fixtures/golden"


def candidate_from(reference: RunCorpus, run_id: str) -> RunCorpus:
    assert reference.report is not None
    manifest = {**reference.manifest, "run_id": run_id}
    report = reference.report.model_copy(update={"run_id": run_id})
    candidate = replace(
        reference,
        manifest=manifest,
        report=report,
        summary=derive_summary(report),
    )
    candidate.validate()
    return candidate


def test_reads_historical_comparison_revision_without_relabeling() -> None:
    compatible = read_comparison(GOLDEN / "comparison/compatible-v1.json")
    incompatible = read_comparison(GOLDEN / "comparison/incompatible-v1.json")
    assert compatible.comparison_derivation_revision == 2
    assert compatible.compatible
    assert not incompatible.compatible


def test_current_comparison_matches_cells_and_preserves_statistics() -> None:
    reference = RunCorpus.open(GOLDEN / "rust/quick-smoke-completed")
    candidate = candidate_from(reference, "candidate-run")
    comparison = compare_runs(reference, candidate)
    assert comparison.comparison_derivation_revision == 3
    assert comparison.compatible
    assert len(comparison.matched_cells) == len(reference.report.cells)
    assert comparison.deltas
    assert all(delta["absolute_change"] == 0 for delta in comparison.deltas if delta["absolute_change"] is not None)
    assert comparison.phase_comparisons


def test_undeclared_treatment_difference_blocks_aggregate_deltas() -> None:
    reference = RunCorpus.open(GOLDEN / "rust/quick-smoke-completed")
    candidate = candidate_from(reference, "candidate-run")
    candidate.manifest["treatment"] = {
        **candidate.manifest["treatment"],
        "source_commit": "different",
    }
    comparison = compare_runs(reference, candidate)
    assert not comparison.compatible
    assert comparison.deltas == []
    assert any(not check["compatible"] for check in comparison.checks)

    descriptive = compare_runs(reference, candidate, descriptive_override=True)
    assert descriptive.descriptive_only
    assert descriptive.deltas


def test_same_run_is_rejected() -> None:
    corpus = RunCorpus.open(GOLDEN / "rust/quick-smoke-completed")
    with pytest.raises(ComparisonError, match="must differ"):
        compare_runs(corpus, corpus)
