from __future__ import annotations

import copy
import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, ValidationError

from .models import StrictModel


class PlanError(ValueError):
    pass


class Factor(StrictModel):
    role: Literal["varied", "controlled"]
    values: list[Any] = Field(min_length=1, max_length=256)
    control: Any | None = None


class OperationConfiguration(StrictModel):
    enabled: bool
    factors: dict[str, Factor]


class OperationPlan(StrictModel):
    operation: str
    configuration: OperationConfiguration


class ConfigurationBase(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    version: int = Field(ge=1)
    scope: Literal["all", "command", "files", "workspace", "layerstack"]


class PlanEnvironment(StrictModel):
    image: str = Field(min_length=1, max_length=512)
    client_cohort: Literal["direct_client"]


class TrialCount(StrictModel):
    warmups: int = Field(ge=0, le=100)
    measured_trials: int = Field(ge=1, le=10_000)


class TrialDefaults(StrictModel):
    fast: TrialCount
    destructive: TrialCount


class TimeoutDefaults(StrictModel):
    default: int = Field(ge=100, le=3_600_000)
    squash_layerstack: int = Field(ge=100, le=3_600_000)


class Protocol(StrictModel):
    order: Literal["randomized_blocks"]
    resource_interval_ms: int = Field(ge=10, le=60_000)
    trial_defaults: TrialDefaults
    timeout_ms: TimeoutDefaults


class ComparisonProtocol(StrictModel):
    protocol_id: Literal["release_comparison"]
    protocol_version: Literal[1]
    treatment_fields: list[
        Literal[
            "source_commit",
            "source_diff_hash",
            "daemon_binary_hash",
            "gateway_binary_hash",
        ]
    ] = Field(min_length=1, max_length=4)


class ExperimentPlan(StrictModel):
    schema_version: Literal[1]
    name: str = Field(min_length=1, max_length=128)
    configuration_base: ConfigurationBase
    seed: int = Field(ge=0)
    environment: PlanEnvironment
    protocol: Protocol
    operations: list[OperationPlan] = Field(min_length=1, max_length=64)
    comparison: ComparisonProtocol | None = None


class Preset(StrictModel):
    schema_version: Literal[1]
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    version: int = Field(ge=1)
    plan: ExperimentPlan


@dataclass(frozen=True, slots=True)
class RuntimeEnvironment:
    test_workspace_root: str
    image_digest: str | None
    filesystem: str | None
    free_space_bytes: int | None
    workspace_root_identity: str | None = None


_FAMILIES = {
    "exec_command": "command",
    "file_read": "files",
    "file_write": "files",
    "file_edit": "files",
    "file_blame": "files",
    "create_workspace": "workspace_lifecycle",
    "squash_layerstack": "layer_stack",
}
_FAMILY_ORDER = ("command", "files", "workspace_lifecycle", "layer_stack")
_OPERATION_ORDER = ("exec_command", "file_read", "file_write", "file_edit", "file_blame", "create_workspace", "squash_layerstack")
_FAMILY_SEEDS = {
    "command": 0x434F4D4D414E4401,
    "files": 0x46494C4553000002,
    "workspace_lifecycle": 0x574F524B53504303,
    "layer_stack": 0x4C41594552535404,
}
_ACCESS = {
    "exec_command": ("public_gateway", "exec_command"),
    "file_read": ("public_gateway", "file_read"),
    "file_write": ("public_gateway", "file_write"),
    "file_edit": ("public_gateway", "file_edit"),
    "file_blame": ("public_gateway", "file_blame"),
    "create_workspace": ("internal_workspace", "create_no_op_session"),
    "squash_layerstack": ("public_gateway", "squash_layerstacks"),
}
_COUNT = {
    "exec_command": {"kind": "concurrent_requests", "factor": "concurrent_requests"},
    "file_read": {"kind": "concurrent_requests", "factor": "concurrent_requests"},
    "file_write": {"kind": "concurrent_requests", "factor": "concurrent_requests"},
    "file_edit": {"kind": "concurrent_requests", "factor": "concurrent_requests"},
    "file_blame": {"kind": "concurrent_requests", "factor": "concurrent_requests"},
    "create_workspace": {"kind": "concurrent_workspace_creates", "factor": "workspace_count"},
    "squash_layerstack": {"kind": "single_request_with_prepared_load", "load_factor": "live_sessions"},
}
_CLEANUP = {
    "exec_command": "resolve_from_isolation",
    "file_read": "verify_fixture_unchanged",
    "file_write": "resolve_from_isolation",
    "file_edit": "resolve_from_isolation",
    "file_blame": "verify_fixture_unchanged",
    "create_workspace": "destroy_sessions_and_verify_baseline",
    "squash_layerstack": "destroy_topology_and_verify_baseline",
}
_EXPECTED_FACTORS = {
    "exec_command": {"concurrent_requests", "workspace_profile", "session_mode", "command_case"},
    "file_read": {"concurrent_requests", "returned_bytes", "source", "target_mode"},
    "file_write": {"concurrent_requests", "content_bytes", "destination", "target_mode"},
    "file_edit": {"concurrent_requests", "file_bytes", "replacement_count", "match_density", "destination", "target_mode"},
    "file_blame": {"concurrent_requests", "line_count", "ownership_segments", "auditability_event_count"},
    "create_workspace": {"workspace_count", "workspace_profile", "network_profile"},
    "squash_layerstack": {"live_sessions", "requested_migration_ratio", "remount_parallelism", "squashable_blocks", "layers_per_block", "payload_bytes", "session_activity"},
}
_CHOICES = {
    "workspace_profile": None,
    "session_mode": {"explicit", "automatic"},
    "command_case": {"noop", "output64_kib", "cpu50_ms", "fixture_read"},
    "source": {"snapshot", "session"},
    "target_mode": {"independent", "same_target"},
    "destination": {"session", "publish"},
    "network_profile": {"shared", "isolated"},
    "session_activity": {"idle", "active"},
}
_NON_NEGATIVE = {"live_sessions"}
_RATIOS = {"match_density", "requested_migration_ratio"}
_BOUNDS = {
    "concurrent_requests": 256,
    "workspace_count": 256,
    "live_sessions": 256,
    "returned_bytes": 16 * 1024 * 1024,
    "content_bytes": 16 * 1024 * 1024,
    "file_bytes": 16 * 1024 * 1024,
    "replacement_count": 65_536,
    "line_count": 1_000_000,
    "ownership_segments": 65_536,
    "auditability_event_count": 65_536,
    "remount_parallelism": 256,
    "squashable_blocks": 1_024,
    "layers_per_block": 1_024,
    "payload_bytes": 16 * 1024 * 1024,
}
_MAX_PREPARED_LAYERS = 4_096
_BASE_CATALOG_OPERATIONS = {
    "create_sandbox", "destroy_sandbox", "inspect_sandbox", "cgroup", "snapshot"
}
_OPERATION_CATALOG_OPERATIONS = {
    "exec_command": {"exec_command"},
    "file_read": {"file_read"},
    "file_write": {"file_write"},
    "file_edit": {"file_edit"},
    "file_blame": {"file_blame"},
    "create_workspace": set(),
    "squash_layerstack": {"squash_layerstacks", "trace", "layerstack"},
}


def load_preset(path: Path) -> Preset:
    try:
        return Preset.model_validate(yaml.safe_load(path.read_text()))
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise PlanError(f"invalid benchmark preset: {path}") from error


def load_workspace_profiles(directory: Path) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.yml")):
        value = yaml.safe_load(path.read_text())
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise PlanError(f"invalid workspace profile: {path}")
        identifier = value.get("id")
        if not isinstance(identifier, str) or identifier in profiles:
            raise PlanError(f"invalid workspace profile identity: {path}")
        profiles[identifier] = value
    return profiles


def expand_plan(
    plan: ExperimentPlan,
    *,
    environment: RuntimeEnvironment,
    profiles: dict[str, dict[str, Any]],
    declared_default: ExperimentPlan | None = None,
    catalog_operations: frozenset[str] | set[str] | None = None,
) -> dict[str, Any]:
    canonical = plan.model_dump(mode="json")
    canonical["operations"].sort(key=lambda item: _OPERATION_ORDER.index(item["operation"]) if item["operation"] in _OPERATION_ORDER else len(_OPERATION_ORDER))
    root_identity = environment.workspace_root_identity or _sha(environment.test_workspace_root.encode())
    selected_names: set[str] = set()
    cells: list[dict[str, Any]] = []
    findings = _validate_plan(canonical, profiles, catalog_operations)
    invalid_operations = {
        int(item["path"].split("[")[1].split("]")[0])
        for item in findings
        if item["severity"] == "error"
        and isinstance(item.get("path"), str)
        and item["path"].startswith("operations[")
    }
    for operation_index, operation in enumerate(canonical["operations"]):
        if not operation["configuration"]["enabled"]:
            continue
        operation_id = operation["operation"]
        if operation_id not in _FAMILIES or operation_index in invalid_operations:
            continue
        factors = operation["configuration"]["factors"]
        names = list(factors)
        for values in itertools.product(*(factors[name]["values"] for name in names)):
            raw = dict(zip(names, values, strict=True))
            cell_body, isolation = _operation_cell(operation_id, raw)
            profile_name = cell_body.get("workspace_profile")
            profile = profiles.get(profile_name) if profile_name else None
            if profile_name:
                if profile is None:
                    findings.append(_finding("error", "unknown_workspace_profile", profile_name, "operations"))
                    continue
                selected_names.add(profile_name)
            destructive = operation_id in {"create_workspace", "squash_layerstack"}
            trial_kind = "destructive" if destructive else "fast"
            trial_counts = canonical["protocol"]["trial_defaults"][trial_kind]
            timeout_key = "squash_layerstack" if operation_id == "squash_layerstack" else "default"
            protocol = {
                "destructive": destructive,
                "warmups": trial_counts["warmups"],
                "measured_trials": trial_counts["measured_trials"],
                "timeout_ms": canonical["protocol"]["timeout_ms"][timeout_key],
                "cleanup": _CLEANUP[operation_id],
            }
            operation_cell = {"operation": operation_id, "cell": cell_body}
            profile_material = profile if profile else None
            cell_id = _sha_json([
                _FAMILIES[operation_id], operation_id, 1, 1, root_identity,
                canonical["environment"]["client_cohort"], protocol, profile_material, operation_cell,
            ])
            access_kind, action = _ACCESS[operation_id]
            identity = {key: value for key, value in cell_body.items() if key not in {"command", "expected_exit_code", "output_limit_bytes", "resolved_isolation"}}
            comparison = {
                "operation": operation_id,
                "semantic_revision": 1,
                "factor_schema_revision": 1,
                "comparison_projection_revision": 1,
                "count_semantics": _COUNT[operation_id],
                "product_access": {"kind": access_kind, "action": action},
                "isolation": isolation,
                "identity": {"operation": operation_id, "identity": identity},
            }
            cells.append({
                "cell_id": cell_id, "family_id": _FAMILIES[operation_id], "operation_id": operation_id,
                "operation_semantic_revision": 1, "factor_schema_revision": 1,
                "protocol": protocol, "comparison_key": comparison, "operation": operation_cell,
            })
    blocks = _order_cells(cells, canonical["seed"])
    selected = [profiles[name] for name in sorted(selected_names)]
    effective = {
        "test_workspace_root": environment.test_workspace_root,
        "workspace_root_identity": root_identity,
        "client_cohort": canonical["environment"]["client_cohort"],
        "image_digest": environment.image_digest,
        "filesystem": environment.filesystem,
        "free_space_bytes": environment.free_space_bytes,
        "gateway_mode": "isolated",
    }
    lifecycle = {"lifecycle_revision": 1, "failure_revision": 1, "stabilization_revision": 1, "automatic_retries": 0, "one_active_campaign": True, "sequential_families": True}
    revisions = [{"operation_id": name, "semantic_revision": 1, "factor_schema_revision": 1, "comparison_projection_revision": 1} for name in ("exec_command", "file_read", "file_write", "file_edit", "file_blame", "create_workspace", "squash_layerstack")]
    hash_environment = {key: value for key, value in effective.items() if key != "free_space_bytes"}
    plan_hash = _sha_json({"schema_version": 1, "plan_hash_revision": 2, "definition_schema_version": 2, "canonical_plan": canonical, "effective_environment": hash_environment, "fixed_lifecycle_policy": lifecycle, "definition_revisions": revisions, "selected_workspace_profiles": selected, "cells": cells, "execution_blocks": blocks})
    trial_batches = sum(cell["protocol"]["warmups"] + cell["protocol"]["measured_trials"] for cell in cells)
    requests = sum((cell["protocol"]["warmups"] + cell["protocol"]["measured_trials"]) * _request_count(cell) for cell in cells)
    peak = max((profile["fixture"]["logical_bytes"] for profile in selected), default=0)
    estimates = {"cell_count": len(cells), "trial_batch_count": trial_batches, "issued_operation_request_count": requests, "duration_range": {"minimum_ns": 0, "maximum_ns": sum((cell["protocol"]["warmups"] + cell["protocol"]["measured_trials"]) * cell["protocol"]["timeout_ms"] * 1_000_000 for cell in cells)}, "estimated_peak_disk_bytes": peak or None, "required_free_space_bytes": peak * 2 or None, "gateway_restart_count": sum(block["restart_reason"] is not None for block in blocks), "warnings": []}
    return {"schema_version": 1, "runnable": not any(item["severity"] == "error" for item in findings), "is_customized": declared_default is None or canonical != declared_default.model_dump(mode="json"), "plan_hash": plan_hash, "canonical_plan": canonical, "effective_environment": effective, "fixed_lifecycle_policy": lifecycle, "selected_workspace_profiles": selected, "cells": cells, "execution_blocks": blocks, "estimates": estimates, "validation": findings}


def _validate_plan(
    plan: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    catalog_operations: frozenset[str] | set[str] | None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    image = plan["environment"]["image"]
    if (
        any(character.isspace() or ord(character) < 32 for character in image)
        or image.startswith(("/", "."))
        or "://" in image
        or "@" in image and not image.rsplit("@", 1)[1].startswith("sha256:")
    ):
        findings.append(_finding("error", "unsafe_image_reference", image, "environment.image"))
    operation_ids = [item["operation"] for item in plan["operations"]]
    for operation_id in sorted({item for item in operation_ids if operation_ids.count(item) > 1}):
        findings.append(_finding("error", "duplicate_operation", operation_id, "operations"))
    required_catalog = set(_BASE_CATALOG_OPERATIONS)
    for index, operation in enumerate(plan["operations"]):
        operation_id = operation["operation"]
        path = f"operations[{index}]"
        if operation_id not in _FAMILIES:
            findings.append(_finding("error", "unknown_operation", operation_id, path))
            continue
        if operation["configuration"]["enabled"]:
            required_catalog.update(_OPERATION_CATALOG_OPERATIONS[operation_id])
        factors = operation["configuration"]["factors"]
        expected = _EXPECTED_FACTORS[operation_id]
        if set(factors) != expected:
            findings.append(
                _finding(
                    "error",
                    "factor_schema_mismatch",
                    f"expected {sorted(expected)}, received {sorted(factors)}",
                    f"{path}.configuration.factors",
                )
            )
            continue
        for name, factor in factors.items():
            factor_path = f"{path}.configuration.factors.{name}"
            keys = [_value_key(value) for value in factor["values"]]
            if len(keys) != len(set(keys)):
                findings.append(_finding("error", "duplicate_factor_value", name, factor_path))
            if factor["role"] == "varied":
                if factor["control"] is None or _value_key(factor["control"]) not in keys:
                    findings.append(_finding("error", "invalid_factor_control", name, factor_path))
            elif factor["control"] is not None:
                findings.append(_finding("error", "controlled_factor_has_control", name, factor_path))
            for value in factor["values"]:
                if not _valid_factor_value(name, value, profiles):
                    code = (
                        "unknown_workspace_profile"
                        if name == "workspace_profile" and isinstance(value, str)
                        else "invalid_factor_value"
                    )
                    findings.append(_finding("error", code, f"{name}={value!r}", factor_path))
            if factor["control"] is not None and not _valid_factor_value(name, factor["control"], profiles):
                findings.append(_finding("error", "invalid_factor_control", name, factor_path))
        if operation_id == "file_blame":
            values = factors
            if max(values["ownership_segments"]["values"]) > min(values["line_count"]["values"]):
                findings.append(_finding("error", "invalid_blame_shape", "ownership segments exceed line count", path))
            if max(values["auditability_event_count"]["values"]) > min(values["line_count"]["values"]):
                findings.append(_finding("error", "invalid_blame_shape", "auditability events exceed line count", path))
        if operation_id == "squash_layerstack":
            values = factors
            layers = values["layers_per_block"]["values"]
            blocks = values["squashable_blocks"]["values"]
            sessions = values["live_sessions"]["values"]
            ratios = values["requested_migration_ratio"]["values"]
            if any(type(value) is int and value < 2 for value in layers):
                findings.append(_finding(
                    "error",
                    "invalid_squash_shape",
                    "layers per block must be at least two",
                    path,
                ))
            if any(
                type(block) is int
                and type(per_block) is int
                and block * per_block > _MAX_PREPARED_LAYERS
                for block in blocks
                for per_block in layers
            ):
                findings.append(_finding(
                    "error",
                    "invalid_squash_shape",
                    f"prepared topology exceeds {_MAX_PREPARED_LAYERS} layers",
                    path,
                ))
            if any(
                type(block) is int
                and type(live) is int
                and type(ratio) in {int, float}
                and 0 <= float(ratio) <= 1
                and int(live * float(ratio) + 0.5) < block - 1
                for block in blocks
                for live in sessions
                for ratio in ratios
            ):
                findings.append(_finding(
                    "error",
                    "invalid_squash_shape",
                    "requested eligible sessions cannot form every block boundary",
                    path,
                ))
    if catalog_operations is not None:
        missing = sorted(required_catalog - set(catalog_operations))
        if missing:
            findings.append(_finding("error", "catalog_operations_missing", ", ".join(missing), "product_catalog"))
    return findings


def _valid_factor_value(name: str, value: Any, profiles: dict[str, dict[str, Any]]) -> bool:
    if name in _CHOICES:
        return isinstance(value, str) and (
            value in profiles if _CHOICES[name] is None else value in _CHOICES[name]
        )
    if name in _RATIOS:
        lower_bound = 0 if name == "requested_migration_ratio" else 0.0
        return type(value) in {int, float} and lower_bound <= float(value) <= 1 and (
            name == "requested_migration_ratio" or float(value) > 0
        )
    if type(value) is not int:
        return False
    minimum = 0 if name in _NON_NEGATIVE else 1
    return minimum <= value <= _BOUNDS[name]


def _value_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _operation_cell(operation: str, raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
    body = copy.deepcopy(raw)
    if operation == "exec_command":
        commands = {
            "noop": ("true", 0),
            "output64_kib": ("head -c 65536 /dev/zero | tr '\\000' x", 0),
            "cpu50_ms": ('i=0; while [ "$i" -lt 20000 ]; do i=$((i + 1)); done', 0),
            "fixture_read": ("wc -c < .eos-benchmark-fixture/command-read.bin", 0),
        }
        command, exit_code = commands[body["command_case"]]
        isolation = "reusable_verified_fixture" if body["session_mode"] == "explicit" else "automatic_session_per_request"
        body.update(template_revision=1, command=command, command_sha256=_sha(command.encode()), expected_exit_code=exit_code, output_limit_bytes=65536, resolved_isolation=isolation)
    elif operation == "file_read":
        isolation = "reusable_verified_fixture"
        body["resolved_isolation"] = isolation
    elif operation in {"file_write", "file_edit"}:
        isolation = "fresh_sessions_per_trial" if body["destination"] == "session" else "fresh_publish_topology_per_trial"
        body["resolved_isolation"] = isolation
    elif operation == "file_blame":
        isolation = "reusable_verified_fixture"
        body["resolved_isolation"] = isolation
    elif operation == "create_workspace":
        isolation = "prepared_sandbox_per_cell"
        body["resolved_isolation"] = isolation
    else:
        isolation = "fresh_topology_per_trial"
        body["resolved_isolation"] = isolation
    return body, isolation


def _order_cells(cells: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    for family in _FAMILY_ORDER:
        family_cells = [cell for cell in cells if cell["family_id"] == family]
        if not family_cells:
            continue
        groups: list[tuple[int | None, list[dict[str, Any]]]]
        if family == "layer_stack":
            widths = sorted({cell["operation"]["cell"]["remount_parallelism"] for cell in family_cells})
            groups = [(width, [cell for cell in family_cells if cell["operation"]["cell"]["remount_parallelism"] == width]) for width in widths]
        else:
            groups = [(None, family_cells)]
        for index, (width, group) in enumerate(groups):
            _shuffle(group, seed ^ _FAMILY_SEEDS[family] ^ (width or 0))
            cell_ids = [cell["cell_id"] for cell in group]
            rust_family = {"command": "Command", "files": "Files", "workspace_lifecycle": "WorkspaceLifecycle", "layer_stack": "LayerStack"}[family]
            blocks.append({"block_id": _sha(f"v1:{rust_family}:{':'.join(cell_ids)}".encode()), "family_id": family, "cell_ids": cell_ids, "restart_reason": f"layerstack_remount_parallelism_changed:{width}" if index else None})
            ordered.extend(group)
    cells[:] = ordered
    return blocks


def _shuffle(values: list[Any], seed: int) -> None:
    state = seed & ((1 << 64) - 1)
    for index in range(len(values) - 1, 0, -1):
        state = _splitmix64(state)
        selected = state % (index + 1)
        values[index], values[selected] = values[selected], values[index]


def _splitmix64(state: int) -> int:
    mask = (1 << 64) - 1
    value = (state + 0x9E3779B97F4A7C15) & mask
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
    return value ^ (value >> 31)


def _request_count(cell: dict[str, Any]) -> int:
    body = cell["operation"]["cell"]
    return body.get("concurrent_requests", body.get("workspace_count", 1))


def _sha_json(value: Any) -> str:
    return _sha(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode())


def _sha(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _finding(severity: str, code: str, message: str, path: str | None) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, "path": path}
