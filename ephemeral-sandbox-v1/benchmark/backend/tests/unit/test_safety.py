from pathlib import Path

import pytest

from benchmark_lab.models import OwnedPathMarker
from benchmark_lab.paths import BenchmarkRoots, MARKER_NAME
from benchmark_lab.safety import OwnershipError, OwnershipLedger

from .test_paths import repositories


def marker(identity: str = "trial-1") -> OwnedPathMarker:
    return OwnedPathMarker(role="runs", identity={"run_id": "run-1", "trial_id": identity})


def test_deletion_requires_exact_marker_and_active_ledger(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    target = roots.runs / "run-1" / "trial-1"
    target.mkdir(parents=True)
    (target / "sentinel").write_text("owned")
    ledger = OwnershipLedger(roots)
    ledger.register(target, marker())

    with pytest.raises(OwnershipError, match="identity mismatch"):
        ledger.remove(target, marker("trial-2"))
    assert target.exists()

    restarted = OwnershipLedger(roots)
    with pytest.raises(OwnershipError, match="active ownership ledger"):
        restarted.remove(target, marker())
    restarted.adopt(target, marker())
    restarted.remove(target, marker())
    assert not target.exists()


def test_outside_paths_roles_and_corrupt_markers_fail_closed(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    outside = roots.tmp / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("keep")
    ledger = OwnershipLedger(roots)
    with pytest.raises(OwnershipError, match="outside its owned role"):
        ledger.register(outside, marker())
    assert (outside / "sentinel").read_text() == "keep"

    target = roots.runs / "run-1" / "trial-1"
    target.mkdir(parents=True)
    ledger.register(target, marker())
    (target / MARKER_NAME).write_text("not-json")
    with pytest.raises(OwnershipError, match="invalid"):
        ledger.remove(target, marker())
    assert target.exists()


def test_symlink_target_never_gains_cleanup_authority(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    outside = roots.tmp / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("keep")
    link = roots.runs / "linked"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OwnershipError, match="symlink"):
        OwnershipLedger(roots).register(link, marker())
    assert sentinel.read_text() == "keep"


def test_symlink_ancestor_is_rejected_even_when_it_points_inside_role(tmp_path: Path) -> None:
    test, product, binaries = repositories(tmp_path)
    roots = BenchmarkRoots.resolve(test, product, binaries, initialize=True)
    real = roots.runs / "real"
    target = real / "trial-1"
    target.mkdir(parents=True)
    link = roots.runs / "linked"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(OwnershipError, match="crosses a symlink"):
        OwnershipLedger(roots).register(link / "trial-1", marker())
    assert not (target / MARKER_NAME).exists()
