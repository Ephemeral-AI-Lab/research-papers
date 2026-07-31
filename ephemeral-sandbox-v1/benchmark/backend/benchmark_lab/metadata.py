from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .catalog import _prebuilt_executable
from .gateway import _container_daemon_executable
from .paths import BenchmarkRoots


_EXP1_PAPER_PLANS = frozenset(
    {"paper-env-smoke", "paper-pilot", "paper-good-pass"}
)
_EXP1_EXPECTED_HOST = {
    "computer_name": "DESKTOP-OLP1ADS",
    "operating_system": "windows",
    "architecture": "x64",
    "os_build_number": 26200,
    "logical_processors": 48,
    "total_memory_bytes": 137_438_953_472,
    "filesystem": "NTFS",
}
_EXP1_EXPECTED_SANDBOX_LIMITS = {
    "profile": "standard",
    "nano_cpus": 1_000_000_000,
    "vcpus": 1,
    "memory_bytes": 536_870_912,
    "pids_limit": 256,
}


class EnvironmentMetadataError(RuntimeError):
    """Required run-start provenance could not be captured or validated."""


async def collect_environment(roots: BenchmarkRoots, plan: dict[str, Any]) -> dict[str, Any]:
    paper_exp1 = _is_exp1_paper_plan(plan)
    final_host: dict[str, Any] | None = None
    sandbox_limits: dict[str, Any] | None = None
    if paper_exp1:
        final_host = await _capture_windows_final_host(roots.benchmark_state_root)
        sandbox_limits = _configured_sandbox_limits(roots)
        _validate_exp1_host(final_host)
        _validate_exp1_sandbox_limits(sandbox_limits)
    commit = await _command(["git", "rev-parse", "HEAD"], roots.product_root)
    status = await _command(["git", "status", "--porcelain=v1", "-z"], roots.product_root)
    docker_version = await _command(
        ["docker", "version", "--format", "{{.Server.Version}}"], roots.product_root
    )
    image = plan["canonical_plan"]["environment"]["image"]
    image_digest = await _command(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image], roots.product_root
    )
    daemon = _container_daemon_executable(roots)
    gateway = _prebuilt_executable(roots, "sandbox-gateway")
    manager_cli = _prebuilt_executable(roots, "sandbox-manager-cli")
    runtime_cli = _prebuilt_executable(roots, "sandbox-runtime-cli")
    observability_cli = _prebuilt_executable(roots, "sandbox-observability-cli")
    usage = shutil.disk_usage(roots.benchmark_state_root)
    effective = plan["effective_environment"]
    host = {
        "operating_system": platform.system().lower(),
        "architecture": platform.machine().lower(),
        "kernel_release": platform.release() or None,
        "docker_engine_version": docker_version or None,
        "filesystem": effective.get("filesystem"),
        "free_space_bytes": usage.free,
        "monotonic_clock": "time.monotonic_ns",
    }
    if final_host is not None:
        host.update(final_host)
    return {
        "schema_version": 1,
        "treatment": {
            "source_commit": commit or "unavailable",
            "source_dirty": bool(status),
            "source_diff_hash": _sha(status.encode()) if status else None,
            "daemon_binary_hash": _sha_file(daemon),
            "gateway_binary_hash": _sha_file(gateway),
            "manager_cli_binary_hash": _sha_file(manager_cli),
            "runtime_cli_binary_hash": _sha_file(runtime_cli),
            "observability_cli_binary_hash": _sha_file(observability_cli),
        },
        "host": host,
        "sandbox_limits": sandbox_limits,
        "image_reference": image,
        "image_digest": image_digest or effective.get("image_digest"),
        "workspace_root_identity": effective["workspace_root_identity"],
        "client_cohort": effective["client_cohort"],
        "gateway_endpoint_identity": "isolated_loopback_per_execution_block",
    }


def _is_exp1_paper_plan(plan: dict[str, Any]) -> bool:
    canonical = plan.get("canonical_plan")
    return (
        isinstance(canonical, dict)
        and canonical.get("name") in _EXP1_PAPER_PLANS
    )


async def _capture_windows_final_host(target_path: Path) -> dict[str, Any]:
    if os.name != "nt":
        raise EnvironmentMetadataError(
            "EXP1 final-host capture requires native Windows"
        )
    script = (
        "$ErrorActionPreference='Stop'; "
        "$target=(Get-Item -LiteralPath '.').FullName; "
        "$os=Get-CimInstance Win32_OperatingSystem; "
        "$computer=Get-CimInstance Win32_ComputerSystem; "
        "$processors=@(Get-CimInstance Win32_Processor); "
        "$names=@($processors | ForEach-Object { "
        "([string]$_.Name).Trim() } | Sort-Object -Unique); "
        "$processorLogical=[int](($processors | Measure-Object "
        "-Property NumberOfLogicalProcessors -Sum).Sum); "
        "$volumeRoot=[System.IO.Path]::GetPathRoot($target); "
        "$volume=Get-Volume -DriveLetter $volumeRoot.Substring(0,1); "
        "[ordered]@{"
        "computer_name=[string]$computer.Name;"
        "operating_system='windows';"
        "os_caption=[string]$os.Caption;"
        "os_version=[string]$os.Version;"
        "os_build_number=[int]$os.BuildNumber;"
        "architecture=[System.Runtime.InteropServices.RuntimeInformation]::"
        "OSArchitecture.ToString().ToLowerInvariant();"
        "cpu_model=($names -join ' + ');"
        "logical_processors=[int]$computer.NumberOfLogicalProcessors;"
        "processor_logical_processors=$processorLogical;"
        "total_memory_bytes=[int64]$computer.TotalPhysicalMemory;"
        "filesystem=[string]$volume.FileSystem;"
        "volume_root=$volumeRoot"
        "} | ConvertTo-Json -Compress"
    )
    raw = await _command(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        target_path.resolve(strict=True),
    )
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as error:
        raise EnvironmentMetadataError(
            "Windows final-host capture did not return valid JSON"
        ) from error
    if not isinstance(value, dict):
        raise EnvironmentMetadataError(
            "Windows final-host capture did not return an object"
        )
    value.update(
        {
            "capture_boundary": "run_start_before_gateway_and_measurement",
            "captured_at": datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            "capture_source": (
                "Windows CIM Win32_OperatingSystem, Win32_ComputerSystem, "
                "Win32_Processor, and Get-Volume"
            ),
        }
    )
    return value


def _configured_sandbox_limits(roots: BenchmarkRoots) -> dict[str, Any]:
    template = (
        roots.product_bin_dir.parent / "config/windows-amd64.yml"
        if os.name == "nt"
        else roots.benchmark_source_root / "defaults/gateway.yml"
    )
    return _configured_sandbox_limits_from_template(template)


def _configured_sandbox_limits_from_template(
    template: Path,
) -> dict[str, Any]:
    if template.is_symlink() or not template.is_file():
        raise EnvironmentMetadataError(
            "authoritative gateway configuration is missing or unsafe"
        )
    try:
        config = yaml.safe_load(template.read_bytes())
        docker = config["manager"]["docker"]
        profile_name = docker["resource_profile"]
        profile = docker["resource_profiles"][profile_name]
        nano_cpus = docker.get("nano_cpus", profile["nano_cpus"])
        memory_bytes = docker.get("memory_bytes", profile["memory_max_bytes"])
        pids_limit = profile["pids_max"]
    except (KeyError, TypeError, yaml.YAMLError) as error:
        raise EnvironmentMetadataError(
            "authoritative gateway resource configuration is invalid"
        ) from error
    values = {
        "profile": profile_name,
        "nano_cpus": nano_cpus,
        "vcpus": (
            nano_cpus // 1_000_000_000
            if isinstance(nano_cpus, int)
            and not isinstance(nano_cpus, bool)
            and nano_cpus % 1_000_000_000 == 0
            else None
        ),
        "memory_bytes": memory_bytes,
        "pids_limit": pids_limit,
        "authority": {
            "kind": "released_gateway_configuration",
            "path": os.fspath(template.resolve(strict=True)),
            "sha256": _sha_file(template),
            "selector": (
                f"manager.docker.resource_profiles.{profile_name} "
                "with manager.docker nano_cpus/memory_bytes overrides"
            ),
            "effective_config_builder": (
                "benchmark_lab.gateway._effective_config preserves the "
                "selected profile and resource override fields"
            ),
            "create_request_override": "none",
            "capture_boundary": "run_start_before_gateway_and_measurement",
        },
    }
    return values


def _validate_exp1_host(host: dict[str, Any]) -> None:
    required_text = ("os_caption", "os_version", "cpu_model", "volume_root")
    if any(not isinstance(host.get(field), str) or not host[field].strip() for field in required_text):
        raise EnvironmentMetadataError(
            "EXP1 final-host text fields are incomplete"
        )
    if host.get("logical_processors") != host.get(
        "processor_logical_processors"
    ):
        raise EnvironmentMetadataError(
            "Windows processor and computer-system logical CPU counts disagree"
        )
    mismatches = [
        field
        for field, expected in _EXP1_EXPECTED_HOST.items()
        if (
            str(host.get(field)).casefold() != expected.casefold()
            if isinstance(expected, str)
            else host.get(field) != expected
        )
    ]
    if mismatches:
        raise EnvironmentMetadataError(
            "EXP1 final-host identity drift: " + ", ".join(mismatches)
        )
    if host.get("capture_boundary") != "run_start_before_gateway_and_measurement":
        raise EnvironmentMetadataError("EXP1 host capture boundary is invalid")


def _validate_exp1_sandbox_limits(limits: dict[str, Any]) -> None:
    mismatches = [
        field
        for field, expected in _EXP1_EXPECTED_SANDBOX_LIMITS.items()
        if limits.get(field) != expected
    ]
    authority = limits.get("authority")
    if (
        mismatches
        or not isinstance(authority, dict)
        or authority.get("kind") != "released_gateway_configuration"
        or not isinstance(authority.get("path"), str)
        or not isinstance(authority.get("sha256"), str)
        or not authority["sha256"].startswith("sha256:")
        or authority.get("create_request_override") != "none"
        or authority.get("capture_boundary")
        != "run_start_before_gateway_and_measurement"
    ):
        detail = ", ".join(mismatches) or "authority"
        raise EnvironmentMetadataError(
            f"EXP1 effective sandbox limit drift: {detail}"
        )


async def _command(args: list[str], cwd: Path) -> str:
    process: asyncio.subprocess.Process | None = None
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            env={
                name: os.environ[name]
                for name in (
                    "PATH",
                    "HOME",
                    "USERPROFILE",
                    "SystemRoot",
                    "WINDIR",
                    "DOCKER_HOST",
                    "DOCKER_CONTEXT",
                    "DOCKER_CONFIG",
                    "GIT_CONFIG_GLOBAL",
                    "GIT_CONFIG_SYSTEM",
                )
                if name in os.environ
            },
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), 30)
    except TimeoutError:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        return ""
    except OSError:
        return ""
    if process.returncode != 0 or len(stdout) > 1024 * 1024:
        return ""
    return stdout.decode(errors="replace").strip()


def _sha_file(path: Path) -> str | None:
    try:
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                hasher.update(block)
        return f"sha256:{hasher.hexdigest()}"
    except OSError:
        return None


def _sha(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"
