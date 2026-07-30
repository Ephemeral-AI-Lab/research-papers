import copy
import json
from pathlib import Path

from benchmark_lab.derivation import build_report
from benchmark_lab.resource_sampling import resource_metric_source


GOLDEN = (
    Path(__file__).resolve().parents[3]
    / "tests/fixtures/golden/rust/quick-smoke-completed"
)


def _artifact(name: str) -> dict:
    return json.loads((GOLDEN / name).read_text())["data"]


def _plan_for(*operation_ids: str) -> dict:
    plan = copy.deepcopy(_artifact("expanded-plan.json"))
    plan["cells"] = [
        cell for cell in plan["cells"] if cell["operation_id"] in operation_ids
    ]
    plan["estimates"] = {
        "cell_count": len(plan["cells"]),
        "trial_batch_count": len(plan["cells"]),
        "issued_operation_request_count": len(plan["cells"]),
    }
    return plan


def _record(kind: str, data: dict) -> dict:
    return {"record": {"record": kind, "data": data}}


def _trial(cell: dict, trial_id: str, latency: int) -> dict:
    return _record(
        "trial",
        {
            "operation_id": cell["operation_id"],
            "cell_id": cell["cell_id"],
            "trial_id": trial_id,
            "warmup": False,
            "kind": "measured",
            "sequence_in_cell": 0,
            "reportable": True,
            "latency_ns": latency,
            "request_count": 1,
            "status": "success",
            "product_succeeded": True,
            "infrastructure_failed": False,
            "cleanup_baseline_restored": True,
            "checks_passed": True,
            "setup_ns": 101,
            "operation_ns": latency,
            "verify_ns": 202,
            "teardown_ns": 303,
            "artifacts": [],
        },
    )


def _request(cell: dict, trial_id: str, latency: int) -> dict:
    return _record(
        "request",
        {
            "operation_id": cell["operation_id"],
            "cell_id": cell["cell_id"],
            "trial_id": trial_id,
            "request_id": f"request-{trial_id}",
            "warmup": False,
            "start_offset_ns": 1_000,
            "latency_ns": latency,
            "response_bytes": 10,
            "response_sha256": "sha256:response",
            "status": "success",
        },
    )


def _checks(definitions: dict, cell: dict, trial_id: str) -> list[dict]:
    operation = next(
        item for item in definitions["operations"] if item["id"] == cell["operation_id"]
    )
    return [
        _record(
            "check",
            {
                "operation_id": cell["operation_id"],
                "cell_id": cell["cell_id"],
                "trial_id": trial_id,
                "request_id": None,
                "check_id": check["id"],
                "semantic_revision": check["semantic_revision"],
                "passed": True,
                "expected": "expected",
                "actual": "actual",
                "artifact_id": None,
            },
        )
        for check in operation["checks"]
    ]


def _resource(
    cell: dict,
    trial_id: str,
    definition: dict,
    offset: int,
    value: float | None,
) -> dict:
    source = resource_metric_source(definition["id"])
    observed = (
        {"availability": "available", "value": value}
        if value is not None
        else {
            "availability": "unavailable",
            "source": source,
            "reason": "deliberately unavailable",
        }
    )
    return _record(
        "resource",
        {
            "cell_id": cell["cell_id"],
            "trial_id": trial_id,
            "request_id": None,
            "reading": {
                "schema_version": 1,
                "metric_id": definition["id"],
                "metric_semantic_revision": definition["semantic_revision"],
                "unit": definition["unit"],
                "scope": definition["scope"],
                "kind": definition["kind"],
                "aggregation": definition["aggregation"],
                "source": source,
                "monotonic_offset_ns": offset,
                "value": observed,
            },
        },
    )


def _report(plan: dict, observations: list[dict], state: str = "completed"):
    return build_report(
        run_id="unit-report",
        state=state,
        plan=plan,
        definitions=_artifact("definition-snapshot.json"),
        definition_snapshot_sha256="sha256:fixture-definition-snapshot",
        environment=_artifact("environment-metadata.json"),
        observations=observations,
        started_at="2026-01-01T00:00:00Z",
        ended_at="2026-01-01T00:00:01Z",
    )


def test_derives_all_registered_metrics_lifecycle_and_resource_semantics() -> None:
    plan = _plan_for("file_read")
    cell = plan["cells"][0]
    definitions = _artifact("definition-snapshot.json")
    trial_id = "trial-file-read"
    observations = [_trial(cell, trial_id, 1_000), _request(cell, trial_id, 900)]
    observations.extend(_checks(definitions, cell, trial_id))
    for definition in definitions["metrics"]:
        first = None if definition["id"] == "daemon_rss_bytes" else 10.0
        second = None if definition["id"] == "daemon_rss_bytes" else 25.0
        observations.extend(
            [
                _resource(cell, trial_id, definition, 900, first),
                _resource(cell, trial_id, definition, 2_100, second),
            ]
        )

    report = _report(plan, observations)
    result = report.cells[0]
    metrics = {item["identity"]["id"]: item for item in result["metrics"]}

    assert report.correctness_verdict == "pass"
    assert len(metrics) == 20
    assert metrics["setup_ns"]["raw_points"][0]["value"] == 101
    assert metrics["verify_ns"]["raw_points"][0]["value"] == 202
    assert metrics["teardown_ns"]["raw_points"][0]["value"] == 303
    assert metrics["sandbox_cpu_time_ns"]["raw_points"][0]["value"] == 15
    assert metrics["runner_rss_bytes"]["raw_points"][0]["value"] == 25
    assert metrics["host_free_bytes"]["raw_points"][0]["value"] == 10
    unavailable = metrics["daemon_rss_bytes"]["unavailable"]
    assert unavailable["count"] == 1
    assert unavailable["reasons"] == {
        f'{resource_metric_source("daemon_rss_bytes")}:deliberately unavailable': 1
    }
    correlation = result["cpu_latency_correlation"]
    assert correlation["points"] == [
        {
            "trial_id": trial_id,
            "operation_latency_ns": 1_000.0,
            "sandbox_cpu_time_ns": 15.0,
        }
    ]
    assert [item["identity"]["id"] for item in result["metrics"]] == sorted(metrics)


def test_completed_report_fails_when_a_registered_check_is_missing() -> None:
    plan = _plan_for("file_read")
    cell = plan["cells"][0]
    definitions = _artifact("definition-snapshot.json")
    trial_id = "trial-missing-check"
    observations = [_trial(cell, trial_id, 1_000), _request(cell, trial_id, 900)]
    observations.extend(_checks(definitions, cell, trial_id)[:1])

    report = _report(plan, observations)

    assert report.correctness_verdict == "fail"
    assert {item["code"] for item in report.warnings} == {
        "missing_correctness_observations"
    }


def test_infrastructure_and_cleanup_failures_remain_independently_attributed() -> None:
    plan = _plan_for("file_read")
    cell = plan["cells"][0]
    trial = _trial(cell, "trial-combined-failure", 1_000)
    data = trial["record"]["data"]
    data.update(
        reportable=False,
        status="cleanup_invalid",
        infrastructure_failed=True,
        cleanup_baseline_restored=False,
        checks_passed=False,
    )

    report = _report(plan, [trial], state="failed")

    assert report.cells[0]["counts"]["infrastructure_failed"] == 1
    assert report.cells[0]["counts"]["cleanup_invalid"] == 1


def test_squash_factor_study_and_optional_remount_phase_match_contract() -> None:
    plan = _plan_for("squash_layerstack")
    definitions = _artifact("definition-snapshot.json")
    operation = next(
        item for item in definitions["operations"] if item["id"] == "squash_layerstack"
    )
    observations = []
    for cell in plan["cells"]:
        live_sessions = cell["operation"]["cell"]["live_sessions"]
        trial_id = f"trial-squash-{live_sessions}"
        latency = 1_000 + live_sessions * 1_000
        observations.extend(
            [_trial(cell, trial_id, latency), _request(cell, trial_id, latency - 100)]
        )
        observations.extend(_checks(definitions, cell, trial_id))
        phase_definitions = [
            item
            for item in operation["phases"]
            if item["id"] != "workspace_session_remount" or live_sessions > 0
        ]
        for index, phase in enumerate(phase_definitions):
            observations.append(
                _record(
                    "phase",
                    {
                        "id": phase["id"],
                        "semantic_revision": phase["semantic_revision"],
                        "unit": phase["unit"],
                        "cell_id": cell["cell_id"],
                        "trial_id": trial_id,
                        "request_id": f"request-{trial_id}",
                        "source": phase["source"],
                        "correlation": phase["correlation"],
                        "trace_span_name": phase["trace_span_name"],
                        "start_offset_ns": 1_100 + index * 100,
                        "duration_ns": 50,
                        "status": "succeeded",
                    },
                )
            )

    report = _report(plan, observations)
    by_live_sessions = {
        next(
            factor["value"]["value"]
            for factor in cell["factors"]
            if factor["id"] == "live_sessions"
        ): cell
        for cell in report.cells
    }

    assert report.correctness_verdict == "pass"
    assert report.factor_studies[0]["layout"] == {
        "kind": "trend",
        "factor_id": "live_sessions",
    }
    assert len(report.factor_studies[0]["control_comparisons"]) == 1
    assert "workspace_session_remount" not in {
        item["id"] for item in by_live_sessions[0]["phases"]
    }
    assert "workspace_session_remount" in {
        item["id"] for item in by_live_sessions[1]["phases"]
    }
    first_span = by_live_sessions[1]["timelines"][0]["phase_spans"][0]
    assert first_span["label"] == "Total squash"
    assert first_span["help"] == operation["phases"][0]["help"]
    assert by_live_sessions[1]["timelines"][0]["domain_end_ns"] >= 1_150
