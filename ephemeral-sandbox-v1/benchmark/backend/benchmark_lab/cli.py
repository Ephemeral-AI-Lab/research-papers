from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
from pathlib import Path
from typing import Any, Sequence

import uvicorn

from .api import create_app
from .paths import BenchmarkRoots
from .planning import load_preset
from .service import CampaignService, ServiceError


COMMANDS = ("serve", "validate", "run", "compare", "recover", "cleanup")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="sandbox-benchmark")
    commands = root.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        command = commands.add_parser(name)
        command.add_argument("--test-repository-root", type=Path, required=True)
        command.add_argument("--product-root", type=Path, required=True)
        command.add_argument("--product-bin-dir", type=Path, required=True)
        if name in {"validate", "run"}:
            command.add_argument("--plan", required=True, help="plan YAML path or installed preset id")
        elif name == "compare":
            command.add_argument("--reference", required=True)
            command.add_argument("--candidate", required=True)
            command.add_argument("--descriptive-override", action="store_true")
        elif name == "cleanup":
            command.add_argument("--run-id", required=True)
        elif name == "serve":
            command.add_argument("--host", default="127.0.0.1")
            command.add_argument("--port", type=int, default=7891)
            command.add_argument("--web-dist", type=Path)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    roots = BenchmarkRoots.resolve(
        arguments.test_repository_root,
        arguments.product_root,
        arguments.product_bin_dir,
        initialize=True,
    )
    service = CampaignService(roots)
    try:
        return _dispatch(arguments, service)
    except ServiceError as error:
        raise SystemExit(f"{error.code}: {error}") from error


def _dispatch(arguments: argparse.Namespace, service: CampaignService) -> int:
    if arguments.command == "serve":
        address = ipaddress.ip_address(arguments.host)
        if not address.is_loopback:
            raise SystemExit("serve host must be a loopback IP address")
        if not 1 <= arguments.port <= 65535:
            raise SystemExit("serve port must be between 1 and 65535")
        dist = _resolve_web_dist(arguments.web_dist, service.roots)
        authority = f"[{arguments.host}]:{arguments.port}" if address.version == 6 else f"{arguments.host}:{arguments.port}"
        app = create_app(service, authority=authority, web_dist=dist)
        uvicorn.run(app, host=arguments.host, port=arguments.port, access_log=False)
        return 0
    if arguments.command == "validate":
        service.refresh_product_catalog()
        if service.catalog_error is not None:
            raise SystemExit(f"product_catalog: {service.catalog_error}")
        _print(service.validate_plan(_resolve_plan(service, arguments.plan)))
        return 0
    if arguments.command == "run":
        service.refresh_product_catalog()
        if service.catalog_error is not None:
            raise SystemExit(f"product_catalog: {service.catalog_error}")
        plan = _resolve_plan(service, arguments.plan)
        expanded = service.validate_plan(plan)
        if not expanded["runnable"]:
            _print(expanded)
            return 2
        _print(asyncio.run(service.run_foreground(plan, expanded["plan_hash"])))
        return 0
    if arguments.command == "compare":
        _print(service.compare(arguments.reference, arguments.candidate, arguments.descriptive_override))
        return 0
    if arguments.command == "recover":
        result = asyncio.run(service.recover())
        _print(result)
        return 0 if result["execution_available"] else 2
    if arguments.command == "cleanup":
        _print(asyncio.run(service.cleanup(arguments.run_id)))
        return 0
    raise AssertionError(arguments.command)


def _resolve_plan(service: CampaignService, value: str) -> dict[str, Any]:
    candidate = Path(value).expanduser()
    if candidate.exists():
        if candidate.is_symlink() or not candidate.is_file():
            raise SystemExit("plan path must be a plain file")
        return CampaignService._load_plan(candidate.resolve(strict=True)).model_dump(mode="json")
    for path in sorted((service.roots.benchmark_source_root / "presets").glob("*.yml")):
        preset = load_preset(path)
        if preset.id == value:
            return preset.plan.model_dump(mode="json")
    raise SystemExit(f"unknown plan path or preset: {value}")


def _resolve_web_dist(value: Path | None, roots: BenchmarkRoots) -> Path:
    candidate = value or roots.benchmark_state_root / "web-dist"
    dist = candidate.expanduser().resolve(strict=True)
    if not dist.is_relative_to(roots.benchmark_state_root):
        raise SystemExit("web distribution must be inside the benchmark state root")
    return dist


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))
