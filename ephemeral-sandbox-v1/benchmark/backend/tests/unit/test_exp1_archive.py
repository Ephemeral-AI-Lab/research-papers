import importlib.util
import base64
import json
import subprocess
from pathlib import Path

import pytest

PAPER_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = PAPER_ROOT / "experiments/scripts/archive_exp1_run.py"
SPEC = importlib.util.spec_from_file_location("archive_exp1_run_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
archive_exp1_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive_exp1_run)


def _environment() -> dict:
    host = {
        "computer_name": "DESKTOP-OLP1ADS",
        "operating_system": "windows",
        "architecture": "x64",
        "os_caption": "Microsoft Windows 11",
        "os_version": "10.0.26200",
        "os_build_number": 26200,
        "cpu_model": "AMD Ryzen Threadripper 7960X 24-Cores",
        "logical_processors": 48,
        "processor_logical_processors": 48,
        "total_memory_bytes": 137_438_953_472,
        "filesystem": "NTFS",
        "volume_root": "C:\\",
        "capture_boundary": "run_start_before_gateway_and_measurement",
        "captured_at": "2026-07-30T00:00:00.000000Z",
        "capture_source": "Windows CIM and Get-Volume",
    }
    limits = {
        "profile": "standard",
        "nano_cpus": 1_000_000_000,
        "vcpus": 1,
        "memory_bytes": 536_870_912,
        "pids_limit": 256,
        "authority": {
            "kind": "released_gateway_configuration",
            "path": "C:\\package\\config\\windows-amd64.yml",
            "sha256": "sha256:" + "a" * 64,
            "selector": "manager.docker.resource_profiles.standard",
            "effective_config_builder": "benchmark_lab.gateway._effective_config",
            "create_request_override": "none",
            "capture_boundary": "run_start_before_gateway_and_measurement",
        },
    }
    return {
        "schema_version": 1,
        "host": host,
        "sandbox_limits": limits,
    }


def _envelope(name: str, data: dict) -> dict:
    return {
        "schema_name": name,
        "schema_version": 1,
        "data": data,
    }


def _refresh_inventory(
    root: Path,
    run_id: str,
    disposition: str = "exploratory",
    run_status: str = "completed",
) -> None:
    entries, total_bytes, tree_hash = archive_exp1_run.archive_inventory(root)
    archive_exp1_run.write_json(
        root / "archive-manifest.json",
        {
            "schema_version": 1,
            "run_id": run_id,
            "disposition": disposition,
            "run_status": run_status,
            "eligibility": archive_exp1_run.archive_eligibility(
                disposition, run_status
            ),
            "archive_file_count": len(entries),
            "archive_bytes": total_bytes,
            "content_tree_sha256": tree_hash,
            "files": entries,
        },
    )


def _archive(
    root: Path,
    disposition: str = "exploratory",
    run_status: str = "completed",
) -> tuple[Path, dict]:
    run_id = "019fb000-0000-7000-8000-000000000000"
    environment = _environment()
    correctness = "pass" if run_status == "completed" else "fail"
    manifest = {
        "run_id": run_id,
        "environment": environment,
        "state": run_status,
        "correctness": correctness,
    }
    if run_status == "failed":
        manifest["failure"] = {
            "code": "campaign_failed",
            "message": "campaign execution failed; inspect raw evidence",
            "infrastructure": True,
        }
    report = {
        "run_id": run_id,
        "state": run_status,
        "correctness_verdict": correctness,
        "warnings": (
            []
            if run_status == "completed"
            else [
                {
                    "code": "missing_correctness_observations",
                    "message": "A measured-trial verdict is missing.",
                }
            ]
        ),
    }
    product_commit = "b" * 40
    treatment = {
        "source_commit": product_commit,
        "source_dirty": False,
        "source_diff_hash": None,
    }
    manifest["treatment"] = treatment
    post_run_commit = product_commit if run_status == "completed" else "e" * 40
    post_run_status = "" if run_status == "completed" else " M crates/fix.rs"
    cleanup = {
        "run_workspace_exists": False,
        "runtime_exists": False,
        "matching_product_processes": [],
        "run_labeled_containers": [],
        "gateway_labeled_containers": [],
        "run_labeled_volumes": [],
        "gateway_labeled_volumes": [],
        "product_branch": "main",
        "product_commit": post_run_commit,
        "product_status_porcelain": post_run_status,
        "product_checkout_policy": (
            "clean_exact_recorded_treatment"
            if run_status == "completed"
            else "post_run_drift_recorded_failed_ineligible"
        ),
    }
    freeze_tag = (
        {
            "availability": "available",
            "name": "paper-v1-freeze",
            "reference": "refs/tags/paper-v1-freeze",
            "object_type": "tag",
            "tag_object": "c" * 40,
            "peeled_commit": product_commit,
        }
        if disposition == "final"
        else {
            "availability": "unavailable",
            "reason": "pre-freeze smoke/exploratory archive",
            "required_final_tag": "paper-v1-freeze",
        }
    )
    product = {
        "commit": product_commit,
        "dirty": False,
        "recorded_treatment": treatment,
        "post_run_checkout": {
            "branch": "main",
            "commit": post_run_commit,
            "status_porcelain": post_run_status,
            "dirty": bool(post_run_status),
            "capture_boundary": (
                archive_exp1_run.product_checkout_capture_boundary(run_status)
            ),
        },
        "freeze_tag": freeze_tag,
    }
    (root / "raw").mkdir(parents=True)
    archive_exp1_run.write_json(
        root / "raw/run-manifest.json",
        _envelope("eos_benchmark_run_manifest", manifest),
    )
    archive_exp1_run.write_json(
        root / "raw/environment-metadata.json",
        _envelope("eos_benchmark_environment_metadata", environment),
    )
    archive_exp1_run.write_json(
        root / "raw/report.json",
        _envelope("eos_benchmark_report", report),
    )
    archive_exp1_run.write_json(
        root / "run-manifest.json",
        _envelope("eos_benchmark_run_manifest", manifest),
    )
    archive_exp1_run.write_json(
        root / "report.json",
        _envelope("eos_benchmark_report", report),
    )
    (root / "failures.md").write_text(
        (
            "# Failures\n\n- None.\n"
            if run_status == "completed"
            else "# Failures\n\n- Terminal campaign failure; raw evidence retained.\n"
        ),
        encoding="utf-8",
    )
    (root / "cleanup").mkdir()
    archive_exp1_run.write_json(
        root / "cleanup/cleanup-proof.json", cleanup
    )
    archive_exp1_run.write_json(
        root / "environment-preflight.txt",
        {
            "recorded_run_environment": environment,
            "final_host": environment["host"],
            "sandbox_limits": environment["sandbox_limits"],
            "product": product,
            "cleanup": cleanup,
        },
    )
    archive_exp1_run.write_json(
        root / "campaign-manifest.json",
        {
            "run_id": run_id,
            "disposition": disposition,
            "run_status": run_status,
            "eligibility": archive_exp1_run.archive_eligibility(
                disposition, run_status
            ),
            "state": run_status,
            "correctness": correctness,
            "benchmark_source": {
                "capture_boundary": (
                    archive_exp1_run.benchmark_source_capture_boundary(
                        run_status
                    )
                ),
            },
            "final_host": environment["host"],
            "sandbox_limits": environment["sandbox_limits"],
            "product": product,
            "cleanup": cleanup,
            "protocol": {
                "version": ("v1.0" if disposition == "final" else "pre-freeze-exp1"),
                "freeze_state": ("frozen" if disposition == "final" else "pre_freeze"),
            },
            "analysis_and_archiving_code": {
                "files": [
                    {"path": ("experiments/analysis/scripts/generate_exp1_tables.py")}
                ]
            },
            "paper_git": {
                "commit": "d" * 40,
                "dirty": False,
                "status_porcelain": [],
                "generated_exclusions": (archive_exp1_run.BENCHMARK_GIT_EXCLUSIONS),
                "freeze_state": (
                    "clean_frozen_commit"
                    if disposition == "final"
                    else "pre_freeze_worktree"
                ),
            },
        },
    )
    _refresh_inventory(root, run_id, disposition, run_status)
    return root, environment


def _source_run(
    root: Path,
    *,
    disposition: str = "smoke",
    run_status: str = "failed",
) -> tuple[str, str]:
    expected = archive_exp1_run.DISPOSITIONS[disposition]
    run_id = "019fb000-0000-7000-8000-000000000001"
    plan_hash = "sha256:" + "e" * 64
    correctness = "pass" if run_status == "completed" else "fail"
    manifest = {
        "run_id": run_id,
        "name": expected["name"],
        "state": run_status,
        "correctness": correctness,
        "plan_hash": plan_hash,
        "environment": _environment(),
    }
    if run_status == "failed":
        manifest["failure"] = {
            "code": "campaign_failed",
            "message": "campaign execution failed; inspect persisted evidence",
            "infrastructure": True,
        }
    plan = {
        "plan_hash": plan_hash,
        "estimates": {
            "cell_count": expected["cells"],
            "trial_batch_count": expected["batches"],
            "issued_operation_request_count": expected["requests"],
        },
        "effective_environment": {"client_cohort": "product_cli"},
        "cells": [
            {
                "protocol": {
                    "warmups": expected["warmups"],
                    "measured_trials": expected["measured"],
                },
                "operation": {"cell": {"workspace_profile": "paper-100m"}},
            }
            for _ in range(expected["cells"])
        ],
    }
    report = {
        "run_id": run_id,
        "state": run_status,
        "correctness_verdict": correctness,
        "cells": [
            {
                "counts": {
                    "warmup": expected["warmups"],
                    "measured_attempted": expected["measured"],
                    "successful": (
                        expected["measured"] if run_status == "completed" else 0
                    ),
                    "product_failed": 0,
                    "correctness_failed": 0,
                    "infrastructure_failed": (0 if run_status == "completed" else 1),
                    "cleanup_invalid": 0,
                    "missing_primary_latency": (0 if run_status == "completed" else 1),
                },
                "checks": [],
            }
            for _ in range(expected["cells"])
        ],
        "warnings": (
            []
            if run_status == "completed"
            else [
                {
                    "code": "missing_correctness_observations",
                    "message": "A measured-trial verdict is missing.",
                }
            ]
        ),
    }
    intent = {"name": expected["name"]}
    root.mkdir(parents=True)
    for name, schema, data in (
        ("run-manifest.json", "eos_benchmark_run_manifest", manifest),
        ("expanded-plan.json", "eos_benchmark_expanded_plan", plan),
        ("report.json", "eos_benchmark_report", report),
        ("intent-plan.json", "eos_benchmark_intent_plan", intent),
    ):
        archive_exp1_run.write_json(root / name, _envelope(schema, data))
    return run_id, plan_hash


def test_archive_verifier_preserves_run_start_provenance_exactly(
    tmp_path: Path,
) -> None:
    root, _ = _archive(tmp_path / "archive")

    result = archive_exp1_run.verify_archive(root)

    assert result["verified"] is True


def test_failed_archive_is_explicitly_ineligible_and_preserves_report(
    tmp_path: Path,
) -> None:
    root, _ = _archive(
        tmp_path / "archive",
        disposition="smoke",
        run_status="failed",
    )

    result = archive_exp1_run.verify_archive(root)

    assert result["verified"] is True
    manifest = archive_exp1_run.load_json(root / "archive-manifest.json")
    campaign = archive_exp1_run.load_json(root / "campaign-manifest.json")
    assert manifest["run_status"] == "failed"
    assert manifest["eligibility"] == "failed_ineligible"
    assert campaign["eligibility"] == "failed_ineligible"
    assert campaign["benchmark_source"]["capture_boundary"] == (
        "captured after terminal cleanup and after the failed-corpus "
        "archival-tool amendment; archived benchmark source is post-run "
        "preservation code and must not be interpreted as byte-identical "
        "run-time source"
    )
    assert campaign["product"]["commit"] == "b" * 40
    assert campaign["product"]["recorded_treatment"]["source_dirty"] is False
    assert campaign["product"]["post_run_checkout"] == {
        "branch": "main",
        "capture_boundary": (
            "post-run checkout HEAD and status were captured after terminal "
            "cleanup; they may reflect a subsequent corrective amendment and "
            "are not the at-run treatment identity"
        ),
        "commit": "e" * 40,
        "dirty": True,
        "status_porcelain": " M crates/fix.rs",
    }
    assert (root / "raw/report.json").read_bytes() == (
        root / "report.json"
    ).read_bytes()


def test_failed_archive_cannot_be_promoted_by_manifest_edit(
    tmp_path: Path,
) -> None:
    run_id = "019fb000-0000-7000-8000-000000000000"
    root, _ = _archive(
        tmp_path / "archive",
        disposition="final",
        run_status="failed",
    )
    archive_manifest = archive_exp1_run.load_json(root / "archive-manifest.json")
    archive_manifest["run_status"] = "completed"
    archive_manifest["eligibility"] = "frozen_final_candidate"
    archive_exp1_run.write_json(root / "archive-manifest.json", archive_manifest)

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="terminal status or eligibility provenance is invalid",
    ):
        archive_exp1_run.verify_archive(root)

    _refresh_inventory(root, run_id, "final", "failed")
    assert archive_exp1_run.verify_archive(root)["verified"] is True


def test_failed_archive_verifier_still_rejects_cleanup_leak(
    tmp_path: Path,
) -> None:
    run_id = "019fb000-0000-7000-8000-000000000000"
    root, _ = _archive(
        tmp_path / "archive",
        disposition="smoke",
        run_status="failed",
    )
    cleanup = archive_exp1_run.load_json(
        root / "cleanup/cleanup-proof.json"
    )
    cleanup["run_labeled_containers"] = ["leaked-container"]
    archive_exp1_run.write_json(
        root / "cleanup/cleanup-proof.json", cleanup
    )
    preflight = archive_exp1_run.load_json(
        root / "environment-preflight.txt"
    )
    preflight["cleanup"] = cleanup
    archive_exp1_run.write_json(
        root / "environment-preflight.txt", preflight
    )
    campaign = archive_exp1_run.load_json(root / "campaign-manifest.json")
    campaign["cleanup"] = cleanup
    archive_exp1_run.write_json(root / "campaign-manifest.json", campaign)
    _refresh_inventory(root, run_id, "smoke", "failed")

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="post-run cleanup proof failed",
    ):
        archive_exp1_run.verify_archive(root)


def test_completed_archive_verifier_rejects_post_run_product_drift(
    tmp_path: Path,
) -> None:
    run_id = "019fb000-0000-7000-8000-000000000000"
    root, _ = _archive(tmp_path / "archive")
    cleanup = archive_exp1_run.load_json(
        root / "cleanup/cleanup-proof.json"
    )
    cleanup["product_commit"] = "e" * 40
    cleanup["product_status_porcelain"] = " M crates/fix.rs"
    archive_exp1_run.write_json(
        root / "cleanup/cleanup-proof.json", cleanup
    )
    preflight = archive_exp1_run.load_json(
        root / "environment-preflight.txt"
    )
    preflight["cleanup"] = cleanup
    preflight["product"]["post_run_checkout"].update(
        {
            "commit": cleanup["product_commit"],
            "status_porcelain": cleanup["product_status_porcelain"],
            "dirty": True,
        }
    )
    archive_exp1_run.write_json(
        root / "environment-preflight.txt", preflight
    )
    campaign = archive_exp1_run.load_json(root / "campaign-manifest.json")
    campaign["cleanup"] = cleanup
    campaign["product"] = preflight["product"]
    archive_exp1_run.write_json(root / "campaign-manifest.json", campaign)
    _refresh_inventory(root, run_id, "exploratory", "completed")

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="completed archive product checkout drift",
    ):
        archive_exp1_run.verify_archive(root)


def test_validate_source_requires_explicit_failed_status(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    run_id, plan_hash = _source_run(source)

    manifest, _, report, _ = archive_exp1_run.validate_source(
        source,
        run_id=run_id,
        disposition="smoke",
        run_status="failed",
        expected_plan_hash=plan_hash,
    )

    assert manifest["failure"]["code"] == "campaign_failed"
    assert report["warnings"]
    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="does not match requested archive status",
    ):
        archive_exp1_run.validate_source(
            source,
            run_id=run_id,
            disposition="smoke",
            run_status="completed",
            expected_plan_hash=plan_hash,
        )


def _write_committed_cli_evidence(source: Path) -> tuple[Path, Path]:
    invocation_id = "a" * 64
    cli = source / "cli-subprocesses"
    cli.mkdir(parents=True)
    stdout = b'{"sandboxes":[]}\n'
    stderr = b""
    stdout_path = cli / f"{invocation_id}.stdout"
    stderr_path = cli / f"{invocation_id}.stderr"
    metadata_path = cli / f"{invocation_id}.json"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    archive_exp1_run.write_json(
        metadata_path,
        {
            "schema_version": 2,
            "invocation_id": invocation_id,
            "request_id": "request-1",
            "return_code": 0,
            "response_validation": "passed",
            "sanitized_argv": ["--gateway-auth-token=[REDACTED]"],
            "stdout_path": f"cli-subprocesses/{invocation_id}.stdout",
            "stderr_path": f"cli-subprocesses/{invocation_id}.stderr",
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "stdout_sha256": f"sha256:{archive_exp1_run.hashlib.sha256(stdout).hexdigest()}",
            "stderr_sha256": f"sha256:{archive_exp1_run.hashlib.sha256(stderr).hexdigest()}",
            "stdout_base64": base64.b64encode(stdout).decode("ascii"),
            "stderr_base64": base64.b64encode(stderr).decode("ascii"),
            "evidence_commit": "metadata-packed-payload-fsync-v1",
        },
    )
    return metadata_path, stdout_path


def test_cli_evidence_v2_commit_validates_payload_integrity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    metadata_path, _ = _write_committed_cli_evidence(source)

    summary = archive_exp1_run.inspect_cli_evidence(source)
    metadata = archive_exp1_run.load_json(metadata_path)

    assert summary["invocation_count"] == 1
    assert summary["return_codes"] == {"0": 1}
    assert summary["auth_redaction"] == "passed"
    assert archive_exp1_run.decode_cli_evidence_payload(
        metadata, "stdout"
    ) == b'{"sandboxes":[]}\n'
    assert archive_exp1_run.decode_cli_evidence_payload(metadata, "stderr") == b""


@pytest.mark.parametrize(
    "mutation",
    ["missing_payload", "changed_payload", "changed_packed_payload", "bad_marker"],
)
def test_cli_evidence_v2_rejects_uncommitted_or_corrupt_payloads(
    tmp_path: Path,
    mutation: str,
) -> None:
    source = tmp_path / "source"
    metadata_path, stdout_path = _write_committed_cli_evidence(source)
    if mutation == "missing_payload":
        stdout_path.unlink()
        expected = "payload"
    elif mutation == "changed_payload":
        stdout_path.write_bytes(b"changed\n")
        expected = "integrity"
    elif mutation == "changed_packed_payload":
        metadata = archive_exp1_run.load_json(metadata_path)
        metadata["stdout_base64"] = base64.b64encode(b"changed\n").decode("ascii")
        archive_exp1_run.write_json(metadata_path, metadata)
        expected = "integrity"
    else:
        metadata = archive_exp1_run.load_json(metadata_path)
        metadata["evidence_commit"] = "unknown"
        archive_exp1_run.write_json(metadata_path, metadata)
        expected = "commit marker"

    with pytest.raises(archive_exp1_run.ArchiveError, match=expected):
        archive_exp1_run.inspect_cli_evidence(source)


def test_failed_observation_and_cli_evidence_may_be_partial(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    cli = source / "cli-subprocesses"
    cli.mkdir(parents=True)
    records = [
        {
            "record": "request",
            "data": {"request_id": "request-1"},
        },
        {"record": "trial", "data": {}},
        {"record": "operation", "data": {}},
    ]
    with (source / "observations.ndjson").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        for sequence, record in enumerate(records, 1):
            stream.write(
                json.dumps(
                    {"data": {"sequence": sequence, "record": record}},
                    sort_keys=True,
                )
                + "\n"
            )
    archive_exp1_run.write_json(
        cli / "request-1.json",
        {
            "request_id": "request-1",
            "return_code": 1,
            "response_validation": "failed",
            "stderr_bytes": 17,
            "sanitized_argv": ["--gateway-auth-token=[REDACTED]"],
        },
    )

    observations, resources = archive_exp1_run.inspect_observations(
        source,
        expected_requests=55,
        expected_batches=19,
        allow_partial=True,
    )
    cli_summary = archive_exp1_run.inspect_cli_evidence(source, allow_failures=True)

    assert observations["request_id_count"] == 1
    assert resources == []
    assert cli_summary["return_codes"] == {"1": 1}
    assert cli_summary["response_validation"] == {"failed": 1}
    with pytest.raises(archive_exp1_run.ArchiveError):
        archive_exp1_run.inspect_observations(
            source,
            expected_requests=55,
            expected_batches=19,
        )
    with pytest.raises(archive_exp1_run.ArchiveError):
        archive_exp1_run.inspect_cli_evidence(source)


def test_archive_verifier_rejects_post_run_limit_substitution(
    tmp_path: Path,
) -> None:
    root, environment = _archive(tmp_path / "archive")
    preflight = archive_exp1_run.load_json(root / "environment-preflight.txt")
    preflight["sandbox_limits"] = {
        **environment["sandbox_limits"],
        "memory_bytes": 0,
    }
    archive_exp1_run.write_json(root / "environment-preflight.txt", preflight)
    _refresh_inventory(root, "019fb000-0000-7000-8000-000000000000")

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="did not preserve run-start provenance exactly",
    ):
        archive_exp1_run.verify_archive(root)


def test_archive_validation_rejects_missing_final_host_fields() -> None:
    environment = _environment()
    del environment["host"]["cpu_model"]

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="final-host text evidence is incomplete",
    ):
        archive_exp1_run.validate_exp1_environment(environment)


def test_final_archive_requires_v1_protocol_and_annotated_product_tag(
    tmp_path: Path,
) -> None:
    root, _ = _archive(tmp_path / "archive", disposition="final")

    result = archive_exp1_run.verify_archive(root)

    assert result["verified"] is True


def test_product_freeze_tag_requires_annotated_tag_peeling_to_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = "a" * 40
    tag_object = "b" * 40

    def git_value(root: Path, *args: str) -> str:
        if args[0] == "rev-parse" and args[1].endswith("^{tag}"):
            return tag_object
        if args[:2] == ("cat-file", "-t"):
            return "tag"
        if args[0] == "rev-parse" and args[1].endswith("^{}"):
            return commit
        raise AssertionError(args)

    monkeypatch.setattr(archive_exp1_run, "git_value", git_value)

    value = archive_exp1_run.product_freeze_tag(
        tmp_path, disposition="final", product_commit=commit
    )

    assert value["name"] == "paper-v1-freeze"
    assert value["tag_object"] == tag_object
    assert value["peeled_commit"] == commit

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="does not peel to the measured product commit",
    ):
        archive_exp1_run.product_freeze_tag(
            tmp_path, disposition="final", product_commit="c" * 40
        )


def test_v11_requires_safe_unique_named_pipe_per_execution_block() -> None:
    environment = _environment()
    environment.update(
        gateway_endpoint_identity=(
            "isolated_windows_named_pipe_per_execution_block"
        ),
        gateway_transport=dict(archive_exp1_run.V11_GATEWAY_TRANSPORT),
    )
    plan = {
        "execution_blocks": [
            {"block_id": "block-1", "family_id": "create"},
            {"block_id": "block-2", "family_id": "runtime"},
        ]
    }
    manifest = {
        "gateway_policy": {
            "protocol_version": archive_exp1_run.PROTOCOLS["v1.1"]["id"],
            "mode": "isolated",
            "isolated_runtime_per_execution_block": True,
            "loopback_only": False,
            **archive_exp1_run.V11_GATEWAY_TRANSPORT,
        },
        "gateway_execution_blocks": [
            {
                "block_id": "block-1",
                "family_id": "create",
                "gateway_instance_id": "gateway-1",
                "endpoint_uri": "npipe://./pipe/eos-exp1-block-1",
                **archive_exp1_run.V11_GATEWAY_TRANSPORT,
            },
            {
                "block_id": "block-2",
                "family_id": "runtime",
                "gateway_instance_id": "gateway-2",
                "endpoint_uri": "npipe://./pipe/eos-exp1-block-2",
                **archive_exp1_run.V11_GATEWAY_TRANSPORT,
            },
        ],
    }

    archive_exp1_run.validate_protocol_transport(
        protocol_version="v1.1",
        environment=environment,
        manifest=manifest,
        plan=plan,
        completed=True,
    )

    manifest["gateway_execution_blocks"][1]["endpoint_uri"] = (
        "npipe://./pipe/eos-exp1-block-1"
    )
    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="execution-block endpoint evidence is unsafe",
    ):
        archive_exp1_run.validate_protocol_transport(
            protocol_version="v1.1",
            environment=environment,
            manifest=manifest,
            plan=plan,
            completed=True,
        )


def test_new_archive_requires_explicit_protocol_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "archive_exp1_run.py",
            "--run-id",
            "run",
            "--disposition",
            "smoke",
            "--expected-plan-hash",
            "sha256:" + "a" * 64,
            "--paper-root",
            ".",
            "--product-root",
            ".",
            "--product-bin-dir",
            ".",
            "--product-archive",
            "package.zip",
            "--image",
            "image",
        ],
    )

    assert archive_exp1_run.main() == 1
    assert "protocol_version" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        archive_exp1_run.parser().parse_args(["--protocol-version", "v1.0"])


def test_v11_final_freeze_uses_annotated_v11_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = "a" * 40

    def git_value(root: Path, *args: str) -> str:
        if args[0] == "rev-parse" and args[1].endswith("^{tag}"):
            assert "paper-v1.1-freeze" in args[1]
            return "b" * 40
        if args[:2] == ("cat-file", "-t"):
            return "tag"
        assert "paper-v1.1-freeze" in args[1]
        return commit

    monkeypatch.setattr(archive_exp1_run, "git_value", git_value)
    value = archive_exp1_run.product_freeze_tag(
        tmp_path,
        disposition="final",
        product_commit=commit,
        protocol_version="v1.1",
    )
    assert value["name"] == "paper-v1.1-freeze"


def test_final_paper_git_provenance_requires_clean_frozen_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def git_value(root: Path, *args: str) -> str:
        if args[:2] == ("rev-parse", "--show-toplevel"):
            return str(tmp_path)
        if args[:2] == ("status", "--porcelain=v1"):
            assert "benchmark" in args
            assert "progress.md" in args
            assert "experiment_inventory.md" in args
            assert "experiments/exp1-v1.1-protocol-amendment.md" in args
            assert "experiments/environment_setup.md" in args
            assert "experiments/experiment_log.md" in args
            assert "paper_state.json" in args
            assert "plan/progress.md" in args
            assert "experiments/scripts/project_exp1_final_runtime.py" in args
            assert "experiments/analysis/scripts/generate_exp1_tables.py" in args
            assert ":(exclude,glob)benchmark/**/*.pyc" in args
            return " M benchmark/backend/benchmark_lab/metadata.py"
        raise AssertionError(args)

    monkeypatch.setattr(archive_exp1_run, "git_value", git_value)

    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="not a clean frozen commit",
    ):
        archive_exp1_run.paper_git_provenance(tmp_path, disposition="final")


def test_v11_archive_binds_protocol_live_state_and_analysis_sources() -> None:
    assert archive_exp1_run.PAPER_PROTOCOL_PATHS == (
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
    assert archive_exp1_run.PAPER_ANALYSIS_PATHS == (
        "benchmark/backend/benchmark_lab/derivation.py",
        "benchmark/backend/benchmark_lab/reports.py",
        "experiments/scripts/archive_exp1_run.py",
        "experiments/scripts/project_exp1_final_runtime.py",
        "experiments/analysis/scripts/generate_exp1_tables.py",
    )
    assert set(archive_exp1_run.PAPER_PROTOCOL_PATHS) <= {
        "benchmark/PAPER_ARTIFACT.md",
        *archive_exp1_run.PAPER_FROZEN_SCOPE,
    }
    assert set(archive_exp1_run.PAPER_ANALYSIS_PATHS) <= {
        "benchmark/backend/benchmark_lab/derivation.py",
        "benchmark/backend/benchmark_lab/reports.py",
        *archive_exp1_run.PAPER_FROZEN_SCOPE,
    }


def test_final_paper_git_ignores_generated_pycache_but_blocks_source(
    tmp_path: Path,
) -> None:
    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    (tmp_path / "benchmark/pkg/__pycache__").mkdir(parents=True)
    source = tmp_path / "benchmark/pkg/source.py"
    bytecode = tmp_path / "benchmark/pkg/__pycache__/source.pyc"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    bytecode.write_bytes(b"initial bytecode")
    git("init", "-q")
    git("config", "user.name", "EXP1 Test")
    git("config", "user.email", "exp1@example.invalid")
    git("add", ".")
    git("commit", "-q", "-m", "fixture")

    bytecode.write_bytes(b"generated bytecode drift")
    provenance = archive_exp1_run.paper_git_provenance(tmp_path, disposition="final")
    assert provenance["dirty"] is False
    assert ":(exclude,glob)benchmark/**/*.pyc" in provenance["generated_exclusions"]

    source.write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(
        archive_exp1_run.ArchiveError,
        match="not a clean frozen commit",
    ):
        archive_exp1_run.paper_git_provenance(tmp_path, disposition="final")
