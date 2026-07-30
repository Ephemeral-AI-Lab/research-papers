from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError

from .models import StrictModel
from .observability import (
    CgroupView,
    LayerstackView,
    SnapshotView,
    TraceView,
    parse_cgroup,
    parse_layerstack,
    parse_snapshot,
    parse_trace,
)
from .transport import GatewayClient, TimedGatewayResponse


_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,256}$")


class ProductAccessError(RuntimeError):
    pass


class DaemonEndpoint(StrictModel):
    host: str
    port: int = Field(ge=1, le=65535)


class SharedBase(StrictModel):
    source: str
    target: str
    root_hash: str
    readonly: bool


class SandboxRecord(StrictModel):
    id: str
    workspace_root: str
    state: str
    daemon: DaemonEndpoint | None
    daemon_http: DaemonEndpoint | None
    shared_base: SharedBase | None


class ProductAccess:
    """Closed product surface; callers cannot choose arbitrary operation names."""

    def __init__(self, client: GatewayClient, runs_root: Path) -> None:
        self._client = client
        self._runs_root = runs_root.resolve(strict=True)
        self._sandboxes: set[str] = set()

    @property
    def owned_sandboxes(self) -> frozenset[str]:
        return frozenset(self._sandboxes)

    async def create_sandbox(self, image: str, workspace_root: Path, *, request_id: str) -> tuple[SandboxRecord, TimedGatewayResponse]:
        workspace = workspace_root.resolve(strict=True)
        if workspace == self._runs_root or not workspace.is_relative_to(self._runs_root):
            raise ProductAccessError("sandbox workspace is not benchmark-owned")
        response = await self._client.request("create_sandbox", {"kind": "system"}, {"image": image, "workspace_root": str(workspace), "count": 1}, timeout_seconds=600, request_id=request_id)
        record = _sandbox_record(response.value)
        if record.state != "ready" or Path(record.workspace_root) != workspace or record.id in self._sandboxes:
            raise ProductAccessError("create_sandbox response violated ownership or readiness")
        self._sandboxes.add(record.id)
        return record, response

    async def inspect_sandbox(self, sandbox_id: str, *, request_id: str) -> SandboxRecord:
        self._require_owned(sandbox_id)
        response = await self._client.request("inspect_sandbox", {"kind": "system"}, {"sandbox_id": sandbox_id}, timeout_seconds=30, request_id=request_id)
        record = _sandbox_record(response.value)
        if record.id != sandbox_id or record.state != "ready":
            raise ProductAccessError("inspect_sandbox response violated identity or readiness")
        return record

    async def destroy_sandbox(self, sandbox_id: str, *, request_id: str) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        response = await self._client.request("destroy_sandbox", {"kind": "system"}, {"sandbox_id": sandbox_id}, timeout_seconds=600, request_id=request_id)
        self._sandboxes.remove(sandbox_id)
        return response

    async def exec_command(self, sandbox_id: str, *, session_id: str | None, command: str, timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        args: dict[str, Any] = {"cmd": command, "timeout_ms": timeout_ms, "yield_time_ms": timeout_ms}
        return await self._sandbox_request("exec_command", sandbox_id, session_id, args, timeout_ms, request_id)

    async def file_read(self, sandbox_id: str, *, session_id: str | None, path: str, offset: int, limit: int, timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        return await self._sandbox_request("file_read", sandbox_id, session_id, {"path": _product_path(path), "offset": offset, "limit": limit}, timeout_ms, request_id)

    async def file_write(self, sandbox_id: str, *, session_id: str | None, path: str, content: str, timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        if len(content.encode()) > 4 * 1024 * 1024:
            raise ProductAccessError("file content exceeds fixed bound")
        return await self._sandbox_request("file_write", sandbox_id, session_id, {"path": _product_path(path), "content": content}, timeout_ms, request_id)

    async def file_edit(self, sandbox_id: str, *, session_id: str | None, path: str, edits: list[dict[str, Any]], timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        allowed = {"old_string", "new_string", "replace_all"}
        if not 1 <= len(edits) <= 256 or any(
            not {"old_string", "new_string"}.issubset(edit)
            or not set(edit).issubset(allowed)
            or not isinstance(edit["old_string"], str)
            or not isinstance(edit["new_string"], str)
            or ("replace_all" in edit and not isinstance(edit["replace_all"], bool))
            for edit in edits
        ):
            raise ProductAccessError("file edits violate fixed contract")
        return await self._sandbox_request("file_edit", sandbox_id, session_id, {"path": _product_path(path), "edits": edits}, timeout_ms, request_id)

    async def file_blame(self, sandbox_id: str, *, path: str, timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        return await self._sandbox_request("file_blame", sandbox_id, None, {"path": _product_path(path)}, timeout_ms, request_id)

    async def squash_layerstacks(self, sandbox_id: str, *, timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        return await self._client.request("squash_layerstacks", {"kind": "system"}, {"sandbox_id": sandbox_id}, timeout_seconds=timeout_ms / 1000, request_id=request_id)

    async def observe_cgroup(self, sandbox_id: str, *, request_id: str) -> CgroupView:
        response = await self._observe(
            "cgroup",
            sandbox_id,
            {"scope": "sandbox", "window_ms": 600_000},
            request_id,
        )
        return parse_cgroup(response.value)

    async def observe_snapshot(self, sandbox_id: str, *, request_id: str) -> SnapshotView:
        response = await self._observe("snapshot", sandbox_id, {}, request_id)
        return parse_snapshot(response.value, sandbox_id)

    async def observe_layerstack(self, sandbox_id: str, *, request_id: str) -> LayerstackView:
        response = await self._observe("layerstack", sandbox_id, {}, request_id)
        return parse_layerstack(response.value)

    async def observe_trace(
        self, sandbox_id: str, *, target_request_id: str, request_id: str
    ) -> TraceView:
        _identity(target_request_id)
        response = await self._observe(
            "trace", sandbox_id, {"trace_id": target_request_id}, request_id
        )
        return parse_trace(response.value, target_request_id)

    async def _observe(
        self, operation: str, sandbox_id: str, args: dict[str, Any], request_id: str
    ) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        return await self._client.request(
            operation,
            {"kind": "sandbox", "sandbox_id": sandbox_id},
            args,
            timeout_seconds=30,
            request_id=request_id,
        )

    async def _sandbox_request(self, operation: str, sandbox_id: str, session_id: str | None, args: dict[str, Any], timeout_ms: int, request_id: str) -> TimedGatewayResponse:
        self._require_owned(sandbox_id)
        if session_id is not None:
            args["workspace_session_id"] = _identity(session_id)
        return await self._client.request(operation, {"kind": "sandbox", "sandbox_id": sandbox_id}, args, timeout_seconds=timeout_ms / 1000, request_id=request_id)

    def _require_owned(self, sandbox_id: str) -> None:
        if _identity(sandbox_id) not in self._sandboxes:
            raise ProductAccessError("sandbox is not owned by this run")


def _sandbox_record(value: Any) -> SandboxRecord:
    try:
        record = SandboxRecord.model_validate(value)
        _identity(record.id)
        if record.daemon is not None and not ipaddress.ip_address(record.daemon.host).is_loopback:
            raise ValueError
    except (ValidationError, ValueError) as error:
        raise ProductAccessError("sandbox response schema is invalid") from error
    return record


def _identity(value: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ProductAccessError("product identity is invalid")
    return value


def _product_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or not value or ".." in path.parts or len(value.encode()) > 4096:
        raise ProductAccessError("product path is invalid")
    return value
