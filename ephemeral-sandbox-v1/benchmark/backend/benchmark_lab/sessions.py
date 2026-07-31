from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from .models import StrictModel
from .product import ProductAccess, ProductAccessError, _identity
from .transport import TimedGatewayResponse


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
        response = await self._product.create_workspace_session(
            sandbox_id,
            network_profile=network_profile,
            timeout_ms=timeout_ms,
            request_id=request_id,
        )
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
        response = await self._product.destroy_workspace_session(
            session.sandbox_id,
            session_id=session.session_id,
            timeout_ms=timeout_ms,
            request_id=request_id,
        )
        try:
            destroyed = DestroyedSession.model_validate(response.value)
        except ValidationError as error:
            raise SessionError("destroy session response schema is invalid") from error
        if not destroyed.destroyed or destroyed.workspace_session_id != session.session_id:
            raise SessionError("destroy session response violated lifecycle contract")
        del self._sessions[session.session_id]
        return response
