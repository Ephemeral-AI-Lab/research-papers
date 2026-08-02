from copy import deepcopy

import pytest
from benchmark_lab.observability import (
    ObservabilityError,
    daemon_from_cgroup,
    parse_cgroup,
    parse_daemon,
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


def _daemon_metrics() -> dict:
    return {
        "available": True,
        "pid": 7,
        "resident_memory_bytes": 1024,
        "peak_resident_memory_bytes": 2048,
        "cpu_time_us": 3,
    }


def _cgroup_with_daemon(daemon: object) -> dict:
    return {
        "view": "cgroup",
        "scope": "sandbox",
        "availability": "partial",
        "errors": ["resource ring is not available yet"],
        "topology": {"daemon": daemon},
        "series": [],
    }


def test_cgroup_daemon_uses_the_standalone_daemon_payload_model() -> None:
    daemon = _daemon_metrics()
    daemon["future_diagnostic"] = {"value": 1}

    embedded = daemon_from_cgroup(parse_cgroup(_cgroup_with_daemon(daemon)))
    standalone = parse_daemon(
        {"view": "daemon", "scope": "sandbox", "daemon": daemon}
    ).daemon

    assert embedded == standalone
    assert embedded.peak_resident_memory_bytes == 2048


@pytest.mark.parametrize(
    "daemon",
    [
        None,
        {},
        {**_daemon_metrics(), "available": 1},
        {**_daemon_metrics(), "pid": True},
        {**_daemon_metrics(), "resident_memory_bytes": -1},
        {key: value for key, value in _daemon_metrics().items() if key != "cpu_time_us"},
    ],
)
def test_cgroup_daemon_rejects_missing_or_malformed_payload(
    daemon: object,
) -> None:
    cgroup = parse_cgroup(_cgroup_with_daemon(daemon))

    with pytest.raises(
        ObservabilityError,
        match="product cgroup topology daemon response schema is invalid",
    ):
        daemon_from_cgroup(cgroup)


def test_cgroup_daemon_requires_the_embedded_object() -> None:
    cgroup = parse_cgroup(_cgroup_with_daemon(_daemon_metrics()))
    del cgroup.topology["daemon"]

    with pytest.raises(
        ObservabilityError,
        match="product cgroup topology daemon response schema is invalid",
    ):
        daemon_from_cgroup(cgroup)


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


def _snapshot_with_bc1e6ee0_resources() -> dict:
    return {
        "sandbox_id": "eos-e173422b-df20-4e1d-a954-c6ebfd659675",
        "lifecycle_state": "ready",
        "availability": "available",
        "sampled_at_unix_ms": 1785457778803,
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
        "resources": {
            "latest": {
                "ts": 1785457778639,
                "sample_delta_ms": 250,
                "metrics": {
                    "metrics_source": "sandbox_cgroup",
                    "cgroup_path": "/sys/fs/cgroup/",
                    "cgroup_available": True,
                    "cpu_usec": 57196,
                    "mem_cur": 5091328,
                    "mem_max": 536870912,
                    "mem_max_unlimited": False,
                    "io_rbytes": 98304,
                    "io_wbytes": 16384,
                    "pids_cur": 12,
                },
                "deltas": {
                    "cpu_usec": 610,
                    "io_rbytes": 0,
                    "io_wbytes": 0,
                },
            },
            "history": [],
        },
        "workspaces": [
            {
                "workspace_id": "00000118c73863b675fec5",
                "lifecycle_state": "active",
                "finalization_state": "active",
                "network_profile": "shared",
                "finalize_policy": "no_op",
                "layers": {
                    "base_root_hash": (
                        "6158805bdb0976490e45c9c206d73f474d7b449a55ba489a5af80fa4f6103070"
                    ),
                    "layer_count": 1,
                },
                "namespace_fd_count": 3,
                "resources": {
                    "latest": {
                        "ts": 1785457778639,
                        "sample_delta_ms": 250,
                        "metrics": {
                            "disk_bytes": 0,
                            "disk_allocated_bytes": 4096,
                            "files": 0,
                            "disk_truncated": False,
                        },
                        "deltas": {},
                    },
                    "history": [],
                },
                "active_namespace_executions": [],
            }
        ],
        "stack": {
            "layer_count": 1,
            "layers_bytes": None,
            "layers_allocated_bytes": None,
            "storage_allocated_bytes": None,
            "staging_entry_count": 0,
            "active_leases": 1,
        },
    }


def test_snapshot_accepts_exact_bc1e6ee0_resource_shape() -> None:
    value = _snapshot_with_bc1e6ee0_resources()

    parsed = parse_snapshot(value, value["sandbox_id"])

    assert parsed.resources.latest is not None
    assert parsed.resources.latest.metrics.metrics_source == "sandbox_cgroup"
    assert parsed.resources.latest.metrics.io_rbytes == 98304
    assert parsed.resources.latest.metrics.pids_cur == 12
    assert parsed.resources.latest.deltas.io_wbytes == 0
    assert parsed.workspaces[0].resources.latest is not None
    assert parsed.workspaces[0].resources.latest.metrics.disk_allocated_bytes == 4096


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        (("resources", "latest", "metrics"), "disk_bytes", 0),
        (("resources", "latest", "metrics"), "future_counter", 1),
        (("resources", "latest", "deltas"), "future_counter", 1),
        (
            ("workspaces", 0, "resources", "latest", "metrics"),
            "metrics_source",
            "sandbox_cgroup",
        ),
        (("workspaces", 0, "resources", "latest", "metrics"), "cpu_usec", 1),
        (("workspaces", 0, "resources", "latest", "deltas"), "io_rbytes", 1),
    ],
)
def test_snapshot_rejects_unknown_or_mixed_scope_resource_keys(
    target: tuple[str | int, ...],
    field: str,
    value: object,
) -> None:
    snapshot = deepcopy(_snapshot_with_bc1e6ee0_resources())
    selected = snapshot
    for part in target:
        selected = selected[part]
    selected[field] = value

    with pytest.raises(
        ObservabilityError, match="product snapshot response schema is invalid"
    ):
        parse_snapshot(snapshot, snapshot["sandbox_id"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metrics_source", None),
        ("metrics_source", "docker_engine"),
        ("cgroup_path", None),
        ("cgroup_available", None),
    ],
)
def test_snapshot_requires_sandbox_cgroup_identity(
    field: str,
    value: object,
) -> None:
    snapshot = deepcopy(_snapshot_with_bc1e6ee0_resources())
    snapshot["resources"]["latest"]["metrics"][field] = value

    with pytest.raises(
        ObservabilityError, match="product snapshot response schema is invalid"
    ):
        parse_snapshot(snapshot, snapshot["sandbox_id"])


def test_snapshot_requires_workspace_disk_identity() -> None:
    snapshot = deepcopy(_snapshot_with_bc1e6ee0_resources())
    del snapshot["workspaces"][0]["resources"]["latest"]["metrics"][
        "disk_truncated"
    ]

    with pytest.raises(
        ObservabilityError, match="product snapshot response schema is invalid"
    ):
        parse_snapshot(snapshot, snapshot["sandbox_id"])
