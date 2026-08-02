import json
import os
import shutil
import subprocess
from pathlib import Path
from threading import Event, Lock

import pytest

import benchmark_lab.fixtures as fixtures
from benchmark_lab.fixtures import (
    FixtureError,
    materialize_workspace,
    materialize_workspaces,
)


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
    first_files = sorted(
        path.relative_to(first) for path in first.rglob("*") if path.is_file()
    )
    second_files = sorted(
        path.relative_to(second) for path in second.rglob("*") if path.is_file()
    )
    assert first_files == second_files
    assert len(first_files) == 8  # seven payloads plus the versioned manifest
    assert (
        sum(
            (first / path).stat().st_size
            for path in first_files
            if path.name != "fixture-manifest.json"
        )
        == 101
    )
    assert all(
        (first / path).read_bytes() == (second / path).read_bytes()
        for path in first_files
    )


def test_stable_cache_content_hash_is_validated_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "fixtures"
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    calls = 0
    hash_tree = fixtures._fixture_tree_hash

    def count_hashes(root: Path, payloads: list[tuple[Path, int]]) -> str:
        nonlocal calls
        calls += 1
        return hash_tree(root, payloads)

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(fixtures, "_fixture_tree_hash", count_hashes)

    materialize_workspace(cache, first, _profile(), 41)
    materialize_workspace(cache, second, _profile(), 41)

    assert calls == 1


def test_batch_materialization_is_exact_independent_and_validates_cache_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "fixtures"
    destinations = tuple(tmp_path / f"workspace-{index}" for index in range(3))
    for destination in destinations:
        destination.mkdir()
    validations = 0
    validate_cache = fixtures._validated_fixture_cache

    def count_validations(
        source: Path,
        profile: dict[str, object],
        manifest: dict[str, object],
    ) -> fixtures._TreeInventory:
        nonlocal validations
        validations += 1
        return validate_cache(source, profile, manifest)

    monkeypatch.setattr(fixtures, "_validated_fixture_cache", count_validations)

    manifest = materialize_workspaces(
        cache, destinations, _profile(), 41, max_workers=2
    )

    assert manifest["actual_file_count"] == 7
    assert validations == 1
    source = next(cache.rglob("fixture-manifest.json")).parent
    relative_files = sorted(
        path.relative_to(destinations[0])
        for path in destinations[0].rglob("*")
        if path.is_file()
    )
    assert len(relative_files) == 8
    for relative in relative_files:
        paths = [
            source / relative,
            *(destination / relative for destination in destinations),
        ]
        assert len({(path.stat().st_dev, path.stat().st_ino) for path in paths}) == len(
            paths
        )
        assert len({path.stat().st_size for path in paths}) == 1
        assert len({path.read_bytes() for path in paths}) == 1


def test_batch_materialization_bounds_concurrent_copies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "fixtures"
    destinations = tuple(tmp_path / f"workspace-{index}" for index in range(5))
    for destination in destinations:
        destination.mkdir()
    active = 0
    maximum_active = 0
    lock = Lock()
    two_workers_started = Event()
    materialize = fixtures._materialize_validated_workspace

    def count_concurrency(
        source: Path,
        destination: Path,
        inventory: fixtures._TreeInventory,
    ) -> None:
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
            if active == 2:
                two_workers_started.set()
        try:
            assert two_workers_started.wait(timeout=5)
            materialize(source, destination, inventory)
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(fixtures, "_materialize_validated_workspace", count_concurrency)

    materialize_workspaces(cache, destinations, _profile(), 41, max_workers=2)

    assert maximum_active == 2


def test_batch_materialization_rejects_extra_destination_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    copy_tree = fixtures._copy_tree_with_python

    def copy_with_extra_entry(
        source: Path,
        destination: Path,
        inventory: fixtures._TreeInventory,
    ) -> None:
        copy_tree(source, destination, inventory)
        (destination / "unexpected.bin").write_bytes(b"unexpected")

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(fixtures, "_copy_tree_with_python", copy_with_extra_entry)

    with pytest.raises(FixtureError, match="drifted"):
        materialize_workspaces(
            tmp_path / "fixtures",
            (workspace,),
            _profile(),
            41,
        )


def test_batch_materialization_rejects_hardlinked_destination_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def hardlink_tree(
        source: Path,
        destination: Path,
        inventory: fixtures._TreeInventory,
    ) -> None:
        for relative in sorted(
            inventory.directories,
            key=lambda value: (value.count("/"), value),
        ):
            if relative != ".":
                (destination / Path(relative)).mkdir(parents=True)
        for relative, _ in inventory.files:
            os.link(source / Path(relative), destination / Path(relative))

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(fixtures, "_copy_tree_with_python", hardlink_tree)

    with pytest.raises(FixtureError, match="not independent"):
        materialize_workspaces(
            tmp_path / "fixtures",
            (workspace,),
            _profile(),
            41,
        )


@pytest.mark.parametrize("max_workers", [True, 0, 9])
def test_batch_materialization_rejects_invalid_worker_limit(
    tmp_path: Path, max_workers: int
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(FixtureError, match="worker limit"):
        materialize_workspaces(
            tmp_path / "fixtures",
            (workspace,),
            _profile(),
            41,
            max_workers=max_workers,
        )


def test_batch_materialization_rejects_duplicate_workspaces(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(FixtureError, match="distinct"):
        materialize_workspaces(
            tmp_path / "fixtures",
            (workspace, workspace),
            _profile(),
            41,
        )


def test_batch_materialization_revalidates_source_after_worker_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "fixtures"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    materialize = fixtures._materialize_validated_workspace

    def drift_source(
        source: Path,
        destination: Path,
        inventory: fixtures._TreeInventory,
    ) -> None:
        materialize(source, destination, inventory)
        payload = next(source.rglob("file-*.bin"))
        payload.write_bytes(b"x" * payload.stat().st_size)
        raise FixtureError("simulated worker failure")

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(fixtures, "_materialize_validated_workspace", drift_source)

    with pytest.raises(FixtureError, match="batch materialization"):
        materialize_workspaces(cache, (workspace,), _profile(), 41, max_workers=1)


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


@pytest.mark.parametrize("returncode", [0, 7])
def test_windows_copy_accepts_success_codes_and_creates_independent_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returncode: int
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "nested").mkdir(parents=True)
    (source / "nested" / "payload.bin").write_bytes(b"original")
    destination.mkdir()
    executable = Path("C:/Windows/System32/robocopy.exe")
    invocations: list[tuple[list[str], dict[str, object]]] = []

    def run(
        arguments: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        invocations.append((arguments, kwargs))
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return subprocess.CompletedProcess(arguments, returncode, b"copy summary", b"")

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: True)
    monkeypatch.setattr(fixtures, "_robocopy_executable", lambda: executable)
    monkeypatch.setattr(fixtures.subprocess, "run", run)

    fixtures._copy_tree(source, destination)

    assert invocations == [
        (
            [
                os.fspath(executable),
                os.fspath(source.resolve(strict=True)),
                os.fspath(destination.resolve(strict=True)),
                *fixtures._ROBOCOPY_OPTIONS,
            ],
            {
                "shell": False,
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "timeout": fixtures._ROBOCOPY_TIMEOUT_SECONDS,
                "check": False,
            },
        )
    ]
    assert fixtures._ROBOCOPY_OPTIONS[:7] == (
        "/E",
        "/COPY:D",
        "/DCOPY:D",
        "/R:0",
        "/W:0",
        "/MT:4",
        "/XJ",
    )
    copied = destination / "nested" / "payload.bin"
    assert not os.path.samefile(source / "nested" / "payload.bin", copied)
    copied.write_bytes(b"modified")
    assert (source / "nested" / "payload.bin").read_bytes() == b"original"


@pytest.mark.parametrize("returncode", [8, 16])
def test_windows_copy_rejects_robocopy_failure_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, returncode: int
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"content")
    destination.mkdir()
    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: True)
    monkeypatch.setattr(fixtures, "_robocopy_executable", lambda: Path("robocopy.exe"))
    monkeypatch.setattr(
        fixtures.subprocess,
        "run",
        lambda arguments, **kwargs: subprocess.CompletedProcess(
            arguments, returncode, b"copy summary", b"copy failure"
        ),
    )

    with pytest.raises(FixtureError, match=f"exit code {returncode}"):
        fixtures._copy_tree(source, destination)


@pytest.mark.parametrize(
    ("stdout", "message"),
    [(None, "output is missing"), (b"", "summary is missing")],
)
def test_windows_copy_rejects_missing_process_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: bytes | None,
    message: str,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "payload.bin").write_bytes(b"content")
    destination.mkdir()
    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: True)
    monkeypatch.setattr(fixtures, "_robocopy_executable", lambda: Path("robocopy.exe"))
    monkeypatch.setattr(
        fixtures.subprocess,
        "run",
        lambda arguments, **kwargs: subprocess.CompletedProcess(
            arguments, 1, stdout, b""
        ),
    )

    with pytest.raises(FixtureError, match=message):
        fixtures._copy_tree(source, destination)


def test_windows_copy_rejects_missing_destination_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "first.bin").write_bytes(b"first")
    (source / "second.bin").write_bytes(b"second")
    destination.mkdir()

    def run(
        arguments: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        shutil.copyfile(source / "first.bin", destination / "first.bin")
        return subprocess.CompletedProcess(arguments, 1, b"copy summary", b"")

    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: True)
    monkeypatch.setattr(fixtures, "_robocopy_executable", lambda: Path("robocopy.exe"))
    monkeypatch.setattr(fixtures.subprocess, "run", run)

    with pytest.raises(FixtureError, match="drifted"):
        fixtures._copy_tree(source, destination)


def test_validated_cache_rejects_same_size_content_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixtures_root = tmp_path / "fixtures"
    _, source = fixtures.prepare_workspace_fixture(fixtures_root, _profile(), 41)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    materialize_workspace(fixtures_root, first, _profile(), 41)
    payload = next(path for path in source.rglob("file-*.bin") if path.is_file())
    state = payload.stat()
    payload.write_bytes(b"x" * state.st_size)
    os.utime(
        payload,
        ns=(state.st_atime_ns, state.st_mtime_ns + 1_000_000),
    )

    with pytest.raises(FixtureError, match="drifted after content validation"):
        materialize_workspace(fixtures_root, second, _profile(), 41)


def test_python_copy_fallback_preserves_identity_without_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "nested").mkdir(parents=True)
    (source / "nested" / "payload.bin").write_bytes(b"original")
    destination.mkdir()
    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: False)
    monkeypatch.setattr(
        fixtures.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("robocopy must not run off Windows"),
    )

    fixtures._copy_tree(source, destination)

    copied = destination / "nested" / "payload.bin"
    assert copied.read_bytes() == b"original"
    assert not os.path.samefile(source / "nested" / "payload.bin", copied)


def test_copy_rejects_source_symlink_before_process_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    symlink_or_skip,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    target = source / "target.bin"
    target.write_bytes(b"content")
    symlink_or_skip(source / "linked.bin", target)
    destination.mkdir()
    monkeypatch.setattr(fixtures, "_uses_native_windows_copy", lambda: True)
    monkeypatch.setattr(
        fixtures.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail(
            "unsafe fixture must fail before process execution"
        ),
    )

    with pytest.raises(FixtureError, match="symbolic link"):
        fixtures._copy_tree(source, destination)


def test_depth_100_is_admitted_and_materializes_on_native_host(
    tmp_path: Path,
) -> None:
    profile = _profile()
    profile["fixture"] = {
        "file_count": 100,
        "logical_bytes": 100,
        "maximum_depth": 100,
    }
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    assert fixtures._validated_fixture_dimensions(profile["fixture"]) == (100, 100, 100)
    deepest = fixtures._relative_path(99, 100)
    assert len(deepest.parent.parts) == 100
    materialize_workspace(tmp_path / "fixtures", workspace, profile, 41)
    assert fixtures.native_filesystem_path(workspace / deepest).is_file()


def test_depth_above_supported_limit_is_rejected() -> None:
    profile = _profile()
    profile["fixture"] = {
        "file_count": 500,
        "logical_bytes": 500,
        "maximum_depth": 500,
    }

    with pytest.raises(FixtureError, match="limits"):
        fixtures._validated_fixture_dimensions(profile["fixture"])
