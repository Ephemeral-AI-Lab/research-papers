import asyncio
import json
from collections.abc import Awaitable, Callable

import pytest

import benchmark_lab.transport as transport_module
from benchmark_lab.transport import (
    AUTH_FIELD,
    GatewayClient,
    GatewayEndpoint,
    GatewayProductError,
    GatewayTransportError,
)


Handler = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]
TOKEN = "private-benchmark-token"


async def server_for(handler: Handler) -> tuple[asyncio.AbstractServer, GatewayEndpoint]:
    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, GatewayEndpoint(host, port)


async def run_request(
    handler: Handler, *, cap: int = 16 * 1024 * 1024, timeout: float = 1.0
):
    server, endpoint = await server_for(handler)
    try:
        return await GatewayClient(endpoint, TOKEN, max_wire_bytes=cap).request(
            "list_sandboxes", {"kind": "system"}, {}, timeout_seconds=timeout
        )
    finally:
        server.close()
        await server.wait_closed()


async def test_sends_exact_authenticated_jsonl_and_times_only_socket_io() -> None:
    received: list[dict[str, object]] = []

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request = json.loads(await reader.readline())
        received.append(request)
        await asyncio.sleep(0.02)
        writer.write(b'{"sandboxes":[]}\n')
        await writer.drain()
        writer.close()

    response = await run_request(handler)
    assert response.value == {"sandboxes": []}
    assert response.latency_ns >= 15_000_000
    assert response.response_bytes == len(b'{"sandboxes":[]}\n')
    assert response.response_sha256.startswith("sha256:")
    assert received == [
        {
            "op": "list_sandboxes",
            "request_id": response.request_id,
            "scope": {"kind": "system"},
            "args": {},
            "_stream_logs": False,
            AUTH_FIELD: TOKEN,
        }
    ]


async def test_request_ids_are_unique_and_credentials_are_redacted() -> None:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(b"{}\n")
        await writer.drain()
        writer.close()

    first = await run_request(handler)
    second = await run_request(handler)
    assert first.request_id != second.request_id
    assert TOKEN not in repr(GatewayClient(GatewayEndpoint("127.0.0.1", 1), TOKEN))


@pytest.mark.parametrize(
    ("response", "kind"),
    [
        (b"", "empty_response"),
        (b"{}", "unterminated_response"),
        (b"not-json\n", "invalid_json"),
        (b'{"error":{"kind":"bad","message":"credential token leaked","details":{}}}\n', None),
    ],
)
async def test_malformed_and_sensitive_responses_fail_closed(
    response: bytes, kind: str | None
) -> None:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(response)
        await writer.drain()
        writer.close()

    if kind is None:
        with pytest.raises(GatewayProductError) as caught:
            await run_request(handler)
        assert caught.value.detail == "details unavailable"
        assert TOKEN not in str(caught.value)
    else:
        with pytest.raises(GatewayTransportError) as caught:
            await run_request(handler)
        assert caught.value.kind == kind


async def test_product_error_is_distinct_from_transport_failure() -> None:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(b'{"error":{"kind":"invalid_request","message":"bad path","details":{}}}\n')
        await writer.drain()
        writer.close()

    with pytest.raises(GatewayProductError, match="bad path") as caught:
        await run_request(handler)
    assert caught.value.kind == "invalid_request"


async def test_second_response_line_is_rejected_outside_the_primary_timing() -> None:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(b"{}\n{}\n")
        await writer.drain()
        writer.close()

    with pytest.raises(GatewayTransportError) as caught:
        await run_request(handler)
    assert caught.value.kind == "multiple_responses"


async def test_response_caps_timeout_and_credential_echo() -> None:
    async def oversized(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(b'x' * 2048 + b"\n")
        await writer.drain()

    with pytest.raises(GatewayTransportError) as caught:
        await run_request(oversized, cap=1024)
    assert caught.value.kind == "response_oversize"

    async def stalled(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        await asyncio.sleep(1)

    with pytest.raises(GatewayTransportError) as caught:
        await run_request(stalled, timeout=0.01)
    assert caught.value.kind == "response_timeout"

    async def echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        writer.write(json.dumps({"echo": TOKEN}).encode() + b"\n")
        await writer.drain()

    with pytest.raises(GatewayTransportError) as caught:
        await run_request(echo)
    assert caught.value.kind == "credential_echo"
    assert TOKEN not in str(caught.value)


async def test_cancellation_closes_the_client_connection() -> None:
    received = asyncio.Event()
    release = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readline()
        received.set()
        try:
            await release.wait()
        finally:
            writer.close()

    server, endpoint = await server_for(handler)
    try:
        task = asyncio.create_task(
            GatewayClient(endpoint, TOKEN).request(
                "list_sandboxes", {"kind": "system"}, {}, timeout_seconds=10
            )
        )
        await asyncio.wait_for(received.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        release.set()
        server.close()
        await server.wait_closed()


def test_endpoint_scope_and_request_validation_are_strict() -> None:
    with pytest.raises(ValueError, match="loopback"):
        GatewayEndpoint("example.com", 80)
    client = GatewayClient(GatewayEndpoint("127.0.0.1", 1), TOKEN)
    with pytest.raises(ValueError, match="scope"):
        asyncio.run(client.request("op", {"kind": "system", "extra": 1}, {}, timeout_seconds=1))
    with pytest.raises(ValueError, match="operation"):
        asyncio.run(client.request("bad operation", {"kind": "system"}, {}, timeout_seconds=1))


def test_named_pipe_endpoint_is_canonical_and_strict() -> None:
    uri = "npipe://./pipe/ephemeral-sandbox-benchmark-0123abcd"
    endpoint = GatewayEndpoint.windows_named_pipe(uri)

    assert endpoint.transport == "windows_named_pipe"
    assert endpoint.address == uri
    assert endpoint.uri == uri
    assert endpoint.native_named_pipe_path == (
        r"\\.\pipe\ephemeral-sandbox-benchmark-0123abcd"
    )
    assert GatewayEndpoint.parse(uri) == endpoint
    assert GatewayEndpoint.parse("tcp://127.0.0.1:47621") == GatewayEndpoint(
        "127.0.0.1", 47621
    )

    for invalid in (
        "npipe://./pipe/",
        "npipe://./pipe/../escape",
        "npipe://./pipe/name with spaces",
        "unix:///tmp/gateway.sock",
    ):
        with pytest.raises(ValueError):
            GatewayEndpoint.parse(invalid)


@pytest.mark.asyncio
async def test_named_pipe_connection_failure_never_falls_back_to_tcp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    named_pipe_attempts = 0
    tcp_attempts = 0

    async def named_pipe(*_args, **_kwargs):
        nonlocal named_pipe_attempts
        named_pipe_attempts += 1
        raise OSError("named pipe unavailable")

    async def tcp(*_args, **_kwargs):
        nonlocal tcp_attempts
        tcp_attempts += 1
        raise AssertionError("TCP fallback is prohibited")

    monkeypatch.setattr(
        transport_module, "_open_windows_named_pipe_connection", named_pipe
    )
    monkeypatch.setattr(transport_module.asyncio, "open_connection", tcp)
    client = GatewayClient(
        GatewayEndpoint.windows_named_pipe(
            "npipe://./pipe/ephemeral-sandbox-benchmark-no-fallback"
        ),
        TOKEN,
    )

    with pytest.raises(GatewayTransportError) as captured:
        await client.request(
            "list_sandboxes",
            {"kind": "system"},
            {},
            timeout_seconds=1,
        )

    assert captured.value.kind == "connection_error"
    assert named_pipe_attempts == 1
    assert tcp_attempts == 0
