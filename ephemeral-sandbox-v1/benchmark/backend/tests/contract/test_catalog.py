import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

import benchmark_lab.catalog as catalog_module
from benchmark_lab.catalog import CatalogError, export_catalog, read_catalog
from benchmark_lab.paths import BenchmarkRoots


GOLDEN = Path(__file__).parents[3] / "tests/fixtures/golden/catalog/product-catalog-v1.json"


def roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark").mkdir(parents=True)
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def fake_exporter(benchmark_roots: BenchmarkRoots) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    executable = benchmark_roots.product_bin_dir / f"sandbox-catalog-export{suffix}"
    executable.write_bytes(b"fixed prebuilt exporter fixture\n")
    executable.chmod(0o700)
    return executable


def test_reads_strict_frozen_catalog_and_required_operations() -> None:
    exported = read_catalog(GOLDEN.read_bytes())
    names = exported.operation_names()
    assert len(names) == 20
    assert {"create_sandbox", "exec_command", "file_read", "file_write", "squash_layerstacks"} <= names
    value = json.loads(GOLDEN.read_bytes())
    argument = next(
        argument
        for operation in value["domains"]["runtime"]["operations"]
        for argument in operation["args"]
    )
    argument["kind"] = "float"
    read_catalog(json.dumps(value).encode())
    with pytest.raises(CatalogError, match="schema"):
        read_catalog(GOLDEN.read_bytes().replace(b'"schema_version": 1', b'"schema_version": 2', 1))


def test_invokes_only_canonical_prebuilt_exporter_and_hashes_exact_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark_roots = roots(tmp_path)
    executable = fake_exporter(benchmark_roots)
    invocations: list[tuple[list[str], dict[str, object]]] = []

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        invocations.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, GOLDEN.read_bytes(), b"")

    monkeypatch.setattr(catalog_module.subprocess, "run", run)
    exported = export_catalog(benchmark_roots)
    assert invocations == [
        (
            [os.fspath(executable)],
            {
                "cwd": benchmark_roots.product_root,
                "env": {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "timeout": 10.0,
                "check": False,
            },
        )
    ]
    assert exported.content == GOLDEN.read_bytes()
    assert exported.sha256 == f"sha256:{hashlib.sha256(GOLDEN.read_bytes()).hexdigest()}"
    assert exported.executable_sha256 == (
        f"sha256:{hashlib.sha256(executable.read_bytes()).hexdigest()}"
    )
    exported.require_operations({"exec_command", "file_read"})
    with pytest.raises(CatalogError, match="missing required"):
        exported.require_operations({"not_a_product_operation"})


def test_exporter_failure_is_bounded_and_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark_roots = roots(tmp_path)
    fake_exporter(benchmark_roots)
    monkeypatch.setattr(
        catalog_module.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(
            args, 7, b"", b"bad exporter"
        ),
    )
    with pytest.raises(CatalogError, match="bad exporter"):
        export_catalog(benchmark_roots)


def test_unsafe_exporter_symlink_fails_before_process_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, symlink_or_skip
) -> None:
    benchmark_roots = roots(tmp_path)
    executable = fake_exporter(benchmark_roots)
    executable.unlink()
    target = benchmark_roots.product_root / "outside-exporter"
    target.write_bytes(b"outside")
    target.chmod(0o700)
    symlink_or_skip(executable, target)
    monkeypatch.setattr(
        catalog_module.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("unsafe exporter was executed"),
    )
    with pytest.raises(CatalogError, match="unsafe"):
        export_catalog(benchmark_roots)


def test_duplicate_or_unknown_catalog_relationships_are_rejected() -> None:
    value = json.loads(GOLDEN.read_bytes())
    value["domains"]["manager"]["operations"][0]["family"] = "unknown"
    with pytest.raises(CatalogError, match="unknown family"):
        read_catalog(json.dumps(value).encode())
