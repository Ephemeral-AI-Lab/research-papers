from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from .artifacts import ARTIFACT_SPECS, PRODUCER_ARTIFACT_IDS, ArtifactId
from .fixtures import workspace_fixture_identity
from .models import BenchmarkReportV4
from .resource_sampling import resource_metric_source
from .statistics import (
    bootstrap_median_difference_interval,
    bootstrap_pearson_interval,
    pearson,
    summarize,
)


_FAMILY_LABELS = {
    "command": "Command",
    "files": "File Operations",
    "workspace_lifecycle": "Workspace Lifecycle",
    "layer_stack": "LayerStack",
}
_DERIVED = {
    "batch_makespan_ns": ("Batch makespan", "Barrier release until the last issued product request reaches a terminal response.", "nanoseconds", "mean", "lower_is_preferred", "runner_monotonic_batch_barrier"),
    "request_latency_ns": ("Request latency", "One issued product request from send until its final response is decoded.", "nanoseconds", "mean", "lower_is_preferred", "raw_asyncio_socket_monotonic"),
    "throughput_ops_s": ("Throughput", "Successful issued product requests divided by batch makespan seconds.", "operations_per_second", "mean", "higher_is_preferred", "successful_requests_per_batch_makespan"),
    "setup_ns": ("Setup", "Harness setup time outside the primary operation window.", "nanoseconds", "mean", "descriptive_only", "runner_monotonic_lifecycle"),
    "verify_ns": ("Verification", "Correctness verification time outside the primary operation window.", "nanoseconds", "mean", "descriptive_only", "runner_monotonic_lifecycle"),
    "teardown_ns": ("Teardown", "Owned cleanup and baseline verification time outside the primary operation window.", "nanoseconds", "mean", "descriptive_only", "runner_monotonic_lifecycle"),
}
_RESOURCE_TEXT = {
    "runner_rss_bytes": ("Runner RSS", "Maximum resident bytes of the benchmark runner."),
    "daemon_rss_bytes": ("Daemon RSS", "Maximum resident bytes of the sandbox daemon."),
    "daemon_cpu_time_ns": ("Daemon CPU time", "Daemon cumulative CPU-time delta."),
    "sandbox_memory_current_bytes": ("Sandbox memory current", "Maximum sampled sandbox cgroup memory.current bytes."),
    "sandbox_memory_peak_bytes": ("Sandbox memory peak", "Sandbox cgroup memory.peak, or an explicitly sampled peak when unavailable."),
    "sandbox_cpu_time_ns": ("Sandbox CPU time", "Sandbox cumulative cgroup CPU-use counter delta over the trial window."),
    "sandbox_block_read_bytes": ("Sandbox block reads", "Sandbox cumulative block-read byte counter delta over the trial window."),
    "sandbox_block_write_bytes": ("Sandbox block writes", "Sandbox cumulative block-write byte counter delta over the trial window."),
    "workspace_logical_bytes": ("Workspace logical bytes", "Maximum logical file bytes in the named workspace scope."),
    "workspace_allocated_bytes": ("Workspace allocated bytes", "Maximum allocated filesystem bytes in the named workspace scope."),
    "workspace_file_count": ("Workspace files", "Maximum file count in the workspace scope."),
    "layerstack_bytes": ("LayerStack bytes", "Maximum allocated LayerStack storage reported by the product."),
    "upperdir_bytes": ("Upperdir bytes", "Maximum allocated bytes in live workspace upperdirs."),
    "host_free_bytes": ("Host free space", "Minimum free bytes on the benchmark volume."),
}
def build_report(
    *, run_id: str, state: str, plan: dict[str, Any], definitions: dict[str, Any],
    definition_snapshot_sha256: str,
    environment: dict[str, Any], observations: list[dict[str, Any]],
    started_at: str, ended_at: str,
) -> BenchmarkReportV4:
    records_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for envelope in observations:
        record = envelope["record"]
        cell_id = record["data"].get("cell_id")
        if isinstance(cell_id, str):
            records_by_cell[cell_id].append(record)
    operation_defs = {item["id"]: item for item in definitions["operations"]}
    metric_defs = {item["id"]: item for item in definitions["metrics"]}
    cells = [
        _cell_report(cell, records_by_cell[cell["cell_id"]], plan, operation_defs[cell["operation_id"]], metric_defs)
        for cell in plan["cells"]
    ]
    measured = sum(cell["counts"]["measured_attempted"] for cell in cells)
    successful = sum(cell["counts"]["successful"] for cell in cells)
    check_failure = any(check["failed"] for cell in cells for check in cell["checks"])
    missing_checks = any(
        check["attempted"] != cell["counts"]["measured_attempted"]
        for cell in cells for check in cell["checks"]
    )
    proved = measured > 0 and successful == measured and not check_failure and not missing_checks
    correctness = "pass" if state == "completed" and proved else (
        "fail" if state == "failed" or (state == "completed" and not proved) else "pending"
    )
    design = {
        "test_combinations": plan["estimates"]["cell_count"],
        "trial_batches": plan["estimates"]["trial_batch_count"],
        "issued_product_requests": plan["estimates"]["issued_operation_request_count"],
    }
    methods = _methods(plan, definitions, environment, design)
    summary = [
        {
            "row_id": f'{cell["cell_id"]}:{metric["identity"]["id"]}',
            "operation_id": cell["operation_id"], "cell_id": cell["cell_id"],
            "metric_id": metric["identity"]["id"], "unit": metric["identity"]["unit"],
            "successful_n": metric["available_n"], "failed_n": metric["failed_n"],
            "unavailable_n": metric["unavailable"]["count"],
            "median": metric["statistics"]["median"],
            "confidence_interval": metric["statistics"]["median_confidence_interval"],
            "interval_omission_reason": metric["statistics"]["confidence_interval_omission"],
            "direction": metric["identity"]["direction"],
        }
        for cell in cells for metric in cell["metrics"]
    ]
    warnings = []
    if successful == 0:
        warnings.append({"code": "no_reportable_trials", "message": "No measured trial completed all correctness and cleanup gates."})
    if missing_checks:
        warnings.append({"code": "missing_correctness_observations", "message": "One or more registered checks lacks a measured-trial verdict."})
    treatment = environment["treatment"]
    return BenchmarkReportV4.model_validate({
        "schema_version": 4, "report_derivation_revision": 3, "run_id": run_id,
        "state": state, "provisional": state not in {"completed", "failed", "cancelled"},
        "correctness_verdict": correctness, "design_counts": design,
        "research_question": f'How does {plan["canonical_plan"]["name"]} behave under its declared factors?',
        "plan_hash": plan["plan_hash"], "source_commit": treatment["source_commit"],
        "source_dirty": treatment["source_dirty"], "environment_fingerprint": _sha_json(environment),
        "definition_snapshot_version": definitions["schema_version"],
        "definition_snapshot_sha256": definition_snapshot_sha256, "started_at": started_at,
        "ended_at": ended_at, "summary": summary,
        "factor_studies": _factor_studies(cells, plan), "cells": cells, "methods": methods,
        "limitations": ["Resource metrics unavailable from the fixed product boundary are represented explicitly."],
        "warnings": warnings,
    })


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cell_report(
    cell: dict[str, Any], records: list[dict[str, Any]], plan: dict[str, Any],
    operation_def: dict[str, Any], metric_defs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    trials = [record["data"] for record in records if record["record"] == "trial"]
    measured = {item["trial_id"]: item for item in trials if not item["warmup"]}
    eligible = {trial_id for trial_id, item in measured.items() if item.get("reportable") is True}
    requests = [record["data"] for record in records if record["record"] == "request" and not record["data"]["warmup"]]
    resources = [record["data"] for record in records if record["record"] == "resource"]
    phases = [record["data"] for record in records if record["record"] == "phase"]
    checks = [record["data"] for record in records if record["record"] == "check" and record["data"]["trial_id"] in measured]
    operation_evidence = [record["data"] for record in records if record["record"] == "operation" and record["data"]["trial_id"] in measured]
    metrics = _derived_metrics(cell["cell_id"], measured, eligible, requests, plan)
    metrics.extend(_resource_metrics(cell["cell_id"], measured, eligible, resources, metric_defs, plan))
    metrics.sort(key=lambda item: item["identity"]["id"])
    status_counts = Counter(item["status"] for item in measured.values())
    factors = _factors(cell, plan, operation_def)
    phase_reports = _phase_reports(cell["cell_id"], measured, eligible, phases, operation_def, plan)
    timelines = _timelines(
        measured, eligible, requests, phases, resources, metric_defs, operation_def
    )
    correlation = _correlation(cell["cell_id"], measured, eligible, metrics, plan)
    return {
        "cell_id": cell["cell_id"], "family_id": cell["family_id"],
        "family_label": _FAMILY_LABELS[cell["family_id"]],
        "operation_id": cell["operation_id"], "operation_label": operation_def["label"],
        "comparison_key": cell["comparison_key"],
        "design_counts": {"test_combinations": 1, "trial_batches": len(trials), "issued_product_requests": sum(item.get("request_count", 0) for item in trials)},
        "factors": factors,
        "counts": {
            "total_attempted": len(trials), "warmup": sum(item["warmup"] for item in trials),
            "measured_attempted": len(measured), "successful": len(eligible),
            "product_failed": status_counts["product_failed"],
            "correctness_failed": status_counts["correctness_failed"],
            "infrastructure_failed": sum(
                bool(item.get("infrastructure_failed"))
                or item["status"] == "cancelled"
                for item in measured.values()
            ),
            "cleanup_invalid": status_counts["cleanup_invalid"],
            "missing_primary_latency": sum(item.get("latency_ns") is None for item in measured.values()),
        },
        "metrics": metrics,
        "checks": [_check_summary(definition, checks) for definition in operation_def["checks"]],
        "phases": phase_reports, "timelines": timelines,
        "check_evidence": _check_evidence(operation_def, checks),
        "operation_evidence": [
            {"trial_id": item["trial_id"], "request_id": item.get("request_id"), "evidence": item["evidence"]}
            for item in operation_evidence
        ],
        "cpu_latency_correlation": correlation,
    }


def _derived_metrics(
    cell_id: str, measured: dict[str, dict[str, Any]], eligible: set[str],
    requests: list[dict[str, Any]], plan: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = []
    request_attempts = sum(item.get("request_count", 0) for item in measured.values())
    request_points = [
        (item["trial_id"], item["request_id"], item["latency_ns"], None, item["latency_ns"])
        for item in requests if item["trial_id"] in eligible and item["status"] == "success"
    ]
    metrics.append(_metric(_derived_identity("request_latency_ns"), request_attempts, request_attempts - len(request_points), request_points, cell_id, plan))
    for metric_id, field in (("batch_makespan_ns", "latency_ns"), ("setup_ns", "setup_ns"), ("verify_ns", "verify_ns"), ("teardown_ns", "teardown_ns")):
        points = [(trial_id, None, item.get(field), None, item.get(field)) for trial_id, item in measured.items() if trial_id in eligible and item.get(field) is not None]
        metrics.append(_metric(_derived_identity(metric_id), len(measured), len(measured) - len(eligible), points, cell_id, plan))
    throughput = []
    for trial_id, item in measured.items():
        latency = item.get("latency_ns")
        if trial_id in eligible and isinstance(latency, int) and latency > 0:
            throughput.append((trial_id, None, item["request_count"] * 1_000_000_000 / latency, None, None))
    metrics.append(_metric(_derived_identity("throughput_ops_s"), len(measured), len(measured) - len(eligible), throughput, cell_id, plan))
    return metrics


def _resource_metrics(
    cell_id: str, measured: dict[str, dict[str, Any]], eligible: set[str],
    resources: list[dict[str, Any]], definitions: dict[str, dict[str, Any]],
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in resources:
        reading = item["reading"]
        if item["trial_id"] in measured and reading["metric_id"] in definitions:
            grouped[(item["trial_id"], reading["metric_id"])].append(reading)
    output = []
    for metric_id, definition in definitions.items():
        points: list[tuple[str, str | None, float | None, str | None, int | None]] = []
        for trial_id in measured:
            if trial_id not in eligible:
                continue
            readings = sorted(grouped[(trial_id, metric_id)], key=lambda item: item["monotonic_offset_ns"])
            value, reason = _aggregate_resource(readings, definition["aggregation"])
            points.append((trial_id, None, value, reason, int(value) if value is not None and value.is_integer() else None))
        identity = _resource_identity(definition, grouped)
        output.append(_metric(identity, len(measured), len(measured) - len(eligible), points, cell_id, plan))
    return output


def _aggregate_resource(readings: list[dict[str, Any]], aggregation: str) -> tuple[float | None, str | None]:
    if not readings:
        return None, "resource observation was not emitted"
    available = [item for item in readings if item["value"]["availability"] == "available"]
    if aggregation == "delta":
        if len(available) < 2 or available[0] is not readings[0] or available[-1] is not readings[-1]:
            return None, _unavailable_reason(readings, "counter window lacks available boundary samples")
        first = float(available[0]["value"]["value"])
        last = float(available[-1]["value"]["value"])
        if last < first:
            return None, "monotonic counter reset during the trial window"
        return last - first, None
    if not available:
        return None, _unavailable_reason(readings, "resource was unavailable")
    values = [float(item["value"]["value"]) for item in available]
    return (min(values) if aggregation == "minimum" else max(values)), None


def _unavailable_reason(readings: list[dict[str, Any]], fallback: str) -> str:
    for item in readings:
        value = item["value"]
        if value["availability"] == "unavailable":
            return f'{value.get("source", item["source"])}:{value.get("reason", fallback)}'
    return fallback


def _metric(
    identity: dict[str, Any], attempted: int, failed: int,
    points: list[tuple[str, str | None, float | int | None, str | None, int | None]],
    cell_id: str, plan: dict[str, Any],
) -> dict[str, Any]:
    available = [item for item in points if item[2] is not None]
    values = [float(item[2]) for item in available]
    statistics = summarize(values, _seed(plan["canonical_plan"]["seed"], cell_id, identity["id"]))
    outliers = set(statistics.outlier_indices)
    reasons = Counter(item[3] for item in points if item[2] is None and item[3])
    return {
        "identity": identity, "attempted_n": attempted, "failed_n": failed,
        "available_n": len(available), "unavailable": {"count": sum(reasons.values()), "reasons": dict(reasons)},
        "statistics": statistics.model_dump(mode="json"),
        "raw_points": [
            {"trial_id": item[0], "request_id": item[1], "value": float(item[2]), "raw_integer_value": item[4], "outlier": index in outliers}
            for index, item in enumerate(available)
        ],
    }


def _derived_identity(metric_id: str) -> dict[str, Any]:
    label, help_text, unit, aggregation, direction, source = _DERIVED[metric_id]
    return {"id": metric_id, "label": label, "help": help_text, "semantic_revision": 1, "unit": unit, "scope": "operation", "kind": "gauge", "availability": "explicit_unavailable", "aggregation": aggregation, "direction": direction, "source": source, "ratio_scale": True, "report_derivation_revision": 3}


def _resource_identity(definition: dict[str, Any], grouped: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any]:
    metric_id = definition["id"]
    label, help_text = _RESOURCE_TEXT[metric_id]
    source = next((readings[0]["source"] for (trial, identifier), readings in grouped.items() if identifier == metric_id and readings), resource_metric_source(metric_id))
    return {**definition, "label": label, "help": help_text, "source": source, "ratio_scale": True, "report_derivation_revision": 3}


def _check_summary(definition: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    observed = [item for item in checks if item["check_id"] == definition["id"]]
    return {"id": definition["id"], "label": definition["label"], "help": definition["help"], "semantic_revision": definition["semantic_revision"], "attempted": len(observed), "passed": sum(item["passed"] for item in observed), "failed": sum(not item["passed"] for item in observed)}


def _check_evidence(operation: dict[str, Any], checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions = {item["id"]: item for item in operation["checks"]}
    output = []
    for item in checks:
        definition = definitions[item["check_id"]]
        output.append({
            "id": item["check_id"], "label": definition["label"], "help": definition["help"],
            "semantic_revision": item["semantic_revision"], "trial_id": item["trial_id"],
            "request_id": item["request_id"], "verdict": "pass" if item["passed"] else "fail",
            "duration_ns": 0, "evidence": {"items": [{"expected": item["expected"], "actual": item["actual"], "artifact_id": item["artifact_id"]}], "truncated_count": 0, "truncated_sha256": None},
        })
    return output


def _phase_reports(
    cell_id: str, measured: dict[str, dict[str, Any]], eligible: set[str],
    phases: list[dict[str, Any]], operation: dict[str, Any], plan: dict[str, Any],
) -> list[dict[str, Any]]:
    reports = []
    for definition in operation["phases"]:
        observed = [item for item in phases if item["id"] == definition["id"] and item["trial_id"] in eligible]
        if definition["id"] == "workspace_session_remount" and not observed:
            continue
        durations = [float(item["duration_ns"]) for item in observed if item["status"] == "succeeded"]
        reports.append({**definition, "attempted": len(observed), "failed": len(observed) - len(durations), "duration": summarize(durations, _seed(plan["canonical_plan"]["seed"], cell_id, f'phase:{definition["id"]}')).model_dump(mode="json")})
    return reports


def _timelines(
    measured: dict[str, dict[str, Any]], eligible: set[str], requests: list[dict[str, Any]],
    phases: list[dict[str, Any]], resources: list[dict[str, Any]], metric_defs: dict[str, dict[str, Any]],
    operation: dict[str, Any],
) -> list[dict[str, Any]]:
    timelines = []
    phase_defs = {item["id"]: item for item in operation["phases"]}
    for trial_id in measured:
        if trial_id not in eligible:
            continue
        trial_requests = [item for item in requests if item["trial_id"] == trial_id]
        trial_phases = [item for item in phases if item["trial_id"] == trial_id]
        trial_resources = [item for item in resources if item["trial_id"] == trial_id]
        offsets = [item["start_offset_ns"] for item in trial_requests] + [item["reading"]["monotonic_offset_ns"] for item in trial_resources] + [item["start_offset_ns"] for item in trial_phases]
        ends = [item["start_offset_ns"] + item["latency_ns"] for item in trial_requests] + [item["start_offset_ns"] + item["duration_ns"] for item in trial_phases] + [item["reading"]["monotonic_offset_ns"] for item in trial_resources]
        series = []
        by_metric: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in trial_resources:
            by_metric[item["reading"]["metric_id"]].append(item)
        for metric_id, items in sorted(by_metric.items()):
            definition = metric_defs[metric_id]
            series.append({"identity": _resource_identity(definition, {(trial_id, metric_id): [item["reading"] for item in items]}), "request_id": None, "points": [{"monotonic_offset_ns": item["reading"]["monotonic_offset_ns"], "sampled": item["reading"].get("sampled", False), "value": item["reading"]["value"]} for item in items]})
        timelines.append({
            "trial_id": trial_id, "domain_start_ns": min(offsets, default=0), "domain_end_ns": max(ends, default=0),
            "operation_window": {"start_offset_ns": min((item["start_offset_ns"] for item in trial_requests), default=0), "duration_ns": measured[trial_id]["latency_ns"] or 0},
            "request_spans": [{"request_id": item["request_id"], "start_offset_ns": item["start_offset_ns"], "duration_ns": item["latency_ns"], "succeeded": item["status"] == "success", "status": "succeeded" if item["status"] == "success" else item["status"]} for item in trial_requests],
            "phase_spans": [{key: item[key] for key in ("id", "semantic_revision", "request_id", "start_offset_ns", "duration_ns", "status")} | {"label": phase_defs[item["id"]]["label"], "help": phase_defs[item["id"]]["help"]} for item in trial_phases],
            "series": series,
        })
    return timelines


def _correlation(cell_id: str, measured: dict[str, dict[str, Any]], eligible: set[str], metrics: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    latency = {item["trial_id"]: item["value"] for metric in metrics if metric["identity"]["id"] == "batch_makespan_ns" for item in metric["raw_points"]}
    cpu = {item["trial_id"]: item["value"] for metric in metrics if metric["identity"]["id"] == "sandbox_cpu_time_ns" for item in metric["raw_points"]}
    points = [
        {
            "trial_id": trial_id,
            "operation_latency_ns": latency[trial_id],
            "sandbox_cpu_time_ns": cpu[trial_id],
        }
        for trial_id in eligible
        if trial_id in latency and trial_id in cpu
    ]
    pairs = [(item["operation_latency_ns"], item["sandbox_cpu_time_ns"]) for item in points]
    estimate = bootstrap_pearson_interval(pairs, _seed(plan["canonical_plan"]["seed"], cell_id, "cpu_latency_correlation"))
    return {"semantic_revision": 1, "method": "pearson", "alignment": "eligible_trial_aggregate_by_trial_id", "eligibility": "measured_product_success_checks_pass_cleanup_restored", "latency_metric_id": "batch_makespan_ns", "cpu_metric_id": "sandbox_cpu_time_ns", "support_count": len(points), "coefficient": pearson(pairs), "confidence_interval": estimate.interval.model_dump(mode="json") if estimate.interval else None, "interval_omission": estimate.omission, "points": points, "exclusions": {"ineligible_trial": len(measured) - len(eligible), "missing_latency": sum(trial_id in eligible and trial_id not in latency for trial_id in measured), "missing_cpu": sum(trial_id in eligible and trial_id not in cpu for trial_id in measured), "unavailable_cpu": sum(trial_id in eligible and trial_id not in cpu for trial_id in measured)}}


def _factors(cell: dict[str, Any], plan: dict[str, Any], operation: dict[str, Any]) -> list[dict[str, Any]]:
    configured = next(item["configuration"]["factors"] for item in plan["canonical_plan"]["operations"] if item["operation"] == cell["operation_id"])
    definitions = {item["id"]: item for item in operation["factors"]}
    aliases = {"read_source": "source", "mutation_destination": "destination"}
    output = []
    for public_id, definition in definitions.items():
        internal = aliases.get(public_id, public_id)
        if internal not in configured:
            continue
        config = configured[internal]
        value = cell["operation"]["cell"][internal]
        output.append({"id": public_id, "label": definition["label"], "help": definition["help"], "role": config["role"], "unit": definition["unit"], "value": _factor_value(value), "control": _factor_value(config["control"]) if config["control"] is not None else None})
    return output


def _factor_studies(cells: list[dict[str, Any]], plan: dict[str, Any]) -> list[dict[str, Any]]:
    studies = []
    for operation_id in dict.fromkeys(cell["operation_id"] for cell in cells):
        members = [cell for cell in cells if cell["operation_id"] == operation_id]
        varied = [item["id"] for item in members[0]["factors"] if item["role"] == "varied"]
        controlled = [item["id"] for item in members[0]["factors"] if item["role"] == "controlled"]
        layout = ({"kind": "single_cell"} if not varied else {"kind": "trend", "factor_id": varied[0]} if len(varied) == 1 else {"kind": "matrix", "row_factor_id": varied[0], "column_factor_id": varied[1]} if len(varied) == 2 else {"kind": "small_multiples", "factor_ids": varied})
        projections = []
        for cell in members:
            metric = next(item for item in cell["metrics"] if item["identity"]["id"] == "batch_makespan_ns")
            projections.append({"cell_id": cell["cell_id"], "factors": cell["factors"], "successful_n": metric["available_n"], "failed_n": metric["failed_n"], "median": metric["statistics"]["median"], "confidence_interval": metric["statistics"]["median_confidence_interval"], "interval_omission_reason": metric["statistics"]["confidence_interval_omission"], "raw_points": metric["raw_points"]})
        studies.append({"operation_id": operation_id, "operation_label": members[0]["operation_label"], "metric": next(item for item in members[0]["metrics"] if item["identity"]["id"] == "batch_makespan_ns")["identity"], "layout": layout, "varied_factor_ids": varied, "controlled_factor_ids": controlled, "cells": projections, "control_comparisons": _control_comparisons(projections, varied, plan)})
    return studies


def _control_comparisons(cells: list[dict[str, Any]], varied: list[str], plan: dict[str, Any]) -> list[dict[str, Any]]:
    if not varied:
        return []
    values = lambda cell: {item["id"]: item for item in cell["factors"]}
    controls = [cell for cell in cells if all(values(cell)[identifier]["control"] is not None and values(cell)[identifier]["value"] == values(cell)[identifier]["control"] for identifier in varied)]
    output = []
    for control in controls:
        control_factors = values(control)
        for candidate in cells:
            if candidate is control:
                continue
            candidate_factors = values(candidate)
            if any(control_factors[item]["value"] != candidate_factors[item]["value"] for item in candidate_factors if item not in varied):
                continue
            changed = [item for item in varied if control_factors[item]["value"] != candidate_factors[item]["value"]]
            if not changed:
                continue
            left = [point["value"] for point in control["raw_points"]]
            right = [point["value"] for point in candidate["raw_points"]]
            interval = bootstrap_median_difference_interval(left, right, _seed(plan["canonical_plan"]["seed"], control["cell_id"], candidate["cell_id"]))
            absolute = None if control["median"] is None or candidate["median"] is None else candidate["median"] - control["median"]
            percentage = None if absolute is None or control["median"] == 0 else absolute / control["median"] * 100
            interval_json = interval.model_dump(mode="json") if interval else None
            if interval_json is not None:
                interval_json["method"] = "percentile_bootstrap_median_difference"
            output.append({"comparison_id": _sha_json({"control": control["cell_id"], "candidate": candidate["cell_id"], "changed": changed}), "control_cell_id": control["cell_id"], "candidate_cell_id": candidate["cell_id"], "changed_factor_ids": changed, "control_median": control["median"], "candidate_median": candidate["median"], "absolute_difference": absolute, "percentage_difference": percentage, "median_difference_confidence_interval": interval_json, "interval_omission_reason": None if interval else "insufficient_n"})
    return output


def _methods(plan: dict[str, Any], definitions: dict[str, Any], environment: dict[str, Any], design: dict[str, int]) -> dict[str, Any]:
    selected = {cell["operation_id"] for cell in plan["cells"]}
    operation_defs = {item["id"]: item for item in definitions["operations"]}
    authorities = []
    for operation_id in dict.fromkeys(cell["operation_id"] for cell in plan["cells"]):
        definition = operation_defs[operation_id]
        members = [cell for cell in plan["cells"] if cell["operation_id"] == operation_id]
        authorities.append({"operation_id": operation_id, "family_id": definition["family"], "semantic_revision": definition["semantic_revision"], "factor_schema_revision": definition["factor_schema_revision"], "comparison_projection_revision": 1, "client_cohort": environment["client_cohort"], "product_access": definition["product_access"], "count_semantics": definition["count_semantics"], "cleanup_policy": definition["cleanup"], "resolved_isolation_policies": sorted({cell["comparison_key"]["isolation"] for cell in members}), "request_timeout_ms": sorted({cell["protocol"]["timeout_ms"] for cell in members}), "stabilization_policy": ({"kind": "exact_snapshot_quiet_window", "semantic_revision": 1, "quiet_window_matches": 3, "poll_interval_ms": 100, "timeout_ms": 5000} if operation_id == "squash_layerstack" else {"kind": "not_required", "semantic_revision": 1})})
    checks = [check for operation in definitions["operations"] if operation["id"] in selected for check in operation["checks"]]
    phases = [phase for operation in definitions["operations"] if operation["id"] in selected for phase in operation["phases"]]
    fixture_hashes = {
        item["id"]: workspace_fixture_identity(item, plan["canonical_plan"]["seed"])[1]
        for item in plan.get("selected_workspace_profiles", [])
    }
    artifact_schemas = {
        identifier.value: {
            "schema_name": spec.schema_name,
            "write_version": spec.write_version,
            "read_versions": sorted(spec.read_versions),
        }
        for identifier, spec in ARTIFACT_SPECS.items()
        if identifier in PRODUCER_ARTIFACT_IDS
    }
    return {"schema_version": 4, "report_derivation_revision": 3, "artifact_reader_revision": 3, "plan_schema_version": plan["schema_version"], "plan_seed": plan["canonical_plan"]["seed"], "cell_order": "randomized_blocks", "resource_sample_interval_ms": plan["canonical_plan"]["protocol"]["resource_interval_ms"], "design_counts": design, "fixture_generator_revision": 2, "fixture_hashes": fixture_hashes, "producer": {"package": "ephemeralos-benchmark", "version": "0.1.0"}, "artifact_schemas": artifact_schemas, "operation_authorities": authorities, "metric_revisions": [{"metric_id": item["id"], "semantic_revision": item["semantic_revision"]} for item in sorted(definitions["metrics"], key=lambda item: item["id"])], "derived_metric_revisions": [{"metric_id": item, "semantic_revision": 1} for item in _DERIVED], "check_revisions": [{"check_id": item["id"], "semantic_revision": item["semantic_revision"]} for item in checks], "phase_revisions": [{"phase_id": item["id"], "semantic_revision": item["semantic_revision"]} for item in phases], "environment": environment, "raw_time_unit": "nanoseconds", "monotonic_clock": "time.monotonic_ns", "quantile_interpolation": "Hyndman-Fan Type 7", "confidence_interval": "10,000-resample deterministic percentile bootstrap", "bootstrap_resamples": 10_000, "outlier_policy": "Tukey 1.5 IQR flag only; never excluded", "warmup_policy": "warmups retained but excluded from aggregates", "failure_policy": "only successful, verified, cleanup-valid measured trials are reportable", "resource_policy": "explicit unavailable observations; never zero-filled", "comparison_policy": "versioned scientific compatibility before aggregation"}


def _factor_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"kind": "choice", "value": str(value).lower()}
    if isinstance(value, int):
        return {"kind": "unsigned_integer", "value": value}
    if isinstance(value, float):
        return {"kind": "ratio", "value": value}
    return {"kind": "choice", "value": value}


def _seed(seed: int, left: str, right: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}:{left}:{right}".encode()).digest()[:8], "little")


def _sha_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
