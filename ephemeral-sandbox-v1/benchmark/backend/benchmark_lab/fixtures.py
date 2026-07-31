from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any


class FixtureError(RuntimeError):
    pass


_MAXIMUM_DEPTH = 499
_BINARY_FLAG = getattr(os, "O_BINARY", 0)
_FIXTURE_VALIDATION_WORKERS = 8
_MAXIMUM_MATERIALIZATION_WORKERS = 8
_ROBOCOPY_TIMEOUT_SECONDS = 300.0
_ROBOCOPY_OPTIONS = (
    "/E",
    "/COPY:D",
    "/DCOPY:D",
    "/R:0",
    "/W:0",
    "/MT:4",
    "/XJ",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NP",
)
_VALIDATED_FIXTURE_CACHES: dict[str, "_ValidatedFixtureCache"] = {}
_VALIDATED_FIXTURE_CACHES_LOCK = Lock()


@dataclass(frozen=True)
class _TreeInventory:
    directories: frozenset[str]
    files: tuple[tuple[str, int], ...]
    fingerprints: tuple[tuple[str, int, int, int], ...]


@dataclass(frozen=True)
class _ValidatedFixtureCache:
    fixture_hash: str
    tree_hash: str
    manifest_sha256: str
    manifest_state: tuple[int, int, int]
    inventory: _TreeInventory


def native_filesystem_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    absolute = os.path.abspath(os.fspath(path))
    if absolute.startswith("\\\\?\\"):
        return Path(absolute)
    if absolute.startswith("\\\\"):
        return Path(f"\\\\?\\UNC\\{absolute[2:]}")
    return Path(f"\\\\?\\{absolute}")


def same_native_path(left: str | Path, right: str | Path) -> bool:
    left_resolved = os.fspath(Path(left).resolve(strict=True))
    right_resolved = os.fspath(Path(right).resolve(strict=True))
    if os.name != "nt":
        return left_resolved == right_resolved
    return os.path.normcase(
        _without_extended_prefix(left_resolved)
    ) == os.path.normcase(_without_extended_prefix(right_resolved))


def _without_extended_prefix(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return f"\\\\{value[8:]}"
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def workspace_fixture_identity(
    profile: dict[str, Any], seed: int
) -> tuple[dict[str, Any], str]:
    identity = {
        "profile_id": profile.get("id"),
        "profile_version": profile.get("version"),
        "profile_generator_version": profile.get("generator_version"),
        "python_generator_revision": 2,
        "fixture": profile.get("fixture"),
        "seed": seed,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return identity, f"sha256:{digest}"


def materialize_workspace(
    fixtures_root: Path,
    workspace: Path,
    profile: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    """Build and copy a deterministic Python-owned workspace fixture.

    The cache identity deliberately names implementation revision 2 so it cannot
    be confused with the historical Rust generator's cache format.
    """

    manifest, cache = prepare_workspace_fixture(fixtures_root, profile, seed)
    inventory = _validated_fixture_cache(cache, profile, manifest)
    _copy_tree(cache, workspace, inventory)
    _verify_materialized_manifest(cache, workspace)
    return manifest


def materialize_workspaces(
    fixtures_root: Path,
    workspaces: list[Path] | tuple[Path, ...],
    profile: dict[str, Any],
    seed: int,
    *,
    max_workers: int = 4,
) -> dict[str, Any]:
    """Copy one validated fixture into distinct fresh workspaces concurrently.

    The source cache receives one authoritative validation before the bounded
    copy batch and an inventory revalidation after every worker has stopped.
    Every destination is checked for an exact directory/file-size manifest and
    for file identity independence from the source and its sibling copies.
    """

    destinations = tuple(workspaces)
    if (
        isinstance(max_workers, bool)
        or not isinstance(max_workers, int)
        or not 1 <= max_workers <= _MAXIMUM_MATERIALIZATION_WORKERS
    ):
        raise FixtureError("fixture materialization worker limit is invalid")
    if not destinations:
        raise FixtureError("fixture materialization requires a workspace")

    manifest, cache = prepare_workspace_fixture(fixtures_root, profile, seed)
    _validate_batch_destinations(cache, destinations)
    inventory = _validated_fixture_cache(cache, profile, manifest)
    first_error: FixtureError | OSError | None = None
    with ThreadPoolExecutor(
        max_workers=min(max_workers, len(destinations))
    ) as executor:
        futures = [
            executor.submit(
                _materialize_validated_workspace,
                cache,
                destination,
                inventory,
            )
            for destination in destinations
        ]
        for future in futures:
            try:
                future.result()
            except (FixtureError, OSError) as error:
                if first_error is None:
                    first_error = error

    if first_error is None:
        try:
            _verify_materialized_file_independence(cache, destinations, inventory)
        except FixtureError as error:
            first_error = error
    if _validated_tree_inventory(cache, "fixture cache") != inventory:
        raise FixtureError("fixture cache drifted during batch materialization")
    if first_error is not None:
        raise first_error
    return manifest


def prepare_workspace_fixture(
    fixtures_root: Path,
    profile: dict[str, Any],
    seed: int,
) -> tuple[dict[str, Any], Path]:
    fixture = profile.get("fixture")
    if not isinstance(fixture, dict):
        raise FixtureError("workspace profile fixture is invalid")
    file_count, logical_bytes, maximum_depth = _validated_fixture_dimensions(fixture)
    identity, fixture_hash = workspace_fixture_identity(profile, seed)
    cache_name = fixture_hash.replace(":", "-")
    cache = fixtures_root / str(profile["id"]) / cache_name
    manifest_path = cache / "fixture-manifest.json"
    if cache.exists():
        manifest = _read_manifest(manifest_path)
        if (
            manifest.get("fixture_hash") != fixture_hash
            or manifest.get("identity") != identity
        ):
            raise FixtureError("fixture cache failed identity validation")
    else:
        staging = cache.parent / f".{cache.name}.tmp-{os.getpid()}"
        staging.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            staging.mkdir(mode=0o700)
            tree_hash = _build_tree(
                staging, file_count, logical_bytes, maximum_depth, seed
            )
            manifest = {
                "schema_version": 2,
                "fixture_hash": fixture_hash,
                "tree_hash": tree_hash,
                "identity": identity,
                "actual_file_count": file_count,
                "actual_logical_bytes": logical_bytes,
            }
            _write_new(manifest_path=staging / "fixture-manifest.json", value=manifest)
            staging.rename(cache)
            _sync_directory(cache.parent)
        except BaseException:
            shutil.rmtree(native_filesystem_path(staging), ignore_errors=True)
            raise
    return manifest, cache


def _validated_fixture_dimensions(fixture: dict[str, Any]) -> tuple[int, int, int]:
    file_count = fixture.get("file_count")
    logical_bytes = fixture.get("logical_bytes")
    maximum_depth = fixture.get("maximum_depth")
    if (
        not isinstance(file_count, int)
        or not 1 <= file_count <= 1_000_000
        or not isinstance(logical_bytes, int)
        or not file_count <= logical_bytes <= 1 << 40
        or not isinstance(maximum_depth, int)
        or not 0 <= maximum_depth <= _MAXIMUM_DEPTH
    ):
        raise FixtureError("workspace profile limits are invalid")
    return file_count, logical_bytes, maximum_depth


def _build_tree(
    root: Path, file_count: int, logical_bytes: int, depth: int, seed: int
) -> str:
    quotient, remainder = divmod(logical_bytes, file_count)
    tree = hashlib.sha256()
    for index in range(file_count):
        size = quotient + (index < remainder)
        relative = _relative_path(index, depth)
        path = native_filesystem_path(root / relative)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        content_digest = hashlib.sha256()
        with path.open("xb") as stream:
            remaining = size
            block_index = 0
            while remaining:
                block_size = min(64 * 1024, remaining)
                token = hashlib.sha256(
                    f"{seed}:{index}:{block_index}".encode()
                ).digest()
                block = (token * ((64 * 1024 + len(token) - 1) // len(token)))[
                    : 64 * 1024
                ]
                payload = block[:block_size]
                stream.write(payload)
                content_digest.update(payload)
                remaining -= block_size
                block_index += 1
            stream.flush()
            os.fsync(stream.fileno())
        encoded = relative.as_posix().encode()
        tree.update(encoded)
        tree.update(b"\0")
        tree.update(size.to_bytes(8, "little"))
        tree.update(content_digest.digest())
    return f"sha256:{tree.hexdigest()}"


def _relative_path(index: int, maximum_depth: int) -> Path:
    depth = 0 if maximum_depth == 0 else 1 + index % maximum_depth
    path = Path()
    for level in range(depth):
        bucket = (index * (131 + level) + level * 17) % 97
        path /= f"d{level:02}-{bucket:03}"
    return path / f"file-{index:08}.bin"


def _copy_tree(
    source: Path,
    destination: Path,
    source_inventory: _TreeInventory | None = None,
) -> _TreeInventory:
    if any(destination.iterdir()):
        raise FixtureError("workspace must be empty before fixture materialization")
    if source_inventory is None:
        source_inventory = _validated_tree_inventory(source, "fixture cache")
    if _uses_native_windows_copy():
        _copy_tree_with_robocopy(source, destination)
    else:
        _copy_tree_with_python(source, destination, source_inventory)
    if _validated_tree_inventory(source, "fixture cache") != source_inventory:
        raise FixtureError("fixture cache drifted during materialization")
    _verify_copied_files(destination, source_inventory)
    return source_inventory


def _validate_batch_destinations(source: Path, destinations: tuple[Path, ...]) -> None:
    try:
        source_resolved = source.resolve(strict=True)
    except OSError as error:
        raise FixtureError("fixture cache cannot be resolved safely") from error
    resolved: list[Path] = []
    for destination in destinations:
        try:
            destination_resolved = destination.resolve(strict=True)
        except OSError as error:
            raise FixtureError("workspace cannot be resolved safely") from error
        if _is_link_or_junction(destination) or not destination.is_dir():
            raise FixtureError("workspace must be a plain directory")
        try:
            if any(destination.iterdir()):
                raise FixtureError(
                    "workspace must be empty before fixture materialization"
                )
        except OSError as error:
            raise FixtureError("workspace cannot be traversed safely") from error
        if (
            destination_resolved == source_resolved
            or destination_resolved in source_resolved.parents
            or source_resolved in destination_resolved.parents
        ):
            raise FixtureError("workspace must be independent from fixture cache")
        if destination_resolved in resolved:
            raise FixtureError("fixture materialization workspaces must be distinct")
        resolved.append(destination_resolved)


def _materialize_validated_workspace(
    source: Path,
    destination: Path,
    source_inventory: _TreeInventory,
) -> None:
    if any(destination.iterdir()):
        raise FixtureError("workspace must be empty before fixture materialization")
    if _uses_native_windows_copy():
        _copy_tree_with_robocopy(source, destination)
    else:
        _copy_tree_with_python(source, destination, source_inventory)
    destination_inventory = _validated_tree_inventory(
        destination, "materialized fixture"
    )
    if (
        destination_inventory.directories != source_inventory.directories
        or destination_inventory.files != source_inventory.files
    ):
        raise FixtureError("materialized fixture drifted from the fixture cache")
    _verify_materialized_manifest(source, destination)


def _verify_materialized_file_independence(
    source: Path,
    destinations: tuple[Path, ...],
    source_inventory: _TreeInventory,
) -> None:
    def file_identities(
        item: tuple[str, int],
    ) -> tuple[tuple[int, int], ...]:
        relative, _ = item
        paths = [
            native_filesystem_path(root / Path(relative))
            for root in (source, *destinations)
        ]
        try:
            return tuple(
                (state.st_dev, state.st_ino)
                for state in (path.stat() for path in paths)
            )
        except OSError as error:
            raise FixtureError(
                "materialized fixture identity cannot be verified"
            ) from error

    identities: set[tuple[int, int]] = set()
    with ThreadPoolExecutor(max_workers=_FIXTURE_VALIDATION_WORKERS) as executor:
        for file_identity_group in executor.map(
            file_identities, source_inventory.files
        ):
            for identity in file_identity_group:
                if identity in identities:
                    raise FixtureError("materialized fixture files are not independent")
                identities.add(identity)


def _validated_tree_inventory(root: Path, label: str) -> _TreeInventory:
    if _is_link_or_junction(root):
        raise FixtureError(f"{label} contains a symbolic link or junction")
    if not root.is_dir():
        raise FixtureError(f"{label} contains a non-plain entry")
    native_root = native_filesystem_path(root)
    directories = {"."}
    files: list[tuple[str, int]] = []
    fingerprints: list[tuple[str, int, int, int]] = []

    def scan_directory(
        item: tuple[str, str],
    ) -> tuple[
        list[tuple[str, str]],
        list[tuple[str, int]],
        list[tuple[str, int, int, int]],
    ]:
        relative_directory, directory = item
        discovered_directories: list[tuple[str, str]] = []
        discovered_files: list[tuple[str, int]] = []
        discovered_fingerprints: list[tuple[str, int, int, int]] = []
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    relative = (
                        entry.name
                        if relative_directory == "."
                        else f"{relative_directory}/{entry.name}"
                    )
                    if entry.is_symlink() or (
                        hasattr(entry, "is_junction") and entry.is_junction()
                    ):
                        raise FixtureError(
                            f"{label} contains a symbolic link or junction"
                        )
                    if entry.is_dir(follow_symlinks=False):
                        discovered_directories.append((relative, entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        state = entry.stat(follow_symlinks=False)
                        discovered_files.append((relative, state.st_size))
                        discovered_fingerprints.append(
                            (relative, state.st_size, state.st_mtime_ns, state.st_ino)
                        )
                    else:
                        raise FixtureError(f"{label} contains a non-plain entry")
        except OSError as error:
            raise FixtureError(f"{label} cannot be traversed safely") from error
        return (
            discovered_directories,
            discovered_files,
            discovered_fingerprints,
        )

    pending = [(".", os.fspath(native_root))]
    with ThreadPoolExecutor(max_workers=_FIXTURE_VALIDATION_WORKERS) as executor:
        while pending:
            next_pending: list[tuple[str, str]] = []
            for (
                discovered_directories,
                discovered_files,
                discovered_fingerprints,
            ) in executor.map(scan_directory, pending):
                next_pending.extend(discovered_directories)
                directories.update(relative for relative, _ in discovered_directories)
                files.extend(discovered_files)
                fingerprints.extend(discovered_fingerprints)
            pending = next_pending
    return _TreeInventory(
        directories=frozenset(directories),
        files=tuple(sorted(files)),
        fingerprints=tuple(sorted(fingerprints)),
    )


def _verify_copied_files(destination: Path, source_inventory: _TreeInventory) -> None:
    if _is_link_or_junction(destination) or not destination.is_dir():
        raise FixtureError("materialized fixture contains a non-plain entry")

    def validate_file(item: tuple[str, int]) -> None:
        relative, expected_size = item
        path = native_filesystem_path(destination / Path(relative))
        try:
            if _is_link_or_junction(path) or not path.is_file():
                raise FixtureError(
                    "materialized fixture drifted from the fixture cache"
                )
            if path.stat().st_size != expected_size:
                raise FixtureError(
                    "materialized fixture drifted from the fixture cache"
                )
        except OSError as error:
            raise FixtureError(
                "materialized fixture drifted from the fixture cache"
            ) from error

    with ThreadPoolExecutor(max_workers=_FIXTURE_VALIDATION_WORKERS) as executor:
        tuple(executor.map(validate_file, source_inventory.files))


def _is_link_or_junction(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _uses_native_windows_copy() -> bool:
    return os.name == "nt"


def _robocopy_executable() -> Path:
    system_root = os.environ.get("SystemRoot")
    if not system_root:
        raise FixtureError("native Windows fixture copy executable is unavailable")
    executable = Path(system_root) / "System32" / "robocopy.exe"
    if _is_link_or_junction(executable) or not executable.is_file():
        raise FixtureError("native Windows fixture copy executable is unavailable")
    return executable


def _copy_tree_with_robocopy(source: Path, destination: Path) -> None:
    executable = _robocopy_executable()
    arguments = [
        os.fspath(executable),
        _without_extended_prefix(os.fspath(source.resolve(strict=True))),
        _without_extended_prefix(os.fspath(destination.resolve(strict=True))),
        *_ROBOCOPY_OPTIONS,
    ]
    try:
        completed = subprocess.run(
            arguments,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_ROBOCOPY_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise FixtureError("native Windows fixture copy failed to execute") from error
    if completed.stdout is None or completed.stderr is None:
        raise FixtureError("native Windows fixture copy output is missing")
    if not completed.stdout:
        raise FixtureError("native Windows fixture copy summary is missing")
    if not 0 <= completed.returncode <= 7:
        raise FixtureError(
            f"native Windows fixture copy failed with exit code {completed.returncode}"
        )


def _copy_tree_with_python(
    source: Path,
    destination: Path,
    inventory: _TreeInventory,
) -> None:
    for relative in sorted(
        inventory.directories, key=lambda value: (value.count("/"), value)
    ):
        if relative != ".":
            native_filesystem_path(destination / Path(relative)).mkdir(
                mode=0o700, parents=True, exist_ok=True
            )
    for relative, _ in inventory.files:
        path = Path(relative)
        shutil.copyfile(
            native_filesystem_path(source / path),
            native_filesystem_path(destination / path),
        )


def _validated_fixture_cache(
    source: Path,
    profile: dict[str, Any],
    manifest: dict[str, Any],
) -> _TreeInventory:
    cache_key = os.path.normcase(os.fspath(source.resolve(strict=True)))
    inventory = _validated_tree_inventory(source, "fixture cache")
    manifest_sha256, manifest_state, manifest_bytes = _manifest_identity(source)
    fixture_hash = manifest.get("fixture_hash")
    tree_hash = manifest.get("tree_hash")
    if not isinstance(fixture_hash, str) or not isinstance(tree_hash, str):
        raise FixtureError("fixture manifest identity is invalid")
    with _VALIDATED_FIXTURE_CACHES_LOCK:
        validated = _VALIDATED_FIXTURE_CACHES.get(cache_key)
    if validated is not None:
        if validated != _ValidatedFixtureCache(
            fixture_hash=fixture_hash,
            tree_hash=tree_hash,
            manifest_sha256=manifest_sha256,
            manifest_state=manifest_state,
            inventory=inventory,
        ):
            raise FixtureError("fixture cache drifted after content validation")
        return inventory

    expected_directories, expected_files, expected_payloads = _expected_fixture_layout(
        profile, len(manifest_bytes)
    )
    if inventory.directories != expected_directories:
        raise FixtureError("fixture cache directory identity drifted")
    if dict(inventory.files) != expected_files:
        raise FixtureError("fixture cache file identity drifted")
    if _fixture_tree_hash(source, expected_payloads) != tree_hash:
        raise FixtureError("fixture cache content hash drifted")
    final_inventory = _validated_tree_inventory(source, "fixture cache")
    final_sha256, final_state, final_bytes = _manifest_identity(source)
    if (
        final_inventory != inventory
        or final_sha256 != manifest_sha256
        or final_state != manifest_state
        or final_bytes != manifest_bytes
    ):
        raise FixtureError("fixture cache drifted during content validation")
    validated = _ValidatedFixtureCache(
        fixture_hash=fixture_hash,
        tree_hash=tree_hash,
        manifest_sha256=manifest_sha256,
        manifest_state=manifest_state,
        inventory=final_inventory,
    )
    with _VALIDATED_FIXTURE_CACHES_LOCK:
        current = _VALIDATED_FIXTURE_CACHES.get(cache_key)
        if current is not None and current != validated:
            raise FixtureError("fixture cache validation identity conflicted")
        _VALIDATED_FIXTURE_CACHES[cache_key] = validated
    return final_inventory


def _manifest_identity(source: Path) -> tuple[str, tuple[int, int, int], bytes]:
    path = native_filesystem_path(source / "fixture-manifest.json")
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
    except OSError as error:
        raise FixtureError("fixture manifest identity cannot be verified") from error
    before_state = (before.st_size, before.st_mtime_ns, before.st_ino)
    after_state = (after.st_size, after.st_mtime_ns, after.st_ino)
    if before_state != after_state:
        raise FixtureError("fixture manifest drifted during identity validation")
    return hashlib.sha256(content).hexdigest(), after_state, content


def _expected_fixture_layout(
    profile: dict[str, Any], manifest_size: int
) -> tuple[frozenset[str], dict[str, int], list[tuple[Path, int]]]:
    fixture = profile.get("fixture")
    if not isinstance(fixture, dict):
        raise FixtureError("workspace profile fixture is invalid")
    file_count, logical_bytes, maximum_depth = _validated_fixture_dimensions(fixture)
    quotient, remainder = divmod(logical_bytes, file_count)
    expected_files: dict[str, int] = {}
    expected_directories = {"."}
    expected_payloads: list[tuple[Path, int]] = []
    for index in range(file_count):
        size = quotient + (index < remainder)
        relative = _relative_path(index, maximum_depth)
        expected_payloads.append((relative, size))
        expected_files[relative.as_posix()] = size
        parent = relative.parent
        while parent != Path("."):
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    expected_files["fixture-manifest.json"] = manifest_size
    return frozenset(expected_directories), expected_files, expected_payloads


def _fixture_tree_hash(root: Path, payloads: list[tuple[Path, int]]) -> str:
    def content_digest(item: tuple[Path, int]) -> bytes:
        relative, _ = item
        digest = hashlib.sha256()
        try:
            with native_filesystem_path(root / relative).open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
        except OSError as error:
            raise FixtureError("fixture content cannot be verified") from error
        return digest.digest()

    tree = hashlib.sha256()
    with ThreadPoolExecutor(max_workers=_FIXTURE_VALIDATION_WORKERS) as executor:
        digests = executor.map(content_digest, payloads)
        for (relative, size), digest in zip(payloads, digests, strict=True):
            tree.update(relative.as_posix().encode())
            tree.update(b"\0")
            tree.update(size.to_bytes(8, "little"))
            tree.update(digest)
    return f"sha256:{tree.hexdigest()}"


def _verify_materialized_manifest(source: Path, destination: Path) -> None:
    source_manifest = native_filesystem_path(source / "fixture-manifest.json")
    destination_manifest = native_filesystem_path(destination / "fixture-manifest.json")
    try:
        source_manifest_bytes = source_manifest.read_bytes()
        destination_manifest_bytes = destination_manifest.read_bytes()
    except OSError as error:
        raise FixtureError("materialized fixture manifest is missing") from error
    if destination_manifest_bytes != source_manifest_bytes:
        raise FixtureError("materialized fixture manifest content drifted")


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise FixtureError("fixture manifest is invalid") from error
    if not isinstance(value, dict) or value.get("schema_version") != 2:
        raise FixtureError("fixture manifest schema is incompatible")
    return value


def _write_new(manifest_path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False).encode() + b"\n"
    descriptor = os.open(
        manifest_path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY_FLAG,
        0o600,
    )
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise FixtureError("fixture manifest write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
