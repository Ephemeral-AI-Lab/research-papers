import pytest

from benchmark_lab.observability import (
    ObservabilityError,
    parse_cgroup,
    parse_snapshot,
    parse_trace,
)


def _trace() -> dict:
    return {
        "view": "trace",
        "trace": "request-1",
        "spans": [{
            "offset_ms": 0,
            "span": {
                "ts": 1,
                "trace": "request-1",
                "span": "root",
                "name": "layerstack.squash",
                "dur_ms": 1.0,
                "status": "completed",
                "attrs": {},
            },
            "children": [],
            "events": [],
        }],
    }


def test_trace_accepts_the_product_root_span_with_omitted_parent() -> None:
    parsed = parse_trace(_trace(), "request-1")

    assert parsed.spans[0].span.parent is None


def test_trace_still_rejects_an_explicit_wrong_root_parent() -> None:
    value = _trace()
    value["spans"][0]["span"]["parent"] = "not-a-root"

    with pytest.raises(ObservabilityError, match="tree contract"):
        parse_trace(value, "request-1")


def test_cgroup_accepts_partial_view_before_resource_ring_is_ready() -> None:
    parsed = parse_cgroup(
        {
            "view": "cgroup",
            "scope": "sandbox",
            "availability": "partial",
            "errors": ["resource ring is not available yet"],
            "topology": {"schema_version": 2, "available": True},
            "series": [],
        }
    )

    assert parsed.series == []


def test_snapshot_accepts_current_daemon_event_store() -> None:
    parsed = parse_snapshot(
        {
            "sandbox_id": "sandbox-1",
            "lifecycle_state": "ready",
            "availability": "available",
            "sampled_at_unix_ms": 1,
            "errors": [],
            "daemon": {
                "daemon_pid": 7,
                "runtime_dir": "/eos/runtime/daemon",
                "event_store": {
                    "dropped_storage": 0,
                    "dropped_oversized": 0,
                    "truncated_records": 0,
                },
            },
            "resources": {"latest": None, "history": []},
            "workspaces": [
                {
                    "workspace_id": "workspace-1",
                    "lifecycle_state": "active",
                    "finalization_state": "active",
                    "network_profile": "shared",
                    "finalize_policy": "no_op",
                    "layers": {"base_root_hash": None, "layer_count": 1},
                    "namespace_fd_count": 0,
                    "resources": {"latest": None, "history": []},
                    "active_namespace_executions": [],
                }
            ],
            "stack": None,
        },
        "sandbox-1",
    )

    assert parsed.daemon.event_store.truncated_records == 0
    assert parsed.workspaces[0].finalization_state == "active"
