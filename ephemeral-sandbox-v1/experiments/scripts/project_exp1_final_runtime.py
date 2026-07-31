#!/usr/bin/env python3
"""Project EXP1 final duration from immutable structural run evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

FINAL_CELLS = 19
FINAL_BATCHES = 1_938
FINAL_REQUESTS = 5_610
FINAL_WARMUPS = 2
FINAL_MEASURED = 100
LIMIT_NS = 1_400_000_000_000
EXPECTED = {
    "smoke": {
        "name": "paper-env-smoke",
        "disposition": "smoke",
        "eligibility": "qualification_only",
        "batches": 19,
        "requests": 55,
        "warmups": 0,
        "measured": 1,
    },
    "pilot": {
        "name": "paper-pilot",
        "disposition": "exploratory",
        "eligibility": "exploratory_ineligible",
        "batches": 133,
        "requests": 385,
        "warmups": 2,
        "measured": 5,
    },
}
PHASES = ("setup", "operation", "verify", "teardown")
STABLE_HOST_FIELDS = (
    "computer_name",
    "operating_system",
    "architecture",
    "os_version",
    "os_build_number",
    "cpu_model",
    "logical_processors",
    "processor_logical_processors",
    "total_memory_bytes",
    "filesystem",
    "volume_root",
    "docker_engine_version",
    "monotonic_clock",
)
PROTOCOLS = {
    "v1.0": {
        "id": "ephemeral-sandbox-v1-practical-performance-v1.0",
        "environment_identity": "isolated_loopback_per_execution_block",
    },
    "v1.1": {
        "id": "ephemeral-sandbox-v1-practical-performance-v1.1",
        "environment_identity": ("isolated_windows_named_pipe_per_execution_block"),
    },
}
V11_GATEWAY_TRANSPORT = {
    "transport": "windows_named_pipe",
    "scope": "local_only",
    "rotation": "per_execution_block",
}
SAFE_NPIPE_ENDPOINT = re.compile(r"npipe://\./pipe/[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA256_IDENTITY = re.compile(r"sha256:[0-9a-f]{64}\Z")
V11_PREFREEZE_MUTABLE_STATUS_PATHS = frozenset(
    {
        "progress.md",
        "experiments/experiment_log.md",
        "paper_state.json",
        "plan/progress.md",
    }
)
V11_PROTOCOL_FILE_PATHS = frozenset(
    {
        "progress.md",
        "plan/task-packets/exp1-cli-performance-campaign.md",
        "experiment_inventory.md",
        "experiments/exp1-v1.1-protocol-amendment.md",
        "experiments/environment_setup.md",
        "experiments/expected_tables.md",
        "experiments/experiment_log.md",
        "benchmark/PAPER_ARTIFACT.md",
        "paper_state.json",
        "plan/progress.md",
    }
)


class ProjectionError(RuntimeError):
    """An input or structural runtime invariant failed closed."""


@dataclass(frozen=True)
class TrialSpan:
    trial_id: str
    warmup: bool
    start_ns: int
    end_ns: int
    phase_ns: dict[str, int]

    @property
    def active_ns(self) -> int:
        return self.end_ns - self.start_ns


@dataclass(frozen=True)
class CellProfile:
    semantic_key: str
    semantic_sha256: str
    family_id: str
    operation_id: str
    leading_ns: int
    trailing_ns: int
    trials: tuple[TrialSpan, ...]
    gaps_ns: tuple[int, ...]

    @property
    def warmups(self) -> tuple[TrialSpan, ...]:
        return tuple(trial for trial in self.trials if trial.warmup)

    @property
    def measured(self) -> tuple[TrialSpan, ...]:
        return tuple(trial for trial in self.trials if not trial.warmup)


@dataclass(frozen=True)
class RunProfile:
    role: str
    identity: dict[str, Any]
    plan: dict[str, Any]
    elapsed_ns: int
    run_residual_ns: int
    family_residual_ns: dict[str, int]
    cells: dict[str, CellProfile]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def envelope_data(path: Path, schema_name: str | None = None) -> dict[str, Any]:
    value = load_json(path)
    if schema_name is not None and value.get("schema_name") != schema_name:
        raise ProjectionError(f"artifact schema is invalid: {path}")
    data = value.get("data")
    if not isinstance(data, dict):
        raise ProjectionError(f"artifact is not an envelope: {path}")
    return data


def expanded_plan_data(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if isinstance(value, dict) and isinstance(value.get("data"), dict):
        if value.get("schema_name") != "eos_benchmark_expanded_plan":
            raise ProjectionError("final plan envelope schema is invalid")
        value = value["data"]
    if not isinstance(value, dict):
        raise ProjectionError("final expanded plan is not an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value).encode()).hexdigest()}"


def elapsed_ns(manifest: dict[str, Any]) -> int:
    try:
        started = datetime.fromisoformat(manifest["started_at"].replace("Z", "+00:00"))
        ended = datetime.fromisoformat(manifest["ended_at"].replace("Z", "+00:00"))
    except (AttributeError, KeyError, ValueError) as error:
        raise ProjectionError("run timestamps are invalid") from error
    if started.tzinfo is None or ended.tzinfo is None or ended <= started:
        raise ProjectionError("run timestamps are not positive offset-aware values")
    delta = ended - started
    return (
        delta.days * 86_400 + delta.seconds
    ) * 1_000_000_000 + delta.microseconds * 1_000


def archive_inventory(root: Path) -> tuple[list[dict[str, Any]], int, str]:
    entries: list[dict[str, Any]] = []
    total_bytes = 0
    tree = hashlib.sha256()
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        if path.is_symlink():
            raise ProjectionError(f"archive contains a symlink: {path}")
        relative = path.relative_to(root).as_posix()
        if relative == "archive-manifest.json":
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        entries.append({"path": relative, "bytes": size, "sha256": digest})
        total_bytes += size
        tree.update(relative.encode())
        tree.update(b"\0")
        tree.update(bytes.fromhex(digest.removeprefix("sha256:")))
        tree.update(b"\n")
    return entries, total_bytes, f"sha256:{tree.hexdigest()}"


def verify_archive_inventory(root: Path, manifest: dict[str, Any]) -> None:
    entries, total_bytes, tree_hash = archive_inventory(root)
    if (
        entries != manifest.get("files")
        or total_bytes != manifest.get("archive_bytes")
        or tree_hash != manifest.get("content_tree_sha256")
        or len(entries) != manifest.get("archive_file_count")
    ):
        raise ProjectionError("archive inventory verification failed")


def _required_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectionError(f"{label} is not an object")
    return value


def _validate_protocol_transport(
    campaign: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
    protocol_version: str,
) -> None:
    protocol = _required_dict(campaign.get("protocol"), "protocol")
    expected_version = (
        protocol_version if protocol_version == "v1.1" else "pre-freeze-exp1"
    )
    if protocol.get("version") != expected_version or protocol.get("id") not in (
        PROTOCOLS[protocol_version]["id"],
        None,
    ):
        raise ProjectionError("archive protocol version is invalid")
    environment = _required_dict(manifest.get("environment"), "run environment")
    if protocol_version == "v1.0":
        if environment.get("gateway_endpoint_identity") not in (
            None,
            PROTOCOLS["v1.0"]["environment_identity"],
        ):
            raise ProjectionError("legacy v1.0 gateway identity drift")
        return
    if (
        protocol.get("id") != PROTOCOLS["v1.1"]["id"]
        or environment.get("gateway_endpoint_identity")
        != PROTOCOLS["v1.1"]["environment_identity"]
        or environment.get("gateway_transport") != V11_GATEWAY_TRANSPORT
    ):
        raise ProjectionError("v1.1 named-pipe environment identity is invalid")
    policy = _required_dict(manifest.get("gateway_policy"), "gateway policy")
    if (
        policy.get("protocol_version") != PROTOCOLS["v1.1"]["id"]
        or any(policy.get(key) != value for key, value in V11_GATEWAY_TRANSPORT.items())
        or policy.get("mode") != "isolated"
        or policy.get("isolated_runtime_per_execution_block") is not True
        or policy.get("loopback_only") is not False
    ):
        raise ProjectionError("v1.1 named-pipe gateway policy is invalid")
    planned = plan.get("execution_blocks")
    launched = manifest.get("gateway_execution_blocks")
    if (
        not isinstance(planned, list)
        or not isinstance(launched, list)
        or len(planned) != len(launched)
    ):
        raise ProjectionError("v1.1 execution-block endpoint count is invalid")
    endpoints: set[str] = set()
    for expected, observed in zip(planned, launched):
        endpoint = observed.get("endpoint_uri") if isinstance(observed, dict) else None
        if (
            not isinstance(expected, dict)
            or not isinstance(observed, dict)
            or observed.get("block_id") != expected.get("block_id")
            or observed.get("family_id") != expected.get("family_id")
            or any(
                observed.get(key) != value
                for key, value in V11_GATEWAY_TRANSPORT.items()
            )
            or not isinstance(observed.get("gateway_instance_id"), str)
            or not observed["gateway_instance_id"]
            or not isinstance(endpoint, str)
            or SAFE_NPIPE_ENDPOINT.fullmatch(endpoint) is None
            or endpoint in endpoints
        ):
            raise ProjectionError("v1.1 execution-block endpoint evidence is unsafe")
        endpoints.add(endpoint)


def _stable_host(campaign: dict[str, Any]) -> dict[str, Any]:
    host = _required_dict(campaign.get("final_host"), "final host")
    try:
        return {field: host[field] for field in STABLE_HOST_FIELDS}
    except KeyError as error:
        raise ProjectionError("final-host identity is incomplete") from error


def _cleanup_identity(campaign: dict[str, Any]) -> dict[str, Any]:
    cleanup = _required_dict(campaign.get("cleanup"), "cleanup")
    if (
        cleanup.get("run_workspace_exists") is not False
        or cleanup.get("runtime_exists") is not False
        or cleanup.get("matching_product_processes") != []
        or cleanup.get("run_labeled_containers") != []
        or cleanup.get("gateway_labeled_containers") != []
        or cleanup.get("run_labeled_volumes") != []
        or cleanup.get("gateway_labeled_volumes") != []
        or cleanup.get("product_branch") != "main"
        or cleanup.get("product_status_porcelain") != ""
    ):
        raise ProjectionError("source archive cleanup proof did not pass")
    return {
        key: cleanup.get(key)
        for key in (
            "product_branch",
            "product_commit",
            "product_status_porcelain",
            "product_checkout_policy",
        )
    }


def _identity(campaign: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    benchmark_source = _required_dict(
        campaign.get("benchmark_source"), "benchmark source"
    )
    fixture = _required_dict(campaign.get("fixture"), "fixture")
    product = _required_dict(campaign.get("product"), "product")
    image = _required_dict(campaign.get("image"), "image")
    protocol = _required_dict(campaign.get("protocol"), "protocol")
    paper_git = _required_dict(campaign.get("paper_git"), "paper Git")
    return {
        "benchmark_source": {
            key: benchmark_source.get(key)
            for key in ("content_tree_sha256", "manifest_sha256")
        },
        "fixture": {
            key: fixture.get(key)
            for key in ("fixture_hash", "tree_hash", "manifest_sha256")
        },
        "product": {
            "branch": product.get("branch"),
            "commit": product.get("commit"),
            "dirty": product.get("dirty"),
            "archive": product.get("archive"),
            "binaries": product.get("binaries"),
            "recorded_treatment": product.get("recorded_treatment"),
        },
        "image": {
            key: image.get(key)
            for key in ("id", "requested", "repo_digests", "architecture", "os")
        },
        "docker": campaign.get("docker"),
        "host": _stable_host(campaign),
        "sandbox_limits": campaign.get("sandbox_limits"),
        "definition_snapshot": campaign.get("definition_snapshot"),
        "artifact_schemas": campaign.get("artifact_schemas"),
        "protocol_files": protocol.get("files"),
        "freeze_state": {
            "protocol": protocol.get("freeze_state"),
            "paper_git": paper_git.get("freeze_state"),
        },
        "analysis_and_archiving_code": campaign.get("analysis_and_archiving_code"),
        "treatment": manifest.get("treatment"),
        "lifecycle": manifest.get("fixed_lifecycle_policy"),
        "gateway": manifest.get("gateway_policy"),
    }


def _validated_protocol_files(
    value: Any,
    *,
    protocol_version: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProjectionError("cross-run protocol-file identity is invalid")
    seen: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise ProjectionError("cross-run protocol-file identity is invalid")
        path = entry.get("path")
        size = entry.get("bytes")
        digest = entry.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or path in seen
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(digest, str)
            or SHA256_IDENTITY.fullmatch(digest) is None
        ):
            raise ProjectionError("cross-run protocol-file identity is invalid")
        seen.add(path)
    if protocol_version == "v1.1" and seen != V11_PROTOCOL_FILE_PATHS:
        raise ProjectionError("v1.1 protocol-file identity set is invalid")
    return value


def _validate_prefreeze_campaign(
    campaign: dict[str, Any], protocol_version: str
) -> None:
    protocol = _required_dict(campaign.get("protocol"), "protocol")
    paper_git = _required_dict(campaign.get("paper_git"), "paper Git")
    if (
        protocol.get("freeze_state") != "pre_freeze"
        or paper_git.get("freeze_state") != "pre_freeze_worktree"
    ):
        raise ProjectionError("projection archive is not in the pre-freeze state")
    _validated_protocol_files(
        protocol.get("files"),
        protocol_version=protocol_version,
    )


def _cross_run_provenance(value: Any, *, protocol_version: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectionError("cross-run provenance identity is invalid")
    normalized = json.loads(canonical_json(value))
    freeze_state = normalized.get("freeze_state")
    if freeze_state != {
        "paper_git": "pre_freeze_worktree",
        "protocol": "pre_freeze",
    }:
        raise ProjectionError("cross-run freeze-state identity is invalid")
    protocol_files = _validated_protocol_files(
        normalized.get("protocol_files"),
        protocol_version=protocol_version,
    )
    for entry in protocol_files:
        if entry["path"] in V11_PREFREEZE_MUTABLE_STATUS_PATHS:
            entry["bytes"] = "<pre-freeze-status-bytes>"
            entry["sha256"] = "<pre-freeze-status-sha256>"
    return normalized


def _read_journal(
    path: Path,
    *,
    schema_name: str,
    schema_version: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for expected_sequence, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
                if (
                    value.get("schema_name") != schema_name
                    or value.get("schema_version") != schema_version
                ):
                    raise ProjectionError(f"journal schema is invalid: {path}")
                data = value["data"]
                if data["sequence"] != expected_sequence:
                    raise ProjectionError(f"journal sequence is invalid: {path}")
                if "monotonic_offset_ns" in data:
                    offset = data["monotonic_offset_ns"]
                    if not isinstance(offset, int) or offset < 0:
                        raise ProjectionError(
                            f"journal monotonic offsets are invalid: {path}"
                        )
                records.append(data)
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                raise ProjectionError(f"journal record is invalid: {path}") from error
    return records


def _cell_semantic(cell: dict[str, Any]) -> str:
    required = {
        "family_id": cell.get("family_id"),
        "operation_id": cell.get("operation_id"),
        "operation_semantic_revision": cell.get("operation_semantic_revision"),
        "factor_schema_revision": cell.get("factor_schema_revision"),
        "comparison_key": cell.get("comparison_key"),
        "operation": cell.get("operation"),
        "protocol": {
            key: cell.get("protocol", {}).get(key)
            for key in ("destructive", "timeout_ms", "cleanup")
        },
    }
    return canonical_json(required)


def _plan_semantics(plan: dict[str, Any]) -> dict[str, Any]:
    cells = plan.get("cells")
    blocks = plan.get("execution_blocks")
    if not isinstance(cells, list) or not isinstance(blocks, list):
        raise ProjectionError("expanded plan cells or execution blocks are invalid")
    by_id: dict[str, str] = {}
    semantics: dict[str, dict[str, Any]] = {}
    for cell in cells:
        cell_id = cell.get("cell_id")
        semantic = _cell_semantic(cell)
        if not isinstance(cell_id, str) or cell_id in by_id or semantic in semantics:
            raise ProjectionError("expanded plan cell identity is ambiguous")
        by_id[cell_id] = semantic
        semantics[semantic] = cell
    block_semantics = []
    for block in blocks:
        try:
            cell_keys = [by_id[cell_id] for cell_id in block["cell_ids"]]
        except (KeyError, TypeError) as error:
            raise ProjectionError(
                "execution block references an unknown cell"
            ) from error
        block_semantics.append(
            {
                "family_id": block.get("family_id"),
                "restart_reason": block.get("restart_reason"),
                "cells": cell_keys,
            }
        )
    canonical = _required_dict(plan.get("canonical_plan"), "canonical plan")
    stable_canonical = {
        key: canonical.get(key)
        for key in (
            "configuration_base",
            "seed",
            "environment",
            "operations",
        )
    }
    protocol = _required_dict(canonical.get("protocol"), "canonical protocol")
    stable_canonical["protocol"] = {
        key: protocol.get(key)
        for key in ("order", "resource_interval_ms", "timeout_ms")
    }
    effective = dict(
        _required_dict(plan.get("effective_environment"), "effective environment")
    )
    effective.pop("free_space_bytes", None)
    return {
        "canonical": stable_canonical,
        "effective_environment": effective,
        "cells": set(semantics),
        "blocks": block_semantics,
        "cell_by_id": by_id,
        "cell_data": semantics,
    }


def _validate_plan(
    plan: dict[str, Any],
    *,
    role: str,
) -> dict[str, Any]:
    expected = EXPECTED.get(role)
    if role == "final":
        expected = {
            "name": "paper-good-pass",
            "batches": FINAL_BATCHES,
            "requests": FINAL_REQUESTS,
            "warmups": FINAL_WARMUPS,
            "measured": FINAL_MEASURED,
        }
    assert expected is not None
    estimates = _required_dict(plan.get("estimates"), "plan estimates")
    canonical = _required_dict(plan.get("canonical_plan"), "canonical plan")
    if (
        plan.get("runnable") is not True
        or plan.get("validation") != []
        or canonical.get("name") != expected["name"]
        or plan.get("effective_environment", {}).get("client_cohort") != "product_cli"
        or estimates.get("cell_count") != FINAL_CELLS
        or estimates.get("trial_batch_count") != expected["batches"]
        or estimates.get("issued_operation_request_count") != expected["requests"]
    ):
        raise ProjectionError(f"{role} expanded plan violates the fixed protocol")
    if any(
        cell.get("protocol", {}).get("warmups") != expected["warmups"]
        or cell.get("protocol", {}).get("measured_trials") != expected["measured"]
        for cell in plan.get("cells", [])
    ):
        raise ProjectionError(f"{role} cell repetition policy is invalid")
    return _plan_semantics(plan)


def _state_times(
    events: Iterable[dict[str, Any]],
    *,
    kind: str,
    identity_field: str,
    required_states: tuple[str, ...],
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, Any]]]:
    values: dict[str, dict[str, int]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.get("data", {})
        if payload.get("kind") != kind:
            continue
        identity = payload.get(identity_field)
        state = payload.get("state")
        if not isinstance(identity, str) or state not in required_states:
            raise ProjectionError(f"{kind} event is invalid")
        states = values.setdefault(identity, {})
        if state in states:
            raise ProjectionError(f"{kind} transition is duplicated")
        states[state] = event["monotonic_offset_ns"]
        metadata.setdefault(identity, payload)
        if any(
            metadata[identity].get(key) != payload.get(key)
            for key in metadata[identity]
            if key not in {"state"}
        ):
            raise ProjectionError(f"{kind} identity metadata drifted")
    if not values or any(
        set(states) != set(required_states) for states in values.values()
    ):
        raise ProjectionError(f"{kind} transitions are incomplete")
    if any(
        any(
            states[left] > states[right]
            for left, right in zip(required_states, required_states[1:])
        )
        for states in values.values()
    ):
        raise ProjectionError(f"{kind} transitions are unordered")
    return values, metadata


def _validate_phases(events: list[dict[str, Any]], trials: set[str]) -> None:
    values: dict[tuple[str, str], dict[str, int]] = {}
    for event in events:
        payload = event.get("data", {})
        if payload.get("kind") != "trial_phase":
            continue
        trial_id = payload.get("trial_id")
        phase = payload.get("phase")
        state = payload.get("state")
        if (
            trial_id not in trials
            or phase not in PHASES
            or state
            not in {
                "running",
                "completed",
            }
        ):
            raise ProjectionError("trial phase event is invalid")
        states = values.setdefault((trial_id, phase), {})
        if state in states:
            raise ProjectionError("trial phase transition is duplicated")
        states[state] = event["monotonic_offset_ns"]
    expected = {(trial_id, phase) for trial_id in trials for phase in PHASES}
    if set(values) != expected or any(
        set(states) != {"running", "completed"}
        or states["running"] > states["completed"]
        for states in values.values()
    ):
        raise ProjectionError("trial phase transitions are incomplete or unordered")


def _validate_observations(
    observations: list[dict[str, Any]],
    trial_states: dict[str, dict[str, int]],
    trial_metadata: dict[str, dict[str, Any]],
    cell_by_id: dict[str, str],
    role: str,
) -> dict[str, dict[str, Any]]:
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for envelope in observations:
        record = _required_dict(envelope.get("record"), "observation record")
        kind = record.get("record")
        data = record.get("data")
        if not isinstance(kind, str) or not isinstance(data, dict):
            raise ProjectionError("observation record is invalid")
        by_kind.setdefault(kind, []).append(data)
    trials = by_kind.get("trial", [])
    if len(trials) != EXPECTED[role]["batches"]:
        raise ProjectionError("trial observation count is invalid")
    by_trial: dict[str, dict[str, Any]] = {}
    for trial in trials:
        trial_id = trial.get("trial_id")
        if trial_id not in trial_states or trial_id in by_trial:
            raise ProjectionError("trial observation identity is invalid")
        event_meta = trial_metadata[trial_id]
        warmup = event_meta.get("warmup")
        if (
            trial.get("cell_id") != event_meta.get("cell_id")
            or trial.get("cell_id") not in cell_by_id
            or trial.get("warmup") is not warmup
            or trial.get("kind") != ("warmup" if warmup else "measured")
            or trial.get("status") != "success"
            or trial.get("product_succeeded") is not True
            or trial.get("checks_passed") is not True
            or trial.get("cleanup_baseline_restored") is not True
            or trial.get("infrastructure_failed") is not False
            or trial.get("reportable") is not (not warmup)
        ):
            raise ProjectionError("trial observation did not pass")
        phase_ns: dict[str, int] = {}
        for phase in PHASES:
            value = trial.get(f"{phase}_ns")
            if not isinstance(value, int) or value < 0:
                raise ProjectionError("trial phase duration is invalid")
            phase_ns[phase] = value
        active_ns = (
            trial_states[trial_id]["completed"] - trial_states[trial_id]["preparing"]
        )
        if sum(phase_ns.values()) > active_ns:
            raise ProjectionError("trial phase sum exceeds its active span")
        by_trial[trial_id] = {**trial, "_phase_ns": phase_ns}
    if set(by_trial) != set(trial_states):
        raise ProjectionError("trial events and observations do not match")

    requests = by_kind.get("request", [])
    request_ids: set[str] = set()
    request_counts: dict[str, int] = {}
    for request in requests:
        request_id = request.get("request_id")
        trial_id = request.get("trial_id")
        if (
            not isinstance(request_id, str)
            or request_id in request_ids
            or trial_id not in by_trial
            or request.get("status") != "success"
            or request.get("cell_id") != by_trial[trial_id]["cell_id"]
            or request.get("warmup") is not by_trial[trial_id]["warmup"]
        ):
            raise ProjectionError("request observation is invalid")
        request_ids.add(request_id)
        request_counts[trial_id] = request_counts.get(trial_id, 0) + 1
    if len(requests) != EXPECTED[role]["requests"] or any(
        request_counts.get(trial_id, 0) != trial["request_count"]
        for trial_id, trial in by_trial.items()
    ):
        raise ProjectionError("request observations do not match trial counts")
    operations = by_kind.get("operation", [])
    if len(operations) != len(by_trial) or {
        item.get("trial_id") for item in operations
    } != set(by_trial):
        raise ProjectionError("operation observations do not match trials")
    if any(item.get("passed") is not True for item in by_kind.get("check", [])):
        raise ProjectionError("a correctness observation failed")
    return by_trial


def load_run_profile(
    root: Path,
    role: str,
    *,
    verify_inventory: bool = True,
    protocol_version: str = "v1.0",
) -> RunProfile:
    if protocol_version not in PROTOCOLS:
        raise ProjectionError("unsupported EXP1 protocol version")
    expected = EXPECTED[role]
    root = root.resolve(strict=True)
    archive_manifest = _required_dict(
        load_json(root / "archive-manifest.json"), "archive manifest"
    )
    if verify_inventory:
        verify_archive_inventory(root, archive_manifest)
    campaign = _required_dict(
        load_json(root / "campaign-manifest.json"), "campaign manifest"
    )
    _validate_prefreeze_campaign(campaign, protocol_version)
    manifest = envelope_data(
        root / "raw/run-manifest.json", "eos_benchmark_run_manifest"
    )
    plan = envelope_data(root / "raw/expanded-plan.json", "eos_benchmark_expanded_plan")
    if (
        archive_manifest.get("run_id") != manifest.get("run_id")
        or campaign.get("run_id") != manifest.get("run_id")
        or archive_manifest.get("disposition") != expected["disposition"]
        or campaign.get("disposition") != expected["disposition"]
        or archive_manifest.get("run_status") != "completed"
        or campaign.get("run_status") != "completed"
        or campaign.get("state") != "completed"
        or campaign.get("correctness") != "pass"
        or campaign.get("eligibility") != expected["eligibility"]
        or manifest.get("state") != "completed"
        or manifest.get("correctness") != "pass"
        or manifest.get("failure") is not None
        or manifest.get("name") != expected["name"]
        or manifest.get("plan_hash") != plan.get("plan_hash")
        or archive_manifest.get("plan_hash") != plan.get("plan_hash")
    ):
        raise ProjectionError(f"{role} archive terminal provenance is invalid")
    if archive_manifest.get("protocol_version") not in (
        None if protocol_version == "v1.0" else protocol_version,
        protocol_version,
    ):
        raise ProjectionError(f"{role} archive protocol identity is invalid")
    _validate_protocol_transport(campaign, manifest, plan, protocol_version)
    cleanup = _cleanup_identity(campaign)
    if cleanup["product_commit"] != campaign.get("product", {}).get("commit"):
        raise ProjectionError("post-run product identity drifted")
    raw_corpus = _required_dict(campaign.get("raw_corpus"), "raw corpus")
    if (
        raw_corpus.get("events_sha256") != sha256_file(root / "raw/events.ndjson")
        or raw_corpus.get("observations_sha256")
        != sha256_file(root / "raw/observations.ndjson")
        or campaign.get("plan", {}).get("expanded_plan_sha256")
        != sha256_file(root / "raw/expanded-plan.json")
    ):
        raise ProjectionError("raw corpus identity is invalid")
    semantics = _validate_plan(plan, role=role)
    events = _read_journal(
        root / "raw/events.ndjson",
        schema_name="eos_benchmark_event",
        schema_version=1,
    )
    observations = _read_journal(
        root / "raw/observations.ndjson",
        schema_name="eos_benchmark_observation",
        schema_version=5,
    )
    family_states, _ = _state_times(
        events,
        kind="family_state",
        identity_field="family",
        required_states=("preparing", "running", "completed"),
    )
    cell_states, _ = _state_times(
        events,
        kind="cell_state",
        identity_field="cell_id",
        required_states=("preparing", "running", "completed"),
    )
    trial_states, trial_metadata = _state_times(
        events,
        kind="trial_state",
        identity_field="trial_id",
        required_states=("preparing", "completed"),
    )
    _validate_phases(events, set(trial_states))
    trial_observations = _validate_observations(
        observations,
        trial_states,
        trial_metadata,
        semantics["cell_by_id"],
        role,
    )
    if set(cell_states) != set(semantics["cell_by_id"]):
        raise ProjectionError("cell events do not match the expanded plan")
    family_blocks = {
        block["family_id"]: block["cell_ids"] for block in plan["execution_blocks"]
    }
    if set(family_states) != set(family_blocks):
        raise ProjectionError("family events do not match execution blocks")
    elapsed = elapsed_ns(manifest)
    family_durations = {
        family: states["completed"] - states["preparing"]
        for family, states in family_states.items()
    }
    run_residual = elapsed - sum(family_durations.values())
    if run_residual < 0:
        raise ProjectionError("run residual duration is negative")
    family_residual: dict[str, int] = {}
    for family, cell_ids in family_blocks.items():
        prior_completed = -1
        cell_total = 0
        for cell_id in cell_ids:
            states = cell_states[cell_id]
            if (
                states["preparing"] < family_states[family]["preparing"]
                or states["completed"] > family_states[family]["completed"]
                or states["preparing"] < prior_completed
            ):
                raise ProjectionError("cell intervals are not sequentially nested")
            prior_completed = states["completed"]
            cell_total += states["completed"] - states["preparing"]
        residual = family_durations[family] - cell_total
        if residual < 0:
            raise ProjectionError("family residual duration is negative")
        family_residual[family] = residual
    trials_by_cell: dict[str, list[tuple[TrialSpan, dict[str, Any]]]] = {
        cell_id: [] for cell_id in cell_states
    }
    for trial_id, states in trial_states.items():
        metadata = trial_metadata[trial_id]
        cell_id = metadata["cell_id"]
        if cell_id not in trials_by_cell:
            raise ProjectionError("trial references an unknown cell")
        observation = trial_observations[trial_id]
        trials_by_cell[cell_id].append(
            (
                TrialSpan(
                    trial_id=trial_id,
                    warmup=metadata["warmup"],
                    start_ns=states["preparing"],
                    end_ns=states["completed"],
                    phase_ns=observation["_phase_ns"],
                ),
                observation,
            )
        )
    cells: dict[str, CellProfile] = {}
    for cell_id, trial_pairs in trials_by_cell.items():
        trial_pairs.sort(key=lambda item: item[0].start_ns)
        trials = tuple(item[0] for item in trial_pairs)
        expected_warmups = expected["warmups"]
        expected_measured = expected["measured"]
        if (
            len(trials) != expected_warmups + expected_measured
            or [trial.warmup for trial in trials]
            != [True] * expected_warmups + [False] * expected_measured
        ):
            raise ProjectionError("cell trial order or count is invalid")
        states = cell_states[cell_id]
        if (
            trials[0].start_ns < states["preparing"]
            or trials[-1].end_ns > states["completed"]
        ):
            raise ProjectionError("trial intervals escaped their cell")
        gaps = tuple(
            right.start_ns - left.end_ns for left, right in zip(trials, trials[1:])
        )
        if any(gap < 0 for gap in gaps):
            raise ProjectionError("trial intervals overlap")
        semantic = semantics["cell_by_id"][cell_id]
        cell = semantics["cell_data"][semantic]
        profile = CellProfile(
            semantic_key=semantic,
            semantic_sha256=canonical_sha256(json.loads(semantic)),
            family_id=cell["family_id"],
            operation_id=cell["operation_id"],
            leading_ns=trials[0].start_ns - states["preparing"],
            trailing_ns=states["completed"] - trials[-1].end_ns,
            trials=trials,
            gaps_ns=gaps,
        )
        cells[semantic] = profile
    return RunProfile(
        role=role,
        identity={
            "run_id": manifest["run_id"],
            "protocol_version": protocol_version,
            "plan_hash": plan["plan_hash"],
            "archive_manifest_sha256": sha256_file(root / "archive-manifest.json"),
            "archive_content_tree_sha256": archive_manifest["content_tree_sha256"],
            "campaign_manifest_sha256": sha256_file(root / "campaign-manifest.json"),
            "raw_events_sha256": raw_corpus["events_sha256"],
            "raw_observations_sha256": raw_corpus["observations_sha256"],
            "provenance": _identity(campaign, manifest),
        },
        plan=semantics,
        elapsed_ns=elapsed,
        run_residual_ns=run_residual,
        family_residual_ns=family_residual,
        cells=cells,
    )


def validate_cross_run(
    smoke: RunProfile,
    pilot: RunProfile,
    final_plan: dict[str, Any],
) -> dict[str, Any]:
    final_semantics = _validate_plan(final_plan, role="final")
    protocol_version = smoke.identity.get("protocol_version")
    if (
        protocol_version not in PROTOCOLS
        or pilot.identity.get("protocol_version") != protocol_version
    ):
        raise ProjectionError("smoke and pilot protocol versions drifted")
    if _cross_run_provenance(
        smoke.identity["provenance"],
        protocol_version=protocol_version,
    ) != _cross_run_provenance(
        pilot.identity["provenance"],
        protocol_version=protocol_version,
    ):
        raise ProjectionError("smoke and pilot provenance identities drifted")
    for candidate in (pilot.plan, final_semantics):
        if (
            smoke.plan["canonical"] != candidate["canonical"]
            or smoke.plan["effective_environment"] != candidate["effective_environment"]
            or smoke.plan["cells"] != candidate["cells"]
            or smoke.plan["blocks"] != candidate["blocks"]
        ):
            raise ProjectionError("smoke, pilot, and final plan semantics drifted")
    return final_semantics


def ceil_fraction(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def seconds_string(nanoseconds: int) -> str:
    whole, fraction = divmod(nanoseconds, 1_000_000_000)
    return f"{whole}.{fraction:09d}"


def fraction_value(value: Fraction) -> dict[str, int]:
    return {
        "numerator_ns": value.numerator,
        "denominator": value.denominator,
        "ceil_ns": ceil_fraction(value),
    }


def project_structural(
    smoke: RunProfile,
    pilot: RunProfile,
    final_plan: dict[str, Any],
    *,
    final_plan_sha256: str,
    script_sha256: str,
    protocol_version: str = "v1.0",
) -> dict[str, Any]:
    validate_cross_run(smoke, pilot, final_plan)
    family_ids = sorted(pilot.family_residual_ns)
    cell_keys = sorted(pilot.cells)
    if set(smoke.family_residual_ns) != set(family_ids) or set(smoke.cells) != set(
        cell_keys
    ):
        raise ProjectionError("smoke and pilot structural identities drifted")
    run_fixed = max(smoke.run_residual_ns, pilot.run_residual_ns)
    family_fixed = {
        family: max(
            smoke.family_residual_ns[family],
            pilot.family_residual_ns[family],
        )
        for family in family_ids
    }
    central = Fraction(run_fixed + sum(family_fixed.values()))
    envelope = run_fixed + sum(family_fixed.values())
    cell_results: list[dict[str, Any]] = []
    for key in cell_keys:
        smoke_cell = smoke.cells[key]
        pilot_cell = pilot.cells[key]
        leading = max(smoke_cell.leading_ns, pilot_cell.leading_ns)
        trailing = max(smoke_cell.trailing_ns, pilot_cell.trailing_ns)
        fixed = leading + trailing
        warmups = pilot_cell.warmups
        measured = pilot_cell.measured
        smoke_cold = smoke_cell.measured
        if (
            len(warmups) != 2
            or len(measured) != 5
            or len(smoke_cold) != 1
            or len(pilot_cell.gaps_ns) != 6
        ):
            raise ProjectionError("source cell does not have the required trial shape")
        warmup_gaps = pilot_cell.gaps_ns[:2]
        measured_gaps = pilot_cell.gaps_ns[2:]
        if len(measured_gaps) != 4:
            raise ProjectionError("pilot measured transitions are incomplete")
        central_cell = (
            Fraction(fixed)
            + sum((Fraction(trial.active_ns) for trial in warmups), Fraction())
            + sum((Fraction(gap) for gap in warmup_gaps), Fraction())
            + Fraction(
                FINAL_MEASURED * sum(trial.active_ns for trial in measured),
                len(measured),
            )
            + Fraction(
                (FINAL_MEASURED - 1) * sum(measured_gaps),
                len(measured_gaps),
            )
        )
        warmup_active_max = max(
            [trial.active_ns for trial in warmups]
            + [trial.active_ns for trial in smoke_cold]
        )
        measured_active_max = max(trial.active_ns for trial in measured)
        gap_max = max(pilot_cell.gaps_ns)
        envelope_cell = (
            fixed
            + FINAL_WARMUPS * warmup_active_max
            + FINAL_MEASURED * measured_active_max
            + (FINAL_WARMUPS + FINAL_MEASURED - 1) * gap_max
        )
        central += central_cell
        envelope += envelope_cell
        cell_results.append(
            {
                "semantic_sha256": pilot_cell.semantic_sha256,
                "family_id": pilot_cell.family_id,
                "operation_id": pilot_cell.operation_id,
                "fixed": {
                    "leading_ns": leading,
                    "trailing_ns": trailing,
                    "total_ns": fixed,
                },
                "source_samples": {
                    "smoke_cold_active_ns": [trial.active_ns for trial in smoke_cold],
                    "pilot_warmup_active_ns": [trial.active_ns for trial in warmups],
                    "pilot_measured_active_ns": [trial.active_ns for trial in measured],
                    "pilot_transition_gap_ns": list(pilot_cell.gaps_ns),
                },
                "central_projected": fraction_value(central_cell),
                "envelope_projected_ns": envelope_cell,
            }
        )
    central_ns = ceil_fraction(central)
    runtime_pass = (
        pilot.elapsed_ns <= LIMIT_NS and central_ns <= LIMIT_NS and envelope <= LIMIT_NS
    )
    return {
        "schema_version": 2,
        "model_revision": 1,
        "protocol_version": protocol_version,
        "purpose": "EXP1 Gate 3 runtime projection; not manuscript evidence",
        "analysis_script_sha256": script_sha256,
        "final_plan": {
            "sha256": final_plan_sha256,
            "plan_hash": final_plan["plan_hash"],
            "cells": FINAL_CELLS,
            "warmups_per_cell": FINAL_WARMUPS,
            "measured_trials_per_cell": FINAL_MEASURED,
            "trial_batches": FINAL_BATCHES,
            "issued_operation_requests": FINAL_REQUESTS,
        },
        "limit_ns": LIMIT_NS,
        "inputs": {
            "smoke": smoke.identity,
            "pilot": pilot.identity,
        },
        "decomposition": {
            "run_fixed_ns": run_fixed,
            "family_fixed_ns": family_fixed,
            "cells": cell_results,
        },
        "models": {
            "pilot_elapsed_lower_bound_ns": pilot.elapsed_ns,
            "central_structural": fraction_value(central),
            "observed_envelope_ns": envelope,
        },
        "display_seconds": {
            "pilot_elapsed": seconds_string(pilot.elapsed_ns),
            "central_structural": seconds_string(central_ns),
            "observed_envelope": seconds_string(envelope),
            "limit": seconds_string(LIMIT_NS),
        },
        "pass_conditions": {
            "pilot_elapsed_within_limit": pilot.elapsed_ns <= LIMIT_NS,
            "central_structural_within_limit": central_ns <= LIMIT_NS,
            "observed_envelope_within_limit": envelope <= LIMIT_NS,
        },
        "gate_3_runtime_pass": runtime_pass,
        "decision": (
            "pass_runtime_projection"
            if runtime_pass
            else "block_freeze_and_final_runtime_projection_exceeds_1400_seconds"
        ),
        "scientific_use": (
            "Exploratory capacity decision only. No smoke, pilot, or projected "
            "value is eligible for manuscript tables."
        ),
    }


def render_json(value: dict[str, Any]) -> str:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser()
    command.add_argument("--smoke-archive", type=Path, required=True)
    command.add_argument("--pilot-archive", type=Path, required=True)
    command.add_argument("--final-plan", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--protocol-version", choices=sorted(PROTOCOLS), required=True)
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        smoke_path = args.smoke_archive.resolve(strict=True)
        pilot_path = args.pilot_archive.resolve(strict=True)
        final_plan_path = args.final_plan.resolve(strict=True)
        output = args.output.resolve()
        if output.exists() or output.is_symlink():
            raise ProjectionError("projection output already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        final_plan = expanded_plan_data(final_plan_path)
        result = project_structural(
            load_run_profile(
                smoke_path, "smoke", protocol_version=args.protocol_version
            ),
            load_run_profile(
                pilot_path, "pilot", protocol_version=args.protocol_version
            ),
            final_plan,
            final_plan_sha256=sha256_file(final_plan_path),
            script_sha256=sha256_file(Path(__file__).resolve(strict=True)),
            protocol_version=args.protocol_version,
        )
        rendered = render_json(result)
        output.write_text(rendered, encoding="utf-8", newline="\n")
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        ProjectionError,
    ) as error:
        print(f"projection_error: {error}", file=sys.stderr)
        return 1
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
