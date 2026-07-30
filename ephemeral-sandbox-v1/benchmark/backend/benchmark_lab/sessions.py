from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from .models import StrictModel
from .product import ProductAccess, ProductAccessError, _identity
from .transport import MAX_WIRE_BYTES, TimedGatewayResponse


DAEMON_AUTH_FIELD = "_sandbox_daemon_auth_token"
DOCKER_AUTH_LABEL = "eos.auth_token"


class SessionError(RuntimeError):
    pass


class CreatedSession(StrictModel):
    workspace_session_id: str
    network_profile: str
    finalize_policy: str


class DestroyedSession(StrictModel):
    workspace_session_id: str
    destroyed: bool
    evicted_upperdir_bytes: int


@dataclass(frozen=True, slots=True)
class Session:
    sandbox_id: str
    session_id: str
    network_profile: str


class SessionLifecycle:
    def __init__(self, product: ProductAccess) -> None:
        self._product = product
        self._sessions: dict[str, str] = {}

    @property
    def owned_count(self) -> int:
        return len(self._sessions)

    def retire_product_destroyed(self, session: Session) -> None:
        """Retire only a session a typed product response says no longer exists."""
        if self._sessions.get(session.session_id) != session.sandbox_id:
            raise SessionError("session is not owned by this lifecycle")
        del self._sessions[session.session_id]

    async def create_no_op(self, sandbox_id: str, network_profile: str, *, request_id: str, timeout_ms: int = 120000) -> tuple[Session, TimedGatewayResponse]:
        if network_profile not in {"shared", "isolated"}:
            raise SessionError("network profile is not allowlisted")
        record = await self._product.inspect_sandbox(sandbox_id, request_id=f"{request_id}.inspect")
        if record.daemon is None:
            raise SessionError("sandbox daemon endpoint is unavailable")
        token = await _lookup_auth(sandbox_id)
        response = await _daemon_request(record.daemon.host, record.daemon.port, token, "create_workspace_session", sandbox_id, {"network_profile": network_profile}, request_id, timeout_ms)
        try:
            created = CreatedSession.model_validate(response.value)
            session_id = _identity(created.workspace_session_id)
        except (ValidationError, ProductAccessError) as error:
            raise SessionError("create session response schema is invalid") from error
        if created.network_profile != network_profile or created.finalize_policy != "no_op" or session_id in self._sessions:
            raise SessionError("create session response violated lifecycle contract")
        self._sessions[session_id] = sandbox_id
        return Session(sandbox_id, session_id, network_profile), response

    async def destroy(self, session: Session, *, request_id: str, timeout_ms: int = 120000) -> TimedGatewayResponse:
        if self._sessions.get(session.session_id) != session.sandbox_id:
            raise SessionError("session is not owned by this lifecycle")
        record = await self._product.inspect_sandbox(session.sandbox_id, request_id=f"{request_id}.inspect")
        if record.daemon is None:
            raise SessionError("sandbox daemon endpoint is unavailable")
        token = await _lookup_auth(session.sandbox_id)
        response = await _daemon_request(record.daemon.host, record.daemon.port, token, "destroy_workspace_session", session.sandbox_id, {"workspace_session_id": session.session_id}, request_id, timeout_ms)
        try:
            destroyed = DestroyedSession.model_validate(response.value)
        except ValidationError as error:
            raise SessionError("destroy session response schema is invalid") from error
        if not destroyed.destroyed or destroyed.workspace_session_id != session.session_id:
            raise SessionError("destroy session response violated lifecycle contract")
        del self._sessions[session.session_id]
        return response


async def _lookup_auth(sandbox_id: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "docker", "inspect", "--format", f'{{{{ index .Config.Labels "{DOCKER_AUTH_LABEL}" }}}}', sandbox_id,
        env={name: os.environ[name] for name in ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG") if name in os.environ},
        stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), 30)
    except TimeoutError as error:
        process.kill(); await process.wait()
        raise SessionError("daemon credential lookup timed out") from error
    token = stdout.decode(errors="strict").strip() if process.returncode == 0 and len(stdout) <= 4096 and len(stderr) <= 16384 else ""
    if not token or token == "<no value>" or any(character.isspace() for character in token):
        raise SessionError("daemon credential lookup failed")
    return token


async def _daemon_request(host: str, port: int, token: str, operation: str, sandbox_id: str, args: dict[str, Any], request_id: str, timeout_ms: int) -> TimedGatewayResponse:
    request = {"op": operation, "request_id": _identity(request_id), "scope": {"kind": "sandbox", "sandbox_id": _identity(sandbox_id)}, "args": args, DAEMON_AUTH_FIELD: token}
    payload = json.dumps(request, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    if len(payload) > MAX_WIRE_BYTES:
        raise SessionError("daemon request exceeds wire bound")
    writer: asyncio.StreamWriter | None = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port, limit=MAX_WIRE_BYTES + 1), timeout_ms / 1000)
        started = time.monotonic_ns()
        async with asyncio.timeout(timeout_ms / 1000):
            writer.write(payload); await writer.drain()
            if writer.can_write_eof(): writer.write_eof()
            raw = await reader.readuntil(b"\n")
            ended = time.monotonic_ns()
            trailing = await reader.read(1)
    except (OSError, TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError) as error:
        raise SessionError("daemon transport failed") from error
    finally:
        if writer is not None:
            writer.close()
            try: await writer.wait_closed()
            except OSError: pass
    if trailing or token.encode() in raw or len(raw) > MAX_WIRE_BYTES:
        raise SessionError("daemon response framing or credential contract failed")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SessionError("daemon response JSON is invalid") from error
    if isinstance(value, dict) and "error" in value:
        raise SessionError("daemon product operation failed")
    return TimedGatewayResponse(request_id, ended - started, len(raw), f"sha256:{hashlib.sha256(raw).hexdigest()}", value)
