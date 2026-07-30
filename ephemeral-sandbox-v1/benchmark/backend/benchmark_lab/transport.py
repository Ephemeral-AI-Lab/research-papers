import asyncio
import hashlib
import ipaddress
import json
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import Field, TypeAdapter, ValidationError

from .models import StrictModel


AUTH_FIELD = "_sandbox_gateway_auth_token"
MAX_WIRE_BYTES = 16 * 1024 * 1024
MAX_ID_BYTES = 256
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SENSITIVE_WORD = re.compile(r"(?i)\b(token|secret|password|credential|authorization)\b")


class GatewayError(RuntimeError):
    """A public gateway failure that never exposes request or credential content."""


class GatewayTransportError(GatewayError):
    def __init__(self, kind: str) -> None:
        self.kind = kind
        super().__init__(f"gateway transport failed ({kind})")


class GatewayProductError(GatewayError):
    def __init__(self, kind: str, detail: str) -> None:
        self.kind = kind
        self.detail = detail
        super().__init__(f"gateway returned an error ({kind}): {detail}")


class SystemScope(StrictModel):
    kind: Literal["system"]


class SandboxScope(StrictModel):
    kind: Literal["sandbox"]
    sandbox_id: str = Field(min_length=1, max_length=MAX_ID_BYTES)


GatewayScope = SystemScope | SandboxScope
_SCOPE_ADAPTER = TypeAdapter(GatewayScope)


class ProductErrorBody(StrictModel):
    kind: str = Field(min_length=1, max_length=MAX_ID_BYTES)
    message: str
    details: Any


class ProductErrorEnvelope(StrictModel):
    error: ProductErrorBody


@dataclass(frozen=True, slots=True)
class GatewayEndpoint:
    host: str
    port: int

    def __post_init__(self) -> None:
        try:
            address = ipaddress.ip_address(self.host)
        except ValueError as error:
            raise ValueError("gateway host must be a numeric loopback address") from error
        if not address.is_loopback or not 1 <= self.port <= 65535:
            raise ValueError("gateway endpoint must be a valid loopback socket")


@dataclass(frozen=True, slots=True)
class TimedGatewayResponse:
    request_id: str
    latency_ns: int
    response_bytes: int
    response_sha256: str
    value: Any
    started_ns: int | None = None


class GatewayClient:
    __slots__ = ("_endpoint", "_token", "_max_wire_bytes")

    def __init__(
        self,
        endpoint: GatewayEndpoint,
        auth_token: str,
        *,
        max_wire_bytes: int = MAX_WIRE_BYTES,
    ) -> None:
        if (
            not auth_token
            or len(auth_token.encode()) > 1024
            or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in auth_token)
        ):
            raise ValueError("gateway credential is invalid")
        if max_wire_bytes < 1024 or max_wire_bytes > MAX_WIRE_BYTES:
            raise ValueError("gateway wire cap is invalid")
        self._endpoint = endpoint
        self._token = auth_token
        self._max_wire_bytes = max_wire_bytes

    def __repr__(self) -> str:
        return f"GatewayClient(endpoint={self._endpoint!r}, auth_token='[REDACTED]')"

    async def request(
        self,
        operation: str,
        scope: GatewayScope | dict[str, Any],
        args: dict[str, Any],
        *,
        timeout_seconds: float,
        request_id: str | None = None,
    ) -> TimedGatewayResponse:
        operation = _validated_id("operation", operation)
        request_id = _validated_id("request_id", request_id or _new_request_id())
        if not isinstance(args, dict):
            raise ValueError("gateway arguments must be an object")
        if not 0 < timeout_seconds <= 3600:
            raise ValueError("gateway timeout is invalid")
        try:
            validated_scope = _SCOPE_ADAPTER.validate_python(scope, strict=True)
        except ValidationError as error:
            raise ValueError("gateway scope is invalid") from error
        if isinstance(validated_scope, SandboxScope):
            _validated_id("sandbox_id", validated_scope.sandbox_id)

        request = {
            "op": operation,
            "request_id": request_id,
            "scope": validated_scope.model_dump(mode="json"),
            "args": args,
            "_stream_logs": False,
            AUTH_FIELD: self._token,
        }
        try:
            payload = json.dumps(
                request, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode() + b"\n"
        except (TypeError, ValueError) as error:
            raise ValueError("gateway arguments are not JSON encodable") from error
        if len(payload) > self._max_wire_bytes:
            raise GatewayTransportError("request_oversize")

        writer: asyncio.StreamWriter | None = None
        try:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        self._endpoint.host,
                        self._endpoint.port,
                        limit=self._max_wire_bytes + 1,
                    ),
                    timeout=timeout_seconds,
                )
            except TimeoutError as error:
                raise GatewayTransportError("connect_timeout") from error
            except OSError as error:
                raise GatewayTransportError("connection_error") from error

            started_ns = time.monotonic_ns()
            try:
                async with asyncio.timeout(timeout_seconds):
                    writer.write(payload)
                    await writer.drain()
                    if writer.can_write_eof():
                        writer.write_eof()
                    response = await reader.readuntil(b"\n")
                    ended_ns = time.monotonic_ns()
                    trailing = await reader.read(1)
            except TimeoutError as error:
                raise GatewayTransportError("response_timeout") from error
            except asyncio.LimitOverrunError as error:
                raise GatewayTransportError("response_oversize") from error
            except asyncio.IncompleteReadError as error:
                kind = "empty_response" if not error.partial else "unterminated_response"
                raise GatewayTransportError(kind) from error
            except (ConnectionError, OSError) as error:
                raise GatewayTransportError("connection_error") from error
            if trailing:
                raise GatewayTransportError("multiple_responses")
        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except (ConnectionError, OSError):
                    pass

        if len(response) > self._max_wire_bytes:
            raise GatewayTransportError("response_oversize")
        if self._token.encode() in response:
            raise GatewayTransportError("credential_echo")
        try:
            value = json.loads(response)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GatewayTransportError("invalid_json") from error
        _raise_product_error(value)
        return TimedGatewayResponse(
            request_id=request_id,
            latency_ns=ended_ns - started_ns,
            response_bytes=len(response),
            response_sha256=f"sha256:{hashlib.sha256(response).hexdigest()}",
            value=value,
            started_ns=started_ns,
        )


def _validated_id(field: str, value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode()) > MAX_ID_BYTES
        or _SAFE_ID.fullmatch(value) is None
    ):
        raise ValueError(f"gateway {field} is invalid")
    return value


def _new_request_id() -> str:
    return f"benchmark-{secrets.token_hex(16)}"


def _raise_product_error(value: Any) -> None:
    if not isinstance(value, dict) or "error" not in value:
        return
    try:
        envelope = ProductErrorEnvelope.model_validate(value)
    except ValidationError as error:
        raise GatewayTransportError("response_schema") from error
    kind = _validated_product_text(envelope.error.kind, fallback="unknown")
    detail = _validated_product_text(envelope.error.message, fallback="details unavailable")
    raise GatewayProductError(kind, detail)


def _validated_product_text(value: str, *, fallback: str) -> str:
    value = " ".join(value.split())[:1024]
    if not value or _SENSITIVE_WORD.search(value):
        return fallback
    return value
