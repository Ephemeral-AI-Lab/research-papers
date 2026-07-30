import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from .redaction import SecretRedactor


_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,256}$")
Cleanup = Callable[[], Awaitable[None]]


class ResourceKind(StrEnum):
    SANDBOX = "sandbox"
    WORKSPACE_SESSION = "workspace_session"
    PROCESS = "process"
    SHARED_VOLUME = "shared_volume"
    RUNTIME_PATH = "runtime_path"


@dataclass(frozen=True, slots=True)
class CleanupIssue:
    kind: ResourceKind
    identity: str
    detail: str


class AggregatedCleanupError(RuntimeError):
    def __init__(self, issues: tuple[CleanupIssue, ...]) -> None:
        self.issues = issues
        super().__init__(f"resource cleanup was incomplete ({len(issues)} failure(s))")


@dataclass(frozen=True, slots=True)
class _Resource:
    kind: ResourceKind
    identity: str
    cleanup: Cleanup


class ResourceRegistry:
    def __init__(self, redactor: SecretRedactor) -> None:
        self._redactor = redactor
        self._resources: list[_Resource] = []
        self._identities: set[tuple[ResourceKind, str]] = set()

    @property
    def active(self) -> tuple[tuple[ResourceKind, str], ...]:
        return tuple((resource.kind, resource.identity) for resource in self._resources)

    def register(self, kind: ResourceKind, identity: str, cleanup: Cleanup) -> None:
        if _SAFE_ID.fullmatch(identity) is None:
            raise ValueError("resource identity is invalid")
        key = (kind, identity)
        if key in self._identities:
            raise ValueError("resource identity is already registered")
        self._resources.append(_Resource(kind, identity, cleanup))
        self._identities.add(key)

    async def cleanup_all(self) -> None:
        issues: list[CleanupIssue] = []
        failed: list[_Resource] = []
        while self._resources:
            resource = self._resources.pop()
            try:
                await resource.cleanup()
            except Exception as error:
                detail = self._redactor.text(str(error), cap=1024) or "details unavailable"
                issues.append(CleanupIssue(resource.kind, resource.identity, detail))
                failed.append(resource)
            else:
                self._identities.remove((resource.kind, resource.identity))
        self._resources.extend(reversed(failed))
        if issues:
            raise AggregatedCleanupError(tuple(issues))
