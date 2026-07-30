import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError

from .models import StrictModel
from .reports import RunCorpus
from .statistics import bootstrap_median_difference_interval


COMPARISON_SCHEMA_VERSION = 1
COMPARISON_DERIVATION_REVISION = 3
DEFAULT_PROTOCOL_ID = "same_treatment"
DEFAULT_PROTOCOL_VERSION = 1


class ComparisonError(ValueError):
    pass


class HistoricalComparisonV2(StrictModel):
    schema_version: Literal[1]
    comparison_derivation_revision: Literal[2]
    reference_run_id: str
    candidate_run_id: str
    protocol: dict[str, Any]
    compatible: bool
    descriptive_only: bool
    treatment_differences: list[str]
    typed_treatment_differences: list[dict[str, Any]]
    checks: list[dict[str, Any]]
    matched_cell_ids: list[str]
    matched_cells: list[dict[str, Any]]
    deltas: list[dict[str, Any]]
    performance_verdict: str | None


class ComparisonV3(HistoricalComparisonV2):
    comparison_derivation_revision: Literal[3]
    phase_comparisons: list[dict[str, Any]]


def read_comparison(path: Path) -> HistoricalComparisonV2 | ComparisonV3:
    try:
        value = json.loads(path.read_bytes())
        revision = value.get("comparison_derivation_revision")
        model = HistoricalComparisonV2 if revision == 2 else ComparisonV3
        return model.model_validate(value)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ComparisonError(f"comparison artifact is invalid: {error}") from error


def compare_runs(
    reference: RunCorpus, candidate: RunCorpus, *, descriptive_override: bool = False
) -> ComparisonV3:
    reference_id = reference.manifest["run_id"]
    candidate_id = candidate.manifest["run_id"]
    if reference_id == candidate_id:
        raise ComparisonError("reference and candidate run ids must differ")
    if reference.report is None or candidate.report is None:
        raise ComparisonError("both runs must have report artifacts")

    reference_protocol = _protocol(reference)
    candidate_protocol = _protocol(candidate)
    declarations_compatible = reference_protocol == candidate_protocol
    protocol = {
        "reference": reference_protocol,
        "candidate": candidate_protocol,
        "declarations_compatible": declarations_compatible,
    }
    checks = [
        _check(
            "comparison_declaration",
            "Versioned comparison declaration",
            declarations_compatible,
            "Both runs must use the same declaration source, protocol id, version, and treatment allowlist.",
            "core_invariant",
            True,
        )
    ]
    terminal = (
        reference.manifest["state"] in {"completed", "failed", "cancelled"}
        and candidate.manifest["state"] in {"completed", "failed", "cancelled"}
        and not reference.report.provisional
        and not candidate.report.provisional
    )
    checks.append(
        _check(
            "terminal_reports",
            "Terminal report evidence",
            terminal,
            "Aggregate comparison requires terminal, non-provisional reports.",
            "core_invariant",
            True,
        )
    )

    treatment_differences, typed_differences = _treatment_differences(
        reference, candidate, reference_protocol["treatment_fields"] if declarations_compatible else []
    )
    for difference in typed_differences:
        checks.append(
            _check(
                f"treatment_{difference['field']}",
                f"Treatment field: {difference['field']}",
                difference["declared"],
                "A differing treatment field must be declared by the common comparison protocol.",
                "treatment",
                True,
            )
        )

    report_authority = (
        reference.report.schema_version == candidate.report.schema_version == 4
        and reference.report.report_derivation_revision
        == candidate.report.report_derivation_revision
        == COMPARISON_DERIVATION_REVISION
        and reference.report.definition_snapshot_version
        == candidate.report.definition_snapshot_version
        and reference.report.definition_snapshot_sha256
        == candidate.report.definition_snapshot_sha256
    )
    checks.append(
        _check(
            "report_and_definition_authority",
            "Report and definition authority",
            report_authority,
            "Report derivation and immutable definition snapshots must match.",
            "core_invariant",
            True,
        )
    )

    pairs, duplicate = _match_cells(reference, candidate)
    checks.append(
        _check(
            "operation_comparison_projection_uniqueness",
            "Operation comparison projection uniqueness",
            not duplicate,
            "Each persisted comparison key must identify at most one cell per run.",
            "core_invariant",
            True,
        )
    )
    exact_scope = (
        bool(pairs)
        and len(pairs) == len(reference.report.cells)
        and len(pairs) == len(candidate.report.cells)
    )
    checks.append(
        _check(
            "matched_cell_scope",
            "Matched operation and factor scope",
            exact_scope,
            "Every report cell must match by its persisted typed comparison key.",
            "core_invariant",
            True,
        )
    )
    protocols_match = all(pair["protocol_match"] for pair in pairs)
    checks.append(
        _check(
            "effective_cell_protocol",
            "Effective per-cell protocol",
            protocols_match,
            "Warmups, measured trials, timeout, destructive boundary, and cleanup must match.",
            "core_invariant",
            True,
        )
    )

    compatible = all(check["compatible"] for check in checks if check["blocks_aggregate"])
    deltas = _metric_deltas(reference, candidate, pairs, descriptive_override)
    phases = _phase_deltas(reference, candidate, pairs, descriptive_override)
    if not compatible and not descriptive_override:
        deltas = []
        phases = []
    matched_cells = [pair["matched"] for pair in pairs]
    return ComparisonV3(
        schema_version=COMPARISON_SCHEMA_VERSION,
        comparison_derivation_revision=COMPARISON_DERIVATION_REVISION,
        reference_run_id=reference_id,
        candidate_run_id=candidate_id,
        protocol=protocol,
        compatible=compatible,
        descriptive_only=descriptive_override,
        treatment_differences=treatment_differences,
        typed_treatment_differences=typed_differences,
        checks=checks,
        matched_cell_ids=[match["reference_cell_id"] for match in matched_cells],
        matched_cells=matched_cells,
        deltas=deltas,
        phase_comparisons=phases,
        performance_verdict=_performance_verdict(deltas) if compatible else None,
    )


def _protocol(corpus: RunCorpus) -> dict[str, Any]:
    comparison = corpus.expanded.get("canonical_plan", {}).get("comparison")
    if comparison is None:
        return {
            "protocol_id": DEFAULT_PROTOCOL_ID,
            "protocol_version": DEFAULT_PROTOCOL_VERSION,
            "treatment_fields": [],
            "source": "defaulted",
        }
    fields = comparison.get("treatment_fields", [])
    return {
        "protocol_id": comparison["protocol_id"],
        "protocol_version": comparison["protocol_version"],
        "treatment_fields": sorted(fields),
        "source": "explicit",
    }


def _treatment_differences(
    reference: RunCorpus, candidate: RunCorpus, declared: list[str]
) -> tuple[list[str], list[dict[str, Any]]]:
    left = reference.manifest.get("treatment", {})
    right = candidate.manifest.get("treatment", {})
    messages = []
    typed = []
    for field in sorted(set(left) | set(right)):
        if left.get(field) == right.get(field):
            continue
        is_declared = field in declared
        messages.append(f"Treatment field {field} differs.")
        typed.append(
            {
                "field": field,
                "identity_component": field,
                "reference": _identity_value(left.get(field)),
                "candidate": _identity_value(right.get(field)),
                "declared": is_declared,
            }
        )
    return messages, typed


def _match_cells(reference: RunCorpus, candidate: RunCorpus) -> tuple[list[dict[str, Any]], bool]:
    assert reference.report is not None and candidate.report is not None
    reference_expanded = {cell["cell_id"]: cell for cell in reference.expanded["cells"]}
    candidate_expanded = {cell["cell_id"]: cell for cell in candidate.expanded["cells"]}

    def index(cells: list[dict[str, Any]]) -> tuple[dict[bytes, dict[str, Any]], bool]:
        result = {}
        duplicate = False
        for cell in cells:
            key = _canonical(cell["comparison_key"])
            duplicate = duplicate or key in result
            result[key] = cell
        return result, duplicate

    left, left_duplicate = index(reference.report.cells)
    right, right_duplicate = index(candidate.report.cells)
    pairs = []
    for key in sorted(set(left) & set(right)):
        reference_cell = left[key]
        candidate_cell = right[key]
        digest = hashlib.sha256(key).hexdigest()
        reference_protocol = reference_expanded[reference_cell["cell_id"]]["protocol"]
        candidate_protocol = candidate_expanded[candidate_cell["cell_id"]]["protocol"]
        match_id = f"match:{digest}"
        pairs.append(
            {
                "reference": reference_cell,
                "candidate": candidate_cell,
                "protocol_match": reference_protocol == candidate_protocol,
                "matched": {
                    "match_id": match_id,
                    "comparison_key_sha256": f"sha256:{digest}",
                    "operation_id": reference_cell["operation_id"],
                    "reference_cell_id": reference_cell["cell_id"],
                    "candidate_cell_id": candidate_cell["cell_id"],
                    "effective_protocol_compatible": reference_protocol == candidate_protocol,
                },
            }
        )
    return pairs, left_duplicate or right_duplicate


def _metric_deltas(
    reference: RunCorpus,
    candidate: RunCorpus,
    pairs: list[dict[str, Any]],
    descriptive: bool,
) -> list[dict[str, Any]]:
    result = []
    seed = reference.expanded["canonical_plan"]["seed"]
    for pair in pairs:
        left = {metric["identity"]["id"]: metric for metric in pair["reference"]["metrics"]}
        right = {metric["identity"]["id"]: metric for metric in pair["candidate"]["metrics"]}
        for metric_id in sorted(set(left) | set(right)):
            reference_metric = left.get(metric_id)
            candidate_metric = right.get(metric_id)
            identities_match = (
                reference_metric is not None
                and candidate_metric is not None
                and reference_metric["identity"] == candidate_metric["identity"]
            )
            reference_values = _raw_values(reference_metric)
            candidate_values = _raw_values(candidate_metric)
            interval = None
            omission = None
            if identities_match:
                interval = bootstrap_median_difference_interval(
                    reference_values,
                    candidate_values,
                    _derived_seed(seed, pair["matched"]["match_id"], metric_id),
                )
                if interval is None:
                    omission = "insufficient_n"
            reference_value = _median(reference_metric)
            candidate_value = _median(candidate_metric)
            absolute = (
                candidate_value - reference_value
                if identities_match and reference_value is not None and candidate_value is not None
                else None
            )
            percent = absolute / reference_value * 100 if absolute is not None and reference_value else None
            unavailable = None
            if not identities_match:
                unavailable = "metric identity is missing or incompatible"
            elif reference_value is None or candidate_value is None:
                unavailable = "median is unavailable in one or both runs"
            digest = hashlib.sha256(
                f"{pair['matched']['match_id']}:{metric_id}".encode()
            ).hexdigest()
            result.append(
                {
                    "comparison_id": f"delta:{digest}",
                    "match_id": pair["matched"]["match_id"],
                    "reference_cell_id": pair["reference"]["cell_id"],
                    "candidate_cell_id": pair["candidate"]["cell_id"],
                    "metric_id": metric_id,
                    "unit": (reference_metric or candidate_metric)["identity"]["unit"],
                    "reference_unit": reference_metric["identity"]["unit"] if reference_metric else None,
                    "candidate_unit": candidate_metric["identity"]["unit"] if candidate_metric else None,
                    "reference_value": reference_value,
                    "candidate_value": candidate_value,
                    "reference_n": len(reference_values),
                    "candidate_n": len(candidate_values),
                    "reference_unavailable_n": _unavailable_count(reference_metric),
                    "candidate_unavailable_n": _unavailable_count(candidate_metric),
                    "reference_statistics": reference_metric["statistics"] if reference_metric else None,
                    "candidate_statistics": candidate_metric["statistics"] if candidate_metric else None,
                    "absolute_change": absolute,
                    "percent_change": percent,
                    "median_difference_confidence_interval": (
                        interval.model_dump(mode="json") if interval else None
                    ),
                    "confidence_interval_omission_reason": omission,
                    "unavailable_reason": unavailable,
                    "direction": (reference_metric or candidate_metric)["identity"]["direction"],
                    "descriptive_only": descriptive,
                    "correctness": {
                        "reference_correctness_failed": pair["reference"]["counts"]["correctness_failed"],
                        "candidate_correctness_failed": pair["candidate"]["counts"]["correctness_failed"],
                        "reference_cleanup_invalid": pair["reference"]["counts"]["cleanup_invalid"],
                        "candidate_cleanup_invalid": pair["candidate"]["counts"]["cleanup_invalid"],
                    },
                }
            )
    return result


def _phase_deltas(
    reference: RunCorpus,
    candidate: RunCorpus,
    pairs: list[dict[str, Any]],
    descriptive: bool,
) -> list[dict[str, Any]]:
    result = []
    seed = reference.expanded["canonical_plan"]["seed"]
    for pair in pairs:
        left = {phase["id"]: phase for phase in pair["reference"]["phases"]}
        right = {phase["id"]: phase for phase in pair["candidate"]["phases"]}
        for phase_id in sorted(set(left) | set(right)):
            reference_phase = left.get(phase_id)
            candidate_phase = right.get(phase_id)
            identity_keys = (
                "id",
                "semantic_revision",
                "unit",
                "source",
                "correlation",
                "trace_span_name",
            )
            compatible = reference_phase is not None and candidate_phase is not None and all(
                reference_phase[key] == candidate_phase[key] for key in identity_keys
            )
            reference_values = _phase_values(reference_phase)
            candidate_values = _phase_values(candidate_phase)
            interval = (
                bootstrap_median_difference_interval(
                    reference_values,
                    candidate_values,
                    _derived_seed(seed, pair["matched"]["match_id"], phase_id),
                )
                if compatible
                else None
            )
            left_value = _phase_median(reference_phase)
            right_value = _phase_median(candidate_phase)
            absolute = right_value - left_value if compatible and left_value is not None and right_value is not None else None
            percent = absolute / left_value * 100 if absolute is not None and left_value else None
            digest = hashlib.sha256(
                f"{pair['matched']['match_id']}:phase:{phase_id}".encode()
            ).hexdigest()
            result.append(
                {
                    "comparison_id": f"phase:{digest}",
                    "match_id": pair["matched"]["match_id"],
                    "reference_cell_id": pair["reference"]["cell_id"],
                    "candidate_cell_id": pair["candidate"]["cell_id"],
                    "phase_id": phase_id,
                    "unit": (reference_phase or candidate_phase)["unit"],
                    "reference_summary": reference_phase,
                    "candidate_summary": candidate_phase,
                    "identity_compatible": compatible,
                    "reference_value": left_value,
                    "candidate_value": right_value,
                    "absolute_change": absolute,
                    "percent_change": percent,
                    "median_difference_confidence_interval": interval.model_dump(mode="json") if interval else None,
                    "confidence_interval_omission_reason": None if interval else "insufficient_n",
                    "unavailable_reason": None if compatible else "phase identity is missing or incompatible",
                    "descriptive_only": descriptive,
                }
            )
    return result


def _raw_values(metric: dict[str, Any] | None) -> list[float]:
    if metric is None:
        return []
    return [float(point["value"]) for point in metric["raw_points"]]


def _phase_values(phase: dict[str, Any] | None) -> list[float]:
    if phase is None:
        return []
    distribution = phase["duration"]["distribution"]
    return [float(value) for value in distribution.get("values", [])]


def _median(metric: dict[str, Any] | None) -> float | None:
    return None if metric is None else metric["statistics"]["median"]


def _phase_median(phase: dict[str, Any] | None) -> float | None:
    return None if phase is None else phase["duration"]["median"]


def _unavailable_count(metric: dict[str, Any] | None) -> int:
    return 0 if metric is None else metric["unavailable"]["count"]


def _derived_seed(seed: int, *parts: str) -> int:
    digest = hashlib.sha256(f"{seed}:".encode() + ":".join(parts).encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _check(
    check_id: str,
    label: str,
    compatible: bool,
    consequence: str,
    scope: str,
    blocks: bool,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "label": label,
        "compatible": compatible,
        "consequence": consequence,
        "scope": scope,
        "blocks_aggregate": blocks,
    }


def _identity_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _performance_verdict(deltas: list[dict[str, Any]]) -> str | None:
    available = [delta for delta in deltas if delta["percent_change"] is not None]
    if not available:
        return None
    slower = sum(
        1
        for delta in available
        if (delta["direction"] == "lower_is_preferred" and delta["percent_change"] > 0)
        or (delta["direction"] == "higher_is_preferred" and delta["percent_change"] < 0)
    )
    if slower == 0:
        return "no descriptive metric regression"
    return f"candidate is descriptively worse on {slower} metric(s)"
