import hashlib
import json
import os
import secrets
import stat
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import EventRecord, SchemaEnvelope
from .paths import BenchmarkRoots, _sync_directory


MAX_DOWNLOAD_BYTES = 16 * 1024 * 1024
MAX_BOUNDED_EVIDENCE_BYTES = 1024 * 1024
RECOVERY_QUARANTINE_DIRECTORY = ".recovery-quarantine"


class ArtifactError(ValueError):
    pass


class ArtifactId(StrEnum):
    RUN_MANIFEST = "run_manifest"
    INTENT_PLAN = "intent_plan"
    EXPANDED_PLAN = "expanded_plan"
    DEFINITION_SNAPSHOT = "definition_snapshot"
    ENVIRONMENT_METADATA = "environment_metadata"
    EVENTS = "events"
    OBSERVATIONS = "observations"
    SUMMARY = "summary"
    REPORT = "report"
    JSON_EXPORT = "json_export"
    CSV_EXPORT = "csv_export"
    BOUNDED_EVIDENCE = "bounded_evidence"


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    file_name: str
    media_type: str
    schema_name: str | None
    write_version: int | None
    read_versions: frozenset[int]
    journal: bool = False


ARTIFACT_SPECS = {
    ArtifactId.RUN_MANIFEST: ArtifactSpec(
        "run-manifest.json", "application/json", "eos_benchmark_run_manifest", 2, frozenset({1, 2})
    ),
    ArtifactId.INTENT_PLAN: ArtifactSpec(
        "intent-plan.json", "application/json", "eos_benchmark_intent_plan", 1, frozenset({1})
    ),
    ArtifactId.EXPANDED_PLAN: ArtifactSpec(
        "expanded-plan.json", "application/json", "eos_benchmark_expanded_plan", 1, frozenset({1})
    ),
    ArtifactId.DEFINITION_SNAPSHOT: ArtifactSpec(
        "definition-snapshot.json",
        "application/json",
        "eos_benchmark_definition_snapshot",
        2,
        frozenset({2}),
    ),
    ArtifactId.ENVIRONMENT_METADATA: ArtifactSpec(
        "environment-metadata.json",
        "application/json",
        "eos_benchmark_environment_metadata",
        1,
        frozenset({1}),
    ),
    ArtifactId.EVENTS: ArtifactSpec(
        "events.ndjson",
        "application/x-ndjson",
        "eos_benchmark_event",
        1,
        frozenset({1}),
        journal=True,
    ),
    ArtifactId.OBSERVATIONS: ArtifactSpec(
        "observations.ndjson",
        "application/x-ndjson",
        "eos_benchmark_observation",
        5,
        frozenset({1, 2, 3, 4, 5}),
        journal=True,
    ),
    ArtifactId.SUMMARY: ArtifactSpec(
        "summary.json", "application/json", "eos_benchmark_summary", 4, frozenset({4})
    ),
    ArtifactId.REPORT: ArtifactSpec(
        "report.json", "application/json", "eos_benchmark_report", 4, frozenset({4})
    ),
    ArtifactId.JSON_EXPORT: ArtifactSpec(
        "export.json", "application/json", "eos_benchmark_json_export", 4, frozenset({4})
    ),
    ArtifactId.CSV_EXPORT: ArtifactSpec(
        "export.csv", "text/csv; charset=utf-8", None, None, frozenset()
    ),
    ArtifactId.BOUNDED_EVIDENCE: ArtifactSpec(
        "bounded-evidence",
        "application/json",
        "eos_benchmark_operation_evidence",
        1,
        frozenset({1}),
    ),
}


# Only producer/raw artifacts belong in a run's reader contract. Summary,
# report, and exports are derived views and advertise their own envelopes.
PRODUCER_ARTIFACT_IDS = frozenset(
    {
        ArtifactId.RUN_MANIFEST,
        ArtifactId.INTENT_PLAN,
        ArtifactId.EXPANDED_PLAN,
        ArtifactId.DEFINITION_SNAPSHOT,
        ArtifactId.ENVIRONMENT_METADATA,
        ArtifactId.EVENTS,
        ArtifactId.OBSERVATIONS,
        ArtifactId.BOUNDED_EVIDENCE,
    }
)


_PHASE_V1_IDENTITIES = {
    "layerstack_squash": ("nanoseconds", "exact_request_trace_span", "layerstack.squash"),
    "layerstack_storage_plan": (
        "nanoseconds",
        "exact_request_trace_span",
        "layerstack.squash.plan",
    ),
    "layerstack_flatten": (
        "nanoseconds",
        "exact_request_trace_span",
        "layerstack.squash.flatten",
    ),
    "layerstack_commit": (
        "nanoseconds",
        "exact_request_trace_span",
        "layerstack.squash.commit",
    ),
    "layerstack_remount_sweep": (
        "nanoseconds",
        "exact_request_trace_span",
        "layerstack.squash.remount_sweep",
    ),
    "workspace_session_remount": (
        "nanoseconds",
        "exact_request_trace_span",
        "workspace_session.remount",
    ),
}


@dataclass(frozen=True, slots=True)
class JournalRead:
    records: list[dict[str, Any]]
    partial_tail_line: int | None


@dataclass(frozen=True, slots=True)
class QuarantinedTail:
    artifact_id: ArtifactId
    line: int
    bytes: int
    sha256: str
    file_name: str


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    artifact_id: str
    label: str
    media_type: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ArtifactDownload:
    reference: ArtifactReference
    content: bytes


_EVIDENCE_NAME = re.compile(r"operation-evidence-([0-9a-f]{64})\.json\Z")


def read_envelope_path(path: Path, artifact_id: ArtifactId) -> dict[str, Any]:
    spec = ARTIFACT_SPECS[artifact_id]
    if spec.schema_name is None:
        raise ArtifactError(f"artifact {artifact_id} is not a JSON envelope")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
        envelope = SchemaEnvelope.model_validate(value)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ArtifactError(f"invalid artifact JSON at {path}: {error}") from error
    return _decode_envelope(envelope, spec, path)


def read_journal_path(
    path: Path, artifact_id: ArtifactId, *, recover_partial_tail: bool = False
) -> JournalRead:
    spec = ARTIFACT_SPECS[artifact_id]
    if not spec.journal:
        raise ArtifactError(f"artifact {artifact_id} is not a journal")
    if not path.exists():
        return JournalRead([], None)
    if path.is_symlink() or not path.is_file():
        raise ArtifactError(f"journal is not a plain file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ArtifactError(f"cannot read journal {path}: {error}") from error
    partial_line = None
    complete = raw
    if raw and not raw.endswith(b"\n"):
        partial_line = raw.count(b"\n") + 1
        if not recover_partial_tail:
            raise ArtifactError(f"partial trailing NDJSON record at line {partial_line} in {path}")
        newline = raw.rfind(b"\n")
        complete = raw[: newline + 1] if newline >= 0 else b""

    records = []
    for line_number, line in enumerate(complete.splitlines(), 1):
        if not line:
            continue
        try:
            envelope = SchemaEnvelope.model_validate(json.loads(line))
            records.append(_decode_envelope(envelope, spec, path))
        except (json.JSONDecodeError, ValidationError, ArtifactError) as error:
            raise ArtifactError(
                f"invalid journal record at line {line_number} in {path}: {error}"
            ) from error
    return JournalRead(records, partial_line)


def _decode_envelope(
    envelope: SchemaEnvelope, spec: ArtifactSpec, path: Path
) -> dict[str, Any]:
    if envelope.schema_name != spec.schema_name:
        raise ArtifactError(
            f"artifact schema mismatch at {path}: expected {spec.schema_name}, "
            f"received {envelope.schema_name}"
        )
    if envelope.schema_version not in spec.read_versions:
        raise ArtifactError(
            f"unsupported artifact schema version {envelope.schema_version} "
            f"for {envelope.schema_name}"
        )
    data = envelope.data
    if spec.schema_name == "eos_benchmark_event":
        try:
            data = EventRecord.model_validate(data).model_dump(mode="json")
        except ValidationError as error:
            raise ArtifactError(f"event record is invalid: {error}") from error
    if spec.schema_name == "eos_benchmark_observation":
        data = _migrate_observation(data, envelope.schema_version)
    return data


def _migrate_observation(data: dict[str, Any], version: int) -> dict[str, Any]:
    if set(data) != {"sequence", "record"} or not isinstance(data["sequence"], int):
        raise ArtifactError("observation sequence envelope is invalid")
    record = data["record"]
    if not isinstance(record, dict) or set(record) != {"record", "data"}:
        raise ArtifactError("observation record envelope is invalid")
    kind = record["record"]
    if kind not in {"trial", "request", "resource", "phase", "check", "operation"}:
        raise ArtifactError(f"unknown observation record type: {kind}")
    if version == 1 and kind == "operation":
        raise ArtifactError("operation observations were not defined in schema version 1")
    record_data = record["data"]
    if not isinstance(record_data, dict):
        raise ArtifactError("observation record data must be an object")
    if version in {4, 5}:
        if version == 5:
            _validate_observation_v5(kind, record_data)
            return data
        _validate_observation_v4(kind, record_data)
        return data
    migrated = dict(record_data)
    if version < 3 and kind == "trial":
        if "artifacts" in migrated:
            raise ArtifactError("historical trial unexpectedly contains artifacts")
        migrated["artifacts"] = []
    if version == 1 and kind == "phase":
        expected = {
            "id",
            "semantic_revision",
            "cell_id",
            "trial_id",
            "request_id",
            "source",
            "start_offset_ns",
            "duration_ns",
            "status",
        }
        if set(migrated) != expected:
            raise ArtifactError("schema version 1 phase fields are invalid")
        identity = _PHASE_V1_IDENTITIES.get(migrated["id"])
        if (
            identity is None
            or migrated["semantic_revision"] != 1
            or migrated["source"] != "product_trace"
        ):
            raise ArtifactError("schema version 1 phase identity is not registered")
        migrated["unit"], migrated["correlation"], migrated["trace_span_name"] = identity
    return {"sequence": data["sequence"], "record": {"record": kind, "data": migrated}}


_OBSERVATION_V4_REQUIRED = {
    "request": {
        "operation_id", "cell_id", "trial_id", "request_id", "warmup",
        "start_offset_ns", "latency_ns", "response_bytes", "response_sha256", "status",
    },
    "check": {
        "operation_id", "cell_id", "trial_id", "request_id", "check_id",
        "semantic_revision", "passed", "expected", "actual", "artifact_id",
    },
    "trial": {
        "operation_id", "cell_id", "trial_id", "warmup", "kind", "sequence_in_cell",
        "reportable", "latency_ns", "request_count", "status", "product_succeeded",
        "infrastructure_failed", "cleanup_baseline_restored", "artifacts",
    },
    "operation": {"operation_id", "cell_id", "trial_id", "request_id", "evidence"},
    "resource": {"cell_id", "trial_id", "request_id", "reading"},
    "phase": {
        "id", "semantic_revision", "unit", "cell_id", "trial_id", "request_id",
        "source", "correlation", "trace_span_name", "start_offset_ns", "duration_ns", "status",
    },
}


def _validate_observation_v4(kind: str, data: dict[str, Any]) -> None:
    required = _OBSERVATION_V4_REQUIRED[kind]
    if set(data) != required:
        raise ArtifactError(f"schema version 4 {kind} fields are invalid")
    for identity in ("cell_id", "trial_id"):
        if not isinstance(data.get(identity), str) or not data[identity]:
            raise ArtifactError(f"schema version 4 {kind} identity is invalid")
    if kind == "request" and (
        not isinstance(data["latency_ns"], int)
        or data["latency_ns"] < 0
        or data["status"] not in {"success", "product_failed", "transport_failed"}
    ):
        raise ArtifactError("schema version 4 request timing is invalid")
    if kind == "trial" and (
        data["kind"] not in {"warmup", "measured"}
        or data["status"] not in {"success", "product_failed", "infrastructure_failed", "cleanup_invalid"}
        or not isinstance(data["artifacts"], list)
    ):
        raise ArtifactError("schema version 4 trial status is invalid")
    if kind == "check" and not isinstance(data["passed"], bool):
        raise ArtifactError("schema version 4 check verdict is invalid")
    if kind == "operation" and not isinstance(data["evidence"], dict):
        raise ArtifactError("schema version 4 operation evidence is invalid")


_OBSERVATION_V5_REQUIRED = dict(_OBSERVATION_V4_REQUIRED)
_OBSERVATION_V5_REQUIRED["trial"] = _OBSERVATION_V4_REQUIRED["trial"] | {
    "setup_ns",
    "operation_ns",
    "verify_ns",
    "teardown_ns",
    "checks_passed",
}


def _validate_observation_v5(kind: str, data: dict[str, Any]) -> None:
    required = _OBSERVATION_V5_REQUIRED[kind]
    if set(data) != required:
        raise ArtifactError(f"schema version 5 {kind} fields are invalid")
    if kind != "trial":
        _validate_observation_v4(kind, data)
        return
    for identity in ("cell_id", "trial_id"):
        if not isinstance(data.get(identity), str) or not data[identity]:
            raise ArtifactError("schema version 5 trial identity is invalid")
    if (
        data["kind"] not in {"warmup", "measured"}
        or data["status"]
        not in {
            "success",
            "product_failed",
            "correctness_failed",
            "infrastructure_failed",
            "cleanup_invalid",
            "cancelled",
        }
        or not isinstance(data["artifacts"], list)
        or not isinstance(data["checks_passed"], bool)
        or any(
            not isinstance(data[field], int) or data[field] < 0
            for field in ("setup_ns", "operation_ns", "verify_ns", "teardown_ns")
        )
    ):
        raise ArtifactError("schema version 5 trial status or lifecycle is invalid")


class ArtifactStore:
    def __init__(self, roots: BenchmarkRoots) -> None:
        roots.validate_state()
        self._roots = roots
        self._results_root = roots.results

    def create_run(self, run_id: str) -> Path:
        _validate_run_id(run_id)
        path = self._results_root / run_id
        try:
            path.mkdir(mode=0o700)
        except FileExistsError as error:
            raise ArtifactError(f"run artifacts already exist for {run_id}") from error
        _sync_directory(self._results_root)
        return path

    def run_path(self, run_id: str) -> Path:
        _validate_run_id(run_id)
        path = self._results_root / run_id
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise ArtifactError(f"run artifacts do not exist for {run_id}") from error
        if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink() or path.resolve() != path:
            raise ArtifactError(f"run artifacts do not exist for {run_id}")
        return path

    def write_immutable(self, run_id: str, artifact_id: ArtifactId, data: dict[str, Any]) -> None:
        spec = ARTIFACT_SPECS[artifact_id]
        if spec.schema_name is None or spec.journal:
            raise ArtifactError(f"artifact {artifact_id} does not support immutable JSON writes")
        self._write_new(self.run_path(run_id) / spec.file_name, _envelope_bytes(spec, data))

    def replace_snapshot(
        self,
        run_id: str,
        artifact_id: ArtifactId,
        data: dict[str, Any],
        *,
        schema_version: int | None = None,
    ) -> None:
        spec = ARTIFACT_SPECS[artifact_id]
        if spec.schema_name is None or spec.journal:
            raise ArtifactError(f"artifact {artifact_id} does not support snapshot writes")
        self._replace(
            self.run_path(run_id) / spec.file_name,
            _envelope_bytes(spec, data, schema_version=schema_version),
        )

    def replace_plain(self, run_id: str, artifact_id: ArtifactId, content: bytes) -> None:
        spec = ARTIFACT_SPECS[artifact_id]
        if artifact_id is not ArtifactId.CSV_EXPORT or spec.schema_name is not None:
            raise ArtifactError(f"artifact {artifact_id} does not support plain writes")
        if len(content) > MAX_DOWNLOAD_BYTES:
            raise ArtifactError("plain artifact exceeds the byte cap")
        self._replace(self.run_path(run_id) / spec.file_name, content)

    def append_record(self, run_id: str, artifact_id: ArtifactId, data: dict[str, Any]) -> None:
        spec = ARTIFACT_SPECS[artifact_id]
        if not spec.journal:
            raise ArtifactError(f"artifact {artifact_id} is not a journal")
        path = self.run_path(run_id) / spec.file_name
        payload = json.dumps(
            _envelope_value(spec, data), separators=(",", ":"), ensure_ascii=False
        ).encode() + b"\n"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def read_envelope(self, run_id: str, artifact_id: ArtifactId) -> dict[str, Any]:
        return read_envelope_path(
            self.run_path(run_id) / ARTIFACT_SPECS[artifact_id].file_name, artifact_id
        )

    def read_records(
        self, run_id: str, artifact_id: ArtifactId, *, recover_partial_tail: bool = False
    ) -> JournalRead:
        return read_journal_path(
            self.run_path(run_id) / ARTIFACT_SPECS[artifact_id].file_name,
            artifact_id,
            recover_partial_tail=recover_partial_tail,
        )

    def quarantine_partial_tail(
        self, run_id: str, artifact_id: ArtifactId
    ) -> QuarantinedTail | None:
        spec = ARTIFACT_SPECS[artifact_id]
        if not spec.journal:
            raise ArtifactError(f"artifact {artifact_id} is not a journal")
        run = self.run_path(run_id)
        path = run / spec.file_name
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            raise ArtifactError(f"journal is not a plain file: {path}")
        raw = path.read_bytes()
        if not raw or raw.endswith(b"\n"):
            return None
        complete_length = raw.rfind(b"\n") + 1
        tail = raw[complete_length:]
        line = raw[:complete_length].count(b"\n") + 1
        digest = hashlib.sha256(tail).hexdigest()
        quarantine = run / RECOVERY_QUARANTINE_DIRECTORY
        self._ensure_plain_directory(quarantine)
        file_name = f"{artifact_id}.partial-tail-{digest}.bin"
        destination = quarantine / file_name
        if destination.exists():
            if destination.is_symlink() or destination.read_bytes() != tail:
                raise ArtifactError(f"quarantine content conflict at {destination}")
        else:
            self._write_new(destination, tail)
        descriptor = os.open(path, os.O_WRONLY)
        try:
            os.ftruncate(descriptor, complete_length)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _sync_directory(run)
        return QuarantinedTail(
            artifact_id=artifact_id,
            line=line,
            bytes=len(tail),
            sha256=f"sha256:{digest}",
            file_name=file_name,
        )

    def write_trial_evidence(
        self,
        run_id: str,
        cell_id: str,
        trial_id: str,
        data: dict[str, Any],
        *,
        forbidden_secrets: tuple[str, ...] = (),
    ) -> ArtifactReference:
        _validate_component(cell_id)
        _validate_component(trial_id)
        run = self.run_path(run_id)
        evidence = run
        for component in ("cells", cell_id, "trials", trial_id, "bounded-evidence"):
            evidence /= component
            self._ensure_plain_directory(evidence)
        spec = ARTIFACT_SPECS[ArtifactId.BOUNDED_EVIDENCE]
        payload = _envelope_bytes(spec, data)
        if len(payload) > MAX_BOUNDED_EVIDENCE_BYTES:
            raise ArtifactError("bounded evidence exceeds the byte cap")
        for secret in forbidden_secrets:
            if secret and secret.encode() in payload:
                raise ArtifactError("bounded evidence contains a runtime secret")
        digest = hashlib.sha256(payload).hexdigest()
        path = evidence / f"operation-evidence-{digest}.json"
        if path.exists():
            if path.is_symlink() or path.read_bytes() != payload:
                raise ArtifactError(f"immutable artifact conflict at {path}")
        else:
            self._write_new(path, payload)
        relative = path.relative_to(run).as_posix()
        opaque = hashlib.sha256(relative.encode()).hexdigest()
        return ArtifactReference(
            artifact_id=f"bounded_evidence_{opaque}",
            label=relative,
            media_type="application/json",
            size_bytes=len(payload),
            sha256=f"sha256:{digest}",
        )

    def list_artifacts(self, run_id: str) -> list[ArtifactReference]:
        run = self.run_path(run_id)
        references: list[ArtifactReference] = []
        for artifact_id, spec in ARTIFACT_SPECS.items():
            if artifact_id is ArtifactId.BOUNDED_EVIDENCE:
                continue
            path = run / spec.file_name
            if path.exists():
                references.append(
                    self._reference(artifact_id.value, spec.file_name, spec.media_type, path)
                )
        references.extend(
            self._reference_for_evidence(run, path) for path in self._evidence_paths(run)
        )
        return sorted(references, key=lambda item: item.artifact_id)

    def download_artifact(self, run_id: str, artifact_id: str) -> ArtifactDownload:
        run = self.run_path(run_id)
        try:
            fixed_id = ArtifactId(artifact_id)
        except ValueError:
            fixed_id = None
        if fixed_id is not None and fixed_id is not ArtifactId.BOUNDED_EVIDENCE:
            spec = ARTIFACT_SPECS[fixed_id]
            path = run / spec.file_name
            reference = self._reference(fixed_id.value, spec.file_name, spec.media_type, path)
            return ArtifactDownload(reference, path.read_bytes())
        for path in self._evidence_paths(run):
            reference = self._reference_for_evidence(run, path)
            if reference.artifact_id == artifact_id:
                return ArtifactDownload(reference, path.read_bytes())
        raise ArtifactError(f"unknown artifact id {artifact_id}")

    def remove_incomplete_run(self, run_id: str) -> None:
        run = self.run_path(run_id)
        allowed = {spec.file_name for spec in ARTIFACT_SPECS.values() if "." in spec.file_name}
        for item in run.iterdir():
            if item.name not in allowed or item.is_symlink() or not item.is_file():
                raise ArtifactError(f"unknown artifact prevents safe removal: {item.name}")
        for item in run.iterdir():
            item.unlink()
        run.rmdir()
        _sync_directory(self._results_root)

    def _write_new(self, path: Path, payload: bytes) -> None:
        temporary = self._stage(payload)
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as error:
            raise ArtifactError(f"immutable artifact already exists at {path}") from error
        finally:
            temporary.unlink(missing_ok=True)
            _sync_directory(self._roots.tmp)
        _sync_directory(path.parent)

    def _replace(self, path: Path, payload: bytes) -> None:
        temporary = self._stage(payload)
        try:
            os.replace(temporary, path)
            _sync_directory(path.parent)
            _sync_directory(self._roots.tmp)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def _stage(self, payload: bytes) -> Path:
        temporary = self._roots.tmp / f"artifact-{os.getpid()}-{secrets.token_hex(12)}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        except BaseException:
            os.close(descriptor)
            temporary.unlink(missing_ok=True)
            raise
        else:
            os.close(descriptor)
        _sync_directory(self._roots.tmp)
        return temporary

    @staticmethod
    def _reference(
        artifact_id: str, label: str, media_type: str, path: Path
    ) -> ArtifactReference:
        try:
            metadata = path.lstat()
        except FileNotFoundError as error:
            raise ArtifactError(f"artifact does not exist: {artifact_id}") from error
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise ArtifactError(f"artifact is not a plain file: {artifact_id}")
        if metadata.st_size > MAX_DOWNLOAD_BYTES:
            raise ArtifactError(f"artifact exceeds the download byte cap: {artifact_id}")
        content = path.read_bytes()
        return ArtifactReference(
            artifact_id=artifact_id,
            label=label,
            media_type=media_type,
            size_bytes=len(content),
            sha256=f"sha256:{hashlib.sha256(content).hexdigest()}",
        )

    def _reference_for_evidence(self, run: Path, path: Path) -> ArtifactReference:
        relative = path.relative_to(run).as_posix()
        opaque = hashlib.sha256(relative.encode()).hexdigest()
        reference = self._reference(
            f"bounded_evidence_{opaque}", relative, "application/json", path
        )
        if reference.size_bytes > MAX_BOUNDED_EVIDENCE_BYTES:
            raise ArtifactError(f"bounded evidence exceeds the byte cap: {relative}")
        match = _EVIDENCE_NAME.fullmatch(path.name)
        assert match is not None
        if reference.sha256 != f"sha256:{match.group(1)}":
            raise ArtifactError(f"bounded evidence digest mismatch: {relative}")
        read_envelope_path(path, ArtifactId.BOUNDED_EVIDENCE)
        return reference

    @staticmethod
    def _evidence_paths(run: Path) -> list[Path]:
        cells = run / "cells"
        if not cells.exists():
            return []
        _require_plain_directory(cells)
        found: list[Path] = []
        for cell in sorted(cells.iterdir()):
            _validate_component(cell.name)
            _require_plain_directory(cell)
            trials = cell / "trials"
            _require_plain_directory(trials)
            for trial in sorted(trials.iterdir()):
                _validate_component(trial.name)
                _require_plain_directory(trial)
                evidence = trial / "bounded-evidence"
                _require_plain_directory(evidence)
                for path in sorted(evidence.iterdir()):
                    if path.is_symlink() or not path.is_file() or not _EVIDENCE_NAME.fullmatch(path.name):
                        raise ArtifactError(f"unexpected bounded evidence entry: {path}")
                    found.append(path)
        return found

    @staticmethod
    def _ensure_plain_directory(path: Path) -> None:
        try:
            path.mkdir(mode=0o700)
            _sync_directory(path.parent)
        except FileExistsError:
            if path.is_symlink() or not path.is_dir():
                raise ArtifactError(f"artifact directory is unsafe: {path}")


def _envelope_value(
    spec: ArtifactSpec,
    data: dict[str, Any],
    *,
    schema_version: int | None = None,
) -> dict[str, Any]:
    assert spec.schema_name is not None and spec.write_version is not None
    version = spec.write_version if schema_version is None else schema_version
    if version not in spec.read_versions:
        raise ArtifactError(
            f"cannot write unsupported artifact schema version {version} for {spec.schema_name}"
        )
    return {
        "schema_name": spec.schema_name,
        "schema_version": version,
        "data": data,
    }


def _envelope_bytes(
    spec: ArtifactSpec,
    data: dict[str, Any],
    *,
    schema_version: int | None = None,
) -> bytes:
    return json.dumps(
        _envelope_value(spec, data, schema_version=schema_version), indent=2, ensure_ascii=False
    ).encode() + b"\n"


def _validate_run_id(run_id: str) -> None:
    if not run_id or len(run_id) > 64 or not all(
        character.isascii() and (character.isalnum() or character == "-")
        for character in run_id
    ):
        raise ArtifactError(f"invalid run id {run_id}")


def _validate_component(value: str) -> None:
    if not value or len(value) > 128 or value in {".", ".."} or not all(
        character.isascii() and (character.isalnum() or character in "-_:")
        for character in value
    ):
        raise ArtifactError(f"invalid artifact path component {value}")


def _require_plain_directory(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise ArtifactError(f"artifact directory is missing: {path}") from error
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        raise ArtifactError(f"artifact directory is unsafe: {path}")


def _write_all(descriptor: int, payload: bytes) -> None:
    written = 0
    while written < len(payload):
        count = os.write(descriptor, payload[written:])
        if count == 0:
            raise OSError("short artifact write")
        written += count
