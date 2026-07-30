from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import json
import secrets
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import yaml
from pydantic import ValidationError

from .artifacts import ArtifactError, ArtifactId, ArtifactStore
from .catalog import CatalogError, export_catalog
from .comparison import compare_runs
from .gateway import recover_stale_gateway
from .planning import (
    ExperimentPlan,
    PlanError,
    RuntimeEnvironment,
    expand_plan,
    load_preset,
    load_workspace_profiles,
)
from .paths import BenchmarkRoots
from .reports import ReportError, RunCorpus
from .recovery import RecoveryScanner
from .runner import CampaignRunner


TERMINAL_STATES = {"completed", "failed", "cancelled"}


class ServiceError(RuntimeError):
    def __init__(self, status: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details


@dataclass(slots=True)
class _ActiveRun:
    run_id: str
    plan: dict[str, Any]
    runner: CampaignRunner
    starting_preset: dict[str, Any] | None = None
    task: asyncio.Task[None] | None = None
    state: str = "queued"


class CampaignService:
    """Read projections plus one admitted campaign, shared by CLI and HTTP."""

    def __init__(self, roots: BenchmarkRoots) -> None:
        self.roots = roots
        self.store = ArtifactStore(roots)
        self.instance_id = secrets.token_hex(16)
        self.nonce = secrets.token_hex(32)
        self._source = roots.benchmark_source_root
        self._profiles = load_workspace_profiles(self._source / "defaults/workspace-profiles")
        self._default = self._load_plan(self._source / "defaults/standard-local.yml")
        self._presets = [load_preset(path) for path in sorted((self._source / "presets").glob("*.yml"))]
        self._definitions = self._load_json(self._source / "defaults/definition-catalog.json")
        self._catalog_operations: frozenset[str] | None = None
        self._catalog_error: str | None = None
        self._active: _ActiveRun | None = None
        self._admission = asyncio.Lock()
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"invalid benchmark source asset: {path}") from error
        if not isinstance(value, dict):
            raise RuntimeError(f"benchmark source asset is not an object: {path}")
        return value

    @staticmethod
    def _load_plan(path: Path) -> ExperimentPlan:
        try:
            return ExperimentPlan.model_validate(yaml.safe_load(path.read_text()))
        except (OSError, yaml.YAMLError, ValidationError) as error:
            raise RuntimeError(f"invalid benchmark default plan: {path}") from error

    def refresh_product_catalog(self) -> None:
        try:
            result = export_catalog(self.roots)
            self._catalog_operations = result.catalog.operation_names()
            self._catalog_error = None
        except CatalogError as error:
            self._catalog_operations = None
            self._catalog_error = str(error)

    @property
    def catalog_error(self) -> str | None:
        return self._catalog_error

    @staticmethod
    def _uuid7() -> str:
        """Return a standards-compliant UUIDv7 without a version-specific dependency."""
        timestamp_ms = time.time_ns() // 1_000_000
        random_bits = secrets.randbits(74)
        value = (
            (timestamp_ms & ((1 << 48) - 1)) << 80
            | 0x7 << 76
            | ((random_bits >> 62) & 0xFFF) << 64
            | 0b10 << 62
            | (random_bits & ((1 << 62) - 1))
        )
        return str(uuid.UUID(int=value))

    def definitions(self) -> dict[str, Any]:
        defaults = [self._scoped_default(scope).model_dump(mode="json") for scope in (
            "all", "command", "files", "workspace", "layerstack"
        )]
        return {
            "schema_version": 1,
            "catalog": copy.deepcopy(self._definitions),
            "defaults": defaults,
            "presets": [preset.model_dump(mode="json") for preset in self._presets],
        }

    def _scoped_default(self, scope: str) -> ExperimentPlan:
        value = self._default.model_dump(mode="json")
        value["configuration_base"] = {"id": "standard-local", "version": 1, "scope": scope}
        family = {
            "command": {"exec_command"},
            "files": {"file_read", "file_write", "file_edit", "file_blame"},
            "workspace": {"create_workspace"},
            "layerstack": {"squash_layerstack"},
        }.get(scope)
        if family is not None:
            value["operations"] = [
                operation for operation in value["operations"]
                if operation["operation"] in family
            ]
        return ExperimentPlan.model_validate(value)

    def validate_plan(self, raw_plan: dict[str, Any]) -> dict[str, Any]:
        try:
            plan = ExperimentPlan.model_validate(raw_plan)
        except ValidationError as error:
            raise ServiceError(422, "invalid_plan", "the benchmark plan is invalid", error.errors()) from error
        usage = shutil.disk_usage(self.roots.benchmark_state_root)
        environment = RuntimeEnvironment(
            test_workspace_root=str(self.roots.test_repository_root),
            image_digest=None,
            filesystem=None,
            free_space_bytes=usage.free,
        )
        try:
            expanded = expand_plan(
                plan,
                environment=environment,
                profiles=self._profiles,
                declared_default=self._scoped_default(plan.configuration_base.scope),
                catalog_operations=self._catalog_operations,
            )
        except PlanError as error:
            raise ServiceError(422, "invalid_plan", str(error)) from error
        required = expanded["estimates"].get("required_free_space_bytes")
        if isinstance(required, int) and required > usage.free:
            expanded["runnable"] = False
            expanded["validation"].append({
                "severity": "error",
                "code": "insufficient_disk_space",
                "message": "the benchmark state root lacks the estimated free space",
                "path": None,
            })
        return expanded

    def health(self) -> dict[str, Any]:
        checks = [{
            "id": "state_root",
            "status": "pass",
            "message": "benchmark state ownership is valid",
        }]
        execution_ready = self._catalog_operations is not None and self._catalog_error is None
        checks.append({
            "id": "execution_backend",
            "status": "pass" if execution_ready else "fail",
            "message": (
                "prebuilt product catalog loaded"
                if execution_ready
                else self._catalog_error or "prebuilt product catalog has not been checked"
            ),
        })
        active = None
        if self._active is not None:
            active = {"run_id": self._active.run_id, "state": self._active.state}
        ready = execution_ready
        return {
            "schema_version": 1,
            "status": "ready" if ready else "unready",
            "execution_ready": ready,
            "version": "0.1.0",
            "runner_instance_id": self.instance_id,
            "active_run": active,
            "checks": checks,
        }

    def settings(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "test_workspace_root": str(self.roots.test_repository_root),
            "source": "command_line",
            "writable": False,
            "path_health": {"canonical": True, "root_marker": True, "outside_repository": False},
        }

    def update_settings(self, path: str) -> dict[str, Any]:
        if path != str(self.roots.test_repository_root):
            raise ServiceError(409, "immutable_roots", "repository roots are fixed for this process")
        return self.settings()

    async def create_run(
        self,
        raw_plan: dict[str, Any],
        reviewed_hash: str,
        client_request_id: str,
        starting_preset: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._catalog_operations is None:
            raise ServiceError(
                503,
                "execution_backend_unavailable",
                self._catalog_error or "the prebuilt product catalog has not been loaded",
            )
        if not client_request_id or len(client_request_id) > 128:
            raise ServiceError(422, "invalid_client_request_id", "client_request_id is required")
        expanded = self.validate_plan(raw_plan)
        if expanded["plan_hash"] != reviewed_hash:
            raise ServiceError(409, "plan_hash_mismatch", "the reviewed plan hash no longer matches")
        if not expanded["runnable"]:
            raise ServiceError(422, "plan_not_runnable", "the plan has validation errors", expanded["validation"])
        async with self._admission:
            if self._active is not None:
                raise ServiceError(409, "campaign_active", "only one campaign may run in this process")
            run_id = self._uuid7()
            runner = CampaignRunner(self.roots, event_sink=self._event_sink(run_id))
            active = _ActiveRun(run_id, expanded, runner, copy.deepcopy(starting_preset))
            self._active = active
            active.task = asyncio.create_task(
                self._execute(active, raw_plan), name=f"benchmark-{run_id}"
            )
        return {"schema_version": 1, "run_id": run_id, "state": "queued"}

    async def run_foreground(self, raw_plan: dict[str, Any], reviewed_hash: str) -> dict[str, Any]:
        created = await self.create_run(raw_plan, reviewed_hash, "cli")
        active = self._active
        assert active is not None and active.task is not None
        await active.task
        return self.run(created["run_id"])

    async def _execute(self, active: _ActiveRun, intent: dict[str, Any]) -> None:
        try:
            await active.runner.run(
                active.run_id,
                active.plan,
                intent=intent,
                definition_snapshot=copy.deepcopy(self._definitions),
                starting_preset=active.starting_preset,
            )
        except BaseException:
            # The runner persists failure and cleanup evidence. Task exceptions
            # must not become unobserved background failures.
            pass
        finally:
            try:
                active.state = self.store.read_envelope(active.run_id, ArtifactId.RUN_MANIFEST)["state"]
            except Exception:
                active.state = "failed"
            async with self._admission:
                if self._active is active:
                    self._active = None

    def _event_sink(self, run_id: str):
        async def publish(record: dict[str, Any]) -> None:
            if self._active is not None and self._active.run_id == run_id:
                data = record.get("data", {})
                if data.get("kind") == "run_state":
                    self._active.state = data.get("state", self._active.state)
            for queue in tuple(self._subscribers.get(run_id, ())):
                try:
                    queue.put_nowait(record)
                except asyncio.QueueFull:
                    self._subscribers.get(run_id, set()).discard(queue)
        return publish

    def list_runs(self) -> dict[str, Any]:
        runs = []
        for path in self._run_paths():
            try:
                runs.append(self._project(path)["manifest"])
            except (ArtifactError, ReportError, OSError, KeyError, ValueError):
                continue
        runs.sort(key=lambda item: item["started_at"], reverse=True)
        return {"schema_version": 1, "runs": runs, "next_cursor": None}

    def run(self, run_id: str) -> dict[str, Any]:
        if self._active is not None and self._active.run_id == run_id:
            active_path = self.roots.results / run_id
            if (active_path / "run-manifest.json").is_file():
                return self._project(active_path)
            plan = self._active.plan
            return {
                "schema_version": 1,
                "manifest": {
                    "run_id": run_id, "name": plan["canonical_plan"]["name"], "state": self._active.state,
                    "plan_hash": plan["plan_hash"], "configuration_scope": plan["canonical_plan"]["configuration_base"]["scope"],
                    "source_commit": "", "source_dirty": False, "started_at": "", "ended_at": None,
                    "correctness": "pending", "definition_snapshot_version": 2, "environment_fingerprint": "",
                },
                "progress": self._empty_progress(plan), "latest_sequence": 0, "report_ready": False,
            }
        return self._project(self.store.run_path(run_id))

    def _project(self, path: Path) -> dict[str, Any]:
        corpus = RunCorpus.open(path, recover_partial_tail=True)
        manifest = corpus.manifest
        treatment = corpus.environment.get("treatment", {})
        events = corpus.events.records
        cell_lookup = {cell["cell_id"]: cell for cell in corpus.expanded.get("cells", [])}
        progress = self._empty_progress(corpus.expanded)
        for event in events:
            data = event["data"]
            kind = data.get("kind")
            cell = cell_lookup.get(data.get("cell_id"), {})
            if kind == "family_state" and data.get("state") in {"preparing", "running"}:
                progress["current_family"] = "layer_stack" if data.get("family") == "layerstack" else data.get("family")
            if kind in {"cell_state", "trial_state", "trial_phase"}:
                progress["current_cell_id"] = data.get("cell_id")
                progress["current_operation"] = cell.get("operation_id")
            if kind in {"trial_state", "trial_phase"}:
                progress["current_trial_id"] = data.get("trial_id")
                progress["trial_kind"] = "warmup" if data.get("warmup") else "measured"
            if kind == "trial_phase" and data.get("state") == "running":
                progress["phase"] = data.get("phase")
            if kind == "trial_state" and data.get("state") in {"completed", "failed"}:
                progress["completed_trial_batches"] += 1
            if kind == "request_state" and data.get("state") == "in_flight":
                progress["issued_operation_requests"] += 1
            if kind == "warning": progress["warning_count"] += 1
            if kind in {"correctness", "trial_state"} and data.get("state") == "failed":
                progress["failure_count"] += 1
        correctness = manifest.get("correctness") or (
            corpus.report.correctness_verdict if corpus.report is not None else "pending"
        )
        definition_version = int(corpus.definitions.get("schema_version", 2))
        environment_bytes = json.dumps(corpus.environment, sort_keys=True, separators=(",", ":")).encode()
        projected_manifest = {
            "run_id": manifest["run_id"], "name": manifest["name"], "state": manifest["state"],
            "plan_hash": manifest["plan_hash"],
            "configuration_scope": corpus.expanded["canonical_plan"]["configuration_base"]["scope"],
            "source_commit": treatment.get("source_commit", ""),
            "source_dirty": bool(treatment.get("source_dirty", False)),
            "started_at": manifest.get("started_at") or "", "ended_at": manifest.get("ended_at"),
            "correctness": correctness,
            "definition_snapshot_version": definition_version,
            "environment_fingerprint": "sha256:" + hashlib.sha256(environment_bytes).hexdigest(),
        }
        return {
            "schema_version": 1, "manifest": projected_manifest, "progress": progress,
            "latest_sequence": events[-1]["sequence"] if events else 0,
            "report_ready": corpus.report is not None,
        }

    @staticmethod
    def _empty_progress(plan: dict[str, Any]) -> dict[str, Any]:
        estimates = plan.get("estimates", {})
        return {
            "current_family": None, "current_operation": None, "current_cell_id": None,
            "current_trial_id": None, "trial_kind": None, "phase": None,
            "completed_trial_batches": 0,
            "total_trial_batches": estimates.get("trial_batch_count", 0),
            "issued_operation_requests": 0, "warning_count": 0, "failure_count": 0,
        }

    def _run_paths(self) -> list[Path]:
        return [path for path in self.roots.results.iterdir() if path.is_dir() and not path.is_symlink()]

    async def cancel(self, run_id: str) -> dict[str, Any]:
        active = self._active
        if active is None or active.run_id != run_id:
            state = self.run(run_id)["manifest"]["state"]
            if state not in TERMINAL_STATES:
                raise ServiceError(409, "detached_run", "the run is not owned by this process")
            return {
                "schema_version": 1,
                "run_id": run_id,
                "state": state,
                "cancellation_requested": False,
            }
        if active.state not in {"cancelling", "cancelled"}:
            requested = await active.runner.request_cancel(run_id)
            active.state = "cancelling"
        else:
            requested = False
        return {
            "schema_version": 1,
            "run_id": run_id,
            "state": active.state,
            "cancellation_requested": requested,
        }

    def report(self, run_id: str) -> dict[str, Any]:
        corpus = RunCorpus.open(self.store.run_path(run_id), recover_partial_tail=True)
        if corpus.report is None:
            raise ServiceError(409, "report_not_ready", "the report is not ready")
        return corpus.report.model_dump(mode="json")

    def artifacts(self, run_id: str) -> dict[str, Any]:
        entries = []
        for reference in self.store.list_artifacts(run_id):
            entries.append({
                "artifact_id": reference.artifact_id, "label": reference.label,
                "media_type": reference.media_type, "size_bytes": reference.size_bytes,
                "sha256": reference.sha256,
            })
        return {"schema_version": 1, "run_id": run_id, "artifacts": entries}

    def artifact(self, run_id: str, artifact_id: str) -> dict[str, Any]:
        download = self.store.download_artifact(run_id, artifact_id)
        try:
            content = download.content.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = base64.b64encode(download.content).decode("ascii")
            encoding = "base64"
        reference = download.reference
        return {
            "schema_version": 1, "artifact_id": reference.artifact_id,
            "label": reference.label, "media_type": reference.media_type,
            "size_bytes": reference.size_bytes, "sha256": reference.sha256,
            "encoding": encoding, "content": content,
        }

    def compare(self, reference_run_id: str, candidate_run_id: str, override: bool) -> dict[str, Any]:
        reference = RunCorpus.open(self.store.run_path(reference_run_id))
        candidate = RunCorpus.open(self.store.run_path(candidate_run_id))
        return compare_runs(reference, candidate, descriptive_override=override).model_dump(mode="json")

    async def events(self, run_id: str, after: int) -> AsyncIterator[dict[str, Any]]:
        # Subscribe before replay. Records published during disk replay remain in
        # the bounded queue and are deduplicated by persisted sequence.
        self.store.run_path(run_id)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1024)
        subscribers = self._subscribers.setdefault(run_id, set())
        subscribers.add(queue)
        last = after
        try:
            replay = self.store.read_records(run_id, ArtifactId.EVENTS, recover_partial_tail=True).records
            for record in replay:
                if record["sequence"] > last:
                    last = record["sequence"]
                    yield record
            while True:
                try:
                    record = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    yield {"heartbeat": True}
                    continue
                if record["sequence"] > last:
                    last = record["sequence"]
                    yield record
        finally:
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(run_id, None)

    async def shutdown(self) -> None:
        active = self._active
        if active is None or active.task is None:
            return
        active.runner.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(active.task), timeout=65.0)
        except TimeoutError as error:
            raise RuntimeError("active campaign did not clean up during shutdown") from error

    async def recover(self) -> dict[str, Any]:
        if self._active is not None:
            raise ServiceError(409, "campaign_active", "recovery is unavailable during a campaign")

        def cleanup(run_id: str) -> None:
            runtime = self.roots.runtime / run_id
            if runtime.exists() or runtime.is_symlink():
                asyncio.run(recover_stale_gateway(self.roots, run_id))

        result = await asyncio.to_thread(RecoveryScanner(self.roots, cleanup).scan)
        return {
            "schema_version": 1,
            "recovered_run_ids": list(result.recovered_run_ids),
            "issues": [
                {"run_id": issue.run_id, "code": issue.code, "message": issue.message}
                for issue in result.issues
            ],
            "execution_available": result.execution_available,
        }

    async def cleanup(self, run_id: str) -> dict[str, Any]:
        if self._active is not None and self._active.run_id == run_id:
            raise ServiceError(409, "campaign_active", "cancel the active campaign before cleanup")
        # Cleanup is intentionally a narrowed recovery scan: unrelated runs are
        # never mutated. Temporarily hide no directories and instead fail closed
        # unless the requested run is the only nonterminal result.
        manifest = self.store.read_envelope(run_id, ArtifactId.RUN_MANIFEST)
        if manifest["state"] in TERMINAL_STATES:
            runtime = self.roots.runtime / run_id
            if runtime.exists() or runtime.is_symlink():
                await recover_stale_gateway(self.roots, run_id)
            return {"schema_version": 1, "run_id": run_id, "cleaned": True, "terminalized": False}

        def cleanup_gateway(_: str) -> None:
            runtime = self.roots.runtime / run_id
            if runtime.exists() or runtime.is_symlink():
                asyncio.run(recover_stale_gateway(self.roots, run_id))

        scanner = RecoveryScanner(self.roots, cleanup_gateway)
        result = await asyncio.to_thread(scanner.recover_run, run_id)
        return {"schema_version": 1, "run_id": run_id, "cleaned": bool(result), "terminalized": bool(result)}
