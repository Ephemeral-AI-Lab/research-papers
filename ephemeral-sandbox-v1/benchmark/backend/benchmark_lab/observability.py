from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationError, model_validator

from .models import StrictModel


class ObservabilityError(RuntimeError):
    pass


class CgroupMetrics(StrictModel):
    metrics_source: Literal["docker_engine"]
    cpu_usec: int | None = Field(ge=0)
    mem_cur: int | None = Field(ge=0)
    mem_max: int | None = Field(ge=0)
    io_rbytes: int | None = Field(ge=0)
    io_wbytes: int | None = Field(ge=0)


class CgroupDeltas(StrictModel):
    cpu_usec: int | None = Field(default=None, ge=0)
    io_rbytes: int | None = Field(default=None, ge=0)
    io_wbytes: int | None = Field(default=None, ge=0)


class CgroupSample(StrictModel):
    ts: int = Field(ge=0)
    sample_delta_ms: int | None = Field(ge=0)
    metrics: CgroupMetrics
    deltas: CgroupDeltas


class CgroupView(StrictModel):
    view: Literal["cgroup"]
    scope: Literal["sandbox"]
    series: list[CgroupSample] = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def validate_series(self) -> "CgroupView":
        previous: CgroupSample | None = None
        for sample in self.series:
            expected_interval = None if previous is None else sample.ts - previous.ts
            if expected_interval is not None and expected_interval < 0:
                raise ValueError("cgroup timestamps regressed")
            if sample.sample_delta_ms != expected_interval:
                raise ValueError("cgroup sample interval is inconsistent")
            if previous is not None:
                for metric, delta in (
                    ("cpu_usec", "cpu_usec"),
                    ("io_rbytes", "io_rbytes"),
                    ("io_wbytes", "io_wbytes"),
                ):
                    current_value = getattr(sample.metrics, metric)
                    previous_value = getattr(previous.metrics, metric)
                    expected_delta = (
                        None
                        if current_value is None or previous_value is None
                        else max(0, current_value - previous_value)
                    )
                    if getattr(sample.deltas, delta) != expected_delta:
                        raise ValueError("cgroup counter delta is inconsistent")
            previous = sample
        return self


class SnapshotMetrics(StrictModel):
    cpu_usec: int | None = Field(default=None, ge=0)
    mem_cur: int | None = Field(default=None, ge=0)
    mem_max: int | None = Field(default=None, ge=0)
    mem_max_unlimited: bool | None = None
    cgroup_available: bool | None = None
    cgroup_error: str | None = None
    disk_bytes: int | None = Field(default=None, ge=0)
    disk_allocated_bytes: int | None = Field(default=None, ge=0)
    files: int | None = Field(default=None, ge=0)
    disk_truncated: bool | None = None
    record_truncated_bytes: int | None = Field(default=None, alias="_truncated", ge=0)


class SnapshotDeltas(StrictModel):
    cpu_usec: int | None = Field(default=None, ge=0)


class SnapshotSample(StrictModel):
    ts: int = Field(ge=0)
    sample_delta_ms: int | None = None
    metrics: SnapshotMetrics
    deltas: SnapshotDeltas


class SnapshotResources(StrictModel):
    latest: SnapshotSample | None
    history: list[SnapshotSample]


class SnapshotLayers(StrictModel):
    base_root_hash: str | None
    layer_count: int | None = Field(ge=0)


class NamespaceExecution(StrictModel):
    namespace_execution_id: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    lifecycle_state: Literal["running"]


class SnapshotWorkspace(StrictModel):
    workspace_id: str = Field(min_length=1)
    lifecycle_state: Literal["active"]
    network_profile: str = Field(min_length=1)
    finalize_policy: str = Field(min_length=1)
    layers: SnapshotLayers
    namespace_fd_count: int | None = Field(ge=0)
    resources: SnapshotResources
    active_namespace_executions: list[NamespaceExecution]


class SnapshotStack(StrictModel):
    layer_count: int = Field(ge=0)
    layers_bytes: int | None = Field(ge=0)
    layers_allocated_bytes: int | None = Field(ge=0)
    storage_allocated_bytes: int | None = Field(ge=0)
    staging_entry_count: int | None = Field(ge=0)
    active_leases: int = Field(ge=0)


class SnapshotDaemon(StrictModel):
    daemon_pid: int = Field(gt=0)
    runtime_dir: str = Field(min_length=1)


class SnapshotView(StrictModel):
    sandbox_id: str = Field(min_length=1)
    lifecycle_state: Literal["ready"]
    availability: Literal["available", "partial"]
    sampled_at_unix_ms: int = Field(ge=0)
    errors: list[str]
    daemon: SnapshotDaemon
    resources: SnapshotResources
    workspaces: list[SnapshotWorkspace] = Field(max_length=4096)
    stack: SnapshotStack | None

    @model_validator(mode="after")
    def validate_availability(self) -> "SnapshotView":
        if (self.availability == "available") != (not self.errors):
            raise ValueError("snapshot availability and errors disagree")
        if not self.daemon.runtime_dir.startswith("/"):
            raise ValueError("snapshot runtime directory is not absolute")
        if self.resources.history or any(item.resources.history for item in self.workspaces):
            raise ValueError("snapshot unexpectedly contains history")
        identities = [item.workspace_id for item in self.workspaces]
        if len(identities) != len(set(identities)):
            raise ValueError("snapshot workspace identities are duplicated")
        return self


class Layer(StrictModel):
    layer_id: str = Field(min_length=1)
    bytes: int | None = Field(ge=0)
    allocated_bytes: int | None = Field(ge=0)
    leased_by_workspaces: int = Field(ge=0)
    booked_by: list[str]


class LayerstackView(StrictModel):
    view: Literal["layerstack"]
    manifest_version: int = Field(ge=0)
    root_hash: str = Field(min_length=1)
    active_lease_count: int = Field(ge=0)
    total_bytes: int | None = Field(ge=0)
    total_allocated_bytes: int | None = Field(ge=0)
    storage_logical_bytes: int | None = Field(ge=0)
    storage_allocated_bytes: int | None = Field(ge=0)
    staging_entry_count: int | None = Field(ge=0)
    layers: list[Layer]

    @model_validator(mode="after")
    def validate_totals(self) -> "LayerstackView":
        identities = [item.layer_id for item in self.layers]
        if len(identities) != len(set(identities)):
            raise ValueError("layerstack identities are duplicated")
        for total, field in (
            (self.total_bytes, "bytes"),
            (self.total_allocated_bytes, "allocated_bytes"),
        ):
            values = [getattr(item, field) for item in self.layers]
            expected = None if any(value is None for value in values) else sum(values)
            if total != expected:
                raise ValueError("layerstack total is inconsistent")
        return self


class TraceSpan(StrictModel):
    ts: int
    trace: str = Field(min_length=1)
    span: str = Field(min_length=1)
    parent: str | None = None
    name: str = Field(min_length=1)
    dur_ms: float = Field(ge=0)
    status: Literal["completed", "error", "cancelled", "timed_out"]
    attrs: dict[str, Any]


class TraceEvent(StrictModel):
    ts: int
    trace: str = Field(min_length=1)
    parent: str | None = None
    name: str = Field(min_length=1)
    attrs: dict[str, Any]


class TraceEventNode(StrictModel):
    offset_ms: float = Field(ge=0)
    event: TraceEvent


class TraceNode(StrictModel):
    span: TraceSpan
    offset_ms: float = Field(ge=0)
    children: list["TraceNode"]
    events: list[TraceEventNode]


class TraceView(StrictModel):
    view: Literal["trace"]
    trace: str = Field(min_length=1)
    spans: list[TraceNode]


def parse_cgroup(value: Any) -> CgroupView:
    return _parse(CgroupView, value, "cgroup")


def parse_snapshot(value: Any, sandbox_id: str) -> SnapshotView:
    result = _parse(SnapshotView, value, "snapshot")
    if result.sandbox_id != sandbox_id:
        raise ObservabilityError("snapshot sandbox identity mismatch")
    return result


def parse_layerstack(value: Any) -> LayerstackView:
    return _parse(LayerstackView, value, "layerstack")


def parse_trace(value: Any, request_id: str) -> TraceView:
    result = _parse(TraceView, value, "trace")
    if result.trace != request_id:
        raise ObservabilityError("trace request identity mismatch")
    seen: set[str] = set()
    remaining = 8192

    def visit(node: TraceNode, parent: str | None) -> None:
        nonlocal remaining
        remaining -= 1
        if (
            remaining < 0
            or node.span.trace != request_id
            or node.span.parent != parent
            or node.span.span in seen
            or any(
                event.event.trace != request_id
                or event.event.parent != node.span.span
                for event in node.events
            )
        ):
            raise ObservabilityError("trace tree contract failed")
        seen.add(node.span.span)
        for child in node.children:
            visit(child, node.span.span)

    for root in result.spans:
        visit(root, None)
    return result


def _parse(model: type[StrictModel], value: Any, label: str) -> Any:
    try:
        return model.model_validate(value)
    except ValidationError as error:
        raise ObservabilityError(f"product {label} response schema is invalid") from error
