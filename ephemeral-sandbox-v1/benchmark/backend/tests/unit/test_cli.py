from pathlib import Path

import pytest

from benchmark_lab.cli import _resolve_web_dist
from benchmark_lab.paths import BenchmarkRoots


def roots(tmp_path: Path) -> BenchmarkRoots:
    test_root = tmp_path / "tests"
    product_root = tmp_path / "product"
    product_bin = product_root / "bin"
    benchmark_source = test_root / "benchmark"
    for path in (product_bin, benchmark_source):
        path.mkdir(parents=True)
    return BenchmarkRoots.resolve(test_root, product_root, product_bin, initialize=True)


def test_default_web_distribution_is_owned_state(tmp_path: Path) -> None:
    configured = roots(tmp_path)
    dist = configured.benchmark_state_root / "web-dist"
    dist.mkdir()

    assert _resolve_web_dist(None, configured) == dist


def test_web_distribution_outside_owned_state_is_rejected(tmp_path: Path) -> None:
    configured = roots(tmp_path)
    dist = configured.benchmark_source_root / "web/dist"
    dist.mkdir(parents=True)

    with pytest.raises(SystemExit, match="inside the benchmark state root"):
        _resolve_web_dist(dist, configured)
