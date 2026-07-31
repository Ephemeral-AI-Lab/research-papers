#!/usr/bin/env python3
"""Generate the four deterministic EXP1 tables from one immutable archive.

The generator deliberately has no live-system fallback.  Every displayed value
is selected from an archive member covered by archive-manifest.json.  Numeric
outputs are accompanied by both a strict ai-research-writing v2 registry and a
machine-readable provenance CSV containing the upstream selector, unit, and
aggregation recipe.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
EVIDENCE_SCHEMA_VERSION = "ai-research-writing/numeric-evidence-v2"
SHA256_PREFIX = "sha256:"
MIB = 1024.0 * 1024.0
EXPECTED_COUNTS = {
    "exploratory": {
        "preset": "paper-pilot",
        "cells": 19,
        "trial_batches": 133,
        "requests": 385,
        "warmups": 2,
        "measured": 5,
        "campaign_eligibility": "exploratory_ineligible",
        "output_eligibility": "exploratory_ineligible",
    },
    "final": {
        "preset": "paper-good-pass",
        "cells": 19,
        "trial_batches": 1938,
        "requests": 5610,
        "warmups": 2,
        "measured": 100,
        "campaign_eligibility": "frozen_final_candidate",
        "output_eligibility": "frozen_final_candidate",
    },
}

PERFORMANCE_ROWS = [
    ("create_sandbox", "create_sandbox", None, 1, "Create sandbox"),
    ("create_workspace", "create_workspace", None, 1, "Create workspace (session)"),
    ("exec_command", "exec_command", "noop", 1, "Exec no-op"),
    ("exec_command", "exec_command", "noop", 5, "Exec no-op"),
    ("exec_command", "exec_command", "fixture_read", 1, "Exec fixture read (4 KiB)"),
    ("exec_command", "exec_command", "fixture_read", 5, "Exec fixture read (4 KiB)"),
    ("file_read", "file_read", 4096, 1, "Read snapshot (4 KiB)"),
    ("file_read", "file_read", 4096, 5, "Read snapshot (4 KiB)"),
    ("file_read", "file_read", 262144, 1, "Read snapshot (256 KiB)"),
    ("file_read", "file_read", 262144, 5, "Read snapshot (256 KiB)"),
    ("file_write", "file_write", 4096, 1, "Write session (4 KiB)"),
    ("file_write", "file_write", 4096, 5, "Write session (4 KiB)"),
    ("file_write", "file_write", 262144, 1, "Write session (256 KiB)"),
    ("file_write", "file_write", 262144, 5, "Write session (256 KiB)"),
    ("file_edit", "file_edit", 4096, 1, "Edit replacement (4 KiB)"),
    ("file_edit", "file_edit", 4096, 5, "Edit replacement (4 KiB)"),
    ("file_edit", "file_edit", 262144, 1, "Edit replacement (256 KiB)"),
    ("file_edit", "file_edit", 262144, 5, "Edit replacement (256 KiB)"),
    ("create_workspace", "create_workspace", None, 5, "Create workspace (session)"),
]

STARTUP_KEYS = [
    ("create_sandbox", None, 1),
    ("create_workspace", None, 1),
    ("create_workspace", None, 5),
    ("exec_command", "noop", 1),
]

PUBLIC_KEYS = [
    ("exec_command", "noop", 1),
    ("exec_command", "noop", 5),
    ("exec_command", "fixture_read", 1),
    ("exec_command", "fixture_read", 5),
    ("file_read", 4096, 1),
    ("file_read", 4096, 5),
    ("file_read", 262144, 1),
    ("file_read", 262144, 5),
    ("file_write", 4096, 1),
    ("file_write", 4096, 5),
    ("file_write", 262144, 1),
    ("file_write", 262144, 5),
    ("file_edit", 4096, 1),
    ("file_edit", 4096, 5),
    ("file_edit", 262144, 1),
    ("file_edit", 262144, 5),
]

RESOURCE_KEYS = [
    ("create_workspace", None, 1),
    ("create_workspace", None, 5),
    ("exec_command", "noop", 1),
    ("exec_command", "noop", 5),
    ("file_read", 262144, 5),
    ("file_write", 262144, 5),
    ("file_edit", 262144, 5),
]

RESOURCE_COLUMNS = [
    ("daemon_rss_bytes", "Peak daemon RSS (MiB)", "bytes", "MiB", "max"),
    ("sandbox_memory_peak_bytes", "Peak sandbox memory (MiB)", "bytes", "MiB", "max"),
    (
        "sandbox_cpu_time_ns",
        "Sandbox CPU (ms/trial)",
        "nanoseconds",
        "milliseconds",
        "mean",
    ),
    ("sandbox_block_read_bytes", "Block read (MiB/trial)", "bytes", "MiB", "mean"),
    ("sandbox_block_write_bytes", "Block write (MiB/trial)", "bytes", "MiB", "mean"),
    (
        "upperdir_bytes",
        "Workspace allocated delta (MiB)",
        "bytes",
        "MiB",
        "mean",
    ),
]


class GenerationError(RuntimeError):
    """A fail-closed archive or generation-contract violation."""


def _sha256_bytes(data: bytes) -> str:
    return SHA256_PREFIX + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return SHA256_PREFIX + digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _load_json(path: Path, *, envelope: bool = False) -> Any:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationError(
            f"cannot read JSON archive member {path.name}: {exc}"
        ) from exc
    if envelope:
        if not isinstance(parsed, dict) or not isinstance(parsed.get("data"), dict):
            raise GenerationError(f"{path.name} is not a valid data envelope")
        return parsed["data"]
    return parsed


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationError(message)


def _nested(value: Any, *path: str) -> Any:
    for part in path:
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _first(value: Any, paths: Sequence[Sequence[str]]) -> Any:
    for path in paths:
        found = _nested(value, *path)
        if found is not None:
            return found
    return None


def _normalize_sha(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if value.startswith(SHA256_PREFIX) and len(value) == 71:
        return value
    if len(value) == 64:
        return SHA256_PREFIX + value
    return value


def _is_git_sha1(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_archive_inventory(
    archive: Path, manifest: Mapping[str, Any]
) -> dict[str, Mapping[str, Any]]:
    entries = manifest.get("files")
    _require(isinstance(entries, list), "archive manifest has no file inventory")
    expected: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        _require(isinstance(entry, dict), "archive inventory entry is not an object")
        relative = entry.get("path")
        _require(
            isinstance(relative, str)
            and relative
            and "\\" not in relative
            and not relative.startswith("/")
            and ".." not in Path(relative).parts,
            f"unsafe archive inventory path: {relative!r}",
        )
        _require(
            relative not in expected, f"duplicate archive inventory path: {relative}"
        )
        expected[relative] = entry

    actual_paths = sorted(
        path.relative_to(archive).as_posix()
        for path in archive.rglob("*")
        if path.is_file() and path.name != "archive-manifest.json"
    )
    _require(
        actual_paths == sorted(expected),
        "archive file set drifted from archive-manifest.json",
    )

    tree = hashlib.sha256()
    total_bytes = 0
    for relative in actual_paths:
        path = archive / Path(relative)
        data = path.read_bytes()
        digest = hashlib.sha256(data).digest()
        entry = expected[relative]
        _require(
            entry.get("bytes") == len(data), f"archive byte-count drift: {relative}"
        )
        _require(
            _normalize_sha(entry.get("sha256")) == SHA256_PREFIX + digest.hex(),
            f"archive content drift: {relative}",
        )
        total_bytes += len(data)
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(digest)
        tree.update(b"\n")

    _require(
        manifest.get("archive_file_count") == len(actual_paths),
        "archive file count drift",
    )
    _require(
        manifest.get("archive_bytes") == total_bytes,
        "archive aggregate byte count drift",
    )
    _require(
        _normalize_sha(manifest.get("content_tree_sha256"))
        == SHA256_PREFIX + tree.hexdigest(),
        "archive content-tree hash drift",
    )
    return expected


def _metric(cell: Mapping[str, Any], metric_id: str) -> Mapping[str, Any]:
    matches = [
        metric
        for metric in cell.get("metrics", [])
        if isinstance(metric, Mapping)
        and _nested(metric, "identity", "id") == metric_id
    ]
    _require(
        len(matches) == 1,
        f"cell {cell.get('cell_id')} must contain one {metric_id} metric",
    )
    return matches[0]


def _cell_key(plan_cell: Mapping[str, Any]) -> tuple[str, Any, int]:
    operation = plan_cell.get("operation_id")
    factors = _nested(plan_cell, "operation", "cell")
    _require(
        isinstance(factors, Mapping),
        f"cell {plan_cell.get('cell_id')} has no operation factors",
    )
    if operation == "create_sandbox":
        return operation, None, 1
    if operation == "create_workspace":
        return operation, None, int(factors.get("workspace_count", -1))
    concurrency = int(factors.get("concurrent_requests", -1))
    if operation == "exec_command":
        return operation, factors.get("command_case"), concurrency
    if operation == "file_read":
        return operation, int(factors.get("returned_bytes", -1)), concurrency
    if operation == "file_write":
        return operation, int(factors.get("content_bytes", -1)), concurrency
    if operation == "file_edit":
        return operation, int(factors.get("file_bytes", -1)), concurrency
    raise GenerationError(f"unexpected EXP1 operation {operation!r}")


def _expected_keys() -> set[tuple[str, Any, int]]:
    return {
        (operation, variant, concurrency)
        for _, operation, variant, concurrency, _ in PERFORMANCE_ROWS
    }


def _validate_factor_contract(
    key: tuple[str, Any, int], factors: Mapping[str, Any]
) -> None:
    operation, variant, concurrency = key
    _require(
        factors.get("workspace_profile") == "paper-100m",
        f"{key}: workspace profile drift",
    )
    if operation == "create_sandbox":
        _require(
            factors.get("network_profile") == "shared", f"{key}: network policy drift"
        )
    elif operation == "create_workspace":
        _require(
            factors.get("workspace_count") == concurrency,
            f"{key}: workspace count drift",
        )
    else:
        _require(
            factors.get("concurrent_requests") == concurrency,
            f"{key}: concurrency drift",
        )
    if operation == "exec_command":
        _require(factors.get("command_case") == variant, f"{key}: command case drift")
        _require(
            factors.get("session_mode") == "explicit", f"{key}: session mode drift"
        )
    elif operation == "file_read":
        _require(factors.get("returned_bytes") == variant, f"{key}: read size drift")
        _require(factors.get("source") == "snapshot", f"{key}: read source drift")
    elif operation == "file_write":
        _require(factors.get("content_bytes") == variant, f"{key}: write size drift")
        _require(
            factors.get("destination") == "session", f"{key}: write destination drift"
        )
    elif operation == "file_edit":
        _require(factors.get("file_bytes") == variant, f"{key}: edit size drift")
        _require(
            factors.get("destination") == "session", f"{key}: edit destination drift"
        )
        _require(
            factors.get("replacement_count") == 1, f"{key}: replacement count drift"
        )


def _raw_values(
    metric: Mapping[str, Any], measured: int, *, allow_unavailable: bool
) -> list[float] | None:
    attempted = metric.get("attempted_n")
    available = metric.get("available_n")
    failed = metric.get("failed_n")
    unavailable = _nested(metric, "unavailable", "count")
    _require(
        attempted == measured,
        f"metric {_nested(metric, 'identity', 'id')}: attempted_n drift",
    )
    _require(failed == 0, f"metric {_nested(metric, 'identity', 'id')}: failed samples")
    if available != measured or unavailable != 0:
        if allow_unavailable:
            return None
        raise GenerationError(
            f"metric {_nested(metric, 'identity', 'id')}: incomplete measured samples "
            f"(available={available}, unavailable={unavailable}, expected={measured})"
        )
    points = metric.get("raw_points")
    _require(
        isinstance(points, list) and len(points) == measured,
        "raw metric point count drift",
    )
    trial_ids: set[str] = set()
    values: list[float] = []
    for point in points:
        _require(isinstance(point, Mapping), "raw metric point is not an object")
        trial_id = point.get("trial_id")
        _require(
            isinstance(trial_id, str)
            and "-measured-" in trial_id
            and trial_id not in trial_ids,
            "raw metric trial identity drift",
        )
        trial_ids.add(trial_id)
        value = point.get("value")
        _require(
            isinstance(value, (int, float)) and math.isfinite(float(value)),
            "non-finite raw metric value",
        )
        values.append(float(value))
    return values


def _quantile(values: Sequence[float], probability: float) -> float:
    _require(bool(values), "cannot calculate quantile of empty samples")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _mean(values: Sequence[float]) -> float:
    _require(bool(values), "cannot calculate mean of empty samples")
    return math.fsum(values) / len(values)


def _convert(value: float, input_unit: str, output_unit: str) -> float:
    if (input_unit, output_unit) == ("nanoseconds", "milliseconds"):
        return value / 1_000_000.0
    if (input_unit, output_unit) == ("bytes", "MiB"):
        return value / MIB
    if input_unit == output_unit:
        return value
    raise GenerationError(f"unsupported unit conversion: {input_unit} -> {output_unit}")


def _display(value: float, *, digits: int = 3) -> str:
    rendered = f"{value:.{digits}f}"
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _archive_selector(
    path: str, *, cell_id: str | None = None, metric_id: str | None = None
) -> dict[str, Any]:
    selector: dict[str, Any] = {"artifact": path}
    if cell_id is not None:
        selector["cell_id"] = cell_id
    if metric_id is not None:
        selector["metric_id"] = metric_id
        selector["field"] = "raw_points[].value"
        selector["trial_scope"] = "reportable_measured"
    return selector


class Evidence:
    def __init__(self, source_hashes: Mapping[str, str], eligibility: str) -> None:
        self.source_hashes = source_hashes
        self.eligibility = eligibility
        self.rows: list[dict[str, Any]] = []

    def add(
        self,
        evidence_id: str,
        value: float,
        *,
        source_file: str,
        selector: Mapping[str, Any],
        input_unit: str,
        output_unit: str,
        aggregation: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> float:
        _require(
            source_file in self.source_hashes,
            f"unmanifested evidence source: {source_file}",
        )
        number = float(value)
        _require(math.isfinite(number), f"non-finite evidence value: {evidence_id}")
        self.rows.append(
            {
                "evidence_id": evidence_id,
                "value": format(number, ".17g"),
                "source_file": source_file,
                "source_sha256": self.source_hashes[source_file],
                "selector_kind": "archive-json",
                "selector_json": json.dumps(
                    selector, separators=(",", ":"), sort_keys=True
                ),
                "input_unit": input_unit,
                "output_unit": output_unit,
                "aggregation": aggregation,
                "aggregation_parameters_json": json.dumps(
                    parameters or {}, separators=(",", ":"), sort_keys=True
                ),
                "eligibility": self.eligibility,
            }
        )
        return number

    def csv_bytes(self) -> bytes:
        output = io.StringIO(newline="")
        fieldnames = [
            "evidence_id",
            "value",
            "source_file",
            "source_sha256",
            "selector_kind",
            "selector_json",
            "input_unit",
            "output_unit",
            "aggregation",
            "aggregation_parameters_json",
            "eligibility",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(self.rows, key=lambda row: row["evidence_id"]))
        return output.getvalue().encode("utf-8")

    def registry(self) -> dict[str, Any]:
        entries = []
        for row in sorted(self.rows, key=lambda item: item["evidence_id"]):
            note = (
                f"{row['evidence_id']}; upstream={row['source_file']}#{row['selector_json']}; "
                f"units={row['input_unit']}->{row['output_unit']}; "
                f"aggregation={row['aggregation']} {row['aggregation_parameters_json']}; "
                f"eligibility={row['eligibility']}"
            )
            entries.append(
                {
                    "aggregate": "identity",
                    "note": note,
                    "representations": ["raw"],
                    "selector": {
                        "column": "value",
                        "kind": "csv",
                        "where": {"evidence_id": row["evidence_id"]},
                    },
                    "source": "numeric-provenance.csv",
                    "tolerance": 0,
                    "value": float(row["value"]),
                }
            )
        return {"entries": entries, "schema_version": EVIDENCE_SCHEMA_VERSION}


def _eligibility_banner(disposition: str) -> str:
    if disposition == "exploratory":
        return (
            "> **INELIGIBLE EXPLORATORY OUTPUT.** This archive is a pilot. "
            "Do not copy these values into the manuscript or paper tables."
        )
    return (
        "> **FROZEN FINAL CANDIDATE.** Values are archive-derived and may be used only "
        "after the remaining paper evidence/build gates pass."
    )


def _markdown_table(
    headers: Sequence[str], rows: Sequence[Sequence[str]], banner: str, title: str
) -> bytes:
    lines = [f"# {title}", "", banner, "", "| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _label_for_key(key: tuple[str, Any, int]) -> str:
    for _, operation, variant, concurrency, label in PERFORMANCE_ROWS:
        if key == (operation, variant, concurrency):
            return label
    raise GenerationError(f"no table label for cell key {key}")


def _validate_archive(archive: Path) -> dict[str, Any]:
    manifest_path = archive / "archive-manifest.json"
    _require(manifest_path.is_file(), "archive-manifest.json is required")
    manifest = _load_json(manifest_path)
    _require(
        isinstance(manifest, dict) and manifest.get("schema_version") == 1,
        "unsupported archive manifest",
    )
    inventory = _verify_archive_inventory(archive, manifest)
    required = {
        "campaign-manifest.json",
        "run-manifest.json",
        "expanded-plan.json",
        "report.json",
        "environment-preflight.txt",
        "fixture-manifest.json",
    }
    _require(
        required <= set(inventory),
        f"archive is missing required members: {sorted(required - set(inventory))}",
    )

    campaign = _load_json(archive / "campaign-manifest.json")
    run = _load_json(archive / "run-manifest.json", envelope=True)
    expanded = _load_json(archive / "expanded-plan.json", envelope=True)
    report = _load_json(archive / "report.json", envelope=True)
    preflight = _load_json(archive / "environment-preflight.txt")
    fixture = _load_json(archive / "fixture-manifest.json")
    _require(
        all(isinstance(item, dict) for item in (campaign, preflight, fixture)),
        "invalid archive metadata",
    )

    disposition = manifest.get("disposition")
    _require(
        disposition in EXPECTED_COUNTS,
        f"unsupported table-generation disposition: {disposition!r}",
    )
    expected = EXPECTED_COUNTS[disposition]
    _require(
        campaign.get("disposition") == disposition, "campaign/archive disposition drift"
    )
    _require(
        campaign.get("eligibility") == expected["campaign_eligibility"],
        "campaign eligibility drift",
    )
    _require(run.get("name") == expected["preset"], "run preset/disposition drift")
    _require(
        campaign.get("state") == run.get("state") == report.get("state") == "completed",
        "run state is not completed",
    )
    _require(
        campaign.get("correctness")
        == run.get("correctness")
        == report.get("correctness_verdict")
        == "pass",
        "correctness verdict drift or failure",
    )
    _require(
        report.get("warnings") == [], "report warnings make table derivation ineligible"
    )

    run_id = campaign.get("run_id")
    _require(
        isinstance(run_id, str)
        and run_id
        == manifest.get("run_id")
        == run.get("run_id")
        == report.get("run_id"),
        "run identity drift",
    )
    plan_hash = _nested(campaign, "plan", "hash")
    _require(
        isinstance(plan_hash, str)
        and plan_hash
        == run.get("plan_hash")
        == expanded.get("plan_hash")
        == report.get("plan_hash"),
        "plan identity drift",
    )
    _require(
        _nested(campaign, "plan", "client_cohort") == "product_cli",
        "non-product CLI cohort",
    )
    _require(
        _nested(run, "environment", "client_cohort") == "product_cli",
        "run client cohort drift",
    )

    design = report.get("design_counts")
    _require(
        _nested(campaign, "plan", "cells") == expected["cells"]
        and _nested(campaign, "plan", "trial_batches") == expected["trial_batches"]
        and _nested(campaign, "plan", "issued_operation_requests")
        == expected["requests"],
        "campaign count contract drift",
    )
    _require(
        isinstance(design, Mapping)
        and design.get("test_combinations") == expected["cells"]
        and design.get("trial_batches") == expected["trial_batches"]
        and design.get("issued_product_requests") == expected["requests"],
        "report count contract drift",
    )

    product_commit = _nested(campaign, "product", "commit")
    _require(
        _is_git_sha1(product_commit)
        and product_commit == _nested(campaign, "cleanup", "product_commit")
        and product_commit == _nested(run, "producer", "source_commit")
        and product_commit == _nested(run, "treatment", "source_commit")
        and product_commit == report.get("source_commit"),
        "product source identity drift",
    )
    freeze_tag = _nested(campaign, "product", "freeze_tag")
    if disposition == "final":
        _require(
            isinstance(freeze_tag, Mapping)
            and freeze_tag.get("availability") == "available"
            and freeze_tag.get("name") == "paper-v1-freeze"
            and freeze_tag.get("reference") == "refs/tags/paper-v1-freeze"
            and freeze_tag.get("object_type") == "tag"
            and _is_git_sha1(freeze_tag.get("tag_object"))
            and freeze_tag.get("peeled_commit") == product_commit,
            "final product freeze-tag provenance is invalid",
        )
    elif freeze_tag is not None:
        _require(
            isinstance(freeze_tag, Mapping)
            and freeze_tag.get("availability") == "unavailable"
            and freeze_tag.get("required_final_tag") == "paper-v1-freeze",
            "exploratory product freeze-tag provenance is invalid",
        )
    _require(
        _nested(campaign, "product", "dirty") is False
        and _nested(run, "treatment", "source_dirty") is False
        and _nested(campaign, "cleanup", "product_status_porcelain") == "",
        "dirty product source is ineligible",
    )
    binary_pairs = {
        "daemon": "daemon_binary_hash",
        "gateway": "gateway_binary_hash",
        "manager": "manager_cli_binary_hash",
        "runtime": "runtime_cli_binary_hash",
        "observability": "observability_cli_binary_hash",
    }
    for binary, treatment_key in binary_pairs.items():
        _require(
            _nested(campaign, "product", "binaries", binary, "sha256")
            == _nested(run, "treatment", treatment_key),
            f"{binary} binary identity drift",
        )
    _require(
        _nested(campaign, "image", "id") == _nested(run, "environment", "image_digest"),
        "container image identity drift",
    )
    cleanup = campaign.get("cleanup")
    _require(
        isinstance(cleanup, Mapping)
        and cleanup.get("run_workspace_exists") is False
        and cleanup.get("runtime_exists") is False
        and all(
            cleanup.get(key) == []
            for key in (
                "gateway_labeled_containers",
                "gateway_labeled_volumes",
                "matching_product_processes",
                "run_labeled_containers",
                "run_labeled_volumes",
            )
        ),
        "terminal cleanup proof failed",
    )
    _require(
        _nested(fixture, "identity", "profile_id") == "paper-100m"
        and _nested(fixture, "identity", "fixture", "file_count") == 4000
        and _nested(fixture, "identity", "fixture", "logical_bytes") == 104857600
        and _nested(fixture, "identity", "fixture", "maximum_depth") == 100
        and _nested(fixture, "identity", "seed") == 20260712,
        "fixture identity drift",
    )
    _require(
        fixture.get("fixture_hash") == _nested(campaign, "fixture", "fixture_hash")
        and fixture.get("tree_hash") == _nested(campaign, "fixture", "tree_hash"),
        "fixture/campaign identity drift",
    )

    plan_cells = expanded.get("cells")
    report_cells = report.get("cells")
    _require(
        isinstance(plan_cells, list)
        and isinstance(report_cells, list)
        and len(plan_cells) == len(report_cells) == expected["cells"],
        "cell count drift",
    )
    report_by_id: dict[str, Mapping[str, Any]] = {}
    for cell in report_cells:
        _require(isinstance(cell, Mapping), "report cell is not an object")
        cell_id = cell.get("cell_id")
        _require(
            isinstance(cell_id, str) and cell_id not in report_by_id,
            "duplicate/invalid report cell id",
        )
        report_by_id[cell_id] = cell

    cells: dict[tuple[str, Any, int], dict[str, Any]] = {}
    for plan_cell in plan_cells:
        _require(isinstance(plan_cell, Mapping), "expanded-plan cell is not an object")
        cell_id = plan_cell.get("cell_id")
        _require(cell_id in report_by_id, f"expanded-plan/report cell drift: {cell_id}")
        report_cell = report_by_id[cell_id]
        _require(
            report_cell.get("operation_id") == plan_cell.get("operation_id"),
            f"operation drift: {cell_id}",
        )
        key = _cell_key(plan_cell)
        _require(key not in cells, f"duplicate EXP1 matrix cell {key}")
        factors = _nested(plan_cell, "operation", "cell")
        _validate_factor_contract(key, factors)
        protocol = plan_cell.get("protocol")
        _require(
            isinstance(protocol, Mapping)
            and protocol.get("warmups") == expected["warmups"]
            and protocol.get("measured_trials") == expected["measured"],
            f"{key}: trial-count drift",
        )
        counts = report_cell.get("counts")
        _require(
            isinstance(counts, Mapping)
            and counts.get("warmup") == expected["warmups"]
            and counts.get("measured_attempted") == expected["measured"]
            and counts.get("total_attempted")
            == expected["warmups"] + expected["measured"]
            and counts.get("successful") == expected["measured"]
            and all(
                counts.get(field) == 0
                for field in (
                    "product_failed",
                    "correctness_failed",
                    "infrastructure_failed",
                    "cleanup_invalid",
                    "missing_primary_latency",
                )
            ),
            f"{key}: reportable trial/correctness count drift",
        )
        checks = report_cell.get("checks")
        _require(
            isinstance(checks, list)
            and bool(checks)
            and all(
                check.get("attempted") == expected["measured"]
                and check.get("passed") == expected["measured"]
                and check.get("failed") == 0
                for check in checks
                if isinstance(check, Mapping)
            )
            and all(isinstance(check, Mapping) for check in checks),
            f"{key}: correctness check drift",
        )
        latency_metric = _metric(report_cell, "batch_makespan_ns")
        throughput_metric = _metric(report_cell, "throughput_ops_s")
        _require(
            _nested(latency_metric, "identity", "unit") == "nanoseconds",
            f"{key}: latency unit drift",
        )
        _require(
            _nested(throughput_metric, "identity", "unit") == "operations_per_second",
            f"{key}: throughput unit drift",
        )
        _raw_values(latency_metric, expected["measured"], allow_unavailable=False)
        _raw_values(throughput_metric, expected["measured"], allow_unavailable=False)
        cells[key] = {
            "cell_id": cell_id,
            "factors": factors,
            "plan_cell": plan_cell,
            "report_cell": report_cell,
        }
    _require(set(cells) == _expected_keys(), "EXP1 19-cell matrix identity drift")

    # If duplicate raw metadata is archived, it must be byte-identical.
    for relative in (
        "report.json",
        "run-manifest.json",
        "expanded-plan.json",
    ):
        raw_relative = f"raw/{relative}"
        if raw_relative in inventory:
            _require(
                inventory[relative].get("sha256")
                == inventory[raw_relative].get("sha256"),
                f"root/raw duplicate drift: {relative}",
            )

    source_hashes = {
        relative: str(entry["sha256"])
        for relative, entry in inventory.items()
        if relative in required
    }
    return {
        "manifest": manifest,
        "inventory": inventory,
        "campaign": campaign,
        "run": run,
        "expanded": expanded,
        "report": report,
        "preflight": preflight,
        "fixture": fixture,
        "cells": cells,
        "expected": expected,
        "disposition": disposition,
        "source_hashes": source_hashes,
    }


def _table_one(
    context: Mapping[str, Any], evidence: Evidence, banner: str
) -> tuple[bytes, dict[str, Any]]:
    campaign = context["campaign"]
    run = context["run"]
    preflight = context["preflight"]
    fixture = context["fixture"]
    disposition = context["disposition"]
    expected = context["expected"]
    product_commit = _nested(campaign, "product", "commit")
    freeze_tag = _nested(campaign, "product", "freeze_tag")
    if disposition == "final":
        product_commit_tag = f"{product_commit}; annotated tag {freeze_tag['name']}"
    else:
        product_commit_tag = f"{product_commit}; tag unavailable"
    host = _first(
        preflight,
        [
            ("recorded_run_environment", "host"),
            ("run_environment", "host"),
            ("host",),
        ],
    )
    if not isinstance(host, Mapping):
        host = _nested(run, "environment", "host") or {}
    run_host = _nested(run, "environment", "host") or {}
    docker = _first(
        preflight, [("docker",), ("recorded_run_environment", "host", "docker")]
    )
    if not isinstance(docker, Mapping):
        docker = campaign.get("docker") or {}
    cpu_model = _first(host, [("cpu_model",), ("processor_model",)])
    logical_processors = _first(host, [("logical_processors",), ("logical_cpu_count",)])
    host_os_name = host.get("operating_system") or run_host.get("operating_system")
    host_os_edition = _first(host, [("os_edition",), ("operating_system_edition",)])
    host_os_build = _first(host, [("os_build",), ("build_number",)])
    host_os_parts = [host_os_name, host_os_edition]
    if host_os_build is not None:
        host_os_parts.append(f"build {host_os_build}")
    host_os_display = (
        " ".join(str(part) for part in host_os_parts if part) or "unavailable"
    )
    if cpu_model is None and logical_processors is None:
        cpu_display: Any = "unavailable"
    elif logical_processors is None:
        cpu_display = str(cpu_model)
    elif cpu_model is None:
        cpu_display = f"{logical_processors} logical processors"
    else:
        cpu_display = f"{cpu_model} / {logical_processors} logical processors"
    sandbox_limits = _first(
        preflight, [("sandbox_limits",), ("recorded_run_environment", "sandbox_limits")]
    )
    storage_model = _first(host, [("storage_model",), ("volume_model",)])
    storage_capacity = _first(
        host, [("storage_capacity_bytes",), ("volume_capacity_bytes",)]
    )
    storage_filesystem = host.get("filesystem") or run_host.get("filesystem")
    storage_parts = []
    if storage_model is not None:
        storage_parts.append(str(storage_model))
    if isinstance(storage_capacity, (int, float)):
        storage_parts.append(f"{_display(float(storage_capacity) / (1024.0**3))} GiB")
    if storage_filesystem is not None:
        storage_parts.append(str(storage_filesystem))
    storage_display = " / ".join(storage_parts) or "unavailable"
    sandbox_limits_display: Any = sandbox_limits
    if isinstance(sandbox_limits, Mapping):
        limit_parts = []
        cpu_limit = sandbox_limits.get("vcpus", sandbox_limits.get("cpu_count"))
        memory_limit = sandbox_limits.get("memory_bytes")
        pids_limit = sandbox_limits.get("pids_limit", sandbox_limits.get("pids"))
        if isinstance(cpu_limit, (int, float)):
            limit_parts.append(f"{_display(float(cpu_limit))} vCPU")
        if isinstance(memory_limit, (int, float)):
            limit_parts.append(f"{_display(float(memory_limit) / MIB)} MiB")
        if isinstance(pids_limit, (int, float)):
            limit_parts.append(f"{_display(float(pids_limit))} PIDs")
        sandbox_limits_display = " / ".join(limit_parts) or json.dumps(
            sandbox_limits, separators=(",", ":"), sort_keys=True
        )

    fields: list[tuple[str, Any, str, Mapping[str, Any], str]] = [
        (
            "Host OS",
            host_os_display,
            "environment-preflight.txt",
            {"pointer": "/recorded_run_environment/host"},
            "text",
        ),
        (
            "Container engine OS",
            docker.get("os_type"),
            "environment-preflight.txt",
            {"pointer": "/docker/os_type"},
            "text",
        ),
        (
            "Architecture",
            host.get("architecture") or run_host.get("architecture"),
            "environment-preflight.txt",
            {"pointer": "/recorded_run_environment/host/architecture"},
            "text",
        ),
        (
            "CPU",
            cpu_display,
            "environment-preflight.txt",
            {"pointer": "/recorded_run_environment/host"},
            "text",
        ),
        (
            "Memory",
            _first(host, [("total_memory_bytes",), ("memory_bytes",)]) or "unavailable",
            "environment-preflight.txt",
            {"pointer": "/recorded_run_environment/host/total_memory_bytes"},
            "bytes",
        ),
        (
            "Storage",
            storage_display,
            "environment-preflight.txt",
            {"pointer": "/recorded_run_environment/host"},
            "text",
        ),
        (
            "Docker Engine",
            docker.get("server_version") or run_host.get("docker_engine_version"),
            "environment-preflight.txt",
            {"pointer": "/docker/server_version"},
            "text",
        ),
        (
            "Cgroup",
            docker.get("cgroup_version"),
            "environment-preflight.txt",
            {"pointer": "/docker/cgroup_version"},
            "text",
        ),
        (
            "Product commit/tag",
            product_commit_tag,
            "campaign-manifest.json",
            {"pointer": "/product"},
            "text",
        ),
        (
            "Benchmark commit",
            _nested(campaign, "paper_git", "commit"),
            "campaign-manifest.json",
            {"pointer": "/paper_git/commit"},
            "text",
        ),
        (
            "Sandbox image",
            _nested(campaign, "image", "requested"),
            "campaign-manifest.json",
            {"pointer": "/image/requested"},
            "text",
        ),
        (
            "Sandbox limits",
            sandbox_limits_display or "unavailable",
            "environment-preflight.txt",
            {"pointer": "/sandbox_limits"},
            "text",
        ),
        (
            "Workspace",
            (
                f"{_nested(fixture, 'identity', 'fixture', 'logical_bytes') // (1024 * 1024)} MiB / "
                f"{_nested(fixture, 'identity', 'fixture', 'file_count')} files / "
                f"depth {_nested(fixture, 'identity', 'fixture', 'maximum_depth')}"
            ),
            "fixture-manifest.json",
            {"pointer": "/identity/fixture"},
            "text",
        ),
        (
            "Client",
            _nested(campaign, "plan", "client_cohort"),
            "campaign-manifest.json",
            {"pointer": "/plan/client_cohort"},
            "text",
        ),
        (
            "Seed",
            _nested(fixture, "identity", "seed"),
            "fixture-manifest.json",
            {"pointer": "/identity/seed"},
            "count",
        ),
        (
            "Trials",
            f"{expected['warmups']} warm-up + {expected['measured']} measured",
            "expanded-plan.json",
            {"pointer": "/data/cells/*/protocol"},
            "text",
        ),
    ]

    # Missing qualification facts are tolerated only for explicitly ineligible pilot output.
    if disposition == "final":
        missing = [
            name for name, value, _, _, _ in fields if value in (None, "unavailable")
        ]
        required_qualification_facts = {
            "host OS edition": host_os_edition,
            "host OS build": host_os_build,
            "CPU model": cpu_model,
            "logical processor count": logical_processors,
            "host memory": _first(host, [("total_memory_bytes",), ("memory_bytes",)]),
            "storage filesystem": storage_filesystem,
            "sandbox limits": sandbox_limits
            if isinstance(sandbox_limits, Mapping)
            else None,
        }
        missing.extend(
            name
            for name, value in required_qualification_facts.items()
            if value is None
        )
        if (
            not isinstance(storage_filesystem, str)
            or storage_filesystem.upper() != "NTFS"
        ):
            missing.append("storage filesystem must be NTFS")
        _require(
            not missing,
            f"final archive lacks required environment fields: {', '.join(missing)}",
        )

    # Register the numeric components embedded in descriptive Table 1 cells.
    embedded_numeric = [
        (
            "table1.workspace_fixture.logical_mib",
            _nested(fixture, "identity", "fixture", "logical_bytes") / MIB,
            "fixture-manifest.json",
            {"pointer": "/identity/fixture/logical_bytes"},
            "bytes",
            "MiB",
            {"divisor": 1048576},
        ),
        (
            "table1.workspace_fixture.file_count",
            _nested(fixture, "identity", "fixture", "file_count"),
            "fixture-manifest.json",
            {"pointer": "/identity/fixture/file_count"},
            "count",
            "count",
            {},
        ),
        (
            "table1.workspace_fixture.maximum_depth",
            _nested(fixture, "identity", "fixture", "maximum_depth"),
            "fixture-manifest.json",
            {"pointer": "/identity/fixture/maximum_depth"},
            "count",
            "count",
            {},
        ),
        (
            "table1.trials.warmups",
            expected["warmups"],
            "expanded-plan.json",
            {"pointer": "/data/cells/*/protocol/warmups", "invariant": "all equal"},
            "count",
            "count",
            {},
        ),
        (
            "table1.trials.measured",
            expected["measured"],
            "expanded-plan.json",
            {
                "pointer": "/data/cells/*/protocol/measured_trials",
                "invariant": "all equal",
            },
            "count",
            "count",
            {},
        ),
    ]
    if isinstance(logical_processors, (int, float)):
        embedded_numeric.append(
            (
                "table1.cpu.logical_processors",
                logical_processors,
                "environment-preflight.txt",
                {"pointer": "/recorded_run_environment/host/logical_processors"},
                "count",
                "count",
                {},
            )
        )
    if isinstance(storage_capacity, (int, float)):
        embedded_numeric.append(
            (
                "table1.storage.capacity_gib",
                storage_capacity / (1024.0**3),
                "environment-preflight.txt",
                {"pointer": "/recorded_run_environment/host/storage_capacity_bytes"},
                "bytes",
                "GiB",
                {"divisor": 1073741824},
            )
        )
    if isinstance(sandbox_limits, Mapping):
        limit_units = {
            "vcpus": "count",
            "cpu_count": "count",
            "memory_bytes": "bytes",
            "pids": "count",
            "pids_limit": "count",
        }
        for field, unit in sorted(limit_units.items()):
            value = sandbox_limits.get(field)
            if isinstance(value, (int, float)):
                output_unit = "MiB" if unit == "bytes" else unit
                converted = value / MIB if unit == "bytes" else value
                embedded_numeric.append(
                    (
                        f"table1.sandbox_limits.{field}",
                        converted,
                        "environment-preflight.txt",
                        {"pointer": f"/sandbox_limits/{field}"},
                        unit,
                        output_unit,
                        {"divisor": 1048576} if unit == "bytes" else {},
                    )
                )
    for (
        evidence_id,
        value,
        source,
        selector,
        input_unit,
        output_unit,
        parameters,
    ) in embedded_numeric:
        evidence.add(
            evidence_id,
            value,
            source_file=source,
            selector=selector,
            input_unit=input_unit,
            output_unit=output_unit,
            aggregation="identity",
            parameters=parameters,
        )

    rows: list[list[str]] = []
    machine_fields: list[dict[str, Any]] = []
    for name, value, source, selector, unit in fields:
        displayed = "unavailable" if value is None else str(value)
        if unit == "bytes" and isinstance(value, (int, float)):
            evidence_id = "table1." + name.lower().replace(" ", "_").replace("/", "_")
            if name == "Memory":
                evidence.add(
                    evidence_id + "_bytes",
                    value,
                    source_file=source,
                    selector=selector,
                    input_unit="bytes",
                    output_unit="bytes",
                    aggregation="identity",
                )
                displayed = f"{int(value):,} bytes"
            else:
                mib = float(value) / MIB
                evidence.add(
                    evidence_id,
                    mib,
                    source_file=source,
                    selector=selector,
                    input_unit="bytes",
                    output_unit="MiB",
                    aggregation="identity",
                    parameters={"divisor": 1048576},
                )
                displayed = f"{_display(mib)} MiB"
        elif unit == "count" and isinstance(value, (int, float)):
            evidence_id = "table1." + name.lower().replace(" ", "_").replace("/", "_")
            evidence.add(
                evidence_id,
                value,
                source_file=source,
                selector=selector,
                input_unit="count",
                output_unit="count",
                aggregation="identity",
            )
        evidence_source = (
            f"{source}#{json.dumps(selector, separators=(',', ':'), sort_keys=True)}"
        )
        rows.append([name, displayed, evidence_source])
        machine_value = value
        if name == "Product commit/tag":
            machine_value = {
                "commit": product_commit,
                "freeze_tag": freeze_tag
                if freeze_tag is not None
                else {
                    "availability": "unavailable",
                    "reason": "legacy pre-freeze exploratory archive",
                    "required_final_tag": "paper-v1-freeze",
                },
            }
        machine_fields.append(
            {
                "field": name,
                "value": machine_value,
                "display": displayed,
                "source": source,
                "selector": selector,
            }
        )
    return (
        _markdown_table(
            ["Field", "Archived value", "Evidence source"],
            rows,
            banner,
            "EXP1 environment and workload",
        ),
        {"fields": machine_fields},
    )


def _performance_row(
    key: tuple[str, Any, int],
    context: Mapping[str, Any],
    evidence: Evidence,
    table_id: str,
) -> tuple[list[str], dict[str, Any]]:
    cell = context["cells"][key]
    measured = context["expected"]["measured"]
    report_cell = cell["report_cell"]
    latency = _raw_values(
        _metric(report_cell, "batch_makespan_ns"), measured, allow_unavailable=False
    )
    throughput = _raw_values(
        _metric(report_cell, "throughput_ops_s"), measured, allow_unavailable=False
    )
    assert latency is not None and throughput is not None
    cell_id = cell["cell_id"]
    label = _label_for_key(key)
    concurrency = key[2]
    selector_latency = _archive_selector(
        "report.json", cell_id=cell_id, metric_id="batch_makespan_ns"
    )
    selector_throughput = _archive_selector(
        "report.json", cell_id=cell_id, metric_id="throughput_ops_s"
    )
    slug = f"{table_id}.{key[0]}.{str(key[1]).lower()}.c{concurrency}"
    values: dict[str, float | int] = {"samples": measured}
    evidence.add(
        slug + ".samples",
        measured,
        source_file="report.json",
        selector={**selector_latency, "field": "available_n"},
        input_unit="count",
        output_unit="count",
        aggregation="identity",
    )
    for label_id, probability in (("p50_ms", 0.50), ("p95_ms", 0.95), ("p99_ms", 0.99)):
        derived = _convert(
            _quantile(latency, probability), "nanoseconds", "milliseconds"
        )
        values[label_id] = evidence.add(
            slug + "." + label_id,
            derived,
            source_file="report.json",
            selector=selector_latency,
            input_unit="nanoseconds",
            output_unit="milliseconds",
            aggregation=f"linear_quantile_p{int(probability * 100)}",
            parameters={
                "probability": probability,
                "position": "(n-1)*q",
                "interpolation": "linear",
                "unit_divisor": 1000000,
            },
        )
    throughput_value = _mean(throughput)
    values["throughput_ops_s"] = evidence.add(
        slug + ".throughput_ops_s",
        throughput_value,
        source_file="report.json",
        selector=selector_throughput,
        input_unit="operations_per_second",
        output_unit="operations_per_second",
        aggregation="arithmetic_mean",
        parameters={"denominator": measured},
    )
    rendered = [
        label,
        str(concurrency),
        str(measured),
        _display(float(values["p50_ms"])),
        _display(float(values["p95_ms"])),
        _display(float(values["p99_ms"])),
        _display(float(values["throughput_ops_s"]), digits=2),
    ]
    return rendered, {
        "cell_id": cell_id,
        "key": list(key),
        "operation": label,
        "concurrency": concurrency,
        "values": values,
    }


def _performance_table(
    keys: Sequence[tuple[str, Any, int]],
    context: Mapping[str, Any],
    evidence: Evidence,
    banner: str,
    table_id: str,
    title: str,
) -> tuple[bytes, dict[str, Any]]:
    rows: list[list[str]] = []
    machine_rows: list[dict[str, Any]] = []
    for key in keys:
        rendered, machine = _performance_row(key, context, evidence, table_id)
        if table_id == "table2":
            stage = {
                ("create_sandbox", None, 1): "Sandbox create + base mount",
                ("create_workspace", None, 1): "Session create to ready",
                ("create_workspace", None, 5): "Session create to ready",
                ("exec_command", "noop", 1): "First no-op command",
            }[key]
            rendered = [stage, *rendered[1:]]
            machine["stage"] = stage
        elif table_id == "table3":
            operation, case, size = {
                ("exec_command", "noop", 1): ("`exec_command`", "no-op", "--"),
                ("exec_command", "noop", 5): ("`exec_command`", "no-op", "--"),
                ("exec_command", "fixture_read", 1): (
                    "`exec_command`",
                    "fixture read",
                    "4 KiB",
                ),
                ("exec_command", "fixture_read", 5): (
                    "`exec_command`",
                    "fixture read",
                    "4 KiB",
                ),
                ("file_read", 4096, 1): ("Read", "snapshot", "4 KiB"),
                ("file_read", 4096, 5): ("Read", "snapshot", "4 KiB"),
                ("file_read", 262144, 1): ("Read", "snapshot", "256 KiB"),
                ("file_read", 262144, 5): ("Read", "snapshot", "256 KiB"),
                ("file_write", 4096, 1): ("Write", "session-local", "4 KiB"),
                ("file_write", 4096, 5): ("Write", "session-local", "4 KiB"),
                ("file_write", 262144, 1): (
                    "Write",
                    "session-local",
                    "256 KiB",
                ),
                ("file_write", 262144, 5): (
                    "Write",
                    "session-local",
                    "256 KiB",
                ),
                ("file_edit", 4096, 1): ("Edit", "one replacement", "4 KiB"),
                ("file_edit", 4096, 5): ("Edit", "one replacement", "4 KiB"),
                ("file_edit", 262144, 1): (
                    "Edit",
                    "one replacement",
                    "256 KiB",
                ),
                ("file_edit", 262144, 5): (
                    "Edit",
                    "one replacement",
                    "256 KiB",
                ),
            }[key]
            rendered = [operation, case, size, *rendered[1:]]
            machine.update(
                operation_label=operation,
                case=case,
                payload_or_file_size=size,
            )
        rows.append(rendered)
        machine_rows.append(machine)
    if table_id == "table2":
        headers = [
            "Stage",
            "Concurrent creates",
            "Samples",
            "p50 (ms)",
            "p95 (ms)",
            "p99 (ms)",
            "Throughput (ready/s)",
        ]
    else:
        headers = [
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
    return _markdown_table(headers, rows, banner, title), {"rows": machine_rows}


def _resource_table(
    context: Mapping[str, Any],
    evidence: Evidence,
    banner: str,
) -> tuple[bytes, dict[str, Any]]:
    headers = ["Operation/case", "Concurrency"] + [
        column[1] for column in RESOURCE_COLUMNS
    ]
    rows: list[list[str]] = []
    machine_rows: list[dict[str, Any]] = []
    measured = context["expected"]["measured"]
    for key in RESOURCE_KEYS:
        cell = context["cells"][key]
        cell_id = cell["cell_id"]
        operation_case = {
            ("create_workspace", None, 1): "Workspace create, 100 MiB/depth 100",
            ("create_workspace", None, 5): "Workspace create, 100 MiB/depth 100",
            ("exec_command", "noop", 1): "`exec_command`, no-op",
            ("exec_command", "noop", 5): "`exec_command`, no-op",
            ("file_read", 262144, 5): "Read, 256 KiB",
            ("file_write", 262144, 5): "Write, 256 KiB",
            ("file_edit", 262144, 5): "Edit, 256 KiB",
        }[key]
        rendered = [operation_case, str(key[2])]
        machine_values: dict[str, Any] = {}
        for metric_id, _, input_unit, output_unit, aggregate in RESOURCE_COLUMNS:
            metric = _metric(cell["report_cell"], metric_id)
            identity_unit = _nested(metric, "identity", "unit")
            _require(
                identity_unit == input_unit, f"{key}/{metric_id}: resource unit drift"
            )
            values = _raw_values(metric, measured, allow_unavailable=True)
            unavailable_reason: str | None = None
            if metric_id == "upperdir_bytes" and (
                _nested(metric, "identity", "aggregation") != "delta"
                or _nested(metric, "identity", "scope") != "workspace"
                or _nested(metric, "identity", "source")
                != (
                    "product_observability.snapshot.workspaces.disk_allocated_bytes.sum"
                )
            ):
                values = None
                unavailable_reason = (
                    "archived metric is not the product-reported before/after "
                    "live-workspace upperdir allocated-space delta"
                )
            if values is None:
                if unavailable_reason is None:
                    reasons = _nested(metric, "unavailable", "reasons")
                    if isinstance(reasons, Mapping) and reasons:
                        unavailable_reason = "; ".join(
                            sorted(str(reason) for reason in reasons)
                        )
                    else:
                        unavailable_reason = "incomplete archived measured samples"
                rendered.append("unavailable")
                machine_values[metric_id] = {
                    "value": None,
                    "display": "unavailable",
                    "reason": unavailable_reason,
                }
                continue
            aggregate_value = max(values) if aggregate == "max" else _mean(values)
            converted = _convert(aggregate_value, input_unit, output_unit)
            slug = f"table4.{key[0]}.{str(key[1]).lower()}.c{key[2]}.{metric_id}"
            evidence.add(
                slug,
                converted,
                source_file="report.json",
                selector=_archive_selector(
                    "report.json", cell_id=cell_id, metric_id=metric_id
                ),
                input_unit=input_unit,
                output_unit=output_unit,
                aggregation="maximum" if aggregate == "max" else "arithmetic_mean",
                parameters={
                    "denominator": measured if aggregate == "mean" else None,
                    "unit_divisor": 1048576 if output_unit == "MiB" else 1000000,
                },
            )
            display = _display(converted)
            rendered.append(display)
            machine_values[metric_id] = {"value": converted, "display": display}
        rows.append(rendered)
        machine_rows.append(
            {
                "cell_id": cell_id,
                "key": list(key),
                "operation": operation_case,
                "concurrency": key[2],
                "values": machine_values,
            }
        )
    return _markdown_table(headers, rows, banner, "EXP1 resource observations"), {
        "rows": machine_rows
    }


def _build_outputs(context: Mapping[str, Any], generator_sha: str) -> dict[str, bytes]:
    disposition = context["disposition"]
    eligibility = context["expected"]["output_eligibility"]
    banner = _eligibility_banner(disposition)
    evidence = Evidence(context["source_hashes"], eligibility)
    table1, machine1 = _table_one(context, evidence, banner)
    table2, machine2 = _performance_table(
        STARTUP_KEYS,
        context,
        evidence,
        banner,
        "table2",
        "EXP1 startup and workspace creation",
    )
    table3, machine3 = _performance_table(
        PUBLIC_KEYS, context, evidence, banner, "table3", "EXP1 public CLI operations"
    )
    table4, machine4 = _resource_table(context, evidence, banner)
    tables = {
        "archive": {
            "content_tree_sha256": context["manifest"]["content_tree_sha256"],
            "disposition": disposition,
            "run_id": context["campaign"]["run_id"],
        },
        "eligibility": eligibility,
        "generator_schema_version": SCHEMA_VERSION,
        "tables": {
            "environment": machine1,
            "startup": machine2,
            "public_cli_operations": machine3,
            "resources": machine4,
        },
    }
    outputs = {
        "table-1-environment.md": table1,
        "table-2-startup.md": table2,
        "table-3-cli-operations.md": table3,
        "table-4-resources.md": table4,
        "tables.json": _json_bytes(tables),
        "numeric-provenance.csv": evidence.csv_bytes(),
        "numeric-evidence.json": _json_bytes(evidence.registry()),
    }
    log_lines = [
        "EXP1 deterministic table generation",
        f"generator_schema_version={SCHEMA_VERSION}",
        f"generator_sha256={generator_sha}",
        f"archive_run_id={context['campaign']['run_id']}",
        f"archive_disposition={disposition}",
        f"archive_eligibility={eligibility}",
        f"archive_content_tree_sha256={context['manifest']['content_tree_sha256']}",
        "archive_inventory_verified=true",
        "semantic_identity_verified=true",
        "correctness_verified=true",
        "command=python experiments/analysis/scripts/generate_exp1_tables.py --archive <ARCHIVE> --output <OUTPUT>",
        "output_path_embedded=false",
        "wall_clock_embedded=false",
    ]
    outputs["generation-log.txt"] = ("\n".join(log_lines) + "\n").encode("utf-8")
    manifest_files = [
        {
            "bytes": len(data),
            "path": relative,
            "sha256": _sha256_bytes(data),
        }
        for relative, data in sorted(outputs.items())
    ]
    output_manifest = {
        "archive_content_tree_sha256": context["manifest"]["content_tree_sha256"],
        "archive_disposition": disposition,
        "archive_run_id": context["campaign"]["run_id"],
        "eligibility": eligibility,
        "files": manifest_files,
        "generator_schema_version": SCHEMA_VERSION,
        "generator_sha256": generator_sha,
        "schema_version": 1,
    }
    outputs["output-manifest.json"] = _json_bytes(output_manifest)
    return outputs


def generate(archive: Path, output: Path) -> dict[str, Any]:
    archive = archive.resolve()
    output = output.resolve()
    _require(archive.is_dir(), f"archive directory does not exist: {archive}")
    _require(
        output != archive and archive not in output.parents,
        "output must be outside the immutable archive",
    )
    _require(not output.exists(), f"output directory already exists: {output}")
    context = _validate_archive(archive)
    generator_sha = _sha256_file(Path(__file__).resolve())
    outputs = _build_outputs(context, generator_sha)
    # Detect a mutation that raced semantic derivation before writing any output.
    _verify_archive_inventory(archive, context["manifest"])
    output.mkdir(parents=True, exist_ok=False)
    for relative, data in sorted(outputs.items()):
        destination = output / relative
        with destination.open("xb") as stream:
            stream.write(data)
    return {
        "archive_run_id": context["campaign"]["run_id"],
        "disposition": context["disposition"],
        "eligibility": context["expected"]["output_eligibility"],
        "files": sorted(outputs),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", required=True, type=Path, help="immutable EXP1 archive directory"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new output directory outside the archive",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = generate(args.archive, args.output)
    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
