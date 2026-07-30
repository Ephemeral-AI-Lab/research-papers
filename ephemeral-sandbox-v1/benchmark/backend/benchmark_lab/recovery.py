import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .artifacts import ArtifactError, ArtifactId, ArtifactStore, read_envelope_path
from .models import OwnedPathMarker
from .paths import BenchmarkRoots
from .safety import OwnershipError, OwnershipLedger


TERMINAL_STATES = {"completed", "failed", "cancelled"}


@dataclass(frozen=True, slots=True)
class RecoveryIssue:
    run_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    recovered_run_ids: tuple[str, ...]
    issues: tuple[RecoveryIssue, ...]

    @property
    def execution_available(self) -> bool:
        return not self.issues


class RecoveryScanner:
    def __init__(
        self,
        roots: BenchmarkRoots,
        cleanup: Callable[[str], None],
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        roots.validate_state()
        self._roots = roots
        self._store = ArtifactStore(roots)
        self._cleanup = cleanup
        self._now = now or (lambda: datetime.now(UTC))

    def scan(self) -> RecoveryResult:
        recovered: list[str] = []
        issues: list[RecoveryIssue] = []
        for path in sorted(self._roots.results.iterdir()):
            run_id = path.name
            try:
                if self._recover_if_needed(path):
                    recovered.append(run_id)
            except Exception as error:
                issues.append(RecoveryIssue(run_id, "recovery_failed", str(error)))
        return RecoveryResult(tuple(recovered), tuple(issues))

    def recover_run(self, run_id: str) -> bool:
        return self._recover_if_needed(self._store.run_path(run_id))

    def _recover_if_needed(self, path: Path) -> bool:
        if path.is_symlink() or not path.is_dir():
            raise ArtifactError(f"unsafe result entry: {path}")
        manifest = read_envelope_path(path / "run-manifest.json", ArtifactId.RUN_MANIFEST)
        manifest_envelope_version = json.loads(
            (path / "run-manifest.json").read_bytes()
        )["schema_version"]
        run_id = manifest.get("run_id")
        if run_id != path.name:
            raise ArtifactError("manifest does not prove the result directory identity")
        state = manifest.get("state")
        if not isinstance(state, str):
            raise ArtifactError("manifest state is missing")
        if state in TERMINAL_STATES:
            return False

        journals = {
            artifact_id: self._store.read_records(
                run_id, artifact_id, recover_partial_tail=True
            )
            for artifact_id in (ArtifactId.EVENTS, ArtifactId.OBSERVATIONS)
        }
        ledger = OwnershipLedger(self._roots)
        owned = []
        for role in ("runs", "runtime"):
            marker = OwnedPathMarker(role=role, identity={"run_id": run_id})
            target = getattr(self._roots, role) / run_id
            # A crash can happen before either disposable directory is created,
            # or after one has already been removed.  Absence is safe; presence
            # must still carry the exact run marker before cleanup is attempted.
            if target.exists() or target.is_symlink():
                ledger.adopt(target, marker)
                owned.append((target, marker))

        self._cleanup(run_id)
        for target, marker in owned:
            # The resource-specific cleanup may itself remove an owned runtime
            # directory after proving its process identity. Absence is then the
            # successful postcondition; any remaining directory must still be
            # removed through the ledger and exact marker.
            if target.exists() or target.is_symlink():
                ledger.remove(target, marker)
        for artifact_id, journal in journals.items():
            if journal.partial_tail_line is not None:
                self._store.quarantine_partial_tail(run_id, artifact_id)

        events = self._store.read_records(run_id, ArtifactId.EVENTS).records
        sequence = max((event["sequence"] for event in events), default=0) + 1
        monotonic_offset_ns = max(
            (event["monotonic_offset_ns"] for event in events), default=0
        ) + 1
        self._store.append_record(
            run_id,
            ArtifactId.EVENTS,
            {
                "sequence": sequence,
                "run_id": run_id,
                "monotonic_offset_ns": monotonic_offset_ns,
                "data": {
                    "kind": "run_state",
                    "state": "failed",
                    "reason": "recovered_interrupted_run",
                },
            },
        )
        failed = dict(manifest)
        failed["state"] = "failed"
        failed["failure"] = {
            "code": "recovered_interrupted_run",
            "message": "the benchmark process stopped before reaching a terminal state",
            "infrastructure": True,
        }
        failed["ended_at"] = self._now().astimezone(UTC).isoformat().replace("+00:00", "Z")
        self._store.replace_snapshot(
            run_id,
            ArtifactId.RUN_MANIFEST,
            failed,
            schema_version=manifest_envelope_version,
        )
        return True
