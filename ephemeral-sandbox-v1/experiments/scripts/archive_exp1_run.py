#!/usr/bin/env python3
"""Archive and verify one terminal EXP1 run without altering raw evidence."""

from __future__ import annotations

import argparse
import base64
import binascii
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

DISPOSITIONS = {
    "smoke": {
        "name": "paper-env-smoke",
        "cells": 19,
        "batches": 19,
        "requests": 55,
        "warmups": 0,
        "measured": 1,
    },
    "exploratory": {
        "name": "paper-pilot",
        "cells": 19,
        "batches": 133,
        "requests": 385,
        "warmups": 2,
        "measured": 5,
    },
    "final": {
        "name": "paper-good-pass",
        "cells": 19,
        "batches": 1938,
        "requests": 5610,
        "warmups": 2,
        "measured": 100,
    },
}

CLI_HELP = {
    "gateway": ("sandbox-gateway.exe", "--help"),
    "manager": ("sandbox-manager-cli.exe", "help"),
    "observability": ("sandbox-observability-cli.exe", "help"),
    "runtime": ("sandbox-runtime-cli.exe", "help"),
}

BENCHMARK_EXCLUDED_PARTS = {
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "playwright-report",
    "test-results",
}
BENCHMARK_GIT_EXCLUSIONS = [
    *[
        f":(exclude,glob)benchmark/**/{part}/**"
        for part in sorted(BENCHMARK_EXCLUDED_PARTS)
    ],
    ":(exclude,glob)benchmark/**/*.pyc",
]
PAPER_PROTOCOL_PATHS = (
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
)
PAPER_ANALYSIS_PATHS = (
    "benchmark/backend/benchmark_lab/derivation.py",
    "benchmark/backend/benchmark_lab/reports.py",
    "experiments/scripts/archive_exp1_run.py",
    "experiments/scripts/project_exp1_final_runtime.py",
    "experiments/analysis/scripts/generate_exp1_tables.py",
)
PAPER_FROZEN_SCOPE = (
    "benchmark",
    *(
        path
        for path in PAPER_PROTOCOL_PATHS
        if not path.startswith("benchmark/")
    ),
    *(
        path
        for path in PAPER_ANALYSIS_PATHS
        if not path.startswith("benchmark/")
    ),
)
EXP1_EXPECTED_HOST = {
    "computer_name": "DESKTOP-OLP1ADS",
    "operating_system": "windows",
    "architecture": "x64",
    "os_build_number": 26200,
    "logical_processors": 48,
    "total_memory_bytes": 137_438_953_472,
    "filesystem": "NTFS",
}
EXP1_EXPECTED_SANDBOX_LIMITS = {
    "profile": "standard",
    "nano_cpus": 1_000_000_000,
    "vcpus": 1,
    "memory_bytes": 536_870_912,
    "pids_limit": 256,
}
RUN_STATUSES = {"completed", "failed"}
CLI_EVIDENCE_COMMIT_PROTOCOL = "metadata-packed-payload-fsync-v1"
PROTOCOLS = {
    "v1.0": {
        "id": "ephemeral-sandbox-v1-practical-performance-v1.0",
        "final_tag": "paper-v1-freeze",
        "gateway_endpoint_identity": "isolated_loopback_per_execution_block",
    },
    "v1.1": {
        "id": "ephemeral-sandbox-v1-practical-performance-v1.1",
        "final_tag": "paper-v1.1-freeze",
        "gateway_endpoint_identity": (
            "isolated_windows_named_pipe_per_execution_block"
        ),
    },
}
V11_GATEWAY_TRANSPORT = {
    "transport": "windows_named_pipe",
    "scope": "local_only",
    "rotation": "per_execution_block",
}
SAFE_NPIPE_ENDPOINT = re.compile(
    r"npipe://\./pipe/[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z"
)


class ArchiveError(RuntimeError):
    """The source corpus or archive contract failed validation."""


def archive_eligibility(disposition: str, run_status: str) -> str:
    if run_status == "failed":
        return "failed_ineligible"
    if run_status != "completed":
        raise ArchiveError("archive run status is invalid")
    if disposition == "smoke":
        return "qualification_only"
    if disposition == "exploratory":
        return "exploratory_ineligible"
    if disposition == "final":
        return "frozen_final_candidate"
    raise ArchiveError("archive disposition is invalid")


def protocol_version_from_campaign(
    campaign: dict[str, Any], *, disposition: str
) -> str:
    protocol = campaign.get("protocol")
    if not isinstance(protocol, dict):
        raise ArchiveError("campaign protocol provenance is missing")
    version = protocol.get("version")
    if version == "v1.1":
        if protocol.get("id") != PROTOCOLS["v1.1"]["id"]:
            raise ArchiveError("campaign v1.1 protocol identity is invalid")
        return "v1.1"
    expected = "v1.0" if disposition == "final" else "pre-freeze-exp1"
    if version == expected and protocol.get("id") in (None, PROTOCOLS["v1.0"]["id"]):
        return "v1.0"
    raise ArchiveError("campaign protocol version is invalid")


def validate_protocol_transport(
    *,
    protocol_version: str,
    environment: dict[str, Any],
    manifest: dict[str, Any],
    plan: dict[str, Any],
    completed: bool,
) -> None:
    if protocol_version not in PROTOCOLS:
        raise ArchiveError("unsupported EXP1 protocol version")
    if protocol_version == "v1.0":
        identity = environment.get("gateway_endpoint_identity")
        if identity not in (None, PROTOCOLS["v1.0"]["gateway_endpoint_identity"]):
            raise ArchiveError("legacy v1.0 gateway endpoint identity drift")
        return

    if (
        environment.get("gateway_endpoint_identity")
        != PROTOCOLS["v1.1"]["gateway_endpoint_identity"]
        or environment.get("gateway_transport") != V11_GATEWAY_TRANSPORT
    ):
        raise ArchiveError("v1.1 named-pipe environment identity is invalid")
    policy = manifest.get("gateway_policy")
    if (
        not isinstance(policy, dict)
        or policy.get("protocol_version") != PROTOCOLS["v1.1"]["id"]
        or any(policy.get(key) != value for key, value in V11_GATEWAY_TRANSPORT.items())
        or policy.get("mode") != "isolated"
        or policy.get("isolated_runtime_per_execution_block") is not True
        or policy.get("loopback_only") is not False
    ):
        raise ArchiveError("v1.1 named-pipe gateway policy is invalid")
    blocks = plan.get("execution_blocks")
    launched = manifest.get("gateway_execution_blocks")
    if not isinstance(blocks, list) or not isinstance(launched, list):
        raise ArchiveError("v1.1 execution-block endpoint evidence is missing")
    if (completed and len(launched) != len(blocks)) or len(launched) > len(blocks):
        raise ArchiveError("v1.1 execution-block endpoint count is invalid")
    endpoints: set[str] = set()
    for expected, observed in zip(blocks, launched):
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
            raise ArchiveError("v1.1 execution-block endpoint evidence is unsafe")
        endpoints.add(endpoint)


def benchmark_source_capture_boundary(run_status: str) -> str:
    if run_status == "completed":
        return (
            "captured after terminal cleanup; no benchmark source file "
            "changed during or between the run clock and this capture"
        )
    if run_status == "failed":
        return (
            "captured after terminal cleanup and after the failed-corpus "
            "archival-tool amendment; archived benchmark source is post-run "
            "preservation code and must not be interpreted as byte-identical "
            "run-time source"
        )
    raise ArchiveError("archive run status is invalid")


def product_checkout_capture_boundary(run_status: str) -> str:
    if run_status == "completed":
        return "post-run checkout is clean and exactly matches the recorded treatment"
    if run_status == "failed":
        return (
            "post-run checkout HEAD and status were captured after terminal cleanup; "
            "they may reflect a subsequent corrective amendment and are not the "
            "at-run treatment identity"
        )
    raise ArchiveError("archive run status is invalid")


def validate_cleanup_proof(
    cleanup: dict[str, Any],
    *,
    run_status: str,
    recorded_product_commit: str,
) -> None:
    if (
        cleanup.get("run_workspace_exists") is not False
        or cleanup.get("runtime_exists") is not False
        or cleanup.get("matching_product_processes") != []
        or cleanup.get("run_labeled_containers") != []
        or cleanup.get("gateway_labeled_containers") != []
        or cleanup.get("run_labeled_volumes") != []
        or cleanup.get("gateway_labeled_volumes") != []
        or cleanup.get("product_branch") != "main"
    ):
        raise ArchiveError("post-run cleanup proof failed")
    status = cleanup.get("product_status_porcelain")
    if not isinstance(status, str):
        raise ArchiveError("post-run product status proof is invalid")
    if run_status == "completed":
        if (
            status
            or cleanup.get("product_commit") != recorded_product_commit
            or cleanup.get("product_checkout_policy")
            not in (None, "clean_exact_recorded_treatment")
        ):
            raise ArchiveError("completed archive product checkout drift")
    elif run_status == "failed":
        if (
            cleanup.get("product_checkout_policy")
            != "post_run_drift_recorded_failed_ineligible"
            or not _is_git_sha1(cleanup.get("product_commit"))
        ):
            raise ArchiveError("failed archive product checkout proof is invalid")
    else:
        raise ArchiveError("archive run status is invalid")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def envelope_data(path: Path) -> dict[str, Any]:
    value = load_json(path)
    data = value.get("data")
    if not isinstance(data, dict):
        raise ArchiveError(f"artifact is not a JSON envelope: {path}")
    return data


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_exp1_environment(environment: dict[str, Any]) -> None:
    if not isinstance(environment, dict):
        raise ArchiveError("recorded run environment is not an object")
    host = environment.get("host")
    limits = environment.get("sandbox_limits")
    if not isinstance(host, dict) or not isinstance(limits, dict):
        raise ArchiveError(
            "recorded run environment lacks final-host or sandbox-limit evidence"
        )
    required_host_text = (
        "os_caption",
        "os_version",
        "cpu_model",
        "volume_root",
        "captured_at",
        "capture_source",
    )
    if any(
        not isinstance(host.get(field), str) or not host[field].strip()
        for field in required_host_text
    ):
        raise ArchiveError("recorded final-host text evidence is incomplete")
    if host.get("logical_processors") != host.get("processor_logical_processors"):
        raise ArchiveError("recorded logical processor counts disagree")
    host_mismatches = [
        field
        for field, expected in EXP1_EXPECTED_HOST.items()
        if (
            str(host.get(field)).casefold() != expected.casefold()
            if isinstance(expected, str)
            else host.get(field) != expected
        )
    ]
    if host.get("capture_boundary") != "run_start_before_gateway_and_measurement":
        host_mismatches.append("capture_boundary")
    if host_mismatches:
        raise ArchiveError(
            "recorded final-host identity drift: "
            + ", ".join(sorted(set(host_mismatches)))
        )
    limit_mismatches = [
        field
        for field, expected in EXP1_EXPECTED_SANDBOX_LIMITS.items()
        if limits.get(field) != expected
    ]
    authority = limits.get("authority")
    if (
        not isinstance(authority, dict)
        or authority.get("kind") != "released_gateway_configuration"
        or not isinstance(authority.get("path"), str)
        or not authority["path"]
        or not isinstance(authority.get("sha256"), str)
        or len(authority["sha256"]) != 71
        or not authority["sha256"].startswith("sha256:")
        or authority.get("create_request_override") != "none"
        or authority.get("capture_boundary")
        != "run_start_before_gateway_and_measurement"
    ):
        limit_mismatches.append("authority")
    if limit_mismatches:
        raise ArchiveError(
            "recorded effective sandbox limit drift: "
            + ", ".join(sorted(set(limit_mismatches)))
        )


def run_checked(
    args: list[str],
    *,
    cwd: Path,
    timeout: float = 30.0,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ArchiveError(f"preflight command failed to execute: {args[0]}") from error
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace")[:4096]
        raise ArchiveError(
            f"preflight command exited {completed.returncode}: {args[0]}: {detail}"
        )
    return completed


def git_value(product_root: Path, *args: str) -> str:
    return (
        run_checked(["git", *args], cwd=product_root)
        .stdout.decode("utf-8", "strict")
        .strip()
    )


def product_freeze_tag(
    product_root: Path,
    *,
    disposition: str,
    product_commit: str,
    protocol_version: str = "v1.0",
) -> dict[str, Any]:
    if protocol_version not in PROTOCOLS:
        raise ArchiveError("unsupported EXP1 protocol version")
    name = PROTOCOLS[protocol_version]["final_tag"]
    if disposition != "final":
        return {
            "availability": "unavailable",
            "reason": "pre-freeze smoke/exploratory archive",
            "required_final_tag": name,
        }
    reference = f"refs/tags/{name}"
    tag_object = git_value(product_root, "rev-parse", f"{reference}^{{tag}}")
    object_type = git_value(product_root, "cat-file", "-t", tag_object)
    peeled_commit = git_value(product_root, "rev-parse", f"{reference}^{{}}")
    if (
        object_type != "tag"
        or not _is_git_sha1(tag_object)
        or not _is_git_sha1(peeled_commit)
        or peeled_commit != product_commit
    ):
        raise ArchiveError(
            f"final product {name} tag is absent, lightweight, "
            "or does not peel to the measured product commit"
        )
    return {
        "availability": "available",
        "name": name,
        "reference": reference,
        "object_type": object_type,
        "tag_object": tag_object,
        "peeled_commit": peeled_commit,
    }


def _is_git_sha1(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value)
    )


def paper_git_provenance(paper_root: Path, *, disposition: str) -> dict[str, Any]:
    git_root = Path(git_value(paper_root, "rev-parse", "--show-toplevel")).resolve(
        strict=True
    )
    frozen_scope = list(PAPER_FROZEN_SCOPE)
    status = git_value(
        paper_root,
        "status",
        "--porcelain=v1",
        "--",
        *frozen_scope,
        *BENCHMARK_GIT_EXCLUSIONS,
    )
    dirty = bool(status)
    if disposition == "final" and dirty:
        raise ArchiveError(
            "final paper benchmark/protocol/analysis scope is not a clean frozen commit"
        )
    return {
        "root": os.fspath(git_root),
        "paper_root": os.fspath(paper_root.resolve(strict=True)),
        "frozen_scope": frozen_scope,
        "generated_exclusions": BENCHMARK_GIT_EXCLUSIONS,
        "branch": git_value(paper_root, "branch", "--show-current"),
        "commit": git_value(paper_root, "rev-parse", "HEAD"),
        "dirty": dirty,
        "status_porcelain": status.splitlines(),
        "freeze_state": (
            "clean_frozen_commit" if disposition == "final" else "pre_freeze_worktree"
        ),
    }


def validate_source(
    run_path: Path,
    *,
    run_id: str,
    disposition: str,
    run_status: str,
    expected_plan_hash: str,
    protocol_version: str = "v1.0",
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected = DISPOSITIONS[disposition]
    manifest = envelope_data(run_path / "run-manifest.json")
    plan = envelope_data(run_path / "expanded-plan.json")
    report = envelope_data(run_path / "report.json")
    intent = envelope_data(run_path / "intent-plan.json")
    if manifest["run_id"] != run_id or report["run_id"] != run_id:
        raise ArchiveError("run identity mismatch")
    if manifest["name"] != expected["name"] or intent["name"] != expected["name"]:
        raise ArchiveError("preset identity mismatch")
    if run_status not in RUN_STATUSES:
        raise ArchiveError("requested archive run status is invalid")
    if manifest["state"] != run_status or report["state"] != run_status:
        raise ArchiveError("run state does not match requested archive status")
    if run_status == "completed":
        if manifest["correctness"] != "pass" or report["correctness_verdict"] != "pass":
            raise ArchiveError("run correctness is not pass")
    else:
        failure = manifest.get("failure")
        if (
            manifest.get("correctness") != "fail"
            or report.get("correctness_verdict") != "fail"
            or not isinstance(failure, dict)
            or not isinstance(failure.get("code"), str)
            or not failure["code"]
            or not isinstance(failure.get("message"), str)
            or not failure["message"]
        ):
            raise ArchiveError(
                "failed archive lacks explicit terminal failure evidence"
            )
    if (
        manifest["plan_hash"] != expected_plan_hash
        or plan["plan_hash"] != expected_plan_hash
    ):
        raise ArchiveError("plan hash mismatch")
    estimates = plan["estimates"]
    for key, expected_value in (
        ("cell_count", expected["cells"]),
        ("trial_batch_count", expected["batches"]),
        ("issued_operation_request_count", expected["requests"]),
    ):
        if estimates[key] != expected_value:
            raise ArchiveError(f"plan estimate mismatch: {key}")
    if plan["effective_environment"]["client_cohort"] != "product_cli":
        raise ArchiveError("archive source is not product_cli")
    validate_exp1_environment(manifest["environment"])
    validate_protocol_transport(
        protocol_version=protocol_version,
        environment=manifest["environment"],
        manifest=manifest,
        plan=plan,
        completed=run_status == "completed",
    )
    if (
        len(plan["cells"]) != expected["cells"]
        or len(report["cells"]) != expected["cells"]
    ):
        raise ArchiveError("cell count mismatch")
    for cell in plan["cells"]:
        protocol = cell["protocol"]
        if (
            protocol["warmups"] != expected["warmups"]
            or protocol["measured_trials"] != expected["measured"]
            or cell["operation"]["cell"].get("workspace_profile") != "paper-100m"
        ):
            raise ArchiveError("cell protocol or workspace profile drift")
    if run_status == "completed":
        for cell in report["cells"]:
            counts = cell["counts"]
            if (
                counts["warmup"] != expected["warmups"]
                or counts["measured_attempted"] != expected["measured"]
                or counts["successful"] != expected["measured"]
                or any(
                    counts[field] != 0
                    for field in (
                        "product_failed",
                        "correctness_failed",
                        "infrastructure_failed",
                        "cleanup_invalid",
                        "missing_primary_latency",
                    )
                )
            ):
                raise ArchiveError("report cell is not fully reportable")
            if any(
                check["failed"] or check["passed"] != expected["measured"]
                for check in cell["checks"]
            ):
                raise ArchiveError("report correctness check failed")
        if report["warnings"]:
            raise ArchiveError("report contains warnings")
    return manifest, plan, report, intent


def inspect_observations(
    run_path: Path,
    *,
    expected_requests: int,
    expected_batches: int,
    allow_partial: bool = False,
) -> tuple[dict[str, Any], list[bytes]]:
    counts: collections.Counter[str] = collections.Counter()
    metric_availability: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    request_ids: list[str] = []
    resource_lines: list[bytes] = []
    sequences: list[int] = []
    with (run_path / "observations.ndjson").open("rb") as stream:
        for raw_line in stream:
            envelope = json.loads(raw_line)
            data = envelope["data"]
            sequences.append(data["sequence"])
            record = data["record"]
            kind = record["record"]
            payload = record["data"]
            counts[kind] += 1
            if kind == "request":
                request_ids.append(payload["request_id"])
            elif kind == "resource":
                reading = payload["reading"]
                metric_availability[reading["metric_id"]][
                    reading["value"]["availability"]
                ] += 1
                resource_lines.append(raw_line)
    if sequences != list(range(1, len(sequences) + 1)):
        raise ArchiveError("observation sequence is not contiguous")
    complete = (
        counts["request"] == expected_requests
        and len(set(request_ids)) == expected_requests
        and counts["trial"] == expected_batches
        and counts["operation"] == expected_batches
        and bool(resource_lines)
    )
    valid_partial = (
        allow_partial
        and len(set(request_ids)) == len(request_ids)
        and counts["request"] <= expected_requests
        and counts["trial"] <= expected_batches
        and counts["operation"] <= expected_batches
    )
    if not complete and not valid_partial:
        raise ArchiveError("observation counts or identities are incomplete")
    return (
        {
            "schema_version": 1,
            "observation_counts": dict(sorted(counts.items())),
            "resource_availability": {
                metric: dict(sorted(availability.items()))
                for metric, availability in sorted(metric_availability.items())
            },
            "request_id_count": len(request_ids),
            "unique_request_id_count": len(set(request_ids)),
        },
        resource_lines,
    )


def inspect_cli_evidence(
    run_path: Path, *, allow_failures: bool = False
) -> dict[str, Any]:
    metadata = []
    for path in sorted((run_path / "cli-subprocesses").glob("*.json")):
        value = load_json(path)
        schema_version = value.get("schema_version", 1)
        if schema_version == 2:
            _validate_cli_evidence_commit(run_path, path, value)
        elif schema_version != 1:
            raise ArchiveError("raw CLI metadata schema is unsupported")
        metadata.append(value)
        if not allow_failures:
            if value["return_code"] != 0 or value["response_validation"] != "passed":
                raise ArchiveError("raw CLI invocation did not pass")
            if value["stderr_bytes"] != 0:
                raise ArchiveError("raw CLI invocation emitted stderr")
        for item in value["sanitized_argv"]:
            if (
                "gateway-auth-token" in item
                and item != "--gateway-auth-token=[REDACTED]"
            ):
                raise ArchiveError("raw CLI argv is not fully redacted")
    if not metadata and not allow_failures:
        raise ArchiveError("raw CLI metadata is absent")
    request_ids = {item["request_id"] for item in metadata}
    if len(request_ids) != len(metadata):
        raise ArchiveError("raw CLI request IDs are not unique")
    return {
        "schema_version": 1,
        "invocation_count": len(metadata),
        "unique_request_id_count": len(request_ids),
        "return_codes": dict(
            sorted(
                collections.Counter(
                    str(item["return_code"]) for item in metadata
                ).items()
            )
        ),
        "response_validation": dict(
            sorted(
                collections.Counter(
                    item["response_validation"] for item in metadata
                ).items()
            )
        ),
        "stderr_bytes": sum(item["stderr_bytes"] for item in metadata),
        "auth_redaction": "passed",
        "terminal_failure_evidence_allowed": allow_failures,
    }


def _validate_cli_evidence_commit(
    run_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> None:
    invocation_id = metadata.get("invocation_id")
    if (
        not isinstance(invocation_id, str)
        or len(invocation_id) != 64
        or any(character not in "0123456789abcdef" for character in invocation_id)
        or metadata_path.name != f"{invocation_id}.json"
        or metadata.get("evidence_commit") != CLI_EVIDENCE_COMMIT_PROTOCOL
    ):
        raise ArchiveError("raw CLI durable commit marker is invalid")
    evidence_root = run_path / "cli-subprocesses"
    if (
        evidence_root.is_symlink()
        or not evidence_root.is_dir()
        or metadata_path.is_symlink()
        or not metadata_path.is_file()
    ):
        raise ArchiveError("raw CLI durable commit marker is unsafe")
    for stream in ("stdout", "stderr"):
        relative = f"cli-subprocesses/{invocation_id}.{stream}"
        if metadata.get(f"{stream}_path") != relative:
            raise ArchiveError("raw CLI payload path is invalid")
        packed_payload = decode_cli_evidence_payload(metadata, stream)
        payload_path = run_path / relative
        if payload_path.is_symlink() or not payload_path.is_file():
            raise ArchiveError("raw CLI committed payload is absent or unsafe")
        if payload_path.parent.resolve(strict=True) != evidence_root.resolve(strict=True):
            raise ArchiveError("raw CLI committed payload escaped evidence directory")
        payload = payload_path.read_bytes()
        if payload != packed_payload:
            raise ArchiveError("raw CLI committed payload failed integrity validation")


def decode_cli_evidence_payload(
    metadata: dict[str, Any],
    stream: str,
) -> bytes:
    if stream not in {"stdout", "stderr"}:
        raise ArchiveError("raw CLI durable commit payload kind is invalid")
    try:
        packed_payload = base64.b64decode(
            metadata[f"{stream}_base64"], validate=True
        )
    except (KeyError, TypeError, ValueError, binascii.Error) as error:
        raise ArchiveError("raw CLI durable commit payload is invalid") from error
    expected_bytes = metadata.get(f"{stream}_bytes")
    expected_sha256 = metadata.get(f"{stream}_sha256")
    packed_sha256 = f"sha256:{hashlib.sha256(packed_payload).hexdigest()}"
    if expected_bytes != len(packed_payload) or expected_sha256 != packed_sha256:
        raise ArchiveError(
            "raw CLI durable commit payload failed integrity validation"
        )
    return packed_payload


def capture_cli_help(product_bin: Path, destination: Path) -> list[dict[str, Any]]:
    destination.mkdir()
    env = {
        name: os.environ[name]
        for name in ("PATH", "SystemRoot", "WINDIR")
        if name in os.environ
    }
    records = []
    for role, (name, help_arg) in CLI_HELP.items():
        executable = (product_bin / name).resolve(strict=True)
        if executable.parent != product_bin.resolve(strict=True):
            raise ArchiveError(f"unsafe CLI help executable: {name}")
        completed = run_checked(
            [os.fspath(executable), help_arg],
            cwd=product_bin.parent,
            timeout=15.0,
            env=env,
        )
        if completed.stderr:
            raise ArchiveError(f"CLI help emitted stderr: {name}")
        (destination / f"{role}.stdout").write_bytes(completed.stdout)
        (destination / f"{role}.stderr").write_bytes(completed.stderr)
        record = {
            "role": role,
            "executable": os.fspath(executable),
            "executable_sha256": f"sha256:{sha256_file(executable)}",
            "argv": [os.fspath(executable), help_arg],
            "return_code": completed.returncode,
            "stdout_bytes": len(completed.stdout),
            "stdout_sha256": f"sha256:{sha256_bytes(completed.stdout)}",
            "stderr_bytes": len(completed.stderr),
            "stderr_sha256": f"sha256:{sha256_bytes(completed.stderr)}",
        }
        write_json(destination / f"{role}.json", record)
        records.append(record)
    return records


def capture_cleanup(
    *,
    paper_root: Path,
    product_root: Path,
    run_id: str,
    run_status: str,
) -> dict[str, Any]:
    if os.name != "nt":
        raise ArchiveError("EXP1 archive cleanup proof requires native Windows")
    process_script = (
        "$names=@('sandbox-gateway.exe','sandbox-manager-cli.exe',"
        "'sandbox-runtime-cli.exe','sandbox-observability-cli.exe');"
        f"$run='{run_id}';"
        "$p=@(Get-CimInstance Win32_Process | "
        'Where-Object {$_.Name -in $names -and $_.CommandLine -like "*$run*"} | '
        "Select-Object ProcessId,Name,CommandLine);"
        "$p | ConvertTo-Json -Compress"
    )
    process_result = run_checked(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", process_script],
        cwd=paper_root,
    )
    process_text = process_result.stdout.decode("utf-8-sig", "strict").strip()
    processes = [] if not process_text else json.loads(process_text)
    if isinstance(processes, dict):
        processes = [processes]
    run_containers = (
        run_checked(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"label=eos.benchmark.run_id={run_id}",
                "--format",
                "{{.ID}} {{.Names}} {{.Status}}",
            ],
            cwd=paper_root,
        )
        .stdout.decode("utf-8", "strict")
        .splitlines()
    )
    gateway_containers = (
        run_checked(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "label=eos.benchmark.gateway_instance_id",
                "--format",
                "{{.ID}} {{.Names}} {{.Status}}",
            ],
            cwd=paper_root,
        )
        .stdout.decode("utf-8", "strict")
        .splitlines()
    )
    run_volumes = (
        run_checked(
            [
                "docker",
                "volume",
                "ls",
                "--filter",
                f"label=eos.benchmark.run_id={run_id}",
                "--format",
                "{{.Name}}",
            ],
            cwd=paper_root,
        )
        .stdout.decode("utf-8", "strict")
        .splitlines()
    )
    gateway_volumes = (
        run_checked(
            [
                "docker",
                "volume",
                "ls",
                "--filter",
                "label=eos.benchmark.gateway_instance_id",
                "--format",
                "{{.Name}}",
            ],
            cwd=paper_root,
        )
        .stdout.decode("utf-8", "strict")
        .splitlines()
    )
    proof = {
        "schema_version": 1,
        "run_id": run_id,
        "run_workspace_exists": (
            paper_root / ".benchmark-state/runs" / run_id
        ).exists(),
        "runtime_exists": (paper_root / ".benchmark-state/runtime" / run_id).exists(),
        "matching_product_processes": processes,
        "run_labeled_containers": run_containers,
        "gateway_labeled_containers": gateway_containers,
        "run_labeled_volumes": run_volumes,
        "gateway_labeled_volumes": gateway_volumes,
        "product_branch": git_value(product_root, "branch", "--show-current"),
        "product_commit": git_value(product_root, "rev-parse", "HEAD"),
        "product_status_porcelain": git_value(product_root, "status", "--porcelain"),
        "product_checkout_policy": (
            "clean_exact_recorded_treatment"
            if run_status == "completed"
            else "post_run_drift_recorded_failed_ineligible"
        ),
    }
    if (
        proof["run_workspace_exists"]
        or proof["runtime_exists"]
        or processes
        or run_containers
        or gateway_containers
        or run_volumes
        or gateway_volumes
        or proof["product_branch"] != "main"
        or (run_status == "completed" and proof["product_status_porcelain"])
    ):
        raise ArchiveError("post-run cleanup proof failed")
    return proof


def capture_environment(
    *,
    paper_root: Path,
    product_root: Path,
    product_bin: Path,
    product_archive: Path,
    image: str,
    manifest: dict[str, Any],
    command: list[str],
    cli_help: list[dict[str, Any]],
    cleanup: dict[str, Any],
    run_status: str,
    protocol_version: str = "v1.0",
) -> dict[str, Any]:
    image_data = json.loads(
        run_checked(["docker", "image", "inspect", image], cwd=paper_root).stdout
    )[0]
    docker_info = json.loads(
        run_checked(["docker", "info", "--format", "{{json .}}"], cwd=paper_root).stdout
    )
    binaries = {
        role: {
            "path": record["executable"],
            "sha256": record["executable_sha256"],
            "bytes": Path(record["executable"]).stat().st_size,
        }
        for role, record in ((item["role"], item) for item in cli_help)
    }
    daemon = product_bin.parent / "dist/sandbox-daemon-linux-amd64"
    binaries["daemon"] = {
        "path": os.fspath(daemon.resolve(strict=True)),
        "sha256": f"sha256:{sha256_file(daemon)}",
        "bytes": daemon.stat().st_size,
    }
    treatment = manifest["treatment"]
    expected_hashes = {
        "gateway": treatment["gateway_binary_hash"],
        "manager": treatment["manager_cli_binary_hash"],
        "runtime": treatment["runtime_cli_binary_hash"],
        "observability": treatment["observability_cli_binary_hash"],
        "daemon": treatment["daemon_binary_hash"],
    }
    for role, expected in expected_hashes.items():
        if binaries[role]["sha256"] != expected:
            raise ArchiveError(f"product binary drift: {role}")
    if (
        treatment.get("source_dirty") is not False
        or treatment.get("source_diff_hash") is not None
    ):
        raise ArchiveError("recorded at-run product treatment was not clean")
    if (
        run_status == "completed"
        and cleanup["product_commit"] != treatment["source_commit"]
    ):
        raise ArchiveError("product source commit drift")
    validate_cleanup_proof(
        cleanup,
        run_status=run_status,
        recorded_product_commit=treatment["source_commit"],
    )
    recorded_environment = manifest["environment"]
    validate_exp1_environment(recorded_environment)
    is_final = manifest["name"] == DISPOSITIONS["final"]["name"]
    freeze_tag = product_freeze_tag(
        product_root,
        disposition=("final" if is_final else "exploratory"),
        product_commit=treatment["source_commit"],
        protocol_version=protocol_version,
    )
    return {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "disposition": manifest["name"],
        "recorded_run_environment": recorded_environment,
        "final_host": recorded_environment["host"],
        "sandbox_limits": recorded_environment["sandbox_limits"],
        "sanitized_campaign_command": command,
        "product": {
            "root": os.fspath(product_root),
            "branch": cleanup["product_branch"],
            "commit": treatment["source_commit"],
            "dirty": treatment["source_dirty"],
            "recorded_treatment": treatment,
            "post_run_checkout": {
                "branch": cleanup["product_branch"],
                "commit": cleanup["product_commit"],
                "status_porcelain": cleanup["product_status_porcelain"],
                "dirty": bool(cleanup["product_status_porcelain"]),
                "capture_boundary": product_checkout_capture_boundary(run_status),
            },
            "freeze_tag": freeze_tag,
            "bin_dir": os.fspath(product_bin),
            "archive": {
                "path": os.fspath(product_archive.resolve(strict=True)),
                "bytes": product_archive.stat().st_size,
                "sha256": f"sha256:{sha256_file(product_archive)}",
            },
            "binaries": binaries,
        },
        "docker": {
            "server_version": docker_info["ServerVersion"],
            "driver": docker_info["Driver"],
            "cgroup_version": docker_info["CgroupVersion"],
            "os_type": docker_info["OSType"],
            "architecture": docker_info["Architecture"],
            "warnings": docker_info["Warnings"],
        },
        "image": {
            "requested": image,
            "id": image_data["Id"],
            "repo_digests": image_data["RepoDigests"],
            "os": image_data["Os"],
            "architecture": image_data["Architecture"],
            "size": image_data["Size"],
        },
        "cleanup": cleanup,
    }


def locate_fixture_manifest(paper_root: Path, plan: dict[str, Any]) -> Path:
    profiles = plan["selected_workspace_profiles"]
    if len(profiles) != 1 or profiles[0]["id"] != "paper-100m":
        raise ArchiveError("unexpected workspace profile set")
    candidates = sorted(
        (paper_root / ".benchmark-state/fixtures/paper-100m").glob(
            "*/fixture-manifest.json"
        )
    )
    if len(candidates) != 1:
        raise ArchiveError("paper-100m fixture manifest identity is ambiguous")
    manifest = load_json(candidates[0])
    identity = manifest["identity"]
    fixture = profiles[0]["fixture"]
    if (
        identity["profile_id"] != profiles[0]["id"]
        or identity["profile_version"] != profiles[0]["version"]
        or identity["profile_generator_version"] != profiles[0]["generator_version"]
        or identity["seed"] != plan["canonical_plan"]["seed"]
        or manifest["actual_file_count"] != fixture["file_count"]
        or manifest["actual_logical_bytes"] != fixture["logical_bytes"]
        or identity["fixture"] != fixture
    ):
        raise ArchiveError("fixture manifest identity or realized size mismatch")
    return candidates[0]


def archive_inventory(root: Path) -> tuple[list[dict[str, Any]], int, str]:
    entries = []
    total_bytes = 0
    tree = hashlib.sha256()
    for path in sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        if relative == "archive-manifest.json":
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        entries.append(
            {
                "path": relative,
                "bytes": size,
                "sha256": f"sha256:{digest}",
            }
        )
        total_bytes += size
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(bytes.fromhex(digest))
        tree.update(b"\n")
    return entries, total_bytes, f"sha256:{tree.hexdigest()}"


def benchmark_source_inventory(paper_root: Path) -> dict[str, Any]:
    benchmark = (paper_root / "benchmark").resolve(strict=True)
    entries = []
    total_bytes = 0
    tree = hashlib.sha256()
    for path in sorted(
        (
            path
            for path in benchmark.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and not BENCHMARK_EXCLUDED_PARTS.intersection(
                path.relative_to(benchmark).parts
            )
            and path.suffix != ".pyc"
        ),
        key=lambda item: item.relative_to(benchmark).as_posix(),
    ):
        relative = path.relative_to(benchmark).as_posix()
        size = path.stat().st_size
        digest = sha256_file(path)
        entries.append(
            {
                "path": relative,
                "bytes": size,
                "sha256": f"sha256:{digest}",
            }
        )
        total_bytes += size
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(bytes.fromhex(digest))
        tree.update(b"\n")
    return {
        "schema_version": 1,
        "root": os.fspath(benchmark),
        "file_count": len(entries),
        "bytes": total_bytes,
        "content_tree_sha256": f"sha256:{tree.hexdigest()}",
        "excluded_parts": sorted(BENCHMARK_EXCLUDED_PARTS),
        "files": entries,
    }


def file_identity(path: Path, paper_root: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    return {
        "path": resolved.relative_to(paper_root).as_posix(),
        "bytes": resolved.stat().st_size,
        "sha256": f"sha256:{sha256_file(resolved)}",
    }


def write_campaign_manifests(
    archive_path: Path,
    *,
    paper_root: Path,
    disposition: str,
    run_status: str,
    protocol_version: str = "v1.0",
) -> None:
    if protocol_version not in PROTOCOLS:
        raise ArchiveError("unsupported EXP1 protocol version")
    source_manifest_path = archive_path / "benchmark-source-manifest.json"
    campaign_manifest_path = archive_path / "campaign-manifest.json"
    if source_manifest_path.exists() or campaign_manifest_path.exists():
        raise ArchiveError("campaign provenance manifest already exists")
    raw = archive_path / "raw"
    manifest = envelope_data(raw / "run-manifest.json")
    plan = envelope_data(raw / "expanded-plan.json")
    report = envelope_data(raw / "report.json")
    if (
        run_status not in RUN_STATUSES
        or manifest.get("state") != run_status
        or report.get("state") != run_status
    ):
        raise ArchiveError("campaign manifest run status drift")
    fixture = load_json(archive_path / "fixture-manifest.json")
    environment = load_json(archive_path / "environment-preflight.txt")
    benchmark_source = benchmark_source_inventory(paper_root)
    write_json(source_manifest_path, benchmark_source)
    raw_files, raw_bytes, raw_tree_hash = archive_inventory(raw)
    paper_git = paper_git_provenance(paper_root, disposition=disposition)
    protocol_paths = [paper_root / relative for relative in PAPER_PROTOCOL_PATHS]
    analysis_paths = [paper_root / relative for relative in PAPER_ANALYSIS_PATHS]
    campaign_manifest = {
        "schema_version": 1,
        "run_id": manifest["run_id"],
        "disposition": disposition,
        "run_status": run_status,
        "eligibility": archive_eligibility(disposition, run_status),
        "state": manifest["state"],
        "correctness": report["correctness_verdict"],
        "started_at": manifest["started_at"],
        "ended_at": manifest["ended_at"],
        "paper_git": {
            **paper_git,
            "note": (
                "The paper checkout is intentionally dirty during pre-freeze "
                "execution; benchmark_source.content_tree_sha256 is the "
                "authoritative run-time benchmark identity."
                if disposition != "final"
                else (
                    "The paper benchmark, protocol, and analysis scope is a "
                    "clean frozen commit."
                )
            ),
        },
        "benchmark_source": {
            "manifest": "benchmark-source-manifest.json",
            "manifest_sha256": (f"sha256:{sha256_file(source_manifest_path)}"),
            "file_count": benchmark_source["file_count"],
            "bytes": benchmark_source["bytes"],
            "content_tree_sha256": benchmark_source["content_tree_sha256"],
            "capture_boundary": benchmark_source_capture_boundary(run_status),
        },
        "protocol": {
            "id": PROTOCOLS[protocol_version]["id"],
            "version": (
                protocol_version
                if protocol_version == "v1.1" or disposition == "final"
                else "pre-freeze-exp1"
            ),
            "freeze_state": ("frozen" if disposition == "final" else "pre_freeze"),
            "files": [file_identity(path, paper_root) for path in protocol_paths],
        },
        "plan": {
            "hash": plan["plan_hash"],
            "cells": plan["estimates"]["cell_count"],
            "trial_batches": plan["estimates"]["trial_batch_count"],
            "issued_operation_requests": plan["estimates"][
                "issued_operation_request_count"
            ],
            "client_cohort": plan["effective_environment"]["client_cohort"],
            "expanded_plan_sha256": (
                f"sha256:{sha256_file(raw / 'expanded-plan.json')}"
            ),
        },
        "fixture": {
            "fixture_hash": fixture["fixture_hash"],
            "tree_hash": fixture["tree_hash"],
            "manifest_sha256": (
                f"sha256:{sha256_file(archive_path / 'fixture-manifest.json')}"
            ),
        },
        "product": environment["product"],
        "docker": environment["docker"],
        "image": environment["image"],
        "final_host": environment["final_host"],
        "sandbox_limits": environment["sandbox_limits"],
        "definition_snapshot": manifest["definition_snapshot"],
        "artifact_schemas": manifest["artifact_schemas"],
        "analysis_and_archiving_code": {
            "files": [file_identity(path, paper_root) for path in analysis_paths],
        },
        "raw_corpus": {
            "path": "raw",
            "file_count": len(raw_files),
            "bytes": raw_bytes,
            "content_tree_sha256": raw_tree_hash,
            "observations_sha256": (
                f"sha256:{sha256_file(raw / 'observations.ndjson')}"
            ),
            "events_sha256": f"sha256:{sha256_file(raw / 'events.ndjson')}",
            "report_sha256": f"sha256:{sha256_file(raw / 'report.json')}",
        },
        "cleanup": environment["cleanup"],
    }
    write_json(campaign_manifest_path, campaign_manifest)


def finalize_existing_archive(path: Path, *, paper_root: Path) -> dict[str, Any]:
    prior = verify_archive(path)
    archive_manifest = load_json(path / "archive-manifest.json")
    disposition = archive_manifest["disposition"]
    if disposition not in DISPOSITIONS:
        raise ArchiveError("existing archive disposition is invalid")
    run_status = archive_manifest.get("run_status", "completed")
    if run_status not in RUN_STATUSES:
        raise ArchiveError("existing archive run status is invalid")
    write_campaign_manifests(
        path,
        paper_root=paper_root,
        disposition=disposition,
        run_status=run_status,
        protocol_version=archive_manifest.get("protocol_version", "v1.0"),
    )
    entries, total_bytes, tree_hash = archive_inventory(path)
    archive_manifest.update(
        {
            "archive_file_count": len(entries),
            "archive_bytes": total_bytes,
            "content_tree_sha256": tree_hash,
            "files": entries,
            "supersedes_preliminary_content_tree_sha256": prior["content_tree_sha256"],
        }
    )
    write_json(path / "archive-manifest.json", archive_manifest)
    result = verify_archive(path)
    result["supersedes_preliminary_content_tree_sha256"] = prior["content_tree_sha256"]
    return result


def verify_archive(path: Path) -> dict[str, Any]:
    manifest = load_json(path / "archive-manifest.json")
    entries, total_bytes, tree_hash = archive_inventory(path)
    if (
        entries != manifest["files"]
        or total_bytes != manifest["archive_bytes"]
        or tree_hash != manifest["content_tree_sha256"]
    ):
        raise ArchiveError("archive inventory verification failed")
    _validate_archive_provenance(path, manifest)
    return {
        "run_id": manifest["run_id"],
        "archive_path": os.fspath(path.resolve(strict=True)),
        "archive_file_count": len(entries),
        "archive_bytes": total_bytes,
        "content_tree_sha256": tree_hash,
        "verified": True,
    }


def _validate_archive_provenance(path: Path, archive_manifest: dict[str, Any]) -> None:
    raw_manifest = envelope_data(path / "raw/run-manifest.json")
    raw_report = envelope_data(path / "raw/report.json")
    raw_environment = envelope_data(path / "raw/environment-metadata.json")
    raw_plan_path = path / "raw/expanded-plan.json"
    raw_plan = envelope_data(raw_plan_path) if raw_plan_path.is_file() else {}
    copied_manifest = envelope_data(path / "run-manifest.json")
    copied_report = envelope_data(path / "report.json")
    preflight = load_json(path / "environment-preflight.txt")
    if raw_manifest != copied_manifest:
        raise ArchiveError("archived run-manifest copies disagree")
    if raw_report != copied_report:
        raise ArchiveError("archived report copies disagree")
    if raw_manifest.get("run_id") != archive_manifest.get("run_id"):
        raise ArchiveError("archive and run manifest identities disagree")
    recorded_environment = raw_manifest.get("environment")
    if raw_environment != recorded_environment:
        raise ArchiveError("run-start environment artifact and run manifest disagree")
    validate_exp1_environment(recorded_environment)
    if (
        preflight.get("recorded_run_environment") != recorded_environment
        or preflight.get("final_host") != recorded_environment["host"]
        or preflight.get("sandbox_limits") != recorded_environment["sandbox_limits"]
    ):
        raise ArchiveError(
            "archive preflight did not preserve run-start provenance exactly"
        )
    campaign_path = path / "campaign-manifest.json"
    if not campaign_path.is_file():
        raise ArchiveError("campaign provenance manifest is missing")
    campaign = load_json(campaign_path)
    if (
        campaign.get("final_host") != recorded_environment["host"]
        or campaign.get("sandbox_limits") != recorded_environment["sandbox_limits"]
        or campaign.get("product") != preflight.get("product")
    ):
        raise ArchiveError(
            "campaign manifest did not preserve run-start/product provenance exactly"
        )
    disposition = archive_manifest.get("disposition")
    if disposition not in DISPOSITIONS:
        raise ArchiveError("archive disposition is invalid")
    run_status = archive_manifest.get("run_status", "completed")
    if run_status not in RUN_STATUSES:
        raise ArchiveError("archive run status is invalid")
    expected_eligibility = archive_eligibility(disposition, run_status)
    benchmark_source = campaign.get("benchmark_source")
    if (
        archive_manifest.get("eligibility", expected_eligibility)
        != expected_eligibility
        or raw_manifest.get("state") != run_status
        or raw_report.get("state") != run_status
        or campaign.get("state") != run_status
        or campaign.get("run_status", run_status) != run_status
        or campaign.get("eligibility") != expected_eligibility
        or raw_manifest.get("correctness") != raw_report.get("correctness_verdict")
        or campaign.get("correctness") != raw_report.get("correctness_verdict")
        or not isinstance(benchmark_source, dict)
        or benchmark_source.get("capture_boundary")
        != benchmark_source_capture_boundary(run_status)
    ):
        raise ArchiveError(
            "archive terminal status or eligibility provenance is invalid"
        )
    if run_status == "completed":
        if raw_report.get("correctness_verdict") != "pass":
            raise ArchiveError("completed archive correctness is not pass")
    else:
        failure = raw_manifest.get("failure")
        if (
            raw_report.get("correctness_verdict") != "fail"
            or not isinstance(failure, dict)
            or not isinstance(failure.get("code"), str)
            or not failure["code"]
            or not isinstance(failure.get("message"), str)
            or not failure["message"]
            or not (path / "failures.md").is_file()
        ):
            raise ArchiveError("failed archive lacks terminal failure evidence")
    protocol = campaign.get("protocol")
    protocol_version = protocol_version_from_campaign(
        campaign, disposition=disposition
    )
    if (
        protocol.get("freeze_state")
        != ("frozen" if disposition == "final" else "pre_freeze")
        or (
            protocol_version == "v1.1"
            and archive_manifest.get("protocol_version") != "v1.1"
        )
        or (
            protocol_version == "v1.0"
            and archive_manifest.get("protocol_version") not in (None, "v1.0")
        )
    ):
        raise ArchiveError("campaign protocol freeze provenance is invalid")
    validate_protocol_transport(
        protocol_version=protocol_version,
        environment=recorded_environment,
        manifest=raw_manifest,
        plan=raw_plan,
        completed=run_status == "completed",
    )
    analysis = campaign.get("analysis_and_archiving_code")
    analysis_paths = (
        {
            item.get("path")
            for item in analysis.get("files", [])
            if isinstance(item, dict)
        }
        if isinstance(analysis, dict)
        else set()
    )
    if "experiments/analysis/scripts/generate_exp1_tables.py" not in analysis_paths:
        raise ArchiveError("table generator identity is absent from the archive")
    product = preflight.get("product")
    paper_git = campaign.get("paper_git")
    if not isinstance(product, dict) or not isinstance(paper_git, dict):
        raise ArchiveError("freeze source provenance is incomplete")
    treatment = raw_manifest.get("treatment")
    cleanup = preflight.get("cleanup")
    archived_cleanup = load_json(path / "cleanup/cleanup-proof.json")
    post_run_checkout = product.get("post_run_checkout")
    if (
        not isinstance(treatment, dict)
        or treatment.get("source_dirty") is not False
        or treatment.get("source_diff_hash") is not None
        or product.get("commit") != treatment.get("source_commit")
        or product.get("dirty") is not False
        or product.get("recorded_treatment", treatment) != treatment
        or not isinstance(cleanup, dict)
        or campaign.get("cleanup") != cleanup
        or archived_cleanup != cleanup
    ):
        raise ArchiveError("recorded at-run product or cleanup provenance is invalid")
    validate_cleanup_proof(
        cleanup,
        run_status=run_status,
        recorded_product_commit=treatment["source_commit"],
    )
    if run_status == "failed":
        if (
            not isinstance(post_run_checkout, dict)
            or post_run_checkout.get("branch") != cleanup["product_branch"]
            or post_run_checkout.get("commit") != cleanup["product_commit"]
            or post_run_checkout.get("status_porcelain")
            != cleanup["product_status_porcelain"]
            or post_run_checkout.get("dirty")
            != bool(cleanup["product_status_porcelain"])
            or post_run_checkout.get("capture_boundary")
            != product_checkout_capture_boundary(run_status)
        ):
            raise ArchiveError("failed archive post-run product provenance is invalid")
    elif post_run_checkout is not None and (
        not isinstance(post_run_checkout, dict)
        or post_run_checkout.get("capture_boundary")
        != product_checkout_capture_boundary(run_status)
    ):
        raise ArchiveError("completed archive post-run product provenance is invalid")
    freeze_tag = product.get("freeze_tag")
    if not isinstance(freeze_tag, dict):
        raise ArchiveError("product freeze-tag provenance is missing")
    if disposition == "final":
        required_tag = PROTOCOLS[protocol_version]["final_tag"]
        if (
            freeze_tag.get("availability") != "available"
            or freeze_tag.get("name") != required_tag
            or freeze_tag.get("reference") != f"refs/tags/{required_tag}"
            or freeze_tag.get("object_type") != "tag"
            or not _is_git_sha1(freeze_tag.get("tag_object"))
            or freeze_tag.get("peeled_commit") != product.get("commit")
            or paper_git.get("dirty") is not False
            or paper_git.get("status_porcelain") != []
            or paper_git.get("freeze_state") != "clean_frozen_commit"
            or paper_git.get("generated_exclusions") != BENCHMARK_GIT_EXCLUSIONS
            or not _is_git_sha1(paper_git.get("commit"))
        ):
            raise ArchiveError("final source/tag freeze provenance is invalid")
    elif (
        freeze_tag.get("availability") != "unavailable"
        or freeze_tag.get("required_final_tag")
        != PROTOCOLS[protocol_version]["final_tag"]
        or paper_git.get("freeze_state") != "pre_freeze_worktree"
    ):
        raise ArchiveError("pre-freeze source/tag provenance is invalid")


def archive(args: argparse.Namespace) -> dict[str, Any]:
    if args.protocol_version != "v1.1":
        raise ArchiveError("new archives require explicit --protocol-version v1.1")
    paper_root = args.paper_root.resolve(strict=True)
    product_root = args.product_root.resolve(strict=True)
    product_bin = args.product_bin_dir.resolve(strict=True)
    product_archive = args.product_archive.resolve(strict=True)
    archive_root = (paper_root / "experiments/runs").resolve()
    run_path = (paper_root / ".benchmark-state/results" / args.run_id).resolve(
        strict=True
    )
    target = archive_root / args.run_id
    staging = archive_root / f".{args.run_id}.staging"
    if target.exists() or staging.exists():
        raise ArchiveError("archive target or staging path already exists")
    if target.parent != archive_root or staging.parent != archive_root:
        raise ArchiveError("archive path escaped the fixed archive root")
    manifest, plan, report, intent = validate_source(
        run_path,
        run_id=args.run_id,
        disposition=args.disposition,
        run_status=args.run_status,
        expected_plan_hash=args.expected_plan_hash,
        protocol_version=args.protocol_version,
    )
    observation_summary, resource_lines = inspect_observations(
        run_path,
        expected_requests=DISPOSITIONS[args.disposition]["requests"],
        expected_batches=DISPOSITIONS[args.disposition]["batches"],
        allow_partial=args.run_status == "failed",
    )
    cli_summary = inspect_cli_evidence(
        run_path, allow_failures=args.run_status == "failed"
    )
    cleanup = capture_cleanup(
        paper_root=paper_root,
        product_root=product_root,
        run_id=args.run_id,
        run_status=args.run_status,
    )
    archive_root.mkdir(parents=True, exist_ok=True)
    staging.mkdir()
    (staging / "raw").mkdir()
    for source in sorted(run_path.iterdir(), key=lambda item: item.name):
        destination = staging / "raw" / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
    for name in ("run-manifest.json", "expanded-plan.json", "report.json"):
        shutil.copy2(run_path / name, staging / name)
    fixture_manifest = locate_fixture_manifest(paper_root, plan)
    shutil.copy2(fixture_manifest, staging / "fixture-manifest.json")
    (staging / "intent-plan.yml").write_text(
        yaml.safe_dump(
            intent,
            allow_unicode=True,
            sort_keys=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    cli_help = capture_cli_help(product_bin, staging / "cli-help")
    (staging / "resources").mkdir()
    with (staging / "resources/resource-observations.ndjson").open("wb") as stream:
        for line in resource_lines:
            stream.write(line)
    write_json(staging / "resources/resource-summary.json", observation_summary)
    (staging / "logs").mkdir()
    shutil.copy2(run_path / "events.ndjson", staging / "logs/events.ndjson")
    write_json(staging / "logs/cli-summary.json", cli_summary)
    (staging / "cleanup").mkdir()
    write_json(staging / "cleanup/cleanup-proof.json", cleanup)
    command = [
        os.fspath(
            (paper_root / ".venv/Scripts/sandbox-benchmark.exe").resolve(strict=True)
        ),
        "run",
        "--test-repository-root",
        os.fspath(paper_root),
        "--product-root",
        os.fspath(product_root),
        "--product-bin-dir",
        os.fspath(product_bin),
        "--plan",
        DISPOSITIONS[args.disposition]["name"],
    ]
    environment = capture_environment(
        paper_root=paper_root,
        product_root=product_root,
        product_bin=product_bin,
        product_archive=product_archive,
        image=args.image,
        manifest=manifest,
        command=command,
        cli_help=cli_help,
        cleanup=cleanup,
        run_status=args.run_status,
        protocol_version=args.protocol_version,
    )
    write_json(staging / "environment-preflight.txt", environment)
    unavailable = observation_summary["resource_availability"]
    unavailable_lines = [
        f"- `{metric}`: {availability.get('unavailable', 0)} unavailable, "
        f"{availability.get('available', 0)} available observations"
        for metric, availability in unavailable.items()
        if availability.get("unavailable", 0)
    ]
    if args.run_status == "failed":
        failure_text = (
            "# Failures, exclusions, warnings, and unavailable fields\n\n"
            "- Failures: terminal campaign failure; authoritative raw evidence is "
            "preserved below `raw/`.\n"
            "- Exclusions: this entire corpus is ineligible for pilot projection, "
            "final tables, and manuscript claims.\n"
            f"- Report warnings: {len(report['warnings'])}; preserved verbatim in "
            "`raw/report.json`.\n"
            "- Correctness: fail.\n"
            "- Pilot/final eligibility: failed_ineligible.\n\n"
            "## Recorded terminal failure\n\n"
            "```json\n"
            + json.dumps(
                manifest["failure"],
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n```\n\n"
            "## Explicitly unavailable resource observations\n\n"
            + ("\n".join(unavailable_lines) if unavailable_lines else "- None.")
            + "\n\n"
            "Unavailable observations remain unavailable; they are never encoded as zero.\n"
        )
    else:
        failure_text = (
            "# Failures, exclusions, warnings, and unavailable fields\n\n"
            "- Failures: none.\n"
            "- Exclusions: none.\n"
            "- Report warnings: none.\n"
            "- Correctness: pass.\n"
            "- Pilot/final eligibility: "
            + (
                "ineligible smoke qualification evidence."
                if args.disposition == "smoke"
                else (
                    "ineligible exploratory pilot evidence."
                    if args.disposition == "exploratory"
                    else "eligible only after complete frozen-corpus verification."
                )
            )
            + "\n\n"
            "## Explicitly unavailable resource observations\n\n"
            + ("\n".join(unavailable_lines) if unavailable_lines else "- None.")
            + "\n\n"
            "Unavailable observations remain unavailable; they are never encoded as zero.\n"
        )
    (staging / "failures.md").write_text(failure_text, encoding="utf-8", newline="\n")
    write_campaign_manifests(
        staging,
        paper_root=paper_root,
        disposition=args.disposition,
        run_status=args.run_status,
        protocol_version=args.protocol_version,
    )
    entries, total_bytes, tree_hash = archive_inventory(staging)
    write_json(
        staging / "archive-manifest.json",
        {
            "schema_version": 1,
            "run_id": args.run_id,
            "disposition": args.disposition,
            "run_status": args.run_status,
            "eligibility": archive_eligibility(args.disposition, args.run_status),
            "protocol_version": args.protocol_version,
            "source_path": os.fspath(run_path),
            "plan_hash": args.expected_plan_hash,
            "archive_file_count": len(entries),
            "archive_bytes": total_bytes,
            "content_tree_sha256": tree_hash,
            "files": entries,
        },
    )
    staging.replace(target)
    return verify_archive(target)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser()
    command.add_argument("--run-id")
    command.add_argument("--disposition", choices=sorted(DISPOSITIONS))
    command.add_argument(
        "--protocol-version",
        choices=("v1.1",),
        help="required explicitly when creating a new archive",
    )
    command.add_argument(
        "--run-status",
        choices=sorted(RUN_STATUSES),
        default="completed",
        help=(
            "expected terminal status; failed must be requested explicitly and "
            "is always archived as ineligible"
        ),
    )
    command.add_argument("--expected-plan-hash")
    command.add_argument("--paper-root", type=Path)
    command.add_argument("--product-root", type=Path)
    command.add_argument("--product-bin-dir", type=Path)
    command.add_argument("--product-archive", type=Path)
    command.add_argument("--image")
    command.add_argument("--verify", type=Path)
    command.add_argument("--finalize-existing", type=Path)
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        if args.verify is not None and args.finalize_existing is not None:
            raise ArchiveError(
                "--verify and --finalize-existing are mutually exclusive"
            )
        if args.verify is not None:
            result = verify_archive(args.verify.resolve(strict=True))
        elif args.finalize_existing is not None:
            if args.paper_root is None:
                raise ArchiveError("--paper-root is required with --finalize-existing")
            result = finalize_existing_archive(
                args.finalize_existing.resolve(strict=True),
                paper_root=args.paper_root.resolve(strict=True),
            )
        else:
            required = (
                "run_id",
                "disposition",
                "expected_plan_hash",
                "paper_root",
                "product_root",
                "product_bin_dir",
                "product_archive",
                "image",
                "protocol_version",
            )
            missing = [name for name in required if getattr(args, name) is None]
            if missing:
                raise ArchiveError(
                    f"archive arguments are missing: {', '.join(missing)}"
                )
            result = archive(args)
    except (ArchiveError, KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"archive_error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
