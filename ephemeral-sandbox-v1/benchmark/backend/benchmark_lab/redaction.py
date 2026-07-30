import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal


REDACTED = "[REDACTED]"
_SENSITIVE = re.compile(
    r"(?i)(authorization|bearer|credential|password|secret|token)(?:\s*[:=]|\b)"
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class RedactionError(ValueError):
    pass


class SecretRedactor:
    __slots__ = ("_secrets",)

    def __init__(self, secrets: set[str] | frozenset[str]) -> None:
        if any(not secret or len(secret) > 4096 for secret in secrets):
            raise RedactionError("redaction secrets must be non-empty and bounded")
        self._secrets = tuple(sorted(secrets, key=len, reverse=True))

    def text(self, value: str, *, cap: int = 16 * 1024) -> str:
        normalized = _CONTROL.sub("�", value).strip()
        if any(secret in normalized for secret in self._secrets) or _SENSITIVE.search(normalized):
            return REDACTED
        encoded = normalized.encode("utf-8")
        if len(encoded) <= cap:
            return normalized
        return encoded[:cap].decode("utf-8", "ignore") + "…[TRUNCATED]"

    def value(self, value: Any, *, depth: int = 0) -> Any:
        if depth > 16:
            raise RedactionError("diagnostic structure exceeds the depth cap")
        if isinstance(value, str):
            return self.text(value)
        if value is None or isinstance(value, bool | int | float):
            return value
        if isinstance(value, list):
            return [self.value(item, depth=depth + 1) for item in value]
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                safe_key = _CONTROL.sub("�", str(key)).strip()[:256]
                redacted[safe_key] = (
                    REDACTED
                    if _SENSITIVE.search(str(key))
                    else self.value(item, depth=depth + 1)
                )
            return redacted
        return self.text(str(value))


@dataclass(frozen=True, slots=True)
class LogRecord:
    stream: Literal["stdout", "stderr"]
    text: str


class BoundedLogCapture:
    def __init__(
        self,
        redactor: SecretRedactor,
        *,
        max_line_bytes: int = 16 * 1024,
        max_total_bytes: int = 1024 * 1024,
        sink: Callable[[LogRecord], None] | None = None,
    ) -> None:
        if max_line_bytes < 128 or max_total_bytes < max_line_bytes:
            raise ValueError("log capture caps are invalid")
        self._redactor = redactor
        self._max_line_bytes = max_line_bytes
        self._max_total_bytes = max_total_bytes
        self._captured_bytes = 0
        self._records: list[LogRecord] = []
        self._capped = False
        self._sink = sink

    @property
    def records(self) -> tuple[LogRecord, ...]:
        return tuple(self._records)

    async def drain(self, reader: Any, stream: Literal["stdout", "stderr"]) -> None:
        pending = bytearray()
        discarding = False
        while chunk := await reader.read(4096):
            for byte in chunk:
                if discarding:
                    if byte == 10:
                        discarding = False
                    continue
                if byte == 10:
                    self._append(stream, bytes(pending))
                    pending.clear()
                elif len(pending) >= self._max_line_bytes:
                    self._append(stream, b"oversized log line")
                    pending.clear()
                    discarding = True
                else:
                    pending.append(byte)
        if pending and not discarding:
            self._append(stream, bytes(pending))

    def _append(self, stream: Literal["stdout", "stderr"], line: bytes) -> None:
        if self._capped:
            return
        remaining = self._max_total_bytes - self._captured_bytes
        if remaining <= 0:
            self._record(LogRecord(stream=stream, text="[LOG CAP REACHED]"))
            self._capped = True
            return
        line = line[:remaining]
        self._captured_bytes += len(line)
        self._record(
            LogRecord(stream=stream, text=self._redactor.text(line.decode("utf-8", "replace")))
        )

    def _record(self, record: LogRecord) -> None:
        self._records.append(record)
        if self._sink is not None:
            self._sink(record)
