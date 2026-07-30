import asyncio

import pytest

from benchmark_lab.redaction import BoundedLogCapture, REDACTED, SecretRedactor
from benchmark_lab.resources import (
    AggregatedCleanupError,
    ResourceKind,
    ResourceRegistry,
)


def test_recursive_redaction_covers_registered_secrets_and_sensitive_keys() -> None:
    redactor = SecretRedactor({"exact-private-value"})
    assert redactor.text("prefix exact-private-value suffix") == REDACTED
    assert redactor.text("Authorization: bearer anything") == REDACTED
    assert redactor.value(
        {"safe": "visible", "password": "hidden", "nested": ["exact-private-value"]}
    ) == {"safe": "visible", "password": REDACTED, "nested": [REDACTED]}


async def test_log_capture_is_line_total_and_secret_bounded() -> None:
    reader = asyncio.StreamReader()
    reader.feed_data(b"safe\nprivate-value\n" + b"x" * 300 + b"\nlast\n")
    reader.feed_eof()
    capture = BoundedLogCapture(
        SecretRedactor({"private-value"}), max_line_bytes=128, max_total_bytes=256
    )
    await capture.drain(reader, "stderr")
    assert capture.records[0].text == "safe"
    assert capture.records[1].text == REDACTED
    assert capture.records[2].text == "oversized log line"
    assert all("private-value" not in record.text for record in capture.records)


async def test_cleanup_is_lifo_aggregated_and_retains_only_failed_resources() -> None:
    calls: list[str] = []
    registry = ResourceRegistry(SecretRedactor({"private-value"}))

    async def succeeds(name: str) -> None:
        calls.append(name)

    async def fails() -> None:
        calls.append("sandbox")
        raise RuntimeError("private-value must not escape")

    registry.register(ResourceKind.PROCESS, "process-1", lambda: succeeds("process"))
    registry.register(ResourceKind.SANDBOX, "sandbox-1", fails)
    registry.register(ResourceKind.WORKSPACE_SESSION, "session-1", lambda: succeeds("session"))
    with pytest.raises(AggregatedCleanupError) as caught:
        await registry.cleanup_all()
    assert calls == ["session", "sandbox", "process"]
    assert caught.value.issues[0].detail == REDACTED
    assert registry.active == ((ResourceKind.SANDBOX, "sandbox-1"),)


def test_duplicate_and_unsafe_resource_identities_are_rejected() -> None:
    registry = ResourceRegistry(SecretRedactor(set()))

    async def cleanup() -> None:
        pass

    registry.register(ResourceKind.SANDBOX, "sandbox-1", cleanup)
    with pytest.raises(ValueError, match="already"):
        registry.register(ResourceKind.SANDBOX, "sandbox-1", cleanup)
    with pytest.raises(ValueError, match="invalid"):
        registry.register(ResourceKind.SANDBOX, "../escape", cleanup)
