from __future__ import annotations

import asyncio
import hashlib
import os
import platform
import shutil
from pathlib import Path
from typing import Any

from .paths import BenchmarkRoots


async def collect_environment(roots: BenchmarkRoots, plan: dict[str, Any]) -> dict[str, Any]:
    commit = await _command(["git", "rev-parse", "HEAD"], roots.product_root)
    status = await _command(["git", "status", "--porcelain=v1", "-z"], roots.product_root)
    docker_version = await _command(
        ["docker", "version", "--format", "{{.Server.Version}}"], roots.product_root
    )
    image = plan["canonical_plan"]["environment"]["image"]
    image_digest = await _command(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image], roots.product_root
    )
    daemon = _daemon_path(roots)
    gateway = roots.product_bin_dir / "sandbox-gateway"
    usage = shutil.disk_usage(roots.benchmark_state_root)
    effective = plan["effective_environment"]
    return {
        "schema_version": 1,
        "treatment": {
            "source_commit": commit or "unavailable",
            "source_dirty": bool(status),
            "source_diff_hash": _sha(status.encode()) if status else None,
            "daemon_binary_hash": _sha_file(daemon),
            "gateway_binary_hash": _sha_file(gateway),
        },
        "host": {
            "operating_system": platform.system().lower(),
            "architecture": platform.machine().lower(),
            "kernel_release": platform.release() or None,
            "docker_engine_version": docker_version or None,
            "filesystem": effective.get("filesystem"),
            "free_space_bytes": usage.free,
            "monotonic_clock": "time.monotonic_ns",
        },
        "image_reference": image,
        "image_digest": image_digest or effective.get("image_digest"),
        "workspace_root_identity": effective["workspace_root_identity"],
        "client_cohort": effective["client_cohort"],
        "gateway_endpoint_identity": "isolated_loopback_per_execution_block",
    }


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


def _daemon_path(roots: BenchmarkRoots) -> Path:
    suffix = "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "amd64"
    return roots.product_root / "dist" / f"sandbox-daemon-linux-{suffix}"


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
