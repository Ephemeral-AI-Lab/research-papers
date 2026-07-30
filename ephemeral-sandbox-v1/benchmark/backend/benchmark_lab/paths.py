import json
import os
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .models import StateMarker


MARKER_NAME = ".ownership.json"
ROLE_NAMES = ("fixtures", "runs", "results", "runtime", "tmp")


class PathContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BenchmarkRoots:
    test_repository_root: Path
    product_root: Path
    product_bin_dir: Path
    benchmark_source_root: Path
    benchmark_state_root: Path
    fixtures: Path
    runs: Path
    results: Path
    runtime: Path
    tmp: Path

    @classmethod
    def resolve(
        cls,
        test_repository_root: Path,
        product_root: Path,
        product_bin_dir: Path,
        *,
        initialize: bool = False,
    ) -> "BenchmarkRoots":
        supplied = (test_repository_root, product_root, product_bin_dir)
        if any(not path.is_absolute() for path in supplied):
            raise PathContractError("all repository and binary roots must be absolute")
        test_root, product, bin_dir = (path.resolve(strict=True) for path in supplied)
        if not all(path.is_dir() for path in (test_root, product, bin_dir)):
            raise PathContractError("all repository and binary roots must be directories")
        if _overlap(test_root, product):
            raise PathContractError("test and product repositories must be disjoint")
        if not bin_dir.is_relative_to(product):
            raise PathContractError("product binary directory must be beneath product root")

        source = (test_root / "benchmark").resolve(strict=True)
        if not source.is_dir() or not source.is_relative_to(test_root):
            raise PathContractError("benchmark source root is invalid")
        state = test_root / ".benchmark-state"
        roots = cls(
            test_repository_root=test_root,
            product_root=product,
            product_bin_dir=bin_dir,
            benchmark_source_root=source,
            benchmark_state_root=state,
            **{name: state / name for name in ROLE_NAMES},
        )
        if initialize:
            roots.initialize_state()
        elif state.exists():
            roots.validate_state()
        return roots

    def initialize_state(self) -> None:
        if self.benchmark_state_root.is_symlink():
            raise PathContractError("benchmark state root must not be a symlink")
        self.benchmark_state_root.mkdir(mode=0o700, exist_ok=True)
        marker = self.benchmark_state_root / MARKER_NAME
        if marker.exists():
            self.validate_state()
        else:
            unexpected = list(self.benchmark_state_root.iterdir())
            if unexpected:
                raise PathContractError("unmarked benchmark state root is not empty")
            _write_new_json(marker, StateMarker().model_dump(mode="json"))
        for role in ROLE_NAMES:
            path = getattr(self, role)
            path.mkdir(mode=0o700, exist_ok=True)
        self.validate_state()

    def validate_state(self) -> None:
        state = self.benchmark_state_root
        if state.is_symlink() or not state.is_dir():
            raise PathContractError("benchmark state root is not an owned directory")
        canonical = state.resolve(strict=True)
        if canonical != state or not canonical.is_relative_to(self.test_repository_root):
            raise PathContractError("benchmark state root escaped the test repository")
        marker_path = state / MARKER_NAME
        if marker_path.is_symlink() or not marker_path.is_file():
            raise PathContractError("benchmark state marker is missing or unsafe")
        try:
            marker = StateMarker.model_validate_json(marker_path.read_bytes())
        except (OSError, ValidationError) as error:
            raise PathContractError("benchmark state marker is invalid") from error
        if marker.model_dump(mode="json") != StateMarker().model_dump(mode="json"):
            raise PathContractError("benchmark state marker is not exact")
        for role in ROLE_NAMES:
            path = getattr(self, role)
            if path.is_symlink() or not path.is_dir() or path.resolve(strict=True) != path:
                raise PathContractError(f"benchmark state role is invalid: {role}")

    def role_root(self, role: str) -> Path:
        if role not in ROLE_NAMES:
            raise PathContractError(f"unknown benchmark state role: {role}")
        self.validate_state()
        return getattr(self, role)

    def require_mutable_path(self, path: Path) -> Path:
        self.validate_state()
        canonical = path.resolve(strict=True)
        if canonical == self.benchmark_state_root or not canonical.is_relative_to(
            self.benchmark_state_root
        ):
            raise PathContractError("mutable path must be below benchmark state root")
        return canonical


def _overlap(left: Path, right: Path) -> bool:
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _write_new_json(path: Path, value: dict[str, object]) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _sync_directory(path.parent)


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
