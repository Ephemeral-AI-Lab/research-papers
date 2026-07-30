import json
from pathlib import Path

import pytest

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


def fake_exporter(benchmark_roots: BenchmarkRoots, script: str) -> Path:
    executable = benchmark_roots.product_bin_dir / "sandbox-catalog-export"
    executable.write_text("#!/bin/sh\n" + script)
    executable.chmod(0o700)
    return executable


def test_reads_strict_frozen_catalog_and_required_operations() -> None:
    exported = read_catalog(GOLDEN.read_bytes())
    names = exported.operation_names()
    assert len(names) == 20
    assert {"create_sandbox", "exec_command", "file_read", "file_write", "squash_layerstacks"} <= names
    with pytest.raises(CatalogError, match="schema"):
        read_catalog(GOLDEN.read_bytes().replace(b'"schema_version": 1', b'"schema_version": 2', 1))


def test_invokes_only_canonical_prebuilt_exporter_and_hashes_exact_bytes(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    fake_exporter(benchmark_roots, f'exec /bin/cat "{GOLDEN}"\n')
    exported = export_catalog(benchmark_roots)
    assert exported.content == GOLDEN.read_bytes()
    assert exported.sha256.startswith("sha256:")
    exported.require_operations({"exec_command", "file_read"})
    with pytest.raises(CatalogError, match="missing required"):
        exported.require_operations({"not_a_product_operation"})


def test_exporter_failure_and_unsafe_binary_fail_closed(tmp_path: Path) -> None:
    benchmark_roots = roots(tmp_path)
    executable = fake_exporter(benchmark_roots, 'printf "bad exporter" >&2\nexit 7\n')
    with pytest.raises(CatalogError, match="bad exporter"):
        export_catalog(benchmark_roots)
    executable.unlink()
    executable.symlink_to("/bin/true")
    with pytest.raises(CatalogError, match="unsafe"):
        export_catalog(benchmark_roots)


def test_duplicate_or_unknown_catalog_relationships_are_rejected() -> None:
    value = json.loads(GOLDEN.read_bytes())
    value["domains"]["manager"]["operations"][0]["family"] = "unknown"
    with pytest.raises(CatalogError, match="unknown family"):
        read_catalog(json.dumps(value).encode())
