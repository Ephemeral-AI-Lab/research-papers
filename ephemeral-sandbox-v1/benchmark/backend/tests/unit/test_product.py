import pytest

from benchmark_lab.product import ProductAccessError, _sandbox_record


def current_sandbox_record() -> dict[str, object]:
    return {
        "id": "sandbox-1",
        "workspace_root": "/benchmark/runs/run-1/workspace",
        "state": "ready",
        "activity_revision": 0,
        "daemon": {"host": "127.0.0.1", "port": 32768},
        "daemon_http": {"host": "127.0.0.1", "port": 32769},
        "shared_base": {
            "source": "/cache/base",
            "target": "/eos/layer-stack/base",
            "root_hash": "abc",
            "readonly": True,
        },
        "resource_profile": {
            "name": "standard",
            "nano_cpus": 1_000_000_000,
            "memory_high_bytes": 402_653_184,
            "memory_max_bytes": 536_870_912,
            "pids_max": 256,
            "workload_memory_high_bytes": 402_653_184,
            "workload_memory_max_bytes": 402_653_184,
            "workload_pids_max": 224,
            "control_plane_pids_reserve": 32,
            "daemon_runtime_profile": "standard",
            "separate_workload_cgroup": True,
        },
    }


def test_accepts_current_sandbox_resource_profile() -> None:
    record = _sandbox_record(current_sandbox_record())
    assert record.activity_revision == 0
    assert record.resource_profile.memory_max_bytes == 536_870_912


def test_rejects_unknown_sandbox_response_fields() -> None:
    value = current_sandbox_record()
    value["unknown"] = True
    with pytest.raises(ProductAccessError, match="schema"):
        _sandbox_record(value)
