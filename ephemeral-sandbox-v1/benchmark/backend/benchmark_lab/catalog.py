import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from .models import StrictModel
from .paths import BenchmarkRoots


CATALOG_EXECUTABLE = "sandbox-catalog-export"
MAX_CATALOG_BYTES = 1024 * 1024
MAX_CATALOG_ERROR_BYTES = 16 * 1024


class CatalogError(ValueError):
    pass


class CatalogFamily(StrictModel):
    id: str = Field(min_length=1)
    title: str
    summary: str
    description: str


class CatalogArgument(StrictModel):
    name: str = Field(min_length=1)
    kind: Literal["float", "integer", "json_array", "path", "string"]
    required: bool
    help: str
    default: str | None


class CatalogOperation(StrictModel):
    name: str = Field(min_length=1)
    family: str = Field(min_length=1)
    summary: str
    description: str
    args: list[CatalogArgument]
    related: list[str]


class CatalogRoute(StrictModel):
    operation: str = Field(min_length=1)
    scope_policy: Literal["system", "sandbox_required", "system_or_sandbox"]
    scope_kind: Literal["system", "sandbox"]
    execution_owner: Literal["manager", "runtime", "observability"]
    visibility: Literal["public"]


class CatalogDomain(StrictModel):
    operation_execution_space: Literal["manager", "runtime", "observability"]
    families: list[CatalogFamily]
    operations: list[CatalogOperation]
    routes: list[CatalogRoute]


class CatalogDomains(StrictModel):
    manager: CatalogDomain
    runtime: CatalogDomain
    observability: CatalogDomain


class ProductCatalogV1(StrictModel):
    schema_version: Literal[1]
    kind: Literal["ephemeral_sandbox_product_catalog"]
    domains: CatalogDomains

    def operation_names(self) -> frozenset[str]:
        return frozenset(
            operation.name
            for domain in (
                self.domains.manager,
                self.domains.runtime,
                self.domains.observability,
            )
            for operation in domain.operations
        )


@dataclass(frozen=True, slots=True)
class CatalogExport:
    catalog: ProductCatalogV1
    content: bytes
    sha256: str
    executable_sha256: str

    def require_operations(self, required: set[str] | frozenset[str]) -> None:
        missing = sorted(required - self.catalog.operation_names())
        if missing:
            raise CatalogError(f"product catalog is missing required operations: {missing}")


def read_catalog(content: bytes) -> ProductCatalogV1:
    if len(content) > MAX_CATALOG_BYTES:
        raise CatalogError("product catalog exceeds the byte cap")
    try:
        catalog = ProductCatalogV1.model_validate_json(content)
    except ValidationError as error:
        raise CatalogError(f"product catalog schema is invalid: {error}") from error
    _validate_catalog(catalog)
    return catalog


def export_catalog(roots: BenchmarkRoots, *, timeout_seconds: float = 10.0) -> CatalogExport:
    roots.validate_state()
    executable = _prebuilt_executable(roots, CATALOG_EXECUTABLE)
    try:
        completed = subprocess.run(
            [os.fspath(executable)],
            cwd=roots.product_root,
            env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CatalogError("prebuilt catalog exporter failed to execute") from error
    if completed.returncode != 0:
        detail = _bounded_diagnostic(completed.stderr)
        raise CatalogError(f"prebuilt catalog exporter exited unsuccessfully: {detail}")
    catalog = read_catalog(completed.stdout)
    return CatalogExport(
        catalog=catalog,
        content=completed.stdout,
        sha256=f"sha256:{hashlib.sha256(completed.stdout).hexdigest()}",
        executable_sha256=f"sha256:{_sha256_file(executable)}",
    )


def _prebuilt_executable(roots: BenchmarkRoots, name: str) -> Path:
    path = roots.product_bin_dir / name
    try:
        metadata = path.lstat()
    except OSError as error:
        raise CatalogError(f"required prebuilt executable is missing: {name}") from error
    try:
        canonical = path.resolve(strict=True)
    except OSError as error:
        raise CatalogError(f"required prebuilt executable is unsafe: {name}") from error
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or canonical != path
        or not canonical.is_relative_to(roots.product_bin_dir)
        or not os.access(canonical, os.X_OK)
    ):
        raise CatalogError(f"required prebuilt executable is unsafe: {name}")
    return canonical


def _validate_catalog(catalog: ProductCatalogV1) -> None:
    all_operations: set[str] = set()
    for name in ("manager", "runtime", "observability"):
        domain = getattr(catalog.domains, name)
        if domain.operation_execution_space != name:
            raise CatalogError(f"catalog domain identity mismatch: {name}")
        families = [family.id for family in domain.families]
        operations = [operation.name for operation in domain.operations]
        if len(families) != len(set(families)) or len(operations) != len(set(operations)):
            raise CatalogError(f"catalog domain contains duplicate identities: {name}")
        if all_operations.intersection(operations):
            raise CatalogError("catalog operation identities are not globally unique")
        all_operations.update(operations)
        family_set = set(families)
        if any(operation.family not in family_set for operation in domain.operations):
            raise CatalogError(f"catalog operation references an unknown family: {name}")
        route_operations = {route.operation for route in domain.routes}
        if route_operations != set(operations):
            raise CatalogError(f"catalog routes disagree with operations: {name}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bounded_diagnostic(content: bytes) -> str:
    text = content[:MAX_CATALOG_ERROR_BYTES].decode("utf-8", "replace")
    text = " ".join(text.split())
    return text or "details unavailable"
