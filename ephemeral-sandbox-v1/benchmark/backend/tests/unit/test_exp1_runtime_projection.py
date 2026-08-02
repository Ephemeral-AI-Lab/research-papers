import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PAPER_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = PAPER_ROOT / "experiments/scripts/project_exp1_final_runtime.py"
SPEC = importlib.util.spec_from_file_location("project_exp1_final_runtime_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
projection = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = projection
SPEC.loader.exec_module(projection)

SMOKE_ARCHIVE = PAPER_ROOT / "experiments/runs/019fb5e4-3f62-7760-bc3f-e7501502ec74"
PILOT_ARCHIVE = PAPER_ROOT / "experiments/runs/019fb5f1-d73a-7128-9bab-d75dd229c020"
V11_SMOKE_ARCHIVE = PAPER_ROOT / "experiments/runs/019fb83a-54bc-79db-b6ac-6189fb28f5f2"
V11_PILOT_ARCHIVE = PAPER_ROOT / "experiments/runs/019fb84e-aef1-7fdc-9a56-1adbe712f30d"
V11_FINAL_PLAN = PAPER_ROOT / "tmp/validate-paper-good-pass-v11-20260731T1327Z.json"


def test_v11_projection_rejects_unsafe_named_pipe_endpoint() -> None:
    campaign = {
        "protocol": {
            "version": "v1.1",
            "id": projection.PROTOCOLS["v1.1"]["id"],
        }
    }
    manifest = {
        "environment": {
            "gateway_endpoint_identity": (
                "isolated_windows_named_pipe_per_execution_block"
            ),
            "gateway_transport": dict(projection.V11_GATEWAY_TRANSPORT),
        },
        "gateway_policy": {
            "protocol_version": projection.PROTOCOLS["v1.1"]["id"],
            "mode": "isolated",
            "isolated_runtime_per_execution_block": True,
            "loopback_only": False,
            **projection.V11_GATEWAY_TRANSPORT,
        },
        "gateway_execution_blocks": [
            {
                "block_id": "block-1",
                "family_id": "runtime",
                "gateway_instance_id": "gateway-1",
                "endpoint_uri": "npipe://./pipe/../unsafe",
                **projection.V11_GATEWAY_TRANSPORT,
            }
        ],
    }
    plan = {"execution_blocks": [{"block_id": "block-1", "family_id": "runtime"}]}

    with pytest.raises(
        projection.ProjectionError,
        match="execution-block endpoint evidence is unsafe",
    ):
        projection._validate_protocol_transport(campaign, manifest, plan, "v1.1")


def _plan(role: str) -> dict:
    repetitions = {
        "smoke": (0, 1, 19, 55, "paper-env-smoke"),
        "pilot": (2, 5, 133, 385, "paper-pilot"),
        "final": (2, 100, 1_938, 5_610, "paper-good-pass"),
    }
    warmups, measured, batches, requests, name = repetitions[role]
    cells = []
    cell_ids = []
    for index in range(19):
        cell_id = f"cell-{index:02d}"
        cell_ids.append(cell_id)
        cells.append(
            {
                "cell_id": cell_id,
                "family_id": "family",
                "operation_id": f"operation-{index:02d}",
                "operation_semantic_revision": 1,
                "factor_schema_revision": 1,
                "comparison_key": {"index": index},
                "operation": {"kind": "synthetic", "index": index},
                "protocol": {
                    "destructive": False,
                    "warmups": warmups,
                    "measured_trials": measured,
                    "timeout_ms": 120_000,
                    "cleanup": "synthetic-cleanup",
                },
            }
        )
    return {
        "schema_version": 1,
        "runnable": True,
        "is_customized": False,
        "plan_hash": f"sha256:{role}",
        "canonical_plan": {
            "name": name,
            "configuration_base": {},
            "seed": 1,
            "environment": {},
            "operations": [],
            "protocol": {
                "order": "randomized_blocks",
                "resource_interval_ms": 100,
                "timeout_ms": {"default": 120_000},
                "trial_defaults": {
                    "fast": {
                        "warmups": warmups,
                        "measured_trials": measured,
                    },
                    "destructive": {
                        "warmups": warmups,
                        "measured_trials": measured,
                    },
                },
            },
        },
        "effective_environment": {"client_cohort": "product_cli"},
        "fixed_lifecycle_policy": {"scope": "synthetic"},
        "selected_workspace_profiles": [],
        "cells": cells,
        "execution_blocks": [
            {
                "block_id": "block-family",
                "family_id": "family",
                "cell_ids": cell_ids,
                "restart_reason": None,
            }
        ],
        "estimates": {
            "cell_count": 19,
            "trial_batch_count": batches,
            "issued_operation_request_count": requests,
        },
        "validation": [],
    }


def _trials(
    prefix: str,
    active_ns: list[int],
    warmups: int,
    gaps_ns: list[int],
) -> tuple:
    trials = []
    cursor = 0
    for index, active in enumerate(active_ns):
        trials.append(
            projection.TrialSpan(
                trial_id=f"{prefix}-{index}",
                warmup=index < warmups,
                start_ns=cursor,
                end_ns=cursor + active,
                phase_ns={phase: 0 for phase in projection.PHASES},
            )
        )
        if index < len(gaps_ns):
            cursor += active + gaps_ns[index]
    return tuple(trials)


def _protocol_file(path: str, marker: str) -> dict:
    return {
        "path": path,
        "bytes": len(marker),
        "sha256": f"sha256:{marker * 64}",
    }


def _v11_provenance(marker: str = "a") -> dict:
    return {
        "same": True,
        "freeze_state": {
            "protocol": "pre_freeze",
            "paper_git": "pre_freeze_worktree",
        },
        "protocol_files": [
            _protocol_file(path, marker)
            for path in sorted(projection.V11_PROTOCOL_FILE_PATHS)
        ],
    }


def _profile(role: str) -> projection.RunProfile:
    raw_plan = _plan(role)
    semantics = projection._validate_plan(raw_plan, role=role)
    cells = {}
    for semantic in semantics["cells"]:
        cell = semantics["cell_data"][semantic]
        if role == "smoke":
            active, warmups, gaps = [5], 0, []
            leading, trailing = 10, 5
        else:
            active, warmups, gaps = (
                [7, 11, 13, 17, 19, 23, 29],
                2,
                [
                    2,
                    3,
                    5,
                    7,
                    11,
                    14,
                ],
            )
            leading, trailing = 12, 4
        cells[semantic] = projection.CellProfile(
            semantic_key=semantic,
            semantic_sha256=projection.canonical_sha256(json.loads(semantic)),
            family_id="family",
            operation_id=cell["operation_id"],
            leading_ns=leading,
            trailing_ns=trailing,
            trials=_trials(cell["operation_id"], active, warmups, gaps),
            gaps_ns=tuple(gaps),
        )
    return projection.RunProfile(
        role=role,
        identity={
            "run_id": role,
            "protocol_version": "v1.1",
            "provenance": _v11_provenance(),
        },
        plan=semantics,
        elapsed_ns=1_000 if role == "smoke" else 900,
        run_residual_ns=100 if role == "smoke" else 101,
        family_residual_ns={"family": 50 if role == "smoke" else 53},
        cells=cells,
    )


def _reviewed_final_plan_from_pilot() -> dict:
    final = copy.deepcopy(
        projection.envelope_data(
            PILOT_ARCHIVE / "raw/expanded-plan.json",
            "eos_benchmark_expanded_plan",
        )
    )
    final["canonical_plan"]["name"] = "paper-good-pass"
    defaults = final["canonical_plan"]["protocol"]["trial_defaults"]
    for trial_class in defaults.values():
        trial_class["warmups"] = 2
        trial_class["measured_trials"] = 100
    for cell in final["cells"]:
        cell["protocol"]["warmups"] = 2
        cell["protocol"]["measured_trials"] = 100
    final["estimates"]["cell_count"] = 19
    final["estimates"]["trial_batch_count"] = 1_938
    final["estimates"]["issued_operation_request_count"] = 5_610
    final["plan_hash"] = projection.canonical_sha256(final)
    return final


def test_cross_run_allows_only_prefreeze_status_hash_evolution():
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    for entry in pilot.identity["provenance"]["protocol_files"]:
        if entry["path"] in projection.V11_PREFREEZE_MUTABLE_STATUS_PATHS:
            entry.update(_protocol_file(entry["path"], "b"))

    projection.validate_cross_run(smoke, pilot, _plan("final"))


def test_cross_run_rejects_scientific_protocol_hash_drift():
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    path = "experiments/exp1-v1.1-protocol-amendment.md"
    for entry in pilot.identity["provenance"]["protocol_files"]:
        if entry["path"] == path:
            entry.update(_protocol_file(path, "b"))

    with pytest.raises(
        projection.ProjectionError,
        match="provenance identities drifted",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


def test_cross_run_rejects_invalid_or_duplicate_protocol_identity():
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    ledger = smoke.identity["provenance"]["protocol_files"][0]
    smoke.identity["provenance"]["protocol_files"].append(copy.deepcopy(ledger))
    pilot.identity["provenance"] = copy.deepcopy(smoke.identity["provenance"])

    with pytest.raises(
        projection.ProjectionError,
        match="protocol-file identity is invalid",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


@pytest.mark.parametrize("invalid", [None, [], "not-a-list"])
def test_cross_run_rejects_missing_protocol_file_identity(invalid):
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    smoke.identity["provenance"]["protocol_files"] = invalid
    pilot.identity["provenance"]["protocol_files"] = copy.deepcopy(invalid)

    with pytest.raises(
        projection.ProjectionError,
        match="protocol-file identity",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


def test_cross_run_rejects_extra_protocol_file_identity():
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    extra = _protocol_file("unexpected.md", "a")
    smoke.identity["provenance"]["protocol_files"].append(extra)
    pilot.identity["provenance"]["protocol_files"].append(copy.deepcopy(extra))

    with pytest.raises(
        projection.ProjectionError,
        match="protocol-file identity set is invalid",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


def test_cross_run_rejects_non_prefreeze_status():
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    smoke.identity["provenance"]["freeze_state"]["protocol"] = "frozen"
    pilot.identity["provenance"] = copy.deepcopy(smoke.identity["provenance"])

    with pytest.raises(
        projection.ProjectionError,
        match="freeze-state identity is invalid",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


@pytest.mark.parametrize(
    "category",
    [
        "benchmark_source",
        "analysis_and_archiving_code",
        "artifact_schemas",
        "definition_snapshot",
        "docker",
        "fixture",
        "gateway",
        "host",
        "image",
        "lifecycle",
        "product",
        "sandbox_limits",
        "treatment",
    ],
)
def test_cross_run_rejects_non_status_provenance_drift(category):
    smoke = _profile("smoke")
    pilot = _profile("pilot")
    smoke.identity["provenance"][category] = {"identity": "same"}
    pilot.identity["provenance"][category] = {"identity": "different"}

    with pytest.raises(
        projection.ProjectionError,
        match="provenance identities drifted",
    ):
        projection.validate_cross_run(smoke, pilot, _plan("final"))


def test_projection_archive_rejects_non_prefreeze_campaign():
    campaign = {
        "protocol": {
            "freeze_state": "frozen",
            "files": [
                _protocol_file(path, "a")
                for path in sorted(projection.V11_PROTOCOL_FILE_PATHS)
            ],
        },
        "paper_git": {"freeze_state": "frozen_worktree"},
    }

    with pytest.raises(
        projection.ProjectionError,
        match="not in the pre-freeze state",
    ):
        projection._validate_prefreeze_campaign(campaign, "v1.1")


def test_structural_projection_uses_exact_arithmetic_and_fixed_units_once():
    result = projection.project_structural(
        _profile("smoke"),
        _profile("pilot"),
        _plan("final"),
        final_plan_sha256="sha256:final-file",
        script_sha256="sha256:script",
    )

    assert result["decomposition"]["run_fixed_ns"] == 101
    assert result["decomposition"]["family_fixed_ns"] == {"family": 53}
    assert {cell["fixed"]["total_ns"] for cell in result["decomposition"]["cells"]} == {
        17
    }
    assert result["models"]["central_structural"] == {
        "numerator_ns": 226_773,
        "denominator": 4,
        "ceil_ns": 56_694,
    }
    assert result["models"]["observed_envelope_ns"] == 82_861
    assert result["gate_3_runtime_pass"] is True
    assert projection.render_json(result) == projection.render_json(result)


def test_v11_smoke_and_pilot_archives_pass_reviewed_runtime_gate():
    smoke = projection.load_run_profile(
        V11_SMOKE_ARCHIVE,
        "smoke",
        protocol_version="v1.1",
    )
    pilot = projection.load_run_profile(
        V11_PILOT_ARCHIVE,
        "pilot",
        protocol_version="v1.1",
    )
    result = projection.project_structural(
        smoke,
        pilot,
        projection.load_json(V11_FINAL_PLAN),
        final_plan_sha256=projection.sha256_file(V11_FINAL_PLAN),
        script_sha256="sha256:test-script",
    )

    assert result["display_seconds"] == {
        "pilot_elapsed": "276.094047000",
        "central_structural": "1179.784426150",
        "observed_envelope": "1303.732241600",
        "limit": "1400.000000000",
    }
    assert result["gate_3_runtime_pass"] is True
    assert result["decision"] == "pass_runtime_projection"


def test_accepted_smoke_and_pilot_archives_still_fail_runtime_gate():
    smoke = projection.load_run_profile(SMOKE_ARCHIVE, "smoke")
    pilot = projection.load_run_profile(PILOT_ARCHIVE, "pilot")
    result = projection.project_structural(
        smoke,
        pilot,
        _reviewed_final_plan_from_pilot(),
        final_plan_sha256="sha256:reviewed-final-fixture",
        script_sha256="sha256:test-script",
    )

    assert result["display_seconds"] == {
        "pilot_elapsed": "609.215958000",
        "central_structural": "2460.664462900",
        "observed_envelope": "2745.098529500",
        "limit": "1400.000000000",
    }
    assert result["pass_conditions"] == {
        "pilot_elapsed_within_limit": True,
        "central_structural_within_limit": False,
        "observed_envelope_within_limit": False,
    }
    assert result["gate_3_runtime_pass"] is False
    assert result["decision"].startswith("block_freeze")
