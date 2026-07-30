from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


OWNER = "ephemeral-sandbox-benchmark"
STATE_ROLE = "benchmark-state"
SCHEMA_VERSION = 1


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class StateMarker(StrictModel):
    owner: Literal["ephemeral-sandbox-benchmark"] = OWNER
    role: Literal["benchmark-state"] = STATE_ROLE
    schema_version: Literal[1] = SCHEMA_VERSION


class OwnedPathMarker(StrictModel):
    owner: Literal["ephemeral-sandbox-benchmark"] = OWNER
    role: Literal["fixtures", "runs", "results", "runtime", "tmp"]
    schema_version: Literal[1] = SCHEMA_VERSION
    identity: dict[str, str]


class SchemaIdentity(StrictModel):
    schema_name: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    readable_versions: list[int] = Field(default_factory=list)


class SchemaEnvelope(StrictModel):
    schema_name: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    data: dict[str, Any]


class EventRecord(StrictModel):
    sequence: int = Field(ge=1)
    run_id: str = Field(min_length=1)
    monotonic_offset_ns: int = Field(ge=0)
    data: dict[str, Any]


class RunState(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    VERIFYING = "verifying"
    TEARING_DOWN = "tearing_down"
    COMPLETED = "completed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RunFailure(StrictModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    infrastructure: bool


class RunManifestCore(StrictModel):
    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    state: RunState
    plan_hash: str = Field(min_length=1)
    failure: RunFailure | None = None


class BenchmarkReportV4(StrictModel):
    schema_version: Literal[4]
    report_derivation_revision: Literal[3]
    run_id: str = Field(min_length=1)
    state: Literal[
        "planned",
        "queued",
        "preparing",
        "running",
        "verifying",
        "tearing_down",
        "completed",
        "cancelling",
        "cancelled",
        "failed",
    ]
    provisional: bool
    correctness_verdict: Literal["pending", "pass", "fail"]
    design_counts: dict[str, int]
    research_question: str
    plan_hash: str = Field(min_length=1)
    source_commit: str
    source_dirty: bool
    environment_fingerprint: str
    definition_snapshot_version: int = Field(ge=1)
    definition_snapshot_sha256: str
    started_at: str | None
    ended_at: str | None
    summary: list[dict[str, Any]]
    factor_studies: list[dict[str, Any]]
    cells: list[dict[str, Any]]
    methods: dict[str, Any]
    limitations: list[str]
    warnings: list[dict[str, Any]]


class RunDerivedSummaryV4(StrictModel):
    schema_version: Literal[4]
    report_derivation_revision: Literal[3]
    run_id: str = Field(min_length=1)
    plan_hash: str = Field(min_length=1)
    state: Literal[
        "planned",
        "queued",
        "preparing",
        "running",
        "verifying",
        "tearing_down",
        "completed",
        "cancelling",
        "cancelled",
        "failed",
    ]
    provisional: bool
    correctness_verdict: Literal["pending", "pass", "fail"]
    design_counts: dict[str, int]
    cells: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
