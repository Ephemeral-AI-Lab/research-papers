import json
import os
import shutil
from pathlib import Path

from pydantic import ValidationError

from .models import OwnedPathMarker
from .paths import BenchmarkRoots, MARKER_NAME, PathContractError, _sync_directory


class OwnershipError(ValueError):
    pass


class OwnershipLedger:
    def __init__(self, roots: BenchmarkRoots) -> None:
        self._roots = roots
        self._entries: dict[Path, OwnedPathMarker] = {}

    def register(self, target: Path, marker: OwnedPathMarker) -> Path:
        canonical = self._validate_target(target, marker.role)
        marker_path = canonical / MARKER_NAME
        payload = json.dumps(marker.model_dump(mode="json"), indent=2, sort_keys=True).encode() + b"\n"
        try:
            descriptor = os.open(marker_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as error:
            raise OwnershipError(f"ownership marker already exists or cannot be created: {marker_path}") from error
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _sync_directory(canonical)
        self._entries[canonical] = marker
        return canonical

    def adopt(self, target: Path, expected: OwnedPathMarker) -> Path:
        canonical = self._validate_target(target, expected.role)
        if self._read_marker(canonical) != expected:
            raise OwnershipError("ownership identity mismatch")
        self._entries[canonical] = expected
        return canonical

    def remove(self, target: Path, expected: OwnedPathMarker) -> None:
        canonical = self._validate_target(target, expected.role)
        if self._read_marker(canonical) != expected:
            raise OwnershipError("ownership identity mismatch")
        if self._entries.get(canonical) != expected:
            raise OwnershipError("target is absent from the active ownership ledger")
        shutil.rmtree(canonical)
        self._entries.pop(canonical)
        _sync_directory(canonical.parent)

    def _read_marker(self, target: Path) -> OwnedPathMarker:
        path = target / MARKER_NAME
        if path.is_symlink() or not path.is_file():
            raise OwnershipError("ownership marker is missing or unsafe")
        try:
            return OwnedPathMarker.model_validate_json(path.read_bytes())
        except (OSError, ValidationError) as error:
            raise OwnershipError("ownership marker is invalid") from error

    def _validate_target(self, target: Path, role: str) -> Path:
        role_root = self._roots.role_root(role)
        if not target.is_absolute():
            raise OwnershipError("cleanup target must be absolute")
        try:
            relative = target.relative_to(role_root)
        except ValueError as error:
            raise OwnershipError("cleanup target is outside its owned role") from error
        current = role_root
        for component in relative.parts:
            if component in {".", ".."}:
                raise OwnershipError("cleanup path contains traversal")
            current /= component
            if current.is_symlink():
                raise OwnershipError("cleanup path crosses a symlink")
        if target.is_symlink() or not target.is_dir():
            raise OwnershipError("cleanup target must be a real directory")
        canonical = target.resolve(strict=True)
        if canonical == role_root or not canonical.is_relative_to(role_root):
            raise OwnershipError("cleanup target is outside its owned role")
        current = role_root
        for component in canonical.relative_to(role_root).parts:
            current /= component
            if current.is_symlink():
                raise OwnershipError("cleanup path crosses a symlink")
            if current.stat().st_dev != role_root.stat().st_dev:
                raise OwnershipError("cleanup path crosses a device boundary")
        try:
            self._roots.require_mutable_path(canonical)
        except PathContractError as error:
            raise OwnershipError(str(error)) from error
        return canonical
