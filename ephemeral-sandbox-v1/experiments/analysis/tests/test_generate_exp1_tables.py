from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_exp1_tables.py"
SPEC = importlib.util.spec_from_file_location("generate_exp1_tables", SCRIPT)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


RUN_ID = "00000000-0000-7000-8000-000000000001"
PLAN_HASH = "sha256:" + "1" * 64
PRODUCT_COMMIT = "2" * 40
IMAGE_DIGEST = "sha256:" + "3" * 64
FIXTURE_HASH = "sha256:" + "4" * 64
TREE_HASH = "sha256:" + "5" * 64
BINARY_HASHES = {
    "daemon": "sha256:" + "6" * 64,
    "gateway": "sha256:" + "7" * 64,
    "manager": "sha256:" + "8" * 64,
    "runtime": "sha256:" + "9" * 64,
    "observability": "sha256:" + "a" * 64,
}


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _factors(operation: str, variant: Any, concurrency: int) -> dict[str, Any]:
    factors: dict[str, Any] = {"workspace_profile": "paper-100m"}
    if operation == "create_sandbox":
        factors.update(
            network_profile="shared", resolved_isolation="fresh_sandbox_per_trial"
        )
    elif operation == "create_workspace":
        factors.update(workspace_count=concurrency)
    else:
        factors["concurrent_requests"] = concurrency
        if operation == "exec_command":
            factors.update(command_case=variant, session_mode="explicit")
        elif operation == "file_read":
            factors.update(returned_bytes=variant, source="snapshot")
        elif operation == "file_write":
            factors.update(content_bytes=variant, destination="session")
        elif operation == "file_edit":
            factors.update(
                file_bytes=variant, destination="session", replacement_count=1
            )
    return factors


def _metric(
    metric_id: str,
    unit: str,
    values: list[float],
    *,
    aggregation: str = "mean",
    scope: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "id": metric_id,
        "unit": unit,
        "aggregation": aggregation,
    }
    if scope is not None:
        identity["scope"] = scope
    if source is not None:
        identity["source"] = source
    return {
        "identity": identity,
        "attempted_n": len(values),
        "failed_n": 0,
        "available_n": len(values),
        "unavailable": {"count": 0, "reasons": {}},
        "raw_points": [
            {
                "trial_id": f"trial-synthetic-measured-{index:06d}",
                "request_id": None,
                "value": value,
                "raw_integer_value": int(value) if value.is_integer() else None,
                "outlier": False,
            }
            for index, value in enumerate(values)
        ],
    }


def _refresh_archive_manifest(root: Path, *, disposition: str = "exploratory") -> None:
    files = []
    tree = hashlib.sha256()
    total = 0
    for path in sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.name != "archive-manifest.json"
        ),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        digest = hashlib.sha256(data).digest()
        files.append(
            {
                "bytes": len(data),
                "path": relative,
                "sha256": "sha256:" + digest.hex(),
            }
        )
        total += len(data)
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(digest)
        tree.update(b"\n")
    _json(
        root / "archive-manifest.json",
        {
            "archive_bytes": total,
            "archive_file_count": len(files),
            "content_tree_sha256": "sha256:" + tree.hexdigest(),
            "disposition": disposition,
            "files": files,
            "run_id": RUN_ID,
            "schema_version": 1,
        },
    )


def _build_archive(root: Path, *, disposition: str = "exploratory") -> Path:
    measured = 5 if disposition == "exploratory" else 100
    trial_batches = 133 if disposition == "exploratory" else 1938
    requests = 385 if disposition == "exploratory" else 5610
    eligibility = (
        "exploratory_ineligible"
        if disposition == "exploratory"
        else "frozen_final_candidate"
    )
    preset = "paper-pilot" if disposition == "exploratory" else "paper-good-pass"
    freeze_tag = (
        {
            "availability": "available",
            "name": "paper-v1-freeze",
            "reference": "refs/tags/paper-v1-freeze",
            "object_type": "tag",
            "tag_object": "c" * 40,
            "peeled_commit": PRODUCT_COMMIT,
        }
        if disposition == "final"
        else {
            "availability": "unavailable",
            "reason": "pre-freeze smoke/exploratory archive",
            "required_final_tag": "paper-v1-freeze",
        }
    )
    cells = []
    report_cells = []
    for index, (_, operation, variant, concurrency, _) in enumerate(
        generator.PERFORMANCE_ROWS
    ):
        cell_id = f"sha256:{index:064x}"
        factors = _factors(operation, variant, concurrency)
        cells.append(
            {
                "cell_id": cell_id,
                "operation_id": operation,
                "operation": {"operation": operation, "cell": factors},
                "protocol": {"warmups": 2, "measured_trials": measured},
            }
        )
        base = float((index + 1) * 1_000_000)
        latency = [base + offset * 100_000.0 for offset in range(measured)]
        throughput = [float(concurrency * 10 + offset) for offset in range(measured)]
        resources = [
            _metric(
                "daemon_rss_bytes",
                "bytes",
                [1048576.0 * (index + offset + 1) for offset in range(measured)],
            ),
            _metric(
                "sandbox_memory_peak_bytes",
                "bytes",
                [2097152.0 * (offset + 1) for offset in range(measured)],
            ),
            _metric(
                "sandbox_cpu_time_ns",
                "nanoseconds",
                [1_000_000.0 * (offset + 1) for offset in range(measured)],
            ),
            _metric(
                "sandbox_block_read_bytes",
                "bytes",
                [1048576.0 * offset for offset in range(measured)],
            ),
            _metric(
                "sandbox_block_write_bytes",
                "bytes",
                [1048576.0 * (offset + 1) for offset in range(measured)],
            ),
            _metric(
                "upperdir_bytes",
                "bytes",
                [1048576.0 * (offset + 1) for offset in range(measured)],
                aggregation="delta",
                scope="workspace",
                source=(
                    "product_observability.snapshot.workspaces.disk_allocated_bytes.sum"
                ),
            ),
        ]
        report_cells.append(
            {
                "cell_id": cell_id,
                "operation_id": operation,
                "counts": {
                    "total_attempted": 2 + measured,
                    "warmup": 2,
                    "measured_attempted": measured,
                    "successful": measured,
                    "product_failed": 0,
                    "correctness_failed": 0,
                    "infrastructure_failed": 0,
                    "cleanup_invalid": 0,
                    "missing_primary_latency": 0,
                },
                "checks": [
                    {
                        "id": "synthetic",
                        "attempted": measured,
                        "passed": measured,
                        "failed": 0,
                    }
                ],
                "metrics": [
                    _metric("batch_makespan_ns", "nanoseconds", latency),
                    _metric("throughput_ops_s", "operations_per_second", throughput),
                    *resources,
                ],
            }
        )

    campaign = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "disposition": disposition,
        "eligibility": eligibility,
        "state": "completed",
        "correctness": "pass",
        "plan": {
            "hash": PLAN_HASH,
            "cells": 19,
            "trial_batches": trial_batches,
            "issued_operation_requests": requests,
            "client_cohort": "product_cli",
        },
        "product": {
            "commit": PRODUCT_COMMIT,
            "dirty": False,
            "freeze_tag": freeze_tag,
            "binaries": {
                name: {"sha256": digest} for name, digest in BINARY_HASHES.items()
            },
        },
        "cleanup": {
            "product_commit": PRODUCT_COMMIT,
            "product_status_porcelain": "",
            "run_workspace_exists": False,
            "runtime_exists": False,
            "gateway_labeled_containers": [],
            "gateway_labeled_volumes": [],
            "matching_product_processes": [],
            "run_labeled_containers": [],
            "run_labeled_volumes": [],
        },
        "image": {
            "id": IMAGE_DIGEST,
            "requested": "example.invalid/exp1@sha256:" + "3" * 64,
        },
        "fixture": {"fixture_hash": FIXTURE_HASH, "tree_hash": TREE_HASH},
        "paper_git": {"commit": "b" * 40},
    }
    treatment = {
        "source_commit": PRODUCT_COMMIT,
        "source_dirty": False,
        "daemon_binary_hash": BINARY_HASHES["daemon"],
        "gateway_binary_hash": BINARY_HASHES["gateway"],
        "manager_cli_binary_hash": BINARY_HASHES["manager"],
        "runtime_cli_binary_hash": BINARY_HASHES["runtime"],
        "observability_cli_binary_hash": BINARY_HASHES["observability"],
    }
    run = {
        "schema_name": "eos_benchmark_run_manifest",
        "schema_version": 2,
        "data": {
            "run_id": RUN_ID,
            "name": preset,
            "plan_hash": PLAN_HASH,
            "state": "completed",
            "correctness": "pass",
            "producer": {"source_commit": PRODUCT_COMMIT},
            "treatment": treatment,
            "environment": {
                "client_cohort": "product_cli",
                "image_digest": IMAGE_DIGEST,
                "host": {
                    "operating_system": "windows",
                    "architecture": "amd64",
                    "filesystem": "NTFS",
                    "docker_engine_version": "29.0.1",
                },
            },
        },
    }
    expanded = {
        "schema_name": "eos_benchmark_expanded_plan",
        "schema_version": 1,
        "data": {"plan_hash": PLAN_HASH, "cells": cells},
    }
    report = {
        "schema_name": "eos_benchmark_report",
        "schema_version": 3,
        "data": {
            "run_id": RUN_ID,
            "plan_hash": PLAN_HASH,
            "state": "completed",
            "correctness_verdict": "pass",
            "source_commit": PRODUCT_COMMIT,
            "design_counts": {
                "test_combinations": 19,
                "trial_batches": trial_batches,
                "issued_product_requests": requests,
            },
            "warnings": [],
            "cells": report_cells,
        },
    }
    preflight = {
        "docker": {
            "architecture": "x86_64",
            "cgroup_version": "2",
            "os_type": "linux",
            "server_version": "29.0.1",
        },
        "recorded_run_environment": {
            "host": {
                "operating_system": "windows",
                "os_edition": "Synthetic Pro",
                "os_build": "99999",
                "architecture": "amd64",
                "cpu_model": "Synthetic CPU",
                "logical_processors": 8,
                "total_memory_bytes": 16 * 1024 * 1024 * 1024,
                "storage_model": "Synthetic NVMe",
                "storage_capacity_bytes": 4 * 1024 * 1024 * 1024 * 1024,
                "filesystem": "NTFS",
            }
        },
        "sandbox_limits": {
            "vcpus": 1,
            "memory_bytes": 512 * 1024 * 1024,
            "pids_limit": 256,
        },
    }
    fixture = {
        "schema_version": 2,
        "fixture_hash": FIXTURE_HASH,
        "tree_hash": TREE_HASH,
        "identity": {
            "profile_id": "paper-100m",
            "seed": 20260712,
            "fixture": {
                "file_count": 4000,
                "logical_bytes": 104857600,
                "maximum_depth": 100,
            },
        },
    }
    _json(root / "campaign-manifest.json", campaign)
    _json(root / "run-manifest.json", run)
    _json(root / "expanded-plan.json", expanded)
    _json(root / "report.json", report)
    _json(root / "environment-preflight.txt", preflight)
    _json(root / "fixture-manifest.json", fixture)
    _refresh_archive_manifest(root, disposition=disposition)
    return root


def _file_hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def _markdown_table(path: Path) -> tuple[list[str], list[list[str]]]:
    table_lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("| ")
    ]
    parsed = [
        [cell.strip() for cell in line.strip("|").split("|")] for line in table_lines
    ]
    return parsed[0], parsed[2:]


def test_generation_is_byte_deterministic_and_marks_pilot_ineligible(
    tmp_path: Path,
) -> None:
    archive = _build_archive(tmp_path / "archive")
    first = tmp_path / "first"
    second = tmp_path / "second"

    result = generator.generate(archive, first)
    generator.generate(archive, second)

    assert result["eligibility"] == "exploratory_ineligible"
    assert _file_hashes(first) == _file_hashes(second)
    assert len(_file_hashes(first)) == 9
    for table in (
        "table-1-environment.md",
        "table-2-startup.md",
        "table-3-cli-operations.md",
        "table-4-resources.md",
    ):
        assert "INELIGIBLE EXPLORATORY OUTPUT" in (first / table).read_text(
            encoding="utf-8"
        )
    registry = json.loads((first / "numeric-evidence.json").read_text(encoding="utf-8"))
    assert registry["schema_version"] == "ai-research-writing/numeric-evidence-v2"
    assert registry["entries"]
    assert all(
        entry["source"] == "numeric-provenance.csv" for entry in registry["entries"]
    )
    assert "linear_quantile_p99" in (first / "numeric-provenance.csv").read_text(
        encoding="utf-8"
    )
    tables = json.loads((first / "tables.json").read_text(encoding="utf-8"))
    assert len(tables["tables"]["startup"]["rows"]) == 4
    assert len(tables["tables"]["public_cli_operations"]["rows"]) == 16
    assert len(tables["tables"]["resources"]["rows"]) == 7

    table1_header, table1_rows = _markdown_table(first / "table-1-environment.md")
    assert table1_header == ["Field", "Archived value", "Evidence source"]
    assert [row[0] for row in table1_rows] == [
        "Host OS",
        "Container engine OS",
        "Architecture",
        "CPU",
        "Memory",
        "Storage",
        "Docker Engine",
        "Cgroup",
        "Product commit/tag",
        "Benchmark commit",
        "Sandbox image",
        "Sandbox limits",
        "Workspace",
        "Client",
        "Seed",
        "Trials",
    ]
    assert all(row[2] for row in table1_rows)
    product_row = next(row for row in table1_rows if row[0] == "Product commit/tag")
    assert product_row[1] == f"{PRODUCT_COMMIT}; tag unavailable"
    product_machine_field = next(
        field
        for field in tables["tables"]["environment"]["fields"]
        if field["field"] == "Product commit/tag"
    )
    assert product_machine_field["value"]["freeze_tag"]["availability"] == "unavailable"

    table2_header, table2_rows = _markdown_table(first / "table-2-startup.md")
    assert table2_header == [
        "Stage",
        "Concurrent creates",
        "Samples",
        "p50 (ms)",
        "p95 (ms)",
        "p99 (ms)",
        "Throughput (ready/s)",
    ]
    assert table2_rows == [
        ["Sandbox create + base mount", "1", "5", "1.2", "1.38", "1.396", "12"],
        ["Session create to ready", "1", "5", "2.2", "2.38", "2.396", "12"],
        ["Session create to ready", "5", "5", "19.2", "19.38", "19.396", "52"],
        ["First no-op command", "1", "5", "3.2", "3.38", "3.396", "12"],
    ]

    table3_header, table3_rows = _markdown_table(first / "table-3-cli-operations.md")
    assert table3_header == [
        "Operation",
        "Case",
        "Payload/file size",
        "Concurrency",
        "Samples",
        "p50 (ms)",
        "p95 (ms)",
        "p99 (ms)",
        "Throughput (ops/s)",
    ]
    assert [row[:4] for row in table3_rows] == [
        ["`exec_command`", "no-op", "--", "1"],
        ["`exec_command`", "no-op", "--", "5"],
        ["`exec_command`", "fixture read", "4 KiB", "1"],
        ["`exec_command`", "fixture read", "4 KiB", "5"],
        ["Read", "snapshot", "4 KiB", "1"],
        ["Read", "snapshot", "4 KiB", "5"],
        ["Read", "snapshot", "256 KiB", "1"],
        ["Read", "snapshot", "256 KiB", "5"],
        ["Write", "session-local", "4 KiB", "1"],
        ["Write", "session-local", "4 KiB", "5"],
        ["Write", "session-local", "256 KiB", "1"],
        ["Write", "session-local", "256 KiB", "5"],
        ["Edit", "one replacement", "4 KiB", "1"],
        ["Edit", "one replacement", "4 KiB", "5"],
        ["Edit", "one replacement", "256 KiB", "1"],
        ["Edit", "one replacement", "256 KiB", "5"],
    ]

    table4_header, table4_rows = _markdown_table(first / "table-4-resources.md")
    assert table4_header == [
        "Operation/case",
        "Concurrency",
        "Peak daemon RSS (MiB)",
        "Peak sandbox memory (MiB)",
        "Sandbox CPU (ms/trial)",
        "Block read (MiB/trial)",
        "Block write (MiB/trial)",
        "Workspace allocated delta (MiB)",
    ]
    assert [row[:2] for row in table4_rows] == [
        ["Workspace create, 100 MiB/depth 100", "1"],
        ["Workspace create, 100 MiB/depth 100", "5"],
        ["`exec_command`, no-op", "1"],
        ["`exec_command`, no-op", "5"],
        ["Read, 256 KiB", "5"],
        ["Write, 256 KiB", "5"],
        ["Edit, 256 KiB", "5"],
    ]
    resource_rows = tables["tables"]["resources"]["rows"]
    assert all(
        "upperdir_bytes" in row["values"]
        and "workspace_allocated_bytes" not in row["values"]
        for row in resource_rows
    )
    with (first / "numeric-provenance.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        provenance = list(csv.DictReader(stream))
    upperdir_provenance = [
        row for row in provenance if row["evidence_id"].endswith(".upperdir_bytes")
    ]
    assert len(upperdir_provenance) == 7
    assert all(
        '"metric_id":"upperdir_bytes"' in row["selector_json"]
        for row in upperdir_provenance
    )
    output_manifest = json.loads(
        (first / "output-manifest.json").read_text(encoding="utf-8")
    )
    for entry in output_manifest["files"]:
        data = (first / entry["path"]).read_bytes()
        assert entry["bytes"] == len(data)
        assert entry["sha256"] == "sha256:" + hashlib.sha256(data).hexdigest()


def test_frozen_final_candidate_uses_exact_final_contract(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path / "archive", disposition="final")
    _mutate_json(
        archive / "environment-preflight.txt",
        lambda value: (
            value["recorded_run_environment"]["host"].pop("storage_model"),
            value["recorded_run_environment"]["host"].pop("storage_capacity_bytes"),
        ),
    )
    _refresh_archive_manifest(archive, disposition="final")
    output = tmp_path / "output"

    result = generator.generate(archive, output)

    assert result["eligibility"] == "frozen_final_candidate"
    table = (output / "table-2-startup.md").read_text(encoding="utf-8")
    assert "FROZEN FINAL CANDIDATE" in table
    assert "INELIGIBLE EXPLORATORY OUTPUT" not in table
    tables = json.loads((output / "tables.json").read_text(encoding="utf-8"))
    assert all(
        row["values"]["samples"] == 100 for row in tables["tables"]["startup"]["rows"]
    )
    product_field = next(
        field
        for field in tables["tables"]["environment"]["fields"]
        if field["field"] == "Product commit/tag"
    )
    assert product_field["display"] == (
        f"{PRODUCT_COMMIT}; annotated tag paper-v1-freeze"
    )
    assert product_field["value"]["freeze_tag"]["object_type"] == "tag"
    assert product_field["value"]["freeze_tag"]["tag_object"] == "c" * 40
    assert product_field["value"]["freeze_tag"]["peeled_commit"] == PRODUCT_COMMIT


def test_frozen_final_candidate_requires_ntfs(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path / "archive", disposition="final")
    _mutate_json(
        archive / "environment-preflight.txt",
        lambda value: value["recorded_run_environment"]["host"].update(
            filesystem="ReFS"
        ),
    )
    _refresh_archive_manifest(archive, disposition="final")

    with pytest.raises(
        generator.GenerationError, match="storage filesystem must be NTFS"
    ):
        generator.generate(archive, tmp_path / "output")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda tag: tag.clear(),
        lambda tag: tag.update(object_type="commit"),
        lambda tag: tag.update(peeled_commit="d" * 40),
        lambda tag: tag.update(tag_object="not-a-git-object"),
    ],
)
def test_frozen_final_candidate_requires_valid_annotated_product_tag(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    archive = _build_archive(tmp_path / "archive", disposition="final")
    _mutate_json(
        archive / "campaign-manifest.json",
        lambda value: mutate(value["product"]["freeze_tag"]),
    )
    _refresh_archive_manifest(archive, disposition="final")

    with pytest.raises(
        generator.GenerationError,
        match="final product freeze-tag provenance is invalid",
    ):
        generator.generate(archive, tmp_path / "output")


@pytest.mark.parametrize(
    "mutate,error",
    [
        (
            lambda root: _mutate_json(
                root / "campaign-manifest.json",
                lambda value: value["plan"].update(trial_batches=134),
            ),
            "campaign count contract drift",
        ),
        (
            lambda root: _mutate_json(
                root / "report.json",
                lambda value: value["data"].update(correctness_verdict="fail"),
            ),
            "correctness verdict drift or failure",
        ),
        (
            lambda root: _mutate_json(
                root / "run-manifest.json",
                lambda value: value["data"]["treatment"].update(source_commit="f" * 40),
            ),
            "product source identity drift",
        ),
        (
            lambda root: _mutate_json(
                root / "campaign-manifest.json",
                lambda value: value.update(disposition="final"),
            ),
            "campaign/archive disposition drift",
        ),
    ],
)
def test_semantic_drift_fails_closed(
    tmp_path: Path, mutate: Callable[[Path], None], error: str
) -> None:
    archive = _build_archive(tmp_path / "archive")
    mutate(archive)
    _refresh_archive_manifest(archive)
    with pytest.raises(generator.GenerationError, match=error):
        generator.generate(archive, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def _mutate_json(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    _json(path, value)


def test_archive_content_drift_and_archive_output_path_fail_closed(
    tmp_path: Path,
) -> None:
    archive = _build_archive(tmp_path / "archive")
    report = archive / "report.json"
    report.write_bytes(report.read_bytes() + b" ")
    with pytest.raises(
        generator.GenerationError, match="archive (byte-count|content) drift"
    ):
        generator.generate(archive, tmp_path / "output")

    clean_archive = _build_archive(tmp_path / "clean-archive")
    with pytest.raises(
        generator.GenerationError, match="outside the immutable archive"
    ):
        generator.generate(clean_archive, clean_archive / "generated")
