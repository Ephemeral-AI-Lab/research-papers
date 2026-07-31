from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmark_lab import metadata


def _host() -> dict:
    return {
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


def _limits() -> dict:
    return {
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


def test_released_configuration_resolves_effective_standard_limits(
    tmp_path: Path,
) -> None:
    config = tmp_path / "windows-amd64.yml"
    config.write_text(
        """
manager:
  docker:
    resource_profile: standard
    resource_profiles:
      standard:
        nano_cpus: 2000000000
        memory_max_bytes: 1073741824
        pids_max: 256
    nano_cpus: 1000000000
    memory_bytes: 536870912
""".lstrip(),
        encoding="utf-8",
    )

    limits = metadata._configured_sandbox_limits_from_template(config)

    assert limits["profile"] == "standard"
    assert limits["nano_cpus"] == 1_000_000_000
    assert limits["vcpus"] == 1
    assert limits["memory_bytes"] == 536_870_912
    assert limits["pids_limit"] == 256
    assert limits["authority"]["sha256"].startswith("sha256:")
    assert limits["authority"]["create_request_override"] == "none"


def test_exp1_host_and_limit_validation_fail_closed_on_drift() -> None:
    host = _host()
    host["logical_processors"] = 47
    with pytest.raises(
        metadata.EnvironmentMetadataError, match="logical CPU counts disagree"
    ):
        metadata._validate_exp1_host(host)

    limits = _limits()
    limits["memory_bytes"] = 0
    with pytest.raises(
        metadata.EnvironmentMetadataError,
        match="effective sandbox limit drift",
    ):
        metadata._validate_exp1_sandbox_limits(limits)


@pytest.mark.asyncio
async def test_paper_environment_records_final_host_and_limits_at_run_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "binary"
    binary.write_bytes(b"released")
    host = _host()
    limits = _limits()

    async def capture(target: Path) -> dict:
        assert target == tmp_path
        return dict(host)

    async def command(args: list[str], cwd: Path) -> str:
        if args[:3] == ["git", "rev-parse", "HEAD"]:
            return "1" * 40
        if args[:3] == ["git", "status", "--porcelain=v1"]:
            return ""
        if args[:2] == ["docker", "version"]:
            return "29.0.1"
        if args[:3] == ["docker", "image", "inspect"]:
            return "sha256:" + "2" * 64
        raise AssertionError(args)

    monkeypatch.setattr(metadata, "_capture_windows_final_host", capture)
    monkeypatch.setattr(
        metadata, "_configured_sandbox_limits", lambda roots: dict(limits)
    )
    monkeypatch.setattr(metadata, "_command", command)
    monkeypatch.setattr(
        metadata, "_container_daemon_executable", lambda roots: binary
    )
    monkeypatch.setattr(
        metadata, "_prebuilt_executable", lambda roots, name: binary
    )
    roots = SimpleNamespace(
        product_root=tmp_path,
        benchmark_state_root=tmp_path,
    )
    plan = {
        "canonical_plan": {
            "name": "paper-good-pass",
            "environment": {"image": "ubuntu@sha256:fixed"},
        },
        "effective_environment": {
            "filesystem": None,
            "workspace_root_identity": "sha256:workspace",
            "client_cohort": "product_cli",
            "image_digest": None,
        },
    }

    environment = await metadata.collect_environment(roots, plan)

    assert environment["host"]["capture_boundary"] == (
        "run_start_before_gateway_and_measurement"
    )
    assert environment["host"]["os_build_number"] == 26200
    assert environment["host"]["filesystem"] == "NTFS"
    assert environment["sandbox_limits"] == limits
