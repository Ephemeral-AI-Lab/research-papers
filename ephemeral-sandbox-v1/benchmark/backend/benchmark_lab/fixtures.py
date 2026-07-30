from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


class FixtureError(RuntimeError):
    pass


_MAXIMUM_DEPTH = 499


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

    fixture = profile.get("fixture")
    if not isinstance(fixture, dict):
        raise FixtureError("workspace profile fixture is invalid")
    file_count, logical_bytes, maximum_depth = _validated_fixture_dimensions(fixture)
    identity, fixture_hash = workspace_fixture_identity(profile, seed)
    cache = fixtures_root / str(profile["id"]) / fixture_hash
    manifest_path = cache / "fixture-manifest.json"
    if cache.exists():
        manifest = _read_manifest(manifest_path)
        if manifest.get("fixture_hash") != fixture_hash or manifest.get("identity") != identity:
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
            shutil.rmtree(staging, ignore_errors=True)
            raise
    _copy_tree(cache, workspace)
    return manifest


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


def _build_tree(root: Path, file_count: int, logical_bytes: int, depth: int, seed: int) -> str:
    quotient, remainder = divmod(logical_bytes, file_count)
    tree = hashlib.sha256()
    for index in range(file_count):
        size = quotient + (index < remainder)
        relative = _relative_path(index, depth)
        path = root / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        content_digest = hashlib.sha256()
        with path.open("xb") as stream:
            remaining = size
            block_index = 0
            while remaining:
                block_size = min(64 * 1024, remaining)
                token = hashlib.sha256(f"{seed}:{index}:{block_index}".encode()).digest()
                block = (token * ((64 * 1024 + len(token) - 1) // len(token)))[: 64 * 1024]
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


def _copy_tree(source: Path, destination: Path) -> None:
    if any(destination.iterdir()):
        raise FixtureError("workspace must be empty before fixture materialization")
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_symlink():
            raise FixtureError("fixture cache contains a symbolic link")
        if path.is_dir():
            target.mkdir(mode=0o700, parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        else:
            raise FixtureError("fixture cache contains a non-plain entry")


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
    descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
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
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
