import json
from pathlib import Path

import pytest

from benchmark_lab.models import StateMarker
from benchmark_lab.paths import BenchmarkRoots, MARKER_NAME, PathContractError, ROLE_NAMES


def repositories(tmp_path: Path) -> tuple[Path, Path, Path]:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return test, product, binaries


def test_roots_are_explicit_canonical_and_state_only(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)

    assert roots.benchmark_source_root == test / "benchmark"
    assert roots.benchmark_state_root == test / ".benchmark-state"
    assert json.loads((roots.benchmark_state_root / MARKER_NAME).read_bytes()) == StateMarker().model_dump(mode="json")
    assert {path.name for path in roots.benchmark_state_root.iterdir()} == {MARKER_NAME, *ROLE_NAMES}
    assert set(test.iterdir()) == {test / "benchmark", test / ".benchmark-state"}


def test_relative_or_overlapping_roots_fail_before_state_creation(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    with pytest.raises(PathContractError, match="absolute"):
        BenchmarkRoots.resolve(Path("relative"), product, binaries, initialize=True)
    with pytest.raises(PathContractError, match="disjoint"):
        BenchmarkRoots.resolve(test, test / "benchmark", test / "benchmark", initialize=True)
    assert not (test / ".benchmark-state").exists()


def test_unmarked_or_inexact_state_is_never_adopted(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    state = test / ".benchmark-state"
    state.mkdir()
    sentinel = state / "sentinel"
    sentinel.write_text("keep")
    with pytest.raises(PathContractError, match="not empty"):
        BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    assert sentinel.read_text() == "keep"

    sentinel.unlink()
    (state / MARKER_NAME).write_text('{"owner":"wrong","role":"benchmark-state","schema_version":1}')
    with pytest.raises(PathContractError, match="invalid"):
        BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def test_mutable_paths_must_be_strict_descendants_of_state(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    owned = roots.tmp / "owned"
    owned.mkdir()
    assert roots.require_mutable_path(owned) == owned
    with pytest.raises(PathContractError, match="below"):
        roots.require_mutable_path(roots.benchmark_state_root)
    with pytest.raises(PathContractError, match="below"):
        roots.require_mutable_path(test / "benchmark")
