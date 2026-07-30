import json
import shutil
from pathlib import Path

import pytest

from benchmark_lab.reports import (
    ReportError,
    RunCorpus,
    derive_summary,
    normalized_report,
    persist_report_bundle,
    render_csv_export,
    render_json_export,
)
from benchmark_lab.artifacts import ArtifactStore
from benchmark_lab.paths import BenchmarkRoots


GOLDEN = Path(__file__).parents[3] / "tests/fixtures/golden/rust"


@pytest.mark.parametrize("case", ["quick-smoke-completed", "quick-smoke-cancelled"])
def test_opens_complete_historical_run_without_product_startup(case: str) -> None:
    corpus = RunCorpus.open(GOLDEN / case)
    assert corpus.report is not None
    assert corpus.summary is not None
    assert len(corpus.expanded["cells"]) == len(corpus.report.cells)
    assert derive_summary(corpus.report) == corpus.summary


def test_historical_exports_regenerate_byte_for_byte() -> None:
    corpus = RunCorpus.open(GOLDEN / "quick-smoke-completed")
    assert corpus.report is not None
    assert json.loads(render_json_export(corpus.report)) == json.loads(
        (corpus.path / "export.json").read_bytes()
    )
    assert render_csv_export(corpus.report) == (corpus.path / "export.csv").read_text()


def test_report_bundle_persists_compatible_artifacts_atomically(tmp_path: Path) -> None:
    source = GOLDEN / "quick-smoke-completed"
    corpus = RunCorpus.open(source)
    assert corpus.report is not None
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    shutil.copytree(source, roots.results / corpus.report.run_id)
    store = ArtifactStore(roots)

    persist_report_bundle(store, corpus.report)

    regenerated = RunCorpus.open(store.run_path(corpus.report.run_id))
    assert regenerated.report == corpus.report
    assert regenerated.summary == corpus.summary
    assert (regenerated.path / "export.csv").read_bytes() == (source / "export.csv").read_bytes()
    assert json.loads((regenerated.path / "export.json").read_bytes()) == json.loads(
        (source / "export.json").read_bytes()
    )
    assert list(roots.tmp.iterdir()) == []


def test_failed_pre_report_run_remains_readable() -> None:
    corpus = RunCorpus.open(GOLDEN / "quick-smoke-failed")
    assert corpus.manifest["state"] == "failed"
    assert corpus.report is None


def test_report_normalization_removes_only_run_provenance() -> None:
    corpus = RunCorpus.open(GOLDEN / "quick-smoke-completed")
    assert corpus.report is not None
    normalized = normalized_report(corpus.report)
    assert normalized["run_id"] == "<run_id>"
    assert normalized["plan_hash"] == corpus.report.plan_hash
    assert normalized["cells"] == corpus.report.cells


def test_report_rejects_noncontiguous_authoritative_observations(tmp_path: Path) -> None:
    source = GOLDEN / "quick-smoke-completed"
    target = tmp_path / "run"
    target.mkdir()
    for item in source.iterdir():
        if item.is_file():
            (target / item.name).write_bytes(item.read_bytes())
    observations = target / "observations.ndjson"
    lines = observations.read_bytes().splitlines(keepends=True)
    observations.write_bytes(lines[1] + b"".join(lines[2:]))
    with pytest.raises(ReportError, match="not contiguous"):
        RunCorpus.open(target)
