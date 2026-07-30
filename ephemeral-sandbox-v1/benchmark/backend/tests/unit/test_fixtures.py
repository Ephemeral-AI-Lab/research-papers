import json
from pathlib import Path

import pytest

import benchmark_lab.fixtures as fixtures
from benchmark_lab.fixtures import FixtureError, materialize_workspace


def _profile() -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": "test",
        "version": 1,
        "generator_version": 1,
        "fixture": {"file_count": 7, "logical_bytes": 101, "maximum_depth": 3},
    }


def test_materialized_fixture_is_deterministic_and_exact(tmp_path: Path) -> None:
    cache = tmp_path / "fixtures"
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    manifest = materialize_workspace(cache, first, _profile(), 41)
    reused = materialize_workspace(cache, second, _profile(), 41)

    assert manifest == reused
    first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    assert len(first_files) == 8  # seven payloads plus the versioned manifest
    assert sum(
        (first / path).stat().st_size
        for path in first_files
        if path.name != "fixture-manifest.json"
    ) == 101
    assert all((first / path).read_bytes() == (second / path).read_bytes() for path in first_files)


def test_fixture_cache_rejects_identity_corruption(tmp_path: Path) -> None:
    cache = tmp_path / "fixtures"
    workspace = tmp_path / "first"
    workspace.mkdir()
    materialize_workspace(cache, workspace, _profile(), 41)
    manifest_path = next(cache.rglob("fixture-manifest.json"))
    value = json.loads(manifest_path.read_text())
    value["identity"]["seed"] = 99
    manifest_path.write_text(json.dumps(value))
    destination = tmp_path / "second"
    destination.mkdir()

    with pytest.raises(FixtureError, match="identity"):
        materialize_workspace(cache, destination, _profile(), 41)


def test_fixture_copy_rejects_nonempty_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "user-file").write_text("preserve")
    with pytest.raises(FixtureError, match="empty"):
        materialize_workspace(tmp_path / "fixtures", workspace, _profile(), 41)
    assert (workspace / "user-file").read_text() == "preserve"


def test_depth_100_is_admitted_and_generates_100_parent_components() -> None:
    profile = _profile()
    profile["fixture"] = {
        "file_count": 100,
        "logical_bytes": 100,
        "maximum_depth": 100,
    }

    assert fixtures._validated_fixture_dimensions(profile["fixture"]) == (100, 100, 100)
    assert len(fixtures._relative_path(99, 100).parent.parts) == 100


def test_depth_above_supported_limit_is_rejected() -> None:
    profile = _profile()
    profile["fixture"] = {
        "file_count": 500,
        "logical_bytes": 500,
        "maximum_depth": 500,
    }

    with pytest.raises(FixtureError, match="limits"):
        fixtures._validated_fixture_dimensions(profile["fixture"])
