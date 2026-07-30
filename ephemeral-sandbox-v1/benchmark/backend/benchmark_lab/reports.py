import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .artifacts import (
    ArtifactError,
    ArtifactId,
    ArtifactStore,
    JournalRead,
    read_envelope_path,
    read_journal_path,
)
from .models import BenchmarkReportV4, RunDerivedSummaryV4


CSV_EXPORT_SCHEMA_VERSION = 3
TERMINAL_STATES = {"completed", "failed", "cancelled"}


class ReportError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunCorpus:
    path: Path
    manifest: dict[str, Any]
    intent: dict[str, Any]
    expanded: dict[str, Any]
    definitions: dict[str, Any]
    environment: dict[str, Any]
    events: JournalRead
    observations: JournalRead
    report: BenchmarkReportV4 | None
    summary: RunDerivedSummaryV4 | None

    @classmethod
    def open(cls, path: Path, *, recover_partial_tail: bool = False) -> "RunCorpus":
        try:
            manifest = read_envelope_path(path / "run-manifest.json", ArtifactId.RUN_MANIFEST)
            intent = read_envelope_path(path / "intent-plan.json", ArtifactId.INTENT_PLAN)
            expanded = read_envelope_path(path / "expanded-plan.json", ArtifactId.EXPANDED_PLAN)
            definitions = read_envelope_path(
                path / "definition-snapshot.json", ArtifactId.DEFINITION_SNAPSHOT
            )
            environment = read_envelope_path(
                path / "environment-metadata.json", ArtifactId.ENVIRONMENT_METADATA
            )
            events = read_journal_path(
                path / "events.ndjson",
                ArtifactId.EVENTS,
                recover_partial_tail=recover_partial_tail,
            )
            observations = read_journal_path(
                path / "observations.ndjson",
                ArtifactId.OBSERVATIONS,
                recover_partial_tail=recover_partial_tail,
            )
            report = _optional_report(path / "report.json")
            summary = _optional_summary(path / "summary.json")
        except ArtifactError as error:
            raise ReportError(str(error)) from error
        corpus = cls(
            path.resolve(),
            manifest,
            intent,
            expanded,
            definitions,
            environment,
            events,
            observations,
            report,
            summary,
        )
        corpus.validate()
        return corpus

    def validate(self) -> None:
        run_id = self.manifest.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ReportError("manifest run id is missing")
        if self.manifest.get("schema_version") not in {1, 2}:
            raise ReportError("manifest data schema version is unsupported")
        if self.expanded.get("schema_version") != 1:
            raise ReportError("expanded plan data schema version is unsupported")
        plan_hash = self.manifest.get("plan_hash")
        if plan_hash != self.expanded.get("plan_hash"):
            raise ReportError("manifest and expanded plan hashes differ")
        _validate_sequence(self.events, "event")
        _validate_sequence(self.observations, "observation")
        if self.report is None:
            if self.manifest.get("state") in {"completed", "cancelled"}:
                raise ReportError("terminal retained run is missing its report")
            return
        if self.report.run_id != run_id or self.report.plan_hash != plan_hash:
            raise ReportError("report identity disagrees with authoritative artifacts")
        if self.report.state != self.manifest.get("state"):
            raise ReportError("report state disagrees with manifest")
        if self.report.provisional != (self.report.state not in TERMINAL_STATES):
            raise ReportError("report provisional flag disagrees with state")
        expanded_cells = self.expanded.get("cells")
        if not isinstance(expanded_cells, list):
            raise ReportError("expanded plan cells are invalid")
        planned_ids = [cell.get("cell_id") for cell in expanded_cells]
        report_ids = [cell.get("cell_id") for cell in self.report.cells]
        if planned_ids != report_ids or len(set(report_ids)) != len(report_ids):
            raise ReportError("report cells differ from the deterministic expanded plan")
        if self.summary is not None and self.summary.model_dump(mode="json") != derive_summary(
            self.report
        ).model_dump(mode="json"):
            raise ReportError("summary does not match its report projection")


def derive_summary(report: BenchmarkReportV4) -> RunDerivedSummaryV4:
    return RunDerivedSummaryV4(
        schema_version=4,
        report_derivation_revision=report.report_derivation_revision,
        run_id=report.run_id,
        plan_hash=report.plan_hash,
        state=report.state,
        provisional=report.provisional,
        correctness_verdict=report.correctness_verdict,
        design_counts=report.design_counts,
        cells=report.cells,
        warnings=report.warnings,
    )


def render_json_export(report: BenchmarkReportV4) -> bytes:
    envelope = {
        "schema_name": "eos_benchmark_json_export",
        "schema_version": 4,
        "data": report.model_dump(mode="json"),
    }
    return json.dumps(envelope, indent=2, ensure_ascii=False).encode() + b"\n"


def render_csv_export(report: BenchmarkReportV4) -> str:
    header = [
        "export_schema_version",
        "run_id",
        "plan_hash",
        "record_type",
        "operation_id",
        "cell_id",
        "item_id",
        "semantic_revision",
        "unit",
        "scope",
        "source",
        "correlation",
        "trace_span_name",
        "attempted_n",
        "successful_n",
        "failed_n",
        "unavailable_n",
        "median",
        "p95",
        "ci_lower",
        "ci_upper",
        "trial_id",
        "value",
        "related_value",
        "verdict",
        "detail",
    ]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    for cell in report.cells:
        common = [str(CSV_EXPORT_SCHEMA_VERSION), report.run_id, report.plan_hash]
        operation_id = cell["operation_id"]
        for metric in cell["metrics"]:
            statistics = metric["statistics"]
            interval = statistics["median_confidence_interval"]
            writer.writerow(
                common
                + [
                    "metric_summary",
                    operation_id,
                    cell["cell_id"],
                    metric["identity"]["id"],
                    metric["identity"]["semantic_revision"],
                    metric["identity"]["unit"],
                    metric["identity"]["scope"],
                    metric["identity"]["source"],
                    "",
                    "",
                    metric["attempted_n"],
                    metric["available_n"],
                    metric["failed_n"],
                    metric["unavailable"]["count"],
                    _number(statistics["median"]),
                    _number(statistics["p95"]),
                    _number(interval["lower"] if interval else None),
                    _number(interval["upper"] if interval else None),
                    "",
                    "",
                    "",
                    "",
                    _compact_json(metric["unavailable"]["reasons"]),
                ]
            )
        for check in cell["checks"]:
            writer.writerow(
                common
                + [
                    "check_summary",
                    operation_id,
                    cell["cell_id"],
                    check["id"],
                    check["semantic_revision"],
                    "",
                    "",
                    "",
                    "",
                    "",
                    check["attempted"],
                    check["passed"],
                    check["failed"],
                    0,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "pass" if check["failed"] == 0 else "fail",
                    "",
                ]
            )
        for phase in cell["phases"]:
            statistics = phase["duration"]
            interval = statistics["median_confidence_interval"]
            writer.writerow(
                common
                + [
                    "phase_summary",
                    operation_id,
                    cell["cell_id"],
                    phase["id"],
                    phase["semantic_revision"],
                    phase["unit"],
                    "operation",
                    phase["source"],
                    phase["correlation"],
                    phase["trace_span_name"],
                    phase["attempted"],
                    statistics["count"],
                    phase["failed"],
                    0,
                    _number(statistics["median"]),
                    _number(statistics["p95"]),
                    _number(interval["lower"] if interval else None),
                    _number(interval["upper"] if interval else None),
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for evidence in cell["operation_evidence"]:
            item = evidence["evidence"]
            writer.writerow(
                common
                + [
                    "operation_evidence",
                    operation_id,
                    cell["cell_id"],
                    item["operation"],
                    cell["comparison_key"]["semantic_revision"],
                    "",
                    "",
                    "",
                    "",
                    "",
                    1,
                    1,
                    0,
                    0,
                    "",
                    "",
                    "",
                    "",
                    evidence["trial_id"],
                    "",
                    evidence.get("request_id") or "",
                    "",
                    _compact_json(item),
                ]
            )
        correlation = cell["cpu_latency_correlation"]
        for point in correlation["points"]:
            writer.writerow(
                common
                + [
                    "correlation_point",
                    operation_id,
                    cell["cell_id"],
                    "sandbox_cpu_time_vs_operation_latency",
                    1,
                    "nanoseconds",
                    "trial",
                    correlation["method"],
                    "",
                    "",
                    correlation["support_count"],
                    correlation["support_count"],
                    0,
                    0,
                    "",
                    "",
                    "",
                    "",
                    point["trial_id"],
                    _number(point["operation_latency_ns"]),
                    _number(point["sandbox_cpu_time_ns"]),
                    "",
                    "",
                ]
            )
    return stream.getvalue()


def persist_report_bundle(store: ArtifactStore, report: BenchmarkReportV4) -> None:
    value = report.model_dump(mode="json")
    store.replace_snapshot(report.run_id, ArtifactId.REPORT, value)
    store.replace_snapshot(
        report.run_id,
        ArtifactId.SUMMARY,
        derive_summary(report).model_dump(mode="json"),
    )
    store.replace_snapshot(report.run_id, ArtifactId.JSON_EXPORT, value)
    store.replace_plain(
        report.run_id,
        ArtifactId.CSV_EXPORT,
        render_csv_export(report).encode(),
    )


def normalized_report(report: BenchmarkReportV4) -> dict[str, Any]:
    value = report.model_dump(mode="json")
    for key in ("run_id", "started_at", "ended_at", "source_commit", "environment_fingerprint"):
        value[key] = f"<{key}>"
    return value


def _optional_report(path: Path) -> BenchmarkReportV4 | None:
    if not path.exists():
        return None
    try:
        return BenchmarkReportV4.model_validate(read_envelope_path(path, ArtifactId.REPORT))
    except ValidationError as error:
        raise ReportError(f"report schema is invalid: {error}") from error


def _optional_summary(path: Path) -> RunDerivedSummaryV4 | None:
    if not path.exists():
        return None
    try:
        return RunDerivedSummaryV4.model_validate(read_envelope_path(path, ArtifactId.SUMMARY))
    except ValidationError as error:
        raise ReportError(f"summary schema is invalid: {error}") from error


def _validate_sequence(journal: JournalRead, label: str) -> None:
    for expected, record in enumerate(journal.records, 1):
        if record.get("sequence") != expected:
            raise ReportError(
                f"{label} sequence is not contiguous: expected {expected}, "
                f"received {record.get('sequence')}"
            )


def _number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).lower()


def _compact_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"
