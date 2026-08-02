from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifacts import (
    ARTIFACT_SPECS,
    PRODUCER_ARTIFACT_IDS,
    ArtifactId,
    ArtifactStore,
)
from .derivation import build_report, utc_now
from .fixtures import materialize_workspace, materialize_workspaces, same_native_path
from .gateway import GatewayLauncher, cleanup_gateway_docker_resources
from .metadata import collect_environment
from .models import OwnedPathMarker
from .paths import BenchmarkRoots
from .product import ProductAccess
from .product_cli import ProductCliAccess
from .reports import persist_report_bundle
from .resource_sampling import TrialResourceSampler, WorkspaceMetricCache
from .safety import OwnershipLedger
from .sessions import Session, SessionLifecycle
from .transport import GatewayProductError, TimedGatewayResponse


class CampaignError(RuntimeError):
    pass


EventSink = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(slots=True)
class CampaignResult:
    run_id: str
    state: str
    trial_batches: int
    issued_requests: int
    observations: int


@dataclass(slots=True)
class BatchTiming:
    barrier_released_ns: int | None = None
    batch_completed_ns: int | None = None


@dataclass(frozen=True, slots=True)
class TrialOutcome:
    responses: list[TimedGatewayResponse]
    batch_makespan_ns: int
    artifact: dict[str, Any] | None
    setup_ns: int
    operation_ns: int
    verify_ns: int
    teardown_ns: int
    status: str
    product_succeeded: bool
    checks_passed: bool
    infrastructure_failed: bool
    cleanup_baseline_restored: bool


@dataclass(slots=True)
class CellContext:
    workspace: Path
    sandbox: str
    sessions: list[Session] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TrialContext:
    workspace: Path
    sandbox: str
    destroy_sandbox: bool
    sessions: list[Session] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


class CampaignRunner:
    """The only campaign scheduler used by both CLI and API."""

    _CANCELLATION_GRACE_SECONDS = 5.0
    _CLEANUP_TIMEOUT_SECONDS = 60.0

    def __init__(
        self, roots: BenchmarkRoots, *, event_sink: EventSink | None = None
    ) -> None:
        self._roots = roots
        self._store = ArtifactStore(roots)
        self._event_sink = event_sink
        self._cancel = asyncio.Event()
        self._event_sequence = 0
        self._observation_sequence = 0
        self._started_ns = 0
        self._image = ""
        self._profiles: dict[str, dict[str, Any]] = {}
        self._seed = 0
        self._resource_interval_ms = 100
        self._manifest: dict[str, Any] = {}
        self._definitions: dict[str, Any] = {}
        self._started_at = ""
        self._workspace_metric_cache = WorkspaceMetricCache()
        self._prepared_cell_workspaces: dict[str, Path] = {}
        self._trial_event_buffer: list[dict[str, Any]] | None = None
        self._trial_observation_buffer: list[dict[str, Any]] | None = None
        self._trial_event_sink_buffer: list[dict[str, Any]] | None = None

    def cancel(self) -> None:
        self._cancel.set()

    async def request_cancel(self, run_id: str) -> bool:
        """Request cancellation once and persist the public transition."""
        if self._cancel.is_set():
            return False
        self._cancel.set()
        await self._event(run_id, {"kind": "run_state", "state": "cancelling"})
        return True

    async def run(
        self,
        run_id: str,
        plan: dict[str, Any],
        *,
        intent: dict[str, Any],
        definition_snapshot: dict[str, Any],
        starting_preset: dict[str, Any] | None = None,
    ) -> CampaignResult:
        run_path = self._roots.runs / run_id
        marker = OwnedPathMarker(role="runs", identity={"run_id": run_id})
        ledger = OwnershipLedger(self._roots)
        try:
            run_path.mkdir(mode=0o700)
            ledger.register(run_path, marker)
            self._store.create_run(run_id)
        except Exception as error:
            raise CampaignError("campaign ownership setup failed") from error
        self._store.write_immutable(run_id, ArtifactId.INTENT_PLAN, intent)
        self._store.write_immutable(run_id, ArtifactId.EXPANDED_PLAN, plan)
        self._store.write_immutable(
            run_id, ArtifactId.DEFINITION_SNAPSHOT, definition_snapshot
        )
        definition_reference = self._store.download_artifact(
            run_id, ArtifactId.DEFINITION_SNAPSHOT.value
        ).reference
        self._definitions = definition_snapshot
        self._image = _required_string(plan, "canonical_plan", "environment", "image")
        self._profiles = {
            profile["id"]: profile
            for profile in plan.get("selected_workspace_profiles", [])
        }
        self._seed = plan["canonical_plan"]["seed"]
        self._resource_interval_ms = plan["canonical_plan"]["protocol"][
            "resource_interval_ms"
        ]
        environment = await collect_environment(self._roots, plan)
        self._store.write_immutable(
            run_id, ArtifactId.ENVIRONMENT_METADATA, environment
        )
        self._started_at = utc_now()
        self._manifest = self._new_manifest(
            run_id,
            plan,
            definition_snapshot,
            definition_reference.sha256,
            environment,
            starting_preset,
        )
        self._store.write_immutable(run_id, ArtifactId.RUN_MANIFEST, self._manifest)
        self._started_ns = time.monotonic_ns()
        await self._event(run_id, {"kind": "run_state", "state": "planned"})
        await self._event(run_id, {"kind": "run_state", "state": "queued"})
        await self._event(run_id, {"kind": "run_state", "state": "preparing"})
        state = "completed"
        failure: BaseException | None = None
        trial_batches = issued = 0
        gateway_instance_ids: list[str] = []
        try:
            await self._event(run_id, {"kind": "run_state", "state": "running"})
            cells_by_id = {cell["cell_id"]: cell for cell in plan["cells"]}
            await asyncio.to_thread(
                self._prepare_cell_workspaces, run_path, plan["cells"]
            )
            client_cohort = plan["effective_environment"]["client_cohort"]
            for block in plan["execution_blocks"]:
                self._check_cancelled()
                family = block["family_id"]
                await self._event(
                    run_id,
                    {
                        "kind": "family_state",
                        "family": _event_family(family),
                        "state": "preparing",
                    },
                )
                gateway = await GatewayLauncher(self._roots).start(
                    run_id,
                    remount_sweep_width=_block_width(block, plan),
                    readiness_via_cli=client_cohort == "product_cli",
                )
                gateway_instance_ids.append(gateway.identity.gateway_instance_id)
                endpoint = gateway.identity.endpoint
                self._manifest["gateway_execution_blocks"].append(
                    {
                        "block_id": block["block_id"],
                        "family_id": block["family_id"],
                        "gateway_instance_id": gateway.identity.gateway_instance_id,
                        "endpoint_uri": endpoint.uri,
                        "transport": endpoint.transport,
                        "scope": "local_only",
                        "rotation": "per_execution_block",
                    }
                )
                self._store.replace_snapshot(
                    run_id, ArtifactId.RUN_MANIFEST, self._manifest
                )
                if client_cohort == "product_cli":
                    product = ProductCliAccess(
                        gateway.identity.endpoint,
                        gateway.auth_token,
                        self._roots,
                        self._store.run_path(run_id),
                    )
                elif client_cohort == "direct_client":
                    product = ProductAccess(gateway.client, self._roots.runs)
                else:
                    raise CampaignError(
                        "expanded plan selected an unknown client cohort"
                    )
                sessions = SessionLifecycle(product)
                block_error: BaseException | None = None
                try:
                    await self._event(
                        run_id,
                        {
                            "kind": "family_state",
                            "family": _event_family(family),
                            "state": "running",
                        },
                    )
                    for cell_id in block["cell_ids"]:
                        self._check_cancelled()
                        batches, requests = await self._run_cell(
                            run_id, run_path, product, sessions, cells_by_id[cell_id]
                        )
                        trial_batches += batches
                        issued += requests
                    await self._event(
                        run_id,
                        {
                            "kind": "family_state",
                            "family": _event_family(family),
                            "state": "completed",
                        },
                    )
                except BaseException as error:
                    block_error = error
                    raise
                finally:
                    cleanup_errors: list[BaseException] = []
                    if isinstance(product, ProductCliAccess):
                        try:
                            await self._shielded_cleanup(
                                product.cleanup_owned(
                                    request_prefix=f"{run_id}.{family}.cleanup"
                                )
                            )
                        except BaseException as cleanup_error:
                            cleanup_errors.append(cleanup_error)
                    try:
                        await self._shielded_cleanup(
                            gateway.close(
                                destroy_sandboxes_via_gateway=not isinstance(
                                    product, ProductCliAccess
                                ),
                                retain_shared_base_volumes=True,
                            )
                        )
                        await self._event(
                            run_id,
                            {
                                "kind": "log",
                                "level": "info",
                                "message": _gateway_log_summary(
                                    getattr(gateway, "logs", ())
                                ),
                            },
                        )
                    except BaseException as cleanup_error:
                        cleanup_errors.append(cleanup_error)
                    if cleanup_errors:
                        if block_error is None:
                            raise CampaignError(
                                "gateway cleanup failed"
                            ) from BaseExceptionGroup(
                                "campaign cleanup", cleanup_errors
                            )
                        raise CampaignError(
                            "operation and gateway cleanup both failed"
                        ) from BaseExceptionGroup(
                            "campaign cleanup", [block_error, *cleanup_errors]
                        )
            self._check_cancelled()
            await self._event(run_id, {"kind": "run_state", "state": "verifying"})
            await self._event(run_id, {"kind": "run_state", "state": "tearing_down"})
        except asyncio.CancelledError:
            state = "cancelled"
        except BaseException as error:
            state = "cancelled" if self._cancel.is_set() else "failed"
            failure = error
        finally:
            try:
                await self._shielded_cleanup(
                    cleanup_gateway_docker_resources(tuple(gateway_instance_ids))
                )
            except BaseException as retained_cleanup_error:
                state = "failed"
                if failure is None:
                    failure = CampaignError(
                        "retained shared-base Docker cleanup failed"
                    )
                    failure.__cause__ = retained_cleanup_error
                else:
                    combined = CampaignError(
                        "campaign and retained shared-base Docker cleanup both failed"
                    )
                    combined.__cause__ = BaseExceptionGroup(
                        "campaign final cleanup",
                        [failure, retained_cleanup_error],
                    )
                    failure = combined
            try:
                ended_at = utc_now()
                observations_path = (
                    self._store.run_path(run_id)
                    / ARTIFACT_SPECS[ArtifactId.OBSERVATIONS].file_name
                )
                observations = (
                    self._store.read_records(run_id, ArtifactId.OBSERVATIONS).records
                    if observations_path.exists()
                    else []
                )
                report = build_report(
                    run_id=run_id,
                    state=state,
                    plan=plan,
                    definitions=definition_snapshot,
                    definition_snapshot_sha256=definition_reference.sha256,
                    environment=environment,
                    observations=observations,
                    started_at=self._started_at,
                    ended_at=ended_at,
                )
                if state == "completed" and report.correctness_verdict != "pass":
                    state = "failed"
                    failure = CampaignError(
                        "campaign completed without reportable correctness proof"
                    )
                    report = build_report(
                        run_id=run_id,
                        state=state,
                        plan=plan,
                        definitions=definition_snapshot,
                        definition_snapshot_sha256=definition_reference.sha256,
                        environment=environment,
                        observations=observations,
                        started_at=self._started_at,
                        ended_at=ended_at,
                    )
                persist_report_bundle(self._store, report)
                self._manifest["ended_at"] = ended_at
                self._manifest["correctness"] = report.correctness_verdict
                await self._event(run_id, {"kind": "run_state", "state": state})
                await self._event(
                    run_id,
                    {"kind": "report_ready", "provisional": False},
                )
                self._store.replace_snapshot(
                    run_id, ArtifactId.RUN_MANIFEST, self._manifest
                )
                if state in {"completed", "cancelled"}:
                    ledger.remove(run_path, marker)
            except BaseException as finalization_error:
                if failure is None:
                    failure = CampaignError("terminal artifact finalization failed")
                    failure.__cause__ = finalization_error
                else:
                    failure = CampaignError(
                        "campaign and artifact finalization both failed"
                    )
                    failure.__cause__ = BaseExceptionGroup(
                        "campaign finalization", [failure, finalization_error]
                    )
                state = "failed"
                self._manifest["state"] = state
                self._manifest["failure"] = {
                    "code": "artifact_finalization_failed",
                    "message": "terminal artifact finalization failed",
                    "infrastructure": True,
                }
                try:
                    self._store.replace_snapshot(
                        run_id, ArtifactId.RUN_MANIFEST, self._manifest
                    )
                except BaseException:
                    pass
        if failure is not None:
            raise failure
        return CampaignResult(
            run_id, state, trial_batches, issued, self._observation_sequence
        )

    async def _run_cell(
        self,
        run_id: str,
        run_path: Path,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
    ) -> tuple[int, int]:
        cell_id = cell["cell_id"]
        await self._event(
            run_id, {"kind": "cell_state", "cell_id": cell_id, "state": "preparing"}
        )
        cell_context = await self._setup_cell(run_path, product, sessions, cell)
        await self._event(
            run_id, {"kind": "cell_state", "cell_id": cell_id, "state": "running"}
        )
        counts = [(True, index) for index in range(cell["protocol"]["warmups"])] + [
            (False, index) for index in range(cell["protocol"]["measured_trials"])
        ]
        issued = 0
        cell_error: BaseException | None = None
        try:
            for warmup, index in counts:
                self._check_cancelled()
                trial_id = f"trial-{cell_id[-16:]}-{'warmup' if warmup else 'measured'}-{index:06d}"
                await self._trial_state(run_id, cell_id, trial_id, warmup, "preparing")
                try:
                    outcome = await self._run_trial_with_journal(
                        run_id,
                        run_path,
                        product,
                        sessions,
                        cell,
                        cell_context,
                        trial_id,
                        warmup,
                        index,
                    )
                except BaseException as error:
                    await self._trial_state(
                        run_id,
                        cell_id,
                        trial_id,
                        warmup,
                        "cancelled"
                        if isinstance(error, asyncio.CancelledError)
                        else "failed",
                    )
                    raise
                await self._trial_state(run_id, cell_id, trial_id, warmup, "completed")
                issued += len(outcome.responses)
        except BaseException as error:
            cell_error = error
            raise
        finally:
            try:
                await self._shielded_cleanup(
                    self._teardown_cell(product, sessions, cell_context, cell_id)
                )
            except BaseException as cleanup_error:
                if cell_error is None:
                    raise CampaignError("cell cleanup failed") from cleanup_error
                raise CampaignError(
                    "cell operation and cleanup both failed"
                ) from BaseExceptionGroup("cell cleanup", [cell_error, cleanup_error])
        self._check_cancelled()
        await self._event(
            run_id, {"kind": "cell_state", "cell_id": cell_id, "state": "completed"}
        )
        return len(counts), issued

    async def _run_trial_with_journal(
        self,
        run_id: str,
        run_path: Path,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        cell_context: CellContext | None,
        trial_id: str,
        warmup: bool,
        sequence_in_cell: int,
    ) -> TrialOutcome:
        self._begin_trial_journal()
        outcome: TrialOutcome | None = None
        failure: BaseException | None = None
        cli_evidence_started = False
        try:
            if isinstance(product, ProductCliAccess):
                product.begin_trial_evidence(trial_id)
                cli_evidence_started = True
            outcome = await self._run_trial(
                run_id,
                run_path,
                product,
                sessions,
                cell,
                cell_context,
                trial_id,
                warmup,
                sequence_in_cell,
            )
        except BaseException as error:
            failure = error
        evidence_committed = True
        if cli_evidence_started:
            try:
                await product.flush_trial_evidence(trial_id)
            except BaseException as error:
                evidence_committed = False
                failure = _combine_failures(failure, error, "CLI trial evidence commit")
        if evidence_committed:
            try:
                await self._flush_trial_journal(run_id)
            except BaseException as error:
                failure = _combine_failures(failure, error, "trial journal commit")
        if cli_evidence_started:
            try:
                product.end_trial_evidence(trial_id)
            except BaseException as error:
                failure = _combine_failures(
                    failure, error, "CLI trial evidence boundary"
                )
        self._end_trial_journal()
        if failure is not None:
            raise failure
        if outcome is None:  # pragma: no cover - defensive invariant
            raise CampaignError("trial completed without an outcome")
        return outcome

    async def _run_trial(
        self,
        run_id: str,
        run_path: Path,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        cell_context: CellContext | None,
        trial_id: str,
        warmup: bool,
        sequence_in_cell: int,
    ) -> TrialOutcome:
        cell_id = cell["cell_id"]
        operation_id = cell["operation"]["operation"]
        setup_ns = operation_ns = verify_ns = teardown_ns = 0
        batch_makespan_ns = 0
        responses: list[TimedGatewayResponse] = []
        artifact: dict[str, Any] | None = None
        pending_evidence: dict[str, Any] | None = None
        context: TrialContext | None = None
        failure: BaseException | None = None
        failure_stage = "setup"
        product_succeeded = False
        checks_passed = False
        cleanup_restored = False
        infrastructure_failed = False
        sampler: TrialResourceSampler | None = None
        sampler_stopped = False
        batch_timing = BatchTiming()

        await self._trial_phase(run_id, cell_id, trial_id, warmup, "setup", "running")
        phase_started = time.monotonic_ns()
        try:
            self._check_cancelled()
            context = await self._setup_trial(
                run_path, product, sessions, cell, cell_context, trial_id
            )
            setup_ns = time.monotonic_ns() - phase_started
            await self._trial_phase(
                run_id, cell_id, trial_id, warmup, "setup", "completed"
            )

            if operation_id != "create_sandbox":
                sampler = TrialResourceSampler(
                    product=product,
                    sandbox=context.sandbox,
                    workspace=context.workspace,
                    cell_id=cell_id,
                    trial_id=trial_id,
                    interval_ms=self._resource_interval_ms,
                    campaign_started_ns=self._started_ns,
                    sink=lambda data: self._resource_observations(run_id, data),
                    workspace_cache=self._workspace_metric_cache,
                    expected_post_workspace_count=(
                        cell["operation"]["cell"]["workspace_count"]
                        if operation_id == "create_workspace"
                        else None
                    ),
                )
                await sampler.start()
            failure_stage = "operation"
            await self._trial_phase(
                run_id, cell_id, trial_id, warmup, "operation", "running"
            )
            self._check_cancelled()
            responses = await self._operate(
                product,
                sessions,
                cell,
                context,
                trial_id,
                run_id=run_id,
                batch_timing=batch_timing,
            )
            if batch_timing.barrier_released_ns is None:
                raise CampaignError("request batch did not record its barrier release")
            validated_ended_ns = _validated_response_end_ns(
                responses, fallback=batch_timing.batch_completed_ns
            )
            if validated_ended_ns < batch_timing.barrier_released_ns:
                raise CampaignError("request batch timing preceded its barrier release")
            batch_makespan_ns = validated_ended_ns - batch_timing.barrier_released_ns
            operation_ns = batch_makespan_ns
            product_succeeded = True
            if operation_id == "create_sandbox":
                sampler = TrialResourceSampler(
                    product=product,
                    sandbox=context.sandbox,
                    workspace=context.workspace,
                    cell_id=cell_id,
                    trial_id=trial_id,
                    interval_ms=self._resource_interval_ms,
                    campaign_started_ns=self._started_ns,
                    sink=lambda data: self._resource_observations(run_id, data),
                    workspace_cache=self._workspace_metric_cache,
                    counter_delta_applicable=False,
                )
                await sampler.start()
            # Product responses have now exited and validated. End the resource
            # window before journal persistence and correctness verification so
            # those untimed phases cannot be attributed to the primary work.
            failure_stage = "infrastructure"
            await sampler.stop()
            sampler_stopped = True
            failure_stage = "operation"
            for response in responses:
                await self._request_observation(
                    run_id, cell, trial_id, warmup, response
                )
            await self._trial_phase(
                run_id, cell_id, trial_id, warmup, "operation", "completed"
            )

            failure_stage = "verify"
            await self._trial_phase(
                run_id, cell_id, trial_id, warmup, "verify", "running"
            )
            self._check_cancelled()
            verify_started = time.monotonic_ns()
            await self._verify(product, sessions, cell, responses, context, trial_id)
            if operation_id == "squash_layerstack":
                await self._phase_observations(
                    run_id, cell, trial_id, responses[0], product, context
                )
            evidence = _operation_evidence(cell, responses, context)
            if operation_id == "create_workspace":
                pending_evidence = evidence
            else:
                artifact = self._persist_operation_evidence(
                    run_id, cell_id, trial_id, operation_id, responses, evidence
                )
            verify_ns = time.monotonic_ns() - verify_started
            checks_passed = True
            await self._trial_phase(
                run_id, cell_id, trial_id, warmup, "verify", "completed"
            )
        except BaseException as error:
            failure = error
            infrastructure_failed = (
                _trial_status(error, failure_stage) == "infrastructure_failed"
            )
            now = time.monotonic_ns()
            if failure_stage == "setup":
                setup_ns = now - phase_started
            elif (
                failure_stage == "operation"
                and batch_timing.barrier_released_ns is not None
            ):
                operation_ns = now - batch_timing.barrier_released_ns
                batch_makespan_ns = operation_ns
            elif failure_stage == "verify" and "verify_started" in locals():
                verify_ns = now - verify_started
        finally:
            if sampler is not None and not sampler_stopped:
                try:
                    await sampler.stop()
                except BaseException as sampler_error:
                    failure = _combine_failures(
                        failure, sampler_error, "resource sampling"
                    )
                    failure_stage = "infrastructure"
                    infrastructure_failed = True
            if context is not None:
                await self._trial_phase(
                    run_id, cell_id, trial_id, warmup, "teardown", "running"
                )
                teardown_started = time.monotonic_ns()
                try:
                    await self._shielded_cleanup(
                        self._teardown_trial(product, sessions, context, trial_id)
                    )
                    cleanup_restored = True
                    await self._trial_phase(
                        run_id, cell_id, trial_id, warmup, "teardown", "completed"
                    )
                except BaseException as teardown_error:
                    failure = _combine_failures(
                        failure, teardown_error, "trial teardown"
                    )
                    failure_stage = "cleanup"
                teardown_ns = time.monotonic_ns() - teardown_started

        # A cancellation that arrives while shielded teardown is completing
        # still cancels the trial, without discarding the successful cleanup proof.
        if failure is None and self._cancel.is_set():
            failure = asyncio.CancelledError()
            failure_stage = "teardown"

        if failure is None and operation_id == "create_workspace":
            try:
                if pending_evidence is None or not cleanup_restored:
                    raise CampaignError("workspace evidence is missing cleanup proof")
                detail = pending_evidence["evidence"]
                detail["destroyed_count"] = len(responses)
                detail["registry_baseline_restored"] = True
                artifact = self._persist_operation_evidence(
                    run_id,
                    cell_id,
                    trial_id,
                    operation_id,
                    responses,
                    pending_evidence,
                )
            except BaseException as evidence_error:
                failure = evidence_error
                failure_stage = "infrastructure"
                infrastructure_failed = True

        if failure is None and (
            artifact is None or not checks_passed or not cleanup_restored
        ):
            failure = CampaignError("successful trial is missing required proof")
            failure_stage = "infrastructure"
            infrastructure_failed = True
        status = _trial_status(failure, failure_stage)
        outcome = TrialOutcome(
            responses=responses,
            batch_makespan_ns=batch_makespan_ns,
            artifact=artifact,
            setup_ns=setup_ns,
            operation_ns=operation_ns,
            verify_ns=verify_ns,
            teardown_ns=teardown_ns,
            status=status,
            product_succeeded=product_succeeded,
            checks_passed=checks_passed,
            infrastructure_failed=infrastructure_failed,
            cleanup_baseline_restored=cleanup_restored,
        )
        await self._registered_check_observations(
            run_id,
            cell,
            trial_id,
            passed=checks_passed and cleanup_restored,
            failure_stage=failure_stage if failure is not None else None,
        )
        await self._trial_observation(
            run_id, cell, trial_id, warmup, sequence_in_cell, outcome
        )
        if failure is not None:
            raise failure
        return outcome

    def _persist_operation_evidence(
        self,
        run_id: str,
        cell_id: str,
        trial_id: str,
        operation_id: str,
        responses: list[TimedGatewayResponse],
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        reference = self._store.write_trial_evidence(
            run_id, cell_id, trial_id, evidence
        )
        self._observation(
            run_id,
            {
                "record": "operation",
                "data": {
                    "operation_id": operation_id,
                    "cell_id": cell_id,
                    "trial_id": trial_id,
                    "request_id": (
                        responses[0].request_id
                        if operation_id == "squash_layerstack"
                        else None
                    ),
                    "evidence": evidence,
                },
            },
        )
        return {
            "artifact_id": reference.artifact_id,
            "media_type": reference.media_type,
            "size_bytes": reference.size_bytes,
            "sha256": reference.sha256,
        }

    async def _setup_cell(
        self,
        run_path: Path,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
    ) -> CellContext | None:
        if cell["operation"]["operation"] == "create_sandbox":
            workspace = self._cell_workspace(run_path, cell)
            return CellContext(workspace, "")
        isolation = _isolation(cell)
        if isolation not in {
            "reusable_verified_fixture",
            "prepared_sandbox_per_cell",
            "fresh_sessions_per_trial",
        }:
            return None
        workspace = self._cell_workspace(run_path, cell)
        record, _ = await product.create_sandbox(
            self._image,
            workspace,
            request_id=f"cell-{cell['cell_id'][-16:]}.sandbox.create",
        )
        context = CellContext(workspace, record.id)
        try:
            await self._prepare_operation(
                product, sessions, cell, context, f"cell-{cell['cell_id'][-16:]}"
            )
        except BaseException as setup_error:
            try:
                await self._teardown_cell(product, sessions, context, cell["cell_id"])
            except BaseException as cleanup_error:
                raise CampaignError(
                    "cell setup and cleanup both failed"
                ) from BaseExceptionGroup(
                    "cell setup cleanup", [setup_error, cleanup_error]
                )
            raise
        return context

    async def _setup_trial(
        self,
        run_path: Path,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        cell_context: CellContext | None,
        trial_id: str,
    ) -> TrialContext:
        operation = cell["operation"]["operation"]
        if cell_context is not None:
            context = TrialContext(
                cell_context.workspace,
                cell_context.sandbox,
                False,
                data=dict(cell_context.data),
            )
            if cell_context.sessions:
                context.data["operation_session"] = cell_context.sessions[0]
        else:
            workspace = self._new_workspace(run_path, trial_id, cell)
            if operation == "create_sandbox":
                context = TrialContext(workspace, "", False)
            else:
                record, _ = await product.create_sandbox(
                    self._image, workspace, request_id=f"{trial_id}.sandbox.create"
                )
                context = TrialContext(workspace, record.id, True)
        try:
            if cell_context is None and operation != "create_sandbox":
                await self._prepare_operation(
                    product, sessions, cell, context, trial_id
                )
            body = cell["operation"]["cell"]
            if (
                operation in {"file_write", "file_edit"}
                and body["destination"] == "session"
            ):
                session, _ = await sessions.create_no_op(
                    context.sandbox, "shared", request_id=f"{trial_id}.session.setup"
                )
                context.sessions.append(session)
            context.data["operation_id"] = operation
        except BaseException as setup_error:
            try:
                await self._teardown_trial(product, sessions, context, trial_id)
            except BaseException as cleanup_error:
                raise CampaignError(
                    "trial setup and cleanup both failed"
                ) from BaseExceptionGroup(
                    "trial setup cleanup", [setup_error, cleanup_error]
                )
            raise
        return context

    async def _prepare_operation(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        context: CellContext | TrialContext,
        key: str,
    ) -> None:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        timeout = cell["protocol"]["timeout_ms"]
        if operation == "exec_command":
            if body["command_case"] == "fixture_read":
                await product.file_write(
                    context.sandbox,
                    session_id=None,
                    path=".eos-benchmark-fixture/command-read.bin",
                    content="f" * 4096,
                    timeout_ms=timeout,
                    request_id=f"{key}.fixture.command-read",
                )
            if body["session_mode"] == "explicit":
                session, _ = await sessions.create_no_op(
                    context.sandbox, "shared", request_id=f"{key}.session.setup"
                )
                context.sessions.append(session)
        elif operation == "file_read":
            await self._prepare_reads(product, cell, context, key)
            if body["source"] == "session":
                session, _ = await sessions.create_no_op(
                    context.sandbox, "shared", request_id=f"{key}.session.setup"
                )
                context.sessions.append(session)
                context.data["read_session"] = session
        elif operation in {"file_write", "file_edit"}:
            await self._prepare_mutation(product, cell, context, key)
        elif operation == "file_blame":
            await self._prepare_blame(product, cell, context, key)
        elif operation == "squash_layerstack":
            await self._prepare_squash(product, sessions, cell, context, key)

    async def _prepare_reads(
        self,
        product: ProductAccess,
        cell: dict[str, Any],
        context: CellContext | TrialContext,
        key: str,
    ) -> None:
        body = cell["operation"]["cell"]
        count = (
            body["concurrent_requests"] if body["target_mode"] == "independent" else 1
        )
        paths: list[str] = []
        contents: list[str] = []
        for index in range(count):
            path = f".eos-benchmark/{key}/read-{index}.txt"
            content = _content(body["returned_bytes"], f"read:{key}:{index}")
            paths.append(path)
            contents.append(content)
        writes = [
            product.file_write(
                context.sandbox,
                session_id=None,
                path=path,
                content=contents[index],
                timeout_ms=cell["protocol"]["timeout_ms"],
                request_id=f"{key}.prepare.read.{index}",
            )
            for index, path in enumerate(paths)
        ]
        if len(writes) == 1:
            await writes[0]
        else:
            await _gather_complete(writes, "independent read fixture preparation")
        context.data.update(paths=paths, contents=contents)

    async def _prepare_mutation(
        self,
        product: ProductAccess,
        cell: dict[str, Any],
        context: CellContext | TrialContext,
        key: str,
    ) -> None:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        count = (
            body["concurrent_requests"] if body["target_mode"] == "independent" else 1
        )
        size = (
            body["content_bytes"] if operation == "file_write" else body["file_bytes"]
        )
        paths: list[str] = []
        before: list[str] = []
        expected: list[str] = []
        edits_by_request: list[list[dict[str, Any]]] = []
        replacements_by_request = [0 for _ in range(body["concurrent_requests"])]
        baseline_request_ids: list[str] = []
        if operation == "file_edit":
            edits_by_request = [
                _edits(key, index, body["replacement_count"])
                for index in range(body["concurrent_requests"])
            ]
        for index in range(count):
            path = f".eos-benchmark/{key}/{operation}-{index}.txt"
            if operation == "file_write":
                original = _multiline_content(size, f"write-baseline:{key}:{index}")
                final = original
            else:
                selected = (
                    edits_by_request[index : index + 1]
                    if body["target_mode"] == "independent"
                    else edits_by_request
                )
                path_edits = [edit for request in selected for edit in request]
                original, final, counts = _edit_content(
                    size, body["match_density"], path_edits
                )
                request_indices = (
                    [index]
                    if body["target_mode"] == "independent"
                    else list(range(body["concurrent_requests"]))
                )
                for request_index in request_indices:
                    replacements_by_request[request_index] = sum(
                        counts.get(edit["old_string"], 0)
                        for edit in edits_by_request[request_index]
                    )
            baseline_request_id = f"{key}.prepare.{operation}.{index}"
            paths.append(path)
            before.append(original)
            expected.append(final)
            baseline_request_ids.append(baseline_request_id)
        writes = [
            product.file_write(
                context.sandbox,
                session_id=None,
                path=path,
                content=before[index],
                timeout_ms=cell["protocol"]["timeout_ms"],
                request_id=baseline_request_ids[index],
            )
            for index, path in enumerate(paths)
        ]
        if len(writes) == 1:
            await writes[0]
        else:
            await _gather_complete(
                writes, f"independent {operation} baseline preparation"
            )
        context.data.update(
            paths=paths,
            before=before,
            expected=expected,
            edits=edits_by_request,
            expected_replacements=replacements_by_request,
            baseline_request_ids=baseline_request_ids,
        )

    async def _prepare_blame(
        self,
        product: ProductAccess,
        cell: dict[str, Any],
        context: CellContext | TrialContext,
        key: str,
    ) -> None:
        body = cell["operation"]["cell"]
        path = f".eos-benchmark/{key}/blame.txt"
        events = body["auditability_event_count"]
        segments = body["ownership_segments"]
        write_events = events if segments == 1 else events - 1
        event_request_ids: list[str] = []
        for event in range(write_events):
            request_id = f"{key}.prepare.blame.{event}"
            await product.file_write(
                context.sandbox,
                session_id=None,
                path=path,
                content=_blame_content(body["line_count"], segments, event),
                timeout_ms=cell["protocol"]["timeout_ms"],
                request_id=request_id,
            )
            event_request_ids.append(request_id)
        if segments > 1:
            request_id = f"{key}.prepare.blame.{events - 1}"
            await product.file_edit(
                context.sandbox,
                session_id=None,
                path=path,
                edits=[{"old_string": "A|", "new_string": "C|", "replace_all": True}],
                timeout_ms=cell["protocol"]["timeout_ms"],
                request_id=request_id,
            )
            event_request_ids.append(request_id)
        context.data.update(
            path=path,
            line_count=body["line_count"],
            ownership_segments=segments,
            expected_blame_ranges=_expected_blame_ranges(
                body["line_count"], segments, event_request_ids
            ),
        )

    async def _prepare_squash(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        context: CellContext | TrialContext,
        key: str,
    ) -> None:
        body = cell["operation"]["cell"]
        timeout = cell["protocol"]["timeout_ms"]
        paths: list[str] = []
        contents: list[str] = []
        eligible = min(
            body["live_sessions"],
            int(body["live_sessions"] * body["requested_migration_ratio"] + 0.5),
        )
        boundary_sessions = body["squashable_blocks"] - 1
        if eligible < boundary_sessions:
            raise CampaignError(
                "requested eligible sessions cannot form squash block boundaries"
            )

        session_index = 0

        async def create_session() -> None:
            nonlocal session_index
            session, _ = await sessions.create_no_op(
                context.sandbox,
                "shared",
                request_id=f"{key}.live.{session_index}",
            )
            context.sessions.append(session)
            session_index += 1

        for _ in range(body["live_sessions"] - eligible):
            await create_session()

        layer = 0
        for block in range(body["squashable_blocks"]):
            for in_block in range(body["layers_per_block"]):
                path = (
                    f".eos-benchmark/{key}/block-{block:04d}-layer-{in_block:04d}.txt"
                )
                content = _content(body["payload_bytes"], f"layer:{key}:{layer}")
                await product.file_write(
                    context.sandbox,
                    session_id=None,
                    path=path,
                    content=content,
                    timeout_ms=timeout,
                    request_id=f"{key}.layer.{layer}",
                )
                paths.append(path)
                contents.append(content)
                layer += 1
            if block + 1 < body["squashable_blocks"]:
                await product.file_write(
                    context.sandbox,
                    session_id=None,
                    path=f".eos-benchmark/{key}/boundary-{block:04d}.txt",
                    content=f"boundary:{key}:{block}",
                    timeout_ms=timeout,
                    request_id=f"{key}.boundary.{block}",
                )
                await create_session()
        remaining_eligible = eligible - boundary_sessions
        if remaining_eligible:
            await product.file_write(
                context.sandbox,
                session_id=None,
                path=f".eos-benchmark/{key}/boundary-top.txt",
                content=f"boundary:{key}:top",
                timeout_ms=timeout,
                request_id=f"{key}.boundary.top",
            )
            for _ in range(remaining_eligible):
                await create_session()
        if session_index != body["live_sessions"]:
            raise CampaignError("prepared squash session count is inconsistent")
        for index, session in enumerate(context.sessions):
            if body["session_activity"] == "active":
                await product.file_write(
                    context.sandbox,
                    session_id=session.session_id,
                    path=f".eos-benchmark/{key}/session-activity-{index}.txt",
                    content=f"active:{key}:{index}",
                    timeout_ms=timeout,
                    request_id=f"{key}.activity.{index}",
                )
        baseline = await product.observe_layerstack(
            context.sandbox, request_id=f"{key}.observe.layerstack.s0"
        )
        context.data.update(
            paths=paths,
            contents=contents,
            squash_cell=dict(body),
            eligible_sessions=eligible,
            s0_view=baseline,
            s0_baseline=_layerstack_evidence(
                baseline,
                max(0, time.monotonic_ns() - self._started_ns),
                sampled=False,
            ),
        )

    async def _operate(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        context: TrialContext,
        trial_id: str,
        *,
        run_id: str | None = None,
        batch_timing: BatchTiming | None = None,
    ) -> list[TimedGatewayResponse]:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        cell_id = cell.get("cell_id", "")
        if run_id is not None and not cell_id:
            raise CampaignError("campaign operation requires a cell_id")
        sandbox = context.sandbox
        timeout = cell["protocol"]["timeout_ms"]
        request_count = (
            body["workspace_count"]
            if operation == "create_workspace"
            else 1
            if operation in {"create_sandbox", "squash_layerstack"}
            else body["concurrent_requests"]
        )
        request_ids = (
            ["squash-layerstack-0"]
            if operation == "squash_layerstack"
            else [f"{trial_id}.request.{index}" for index in range(request_count)]
        )
        if operation == "create_sandbox":

            async def create() -> TimedGatewayResponse:
                record, response = await product.create_sandbox(
                    self._image,
                    context.workspace,
                    request_id=request_ids[0],
                )
                context.sandbox = record.id
                context.destroy_sandbox = True
                context.data["created_sandbox"] = record
                return response

            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [create],
                batch_timing=batch_timing,
            )
        if operation == "exec_command":
            operation_session = context.data.get("operation_session")
            session_id = (
                operation_session.session_id
                if operation_session is not None
                else context.sessions[0].session_id
                if context.sessions
                else None
            )
            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [
                    lambda index=index: product.exec_command(
                        sandbox,
                        session_id=session_id,
                        command=body["command"],
                        timeout_ms=timeout,
                        request_id=request_ids[index],
                    )
                    for index in range(body["concurrent_requests"])
                ],
                batch_timing=batch_timing,
            )
        if operation == "file_read":
            session = context.data.get("read_session")
            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [
                    lambda index=index: product.file_read(
                        sandbox,
                        session_id=session.session_id if session else None,
                        path=context.data["paths"][
                            index if body["target_mode"] == "independent" else 0
                        ],
                        offset=1,
                        limit=1,
                        timeout_ms=timeout,
                        request_id=request_ids[index],
                    )
                    for index in range(body["concurrent_requests"])
                ],
                batch_timing=batch_timing,
            )
        if operation == "file_write":
            operation_session = context.data.get("operation_session")
            session_id = (
                operation_session.session_id
                if operation_session is not None
                else context.sessions[0].session_id
                if context.sessions
                else None
            )
            contents = [
                _multiline_content(
                    body["content_bytes"], f"write-request:{trial_id}:{index}"
                )
                for index in range(body["concurrent_requests"])
            ]
            context.data["request_contents"] = contents
            try:
                if isinstance(product, ProductCliAccess):
                    for index, content in enumerate(contents):
                        await product.stage_file_write_content(
                            content, request_id=request_ids[index]
                        )
                return await self._run_request_batch(
                    run_id,
                    cell_id,
                    trial_id,
                    request_ids,
                    [
                        lambda index=index: product.file_write(
                            sandbox,
                            session_id=session_id,
                            path=context.data["paths"][
                                index if body["target_mode"] == "independent" else 0
                            ],
                            content=contents[index],
                            timeout_ms=timeout,
                            request_id=request_ids[index],
                        )
                        for index in range(body["concurrent_requests"])
                    ],
                    batch_timing=batch_timing,
                )
            finally:
                if isinstance(product, ProductCliAccess):
                    for request_id in request_ids:
                        product.discard_file_write_content(request_id)
        if operation == "file_edit":
            operation_session = context.data.get("operation_session")
            session_id = (
                operation_session.session_id
                if operation_session is not None
                else context.sessions[0].session_id
                if context.sessions
                else None
            )
            context.data["operation_request_ids"] = request_ids
            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [
                    lambda index=index: product.file_edit(
                        sandbox,
                        session_id=session_id,
                        path=context.data["paths"][
                            index if body["target_mode"] == "independent" else 0
                        ],
                        edits=context.data["edits"][index],
                        timeout_ms=timeout,
                        request_id=request_ids[index],
                    )
                    for index in range(body["concurrent_requests"])
                ],
                batch_timing=batch_timing,
            )
        if operation == "file_blame":
            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [
                    lambda index=index: product.file_blame(
                        sandbox,
                        path=context.data["path"],
                        timeout_ms=timeout,
                        request_id=request_ids[index],
                    )
                    for index in range(body["concurrent_requests"])
                ],
                batch_timing=batch_timing,
            )
        if operation == "create_workspace":
            created = await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [
                    lambda index=index: sessions.create_no_op(
                        sandbox,
                        body["network_profile"],
                        request_id=request_ids[index],
                        timeout_ms=timeout,
                    )
                    for index in range(body["workspace_count"])
                ],
                batch_timing=batch_timing,
            )
            context.sessions.extend(item[0] for item in created)
            return [item[1] for item in created]
        if operation == "squash_layerstack":

            async def squash() -> TimedGatewayResponse:
                return await product.squash_layerstacks(
                    sandbox, timeout_ms=timeout, request_id=request_ids[0]
                )

            if run_id is None:
                return [await squash()]
            return await self._run_request_batch(
                run_id,
                cell_id,
                trial_id,
                request_ids,
                [squash],
                batch_timing=batch_timing,
            )
        raise CampaignError(f"operation {operation} is not implemented")

    async def _run_request_batch(
        self,
        run_id: str | None,
        cell_id: str,
        trial_id: str,
        request_ids: list[str],
        operations: list[Callable[[], Awaitable[Any]]],
        *,
        batch_timing: BatchTiming | None = None,
    ) -> list[Any]:
        if run_id is None:
            return await self._run_batch(operations, batch_timing=batch_timing)
        terminal: set[str] = set()
        pending_states: list[dict[str, Any]] = []

        def state_record(request_id: str, state: str) -> dict[str, Any]:
            self._event_sequence += 1
            return {
                "sequence": self._event_sequence,
                "run_id": run_id,
                "monotonic_offset_ns": max(0, time.monotonic_ns() - self._started_ns),
                "data": {
                    "kind": "request_state",
                    "cell_id": cell_id,
                    "trial_id": trial_id,
                    "request_id": request_id,
                    "state": state,
                },
            }

        def defer(request_id: str, state: str) -> None:
            pending_states.append(state_record(request_id, state))

        def defer_all(state: str) -> None:
            for request_id in request_ids:
                defer(request_id, state)

        async def commit_pre_release() -> None:
            # Setup/phase, waiting, and all-tasks-ready records form one ordered
            # durability transaction before the gate opens. A failed commit
            # prevents release; a successful commit proves every request was
            # admitted and ready without paying three independent fsyncs.
            defer_all("ready_at_barrier")
            records = list(pending_states)
            pending_states.clear()
            event_buffer = getattr(self, "_trial_event_buffer", None)
            sink_buffer = getattr(self, "_trial_event_sink_buffer", None)
            if event_buffer is None and sink_buffer is None:
                self._store.append_records(run_id, ArtifactId.EVENTS, records)
                if self._event_sink is not None:
                    for record in records:
                        await self._event_sink(record)
                return
            if event_buffer is None or sink_buffer is None:
                raise CampaignError("trial journal transaction is inconsistent")
            event_buffer.extend(records)
            if self._event_sink is not None:
                sink_buffer.extend(records)
            await self._flush_trial_journal(run_id)

        defer_all("waiting_at_barrier")

        async def observed(
            request_id: str, operation: Callable[[], Awaitable[Any]]
        ) -> Any:
            # Record the transition in memory so journal fsync and live-event
            # delivery cannot sit between barrier release and process creation.
            defer(request_id, "in_flight")
            try:
                result = await operation()
            except asyncio.CancelledError:
                terminal.add(request_id)
                defer(request_id, "cancelled")
                raise
            except BaseException:
                terminal.add(request_id)
                defer(request_id, "failed")
                raise
            terminal.add(request_id)
            defer(request_id, "succeeded")
            return result

        wrapped = [
            lambda request_id=request_id, operation=operation: observed(
                request_id, operation
            )
            for request_id, operation in zip(request_ids, operations, strict=True)
        ]
        try:
            return await self._run_batch(
                wrapped,
                batch_timing=batch_timing,
                before_release=commit_pre_release,
            )
        except asyncio.CancelledError:
            for request_id in request_ids:
                if request_id not in terminal:
                    defer(request_id, "cancelled")
            raise
        finally:
            if pending_states:
                records = list(pending_states)
                pending_states.clear()
                self._store.append_records(run_id, ArtifactId.EVENTS, records)
                if self._event_sink is not None:
                    for record in records:
                        await self._event_sink(record)

    async def _run_batch(
        self,
        operations: list[Callable[[], Awaitable[Any]]],
        *,
        batch_timing: BatchTiming | None = None,
        before_release: Callable[[], Awaitable[None]] | None = None,
    ) -> list[Any]:
        """Admit one synchronized request batch and give in-flight work bounded grace."""
        self._check_cancelled()
        if not operations:
            raise CampaignError("request batch must not be empty")
        gate = asyncio.Event()
        all_waiting = asyncio.Event()
        waiting = 0
        results: list[Any] = [None] * len(operations)

        async def run_one(index: int, operation: Callable[[], Awaitable[Any]]) -> None:
            nonlocal waiting
            waiting += 1
            if waiting == len(operations):
                all_waiting.set()
            await gate.wait()
            results[index] = await operation()

        async def run_all() -> None:
            async with asyncio.TaskGroup() as group:
                for index, operation in enumerate(operations):
                    group.create_task(run_one(index, operation))
                await all_waiting.wait()
                if before_release is not None:
                    await before_release()
                if batch_timing is not None:
                    batch_timing.barrier_released_ns = time.monotonic_ns()
                gate.set()

        batch = asyncio.create_task(run_all())
        cancellation = asyncio.create_task(self._cancel.wait())
        try:
            done, _ = await asyncio.wait(
                {batch, cancellation}, return_when=asyncio.FIRST_COMPLETED
            )
            if batch in done:
                await batch
                if batch_timing is not None:
                    batch_timing.batch_completed_ns = time.monotonic_ns()
                return results
            try:
                await asyncio.wait_for(
                    asyncio.shield(batch), timeout=self._CANCELLATION_GRACE_SECONDS
                )
            except TimeoutError:
                batch.cancel()
                try:
                    await batch
                except BaseException:
                    pass
            raise asyncio.CancelledError
        finally:
            cancellation.cancel()
            try:
                await cancellation
            except BaseException:
                pass

    async def _verify(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        cell: dict[str, Any],
        responses: list[TimedGatewayResponse],
        context: TrialContext,
        trial_id: str,
    ) -> None:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        timeout = cell["protocol"]["timeout_ms"]
        for index, response in enumerate(responses):
            value = response.value
            if not isinstance(value, dict):
                raise CampaignError("product response is not an object")
            if operation == "create_sandbox":
                record = await product.inspect_sandbox(
                    context.sandbox,
                    request_id=f"{trial_id}.verify.inspect",
                )
                if (
                    record.state != "ready"
                    or not same_native_path(record.workspace_root, context.workspace)
                    or body["network_profile"] != "shared"
                ):
                    raise CampaignError("sandbox readiness check failed")
                context.data["verified_sandbox"] = record
            elif operation == "exec_command":
                expected = _expected_command_output(body["command_case"])
                if (
                    value.get("status") != "ok"
                    or value.get("exit_code") != body["expected_exit_code"]
                    or value.get("output") != expected
                ):
                    raise CampaignError("command correctness check failed")
            elif operation == "file_read":
                fixture = index if body["target_mode"] == "independent" else 0
                if not _read_matches(
                    value,
                    context.data["paths"][fixture],
                    context.data["contents"][fixture],
                ):
                    raise CampaignError("file read correctness check failed")
            elif operation == "file_write":
                fixture = index if body["target_mode"] == "independent" else 0
                if (
                    value.get("type") not in {"create", "update"}
                    or value.get("path") != context.data["paths"][fixture]
                    or value.get("bytes_written") != body["content_bytes"]
                ):
                    raise CampaignError("file write response check failed")
            elif operation == "file_edit":
                fixture = index if body["target_mode"] == "independent" else 0
                if (
                    value.get("type") != "edit"
                    or value.get("path") != context.data["paths"][fixture]
                    or value.get("edits_applied") != body["replacement_count"]
                    or value.get("replacements")
                    != context.data["expected_replacements"][index]
                    or value.get("bytes_written") != body["file_bytes"]
                ):
                    raise CampaignError("file edit response check failed")
            elif operation == "file_blame":
                if not _blame_matches(
                    value,
                    context.data["path"],
                    body["line_count"],
                    context.data["expected_blame_ranges"],
                ):
                    raise CampaignError("file blame correctness check failed")
            elif operation == "create_workspace":
                if (
                    value.get("finalize_policy") != "no_op"
                    or value.get("network_profile") != body["network_profile"]
                    or not value.get("workspace_session_id")
                ):
                    raise CampaignError("workspace readiness check failed")
        if operation in {"file_write", "file_edit"}:
            expected = (
                context.data.get("request_contents")
                if operation == "file_write"
                else context.data["expected"]
            )
            await _gather_complete(
                [
                    self._verify_mutation_contents(
                        product, cell, context, trial_id, timeout, expected
                    ),
                    self._verify_mutation_attribution(
                        product, cell, context, trial_id, timeout
                    ),
                ],
                "mutation correctness verification",
            )
            context.data["observed_sha256"] = _sha_text("\n".join(expected))
        if operation == "squash_layerstack":
            self._verify_squash_response(responses[0].value, context, sessions)
            for index, path in enumerate(context.data["paths"]):
                observed = await product.file_read(
                    context.sandbox,
                    session_id=None,
                    path=path,
                    offset=1,
                    limit=1,
                    timeout_ms=timeout,
                    request_id=f"{trial_id}.verify.layer.{index}",
                )
                if not _read_matches(
                    observed.value, path, context.data["contents"][index]
                ):
                    raise CampaignError("squash content equivalence check failed")
            context.data["content_equivalent"] = True

    async def _read_exact(
        self,
        product: ProductAccess,
        sandbox: str,
        *,
        session_id: str | None,
        path: str,
        expected_bytes: int,
        timeout_ms: int,
        request_id: str,
    ) -> str:
        if not 1 <= expected_bytes <= 4 * 1024 * 1024:
            raise CampaignError("verification read exceeds its fixed bound")
        page_limit = 2000

        async def read_page(page: int, offset: int) -> Any:
            return await product.file_read(
                sandbox,
                session_id=session_id,
                path=path,
                offset=offset,
                limit=page_limit,
                timeout_ms=timeout_ms,
                request_id=f"{request_id}.{page}",
            )

        first = await read_page(0, 1)
        first_value = first.value
        if not isinstance(first_value, dict):
            raise CampaignError("verification read response is invalid")
        total_lines = first_value.get("total_lines")
        if not isinstance(total_lines, int) or total_lines < 1:
            raise CampaignError("verification read page contract failed")
        page_count = (total_lines + page_limit - 1) // page_limit
        if not 1 <= page_count <= 64:
            raise CampaignError("verification read exceeded its page bound")
        offsets = [1 + page * page_limit for page in range(page_count)]
        responses = [first]
        if page_count > 1:
            responses.extend(
                await _gather_complete(
                    [read_page(page, offsets[page]) for page in range(1, page_count)],
                    "verification read pages",
                )
            )

        content_pages: list[str] = []
        for page, (offset, response) in enumerate(zip(offsets, responses, strict=True)):
            value = response.value
            if not isinstance(value, dict):
                raise CampaignError("verification read response is invalid")
            page_content = value.get("content")
            num_lines = value.get("num_lines")
            known_total_lines = value.get("total_lines")
            next_offset = value.get("next_offset")
            expected_num_lines = min(page_limit, total_lines - offset + 1)
            expected_next = (
                offset + expected_num_lines if page + 1 < page_count else None
            )
            page_valid = (
                value.get("path") == path
                and value.get("start_line") == offset
                and isinstance(page_content, str)
                and num_lines == expected_num_lines
                and known_total_lines == total_lines
                and value.get("bytes_read") == len(page_content.encode())
                and value.get("total_bytes") == expected_bytes
                and next_offset == expected_next
                and value.get("truncated") == (expected_next is not None)
            )
            if not page_valid:
                raise CampaignError("verification read page contract failed")
            content_pages.append(page_content)
        content = "\n".join(content_pages)
        if len(content.encode()) != expected_bytes:
            raise CampaignError("verification read completion contract failed")
        return content

    async def _verify_mutation_contents(
        self,
        product: ProductAccess,
        cell: dict[str, Any],
        context: TrialContext,
        trial_id: str,
        timeout_ms: int,
        expected: list[str],
    ) -> None:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        operation_session = context.data.get("operation_session")
        session_id = (
            operation_session.session_id
            if operation_session is not None
            else context.sessions[0].session_id
            if context.sessions
            else None
        )
        paths = context.data["paths"]
        if body["target_mode"] == "independent" and len(paths) > 1:
            observed_contents = await _gather_complete(
                [
                    self._read_exact(
                        product,
                        context.sandbox,
                        session_id=session_id,
                        path=path,
                        expected_bytes=(
                            body["content_bytes"]
                            if operation == "file_write"
                            else body["file_bytes"]
                        ),
                        timeout_ms=timeout_ms,
                        request_id=f"{trial_id}.verify.{index}",
                    )
                    for index, path in enumerate(paths)
                ],
                "independent content verification",
            )
        else:
            observed_contents = [
                await self._read_exact(
                    product,
                    context.sandbox,
                    session_id=session_id,
                    path=path,
                    expected_bytes=(
                        body["content_bytes"]
                        if operation == "file_write"
                        else body["file_bytes"]
                    ),
                    timeout_ms=timeout_ms,
                    request_id=f"{trial_id}.verify.{index}",
                )
                for index, path in enumerate(paths)
            ]
        for index, observed in enumerate(observed_contents):
            allowed = (
                expected if body["target_mode"] == "same_target" else [expected[index]]
            )
            if observed not in allowed:
                raise CampaignError(f"{operation} content verification failed")

    async def _verify_mutation_attribution(
        self,
        product: ProductAccess,
        cell: dict[str, Any],
        context: TrialContext,
        trial_id: str,
        timeout_ms: int,
    ) -> None:
        operation = cell["operation"]["operation"]
        body = cell["operation"]["cell"]
        paths = context.data["paths"]
        if body["destination"] == "session":
            if body["target_mode"] == "independent" and len(paths) > 1:
                snapshots = await _gather_complete(
                    [
                        self._read_exact(
                            product,
                            context.sandbox,
                            session_id=None,
                            path=path,
                            expected_bytes=(
                                body["content_bytes"]
                                if operation == "file_write"
                                else body["file_bytes"]
                            ),
                            timeout_ms=timeout_ms,
                            request_id=f"{trial_id}.verify.snapshot.{index}",
                        )
                        for index, path in enumerate(paths)
                    ],
                    "independent snapshot verification",
                )
            else:
                snapshots = [
                    await self._read_exact(
                        product,
                        context.sandbox,
                        session_id=None,
                        path=path,
                        expected_bytes=(
                            body["content_bytes"]
                            if operation == "file_write"
                            else body["file_bytes"]
                        ),
                        timeout_ms=timeout_ms,
                        request_id=f"{trial_id}.verify.snapshot.{index}",
                    )
                    for index, path in enumerate(paths)
                ]
            for index, snapshot in enumerate(snapshots):
                if snapshot != context.data["before"][index]:
                    raise CampaignError(
                        "session mutation escaped into the published snapshot"
                    )
            context.data["attributed_layer_count"] = 0
            return

        operation_ids = context.data.get("operation_request_ids") or [
            f"{trial_id}.request.{index}"
            for index in range(body["concurrent_requests"])
        ]
        if body["target_mode"] == "independent" and len(paths) > 1:
            blame_responses = await _gather_complete(
                [
                    product.file_blame(
                        context.sandbox,
                        path=path,
                        timeout_ms=timeout_ms,
                        request_id=f"{trial_id}.verify.blame.{index}",
                    )
                    for index, path in enumerate(paths)
                ],
                "independent attribution verification",
            )
        else:
            blame_responses = [
                await product.file_blame(
                    context.sandbox,
                    path=path,
                    timeout_ms=timeout_ms,
                    request_id=f"{trial_id}.verify.blame.{index}",
                )
                for index, path in enumerate(paths)
            ]
        for index, (path, response) in enumerate(
            zip(paths, blame_responses, strict=True)
        ):
            value = response.value
            if not isinstance(value, dict) or value.get("path") != path:
                raise CampaignError("publish mutation attribution response is invalid")
            ranges = value.get("ranges")
            if not isinstance(ranges, list) or not ranges:
                raise CampaignError("publish mutation has no ownership attribution")
            request_indices = (
                [index]
                if body["target_mode"] == "independent"
                else list(range(body["concurrent_requests"]))
            )
            mutation_owners = {
                f"operation:{operation_ids[request_index]}"
                for request_index in request_indices
            }
            baseline_owner = f"operation:{context.data['baseline_request_ids'][index]}"
            owners = {item.get("owner") for item in ranges if isinstance(item, dict)}
            if not owners.intersection(mutation_owners) or not owners.issubset(
                mutation_owners | {baseline_owner}
            ):
                raise CampaignError("publish mutation attribution check failed")
        context.data["attributed_layer_count"] = len(operation_ids)

    def _verify_squash_response(
        self, value: Any, context: TrialContext, sessions: SessionLifecycle
    ) -> None:
        if (
            not isinstance(value, dict)
            or not set(value).issubset(
                {
                    "manifest_version",
                    "squashed_blocks",
                    "swept_sessions",
                    "faulty_sessions",
                }
            )
            or type(value.get("manifest_version")) is not int
            or value["manifest_version"] <= 0
        ):
            raise CampaignError("squash response schema is invalid")
        blocks = value.get("squashed_blocks")
        swept = value.get("swept_sessions")
        if not isinstance(blocks, list) or not blocks or not isinstance(swept, list):
            raise CampaignError("squash response topology is invalid")
        source_layer_ids: list[str] = []
        squashed_layer_ids: set[str] = set()
        for block in blocks:
            if not isinstance(block, dict) or not set(block).issubset(
                {
                    "squashed_layer_id",
                    "replaced_layer_ids",
                    "replaced_layers",
                    "blocked_reasons",
                }
            ):
                raise CampaignError("squash block schema is invalid")
            squashed_id = block.get("squashed_layer_id")
            replaced = block.get("replaced_layer_ids")
            disposition = block.get("replaced_layers")
            reasons = block.get("blocked_reasons")
            if (
                not isinstance(squashed_id, str)
                or not squashed_id
                or squashed_id in squashed_layer_ids
                or not isinstance(replaced, list)
                or not replaced
                or any(not isinstance(item, str) or not item for item in replaced)
                or disposition not in {"reclaimed", "leased"}
                or (disposition == "reclaimed" and reasons is not None)
                or (
                    disposition == "leased"
                    and (
                        not isinstance(reasons, list)
                        or not reasons
                        or any(
                            not isinstance(reason, str) or not reason
                            for reason in reasons
                        )
                    )
                )
            ):
                raise CampaignError("squash block values are invalid")
            squashed_layer_ids.add(squashed_id)
            source_layer_ids.extend(replaced)
        if len(source_layer_ids) != len(
            set(source_layer_ids)
        ) or squashed_layer_ids.intersection(source_layer_ids):
            raise CampaignError("squash layer identities are inconsistent")
        expected = {session.session_id: session for session in context.sessions}
        observed: set[str] = set()
        dispositions: Counter[str] = Counter()
        faulty_details: dict[str, str] = {}
        for item in swept:
            if (
                not isinstance(item, dict)
                or not set(item).issubset(
                    {"session_id", "disposition", "reason", "class_detail"}
                )
                or item.get("session_id") not in expected
                or item.get("disposition")
                not in {"migrated", "identity", "leased", "faulty", "session_gone"}
            ):
                raise CampaignError("squash session disposition is invalid")
            session_id = item["session_id"]
            if session_id in observed:
                raise CampaignError("squash session disposition is duplicated")
            observed.add(session_id)
            disposition = item["disposition"]
            reason = item.get("reason")
            class_detail = item.get("class_detail")
            fields_valid = (
                reason is None and class_detail is None
                if disposition in {"migrated", "identity", "session_gone"}
                else isinstance(reason, str) and bool(reason) and class_detail is None
                if disposition == "leased"
                else reason is None
                and isinstance(class_detail, str)
                and bool(class_detail)
            )
            if not fields_valid:
                raise CampaignError("squash session disposition fields are invalid")
            dispositions[disposition] += 1
            if disposition == "faulty":
                faulty_details[session_id] = class_detail
            if disposition in {"faulty", "session_gone"}:
                session = expected[session_id]
                sessions.retire_product_destroyed(session)
                context.sessions.remove(session)
        if observed != set(expected):
            raise CampaignError("squash did not account for every live session")
        response_faulty: dict[str, str] = {}
        faulty = value.get("faulty_sessions")
        if faulty is not None:
            if not isinstance(faulty, list) or not faulty:
                raise CampaignError("squash faulty session summary is invalid")
            for item in faulty:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"session_id", "class_detail", "lease_errors"}
                    or not isinstance(item.get("session_id"), str)
                    or not item["session_id"]
                    or not isinstance(item.get("class_detail"), str)
                    or not item["class_detail"]
                    or not isinstance(item.get("lease_errors"), list)
                    or any(
                        not isinstance(error, str) or not error
                        for error in item["lease_errors"]
                    )
                    or item["session_id"] in response_faulty
                ):
                    raise CampaignError("squash faulty session summary is invalid")
                response_faulty[item["session_id"]] = item["class_detail"]
        if response_faulty != faulty_details:
            raise CampaignError(
                "squash faulty session summary disagrees with dispositions"
            )
        body = context.data["squash_cell"]
        expected_replaced = body["squashable_blocks"] * body["layers_per_block"]
        if (
            len(blocks) != body["squashable_blocks"]
            or any(
                len(block["replaced_layer_ids"]) != body["layers_per_block"]
                for block in blocks
            )
            or len(source_layer_ids) != expected_replaced
        ):
            raise CampaignError("squash manifest reduction shape is invalid")
        if dispositions["migrated"] != context.data["eligible_sessions"]:
            raise CampaignError(
                "squash migration count does not match the requested ratio"
            )
        context.data.update(
            expected_remount_spans=dispositions["migrated"],
            dispositions={
                name: dispositions[name]
                for name in ("migrated", "identity", "leased", "faulty", "session_gone")
            },
            source_layer_ids=source_layer_ids,
            observed_squashed_block_count=len(blocks),
        )

    async def _teardown_trial(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        context: TrialContext,
        trial_id: str,
    ) -> None:
        issues: list[BaseException] = []
        owned_sessions = list(reversed(context.sessions))
        if (
            context.data.get("operation_id") == "create_workspace"
            and len(owned_sessions) > 1
        ):
            destroyed = await asyncio.gather(
                *(
                    sessions.destroy(
                        session,
                        request_id=f"{trial_id}.session.destroy.{index}",
                    )
                    for index, session in enumerate(owned_sessions)
                ),
                return_exceptions=True,
            )
            issues.extend(
                result for result in destroyed if isinstance(result, BaseException)
            )
        else:
            for index, session in enumerate(owned_sessions):
                try:
                    await sessions.destroy(
                        session,
                        request_id=f"{trial_id}.session.destroy.{index}",
                    )
                except BaseException as error:
                    issues.append(error)
        if context.destroy_sandbox:
            try:
                await product.destroy_sandbox(
                    context.sandbox, request_id=f"{trial_id}.sandbox.destroy"
                )
            except BaseException as error:
                issues.append(error)
        if issues:
            raise BaseExceptionGroup("aggregated trial cleanup", issues)

    async def _teardown_cell(
        self,
        product: ProductAccess,
        sessions: SessionLifecycle,
        context: CellContext | None,
        cell_id: str,
    ) -> None:
        if context is None:
            return
        issues: list[BaseException] = []
        for index, session in enumerate(reversed(context.sessions)):
            try:
                await sessions.destroy(
                    session, request_id=f"cell-{cell_id[-16:]}.session.destroy.{index}"
                )
            except BaseException as error:
                issues.append(error)
        if context.sandbox:
            try:
                await product.destroy_sandbox(
                    context.sandbox,
                    request_id=f"cell-{cell_id[-16:]}.sandbox.destroy",
                )
            except BaseException as error:
                issues.append(error)
        if issues:
            raise BaseExceptionGroup("aggregated cell cleanup", issues)

    def _check_cancelled(self) -> None:
        if self._cancel.is_set():
            raise asyncio.CancelledError

    def _new_workspace(self, run_path: Path, name: str, cell: dict[str, Any]) -> Path:
        workspace = _new_workspace(run_path, name)
        profile_id = cell["operation"]["cell"].get("workspace_profile")
        if profile_id is not None:
            try:
                profile = self._profiles[profile_id]
            except KeyError as error:
                raise CampaignError(
                    "cell selected an unmaterialized workspace profile"
                ) from error
            materialize_workspace(self._roots.fixtures, workspace, profile, self._seed)
            workspace_manifest = workspace / "fixture-manifest.json"
            workspace_manifest.unlink()
        return workspace

    def _prepare_cell_workspaces(
        self, run_path: Path, cells: list[dict[str, Any]]
    ) -> None:
        if self._prepared_cell_workspaces:
            raise CampaignError("cell workspaces were already prepared")
        grouped: dict[str, list[tuple[str, Path]]] = {}
        for cell in cells:
            operation = cell["operation"]["operation"]
            isolation = None if operation == "create_sandbox" else _isolation(cell)
            if operation != "create_sandbox" and isolation not in {
                "reusable_verified_fixture",
                "prepared_sandbox_per_cell",
                "fresh_sessions_per_trial",
            }:
                continue
            profile_id = cell["operation"]["cell"].get("workspace_profile")
            if profile_id is None:
                continue
            cell_id = cell["cell_id"]
            workspace = _new_workspace(run_path, f"cell-{cell_id[-16:]}")
            grouped.setdefault(profile_id, []).append((cell_id, workspace))
        for profile_id, prepared in grouped.items():
            try:
                profile = self._profiles[profile_id]
            except KeyError as error:
                raise CampaignError(
                    "cell selected an unmaterialized workspace profile"
                ) from error
            workspaces = [workspace for _, workspace in prepared]
            materialize_workspaces(
                self._roots.fixtures,
                workspaces,
                profile,
                self._seed,
                max_workers=4,
            )
            for cell_id, workspace in prepared:
                (workspace / "fixture-manifest.json").unlink()
                self._prepared_cell_workspaces[cell_id] = workspace

    def _cell_workspace(self, run_path: Path, cell: dict[str, Any]) -> Path:
        prepared = self._prepared_cell_workspaces.get(cell["cell_id"])
        if prepared is not None:
            return prepared
        return self._new_workspace(run_path, f"cell-{cell['cell_id'][-16:]}", cell)

    def _begin_trial_journal(self) -> None:
        if any(
            buffer is not None
            for buffer in (
                self._trial_event_buffer,
                self._trial_observation_buffer,
                self._trial_event_sink_buffer,
            )
        ):
            raise CampaignError("trial journal transaction is already active")
        self._trial_event_buffer = []
        self._trial_observation_buffer = []
        self._trial_event_sink_buffer = []

    def _end_trial_journal(self) -> None:
        self._trial_event_buffer = None
        self._trial_observation_buffer = None
        self._trial_event_sink_buffer = None

    async def _flush_trial_journal(self, run_id: str) -> None:
        observations = getattr(self, "_trial_observation_buffer", None)
        events = getattr(self, "_trial_event_buffer", None)
        sink_events = getattr(self, "_trial_event_sink_buffer", None)
        if observations is None and events is None and sink_events is None:
            return
        if observations is None or events is None or sink_events is None:
            raise CampaignError("trial journal transaction is inconsistent")
        if observations:
            self._store.append_records(run_id, ArtifactId.OBSERVATIONS, observations)
            observations.clear()
        if events:
            self._store.append_records(run_id, ArtifactId.EVENTS, events)
            events.clear()
        if sink_events:
            committed = list(sink_events)
            sink_events.clear()
            if self._event_sink is not None:
                for record in committed:
                    await self._event_sink(record)

    async def _event(self, run_id: str, data: dict[str, Any]) -> None:
        force_durable = data.get("kind") == "run_state"
        if force_durable:
            await self._flush_trial_journal(run_id)
        if force_durable and self._manifest:
            self._manifest["state"] = data["state"]
            if data["state"] == "failed" and self._manifest.get("failure") is None:
                self._manifest["failure"] = {
                    "code": "campaign_failed",
                    "message": "campaign execution failed; inspect persisted events and logs",
                    "infrastructure": True,
                }
            self._store.replace_snapshot(
                run_id, ArtifactId.RUN_MANIFEST, self._manifest
            )
        self._event_sequence += 1
        record = {
            "sequence": self._event_sequence,
            "run_id": run_id,
            "monotonic_offset_ns": max(0, time.monotonic_ns() - self._started_ns)
            if self._started_ns
            else 0,
            "data": data,
        }
        if force_durable or getattr(self, "_trial_event_buffer", None) is None:
            self._store.append_record(run_id, ArtifactId.EVENTS, record)
            if self._event_sink is not None:
                await self._event_sink(record)
        else:
            self._trial_event_buffer.append(record)
            if self._event_sink is not None:
                assert self._trial_event_sink_buffer is not None
                self._trial_event_sink_buffer.append(record)

    def _new_manifest(
        self,
        run_id: str,
        plan: dict[str, Any],
        definitions: dict[str, Any],
        definition_sha256: str,
        environment: dict[str, Any],
        starting_preset: dict[str, Any] | None,
    ) -> dict[str, Any]:
        schemas = {
            artifact_id.value: {
                "schema_name": spec.schema_name,
                "write_version": spec.write_version,
                "read_versions": sorted(spec.read_versions),
            }
            for artifact_id, spec in ARTIFACT_SPECS.items()
            if artifact_id in PRODUCER_ARTIFACT_IDS and spec.schema_name is not None
        }
        gateway_policy = {
            "semantic_revision": 1,
            "mode": "isolated",
            "loopback_only": True,
            "isolated_runtime_per_execution_block": True,
            "remount_sweep_widths": sorted(
                {_block_width(block, plan) for block in plan["execution_blocks"]}
            ),
            "maximum_connections": 256,
            "readiness_timeout_ms": 60_000,
            "readiness_probe_timeout_ms": 2_000,
            "readiness_poll_interval_ms": 50,
        }
        if _is_v11_windows_named_pipe_treatment(environment):
            gateway_policy.update(
                {
                    "semantic_revision": 2,
                    "protocol_version": (
                        "ephemeral-sandbox-v1-practical-performance-v1.1"
                    ),
                    "transport": "windows_named_pipe",
                    "scope": "local_only",
                    "rotation": "per_execution_block",
                    "loopback_only": False,
                }
            )
        return {
            "schema_version": 2,
            "run_id": run_id,
            "name": plan["canonical_plan"]["name"],
            "plan_hash": plan["plan_hash"],
            "starting_preset": starting_preset,
            "configuration_scope": plan["canonical_plan"]["configuration_base"][
                "scope"
            ],
            "state": "planned",
            "failure": None,
            "created_at": self._started_at,
            "producer": {
                "implementation": "python",
                "implementation_version": "0.1.0",
                "source_commit": environment["treatment"]["source_commit"],
            },
            "treatment": environment["treatment"],
            "environment": environment,
            "artifact_schemas": schemas,
            "definition_snapshot": {
                "schema_name": "eos_benchmark_definition_snapshot",
                "schema_version": definitions["schema_version"],
                "sha256": definition_sha256,
            },
            "fixed_lifecycle_policy": plan["fixed_lifecycle_policy"],
            "gateway_policy": gateway_policy,
            "gateway_execution_blocks": [],
            "started_at": self._started_at,
            "ended_at": None,
            "correctness": "pending",
        }

    async def _trial_phase(
        self,
        run_id: str,
        cell_id: str,
        trial_id: str,
        warmup: bool,
        phase: str,
        state: str,
    ) -> None:
        await self._event(
            run_id,
            {
                "kind": "trial_phase",
                "cell_id": cell_id,
                "trial_id": trial_id,
                "warmup": warmup,
                "phase": phase,
                "state": state,
            },
        )

    async def _trial_state(
        self, run_id: str, cell_id: str, trial_id: str, warmup: bool, state: str
    ) -> None:
        await self._event(
            run_id,
            {
                "kind": "trial_state",
                "cell_id": cell_id,
                "trial_id": trial_id,
                "warmup": warmup,
                "state": state,
            },
        )

    async def _request_state(
        self,
        run_id: str,
        cell_id: str,
        trial_id: str,
        request_id: str,
        state: str,
    ) -> None:
        await self._event(
            run_id,
            {
                "kind": "request_state",
                "cell_id": cell_id,
                "trial_id": trial_id,
                "request_id": request_id,
                "state": state,
            },
        )

    async def _resource_observations(
        self, run_id: str, samples: list[dict[str, Any]]
    ) -> None:
        observations: list[dict[str, Any]] = []
        events: list[dict[str, Any]] = []
        for data in samples:
            self._observation_sequence += 1
            observations.append(
                {
                    "sequence": self._observation_sequence,
                    "record": {"record": "resource", "data": data},
                }
            )
            reading = data["reading"]
            value = reading["value"]
            available = value["availability"] == "available"
            self._event_sequence += 1
            events.append(
                {
                    "sequence": self._event_sequence,
                    "run_id": run_id,
                    "monotonic_offset_ns": reading["monotonic_offset_ns"],
                    "data": {
                        "kind": "resource_window",
                        "cell_id": data["cell_id"],
                        "trial_id": data["trial_id"],
                        "metric_id": reading["metric_id"],
                        "value": value["value"] if available else None,
                        "unavailable_reason": (None if available else value["reason"]),
                    },
                }
            )
        if getattr(self, "_trial_observation_buffer", None) is None:
            # Non-trial callers retain one append and fsync per journal.
            self._store.append_records(run_id, ArtifactId.OBSERVATIONS, observations)
            self._store.append_records(run_id, ArtifactId.EVENTS, events)
            if self._event_sink is not None:
                for record in events:
                    await self._event_sink(record)
        else:
            assert self._trial_event_buffer is not None
            self._trial_observation_buffer.extend(observations)
            self._trial_event_buffer.extend(events)
            if self._event_sink is not None:
                assert self._trial_event_sink_buffer is not None
                self._trial_event_sink_buffer.extend(events)

    def _observation(self, run_id: str, record: dict[str, Any]) -> None:
        self._observation_sequence += 1
        envelope = {"sequence": self._observation_sequence, "record": record}
        if getattr(self, "_trial_observation_buffer", None) is None:
            self._store.append_record(run_id, ArtifactId.OBSERVATIONS, envelope)
        else:
            self._trial_observation_buffer.append(envelope)

    async def _request_observation(
        self,
        run_id: str,
        cell: dict[str, Any],
        trial_id: str,
        warmup: bool,
        response: TimedGatewayResponse,
    ) -> None:
        self._observation(
            run_id,
            {
                "record": "request",
                "data": {
                    "operation_id": cell["operation"]["operation"],
                    "cell_id": cell["cell_id"],
                    "trial_id": trial_id,
                    "request_id": response.request_id,
                    "warmup": warmup,
                    "start_offset_ns": max(
                        0,
                        (response.started_ns - self._started_ns)
                        if response.started_ns is not None
                        else time.monotonic_ns()
                        - self._started_ns
                        - response.latency_ns,
                    ),
                    "latency_ns": response.latency_ns,
                    "response_bytes": response.response_bytes,
                    "response_sha256": response.response_sha256,
                    "status": "success",
                },
            },
        )

    async def _registered_check_observations(
        self,
        run_id: str,
        cell: dict[str, Any],
        trial_id: str,
        *,
        passed: bool,
        failure_stage: str | None,
    ) -> None:
        operation_id = cell["operation"]["operation"]
        operation = next(
            item
            for item in self._definitions["operations"]
            if item["id"] == operation_id
        )
        checks = operation["checks"]
        if not passed and failure_stage == "setup":
            return
        for check in checks:
            check_passed = passed
            if not passed and failure_stage == "cleanup":
                cleanup_ids = {
                    "command_lifecycle",
                    "mutation_attribution",
                    "workspace_registry_baseline",
                    "layerstack_residue",
                }
                if check["id"] not in cleanup_ids:
                    continue
            expected = check["help"]
            actual = "verified" if check_passed else f"failed during {failure_stage}"
            self._observation(
                run_id,
                {
                    "record": "check",
                    "data": {
                        "operation_id": operation_id,
                        "cell_id": cell["cell_id"],
                        "trial_id": trial_id,
                        "request_id": None,
                        "check_id": check["id"],
                        "semantic_revision": check["semantic_revision"],
                        "passed": check_passed,
                        "expected": expected,
                        "actual": actual,
                        "artifact_id": None,
                    },
                },
            )
            await self._event(
                run_id,
                {
                    "kind": "correctness",
                    "cell_id": cell["cell_id"],
                    "trial_id": trial_id,
                    "check_id": check["id"],
                    "passed": check_passed,
                    "expected": expected,
                    "actual": actual,
                    "artifact_id": None,
                },
            )

    async def _phase_observations(
        self,
        run_id: str,
        cell: dict[str, Any],
        trial_id: str,
        response: TimedGatewayResponse,
        product: ProductAccess,
        context: TrialContext,
    ) -> None:
        trace = await product.observe_trace(
            context.sandbox,
            target_request_id=response.request_id,
            request_id=f"{trial_id}.observe.trace",
        )
        operation = next(
            item
            for item in self._definitions["operations"]
            if item["id"] == cell["operation"]["operation"]
        )
        registered = {item["trace_span_name"]: item for item in operation["phases"]}
        request_start = max(
            0,
            (response.started_ns - self._started_ns)
            if response.started_ns is not None
            else time.monotonic_ns() - self._started_ns - response.latency_ns,
        )
        observed: dict[str, int] = {name: 0 for name in registered}
        failed: dict[str, int] = {name: 0 for name in registered}
        squash_node: Any | None = None
        commit_offset_ns: int | None = None

        def visit(nodes: list[Any]) -> None:
            nonlocal squash_node, commit_offset_ns
            for node in nodes:
                definition = registered.get(node.span.name)
                if definition is not None:
                    observed[node.span.name] += 1
                    if node.span.status != "completed":
                        failed[node.span.name] += 1
                    if node.span.name == "layerstack.squash":
                        squash_node = node
                    if node.span.name == "layerstack.squash.commit":
                        commit_offset_ns = request_start + round(
                            (node.offset_ms + node.span.dur_ms) * 1_000_000
                        )
                    self._observation(
                        run_id,
                        {
                            "record": "phase",
                            "data": {
                                "id": definition["id"],
                                "semantic_revision": definition["semantic_revision"],
                                "unit": definition["unit"],
                                "cell_id": cell["cell_id"],
                                "trial_id": trial_id,
                                "request_id": response.request_id,
                                "source": definition["source"],
                                "correlation": definition["correlation"],
                                "trace_span_name": definition["trace_span_name"],
                                "start_offset_ns": request_start
                                + round(node.offset_ms * 1_000_000),
                                "duration_ns": round(node.span.dur_ms * 1_000_000),
                                "status": {
                                    "completed": "succeeded",
                                    "error": "failed",
                                    "cancelled": "cancelled",
                                    "timed_out": "timed_out",
                                }[node.span.status],
                            },
                        },
                    )
                visit(node.children)

        visit(trace.spans)
        expected = {
            name: (
                context.data.get("expected_remount_spans", 0)
                if name == "workspace_session.remount"
                else 1
            )
            for name in registered
        }
        if observed != expected:
            raise CampaignError(
                f"product trace squash phase cardinality mismatch: expected {expected}, "
                f"observed {observed}"
            )
        if any(failed.values()):
            raise CampaignError(
                f"product trace contains failed squash phases: {failed}"
            )
        if squash_node is None or commit_offset_ns is None:
            raise CampaignError("product trace omitted squash evidence boundaries")
        attrs = squash_node.span.attrs
        value = response.value
        if (
            attrs.get("manifest_version") != value.get("manifest_version")
            or attrs.get("blocks") != len(value.get("squashed_blocks", []))
            or attrs.get("swept") != len(value.get("swept_sessions", []))
            or attrs.get("sweep_width")
            != cell["operation"]["cell"]["remount_parallelism"]
        ):
            raise CampaignError(
                "product squash trace attributes disagree with the response"
            )
        s2 = _trace_layerstack_evidence(attrs, commit_offset_ns, sampled=False)
        if s2["manifest_version"]["value"] != value["manifest_version"]:
            raise CampaignError(
                "product squash trace manifest identity is inconsistent"
            )
        context.data["s2_post_commit"] = s2
        context.data["s1_sampled_peak"] = _sampled_peak(context.data["s0_baseline"], s2)

        settled, settled_offset = await self._settle_layerstack(
            product, context, trial_id
        )
        if (
            settled.manifest_version != value["manifest_version"]
            or settled.root_hash != s2["root_hash"]["value"]
            or len(settled.layers) != s2["active_layer_count"]["value"]
        ):
            raise CampaignError("settled layerstack disagrees with the commit trace")
        context.data["s3_view"] = settled
        context.data["s3_settled"] = _layerstack_evidence(
            settled, settled_offset, sampled=False
        )

    async def _settle_layerstack(
        self,
        product: ProductAccess,
        context: TrialContext,
        trial_id: str,
    ) -> tuple[Any, int]:
        deadline = time.monotonic() + 5.0
        previous: str | None = None
        matches = 0
        sample = None
        sample_offset = 0
        poll = 0
        while time.monotonic() < deadline:
            self._check_cancelled()
            sample = await product.observe_layerstack(
                context.sandbox,
                request_id=f"{trial_id}.observe.layerstack.s3.{poll}",
            )
            sample_offset = max(0, time.monotonic_ns() - self._started_ns)
            signature = json.dumps(
                sample.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            matches = matches + 1 if signature == previous else 1
            if matches == 3:
                return sample, sample_offset
            previous = signature
            poll += 1
            await asyncio.sleep(0.1)
        raise CampaignError(
            "layerstack did not reach an exact three-sample quiet window"
        )

    async def _shielded_cleanup(self, cleanup: Awaitable[None]) -> None:
        task = asyncio.create_task(cleanup)
        started = time.monotonic()
        try:
            await asyncio.wait_for(
                asyncio.shield(task), timeout=self._CLEANUP_TIMEOUT_SECONDS
            )
        except asyncio.CancelledError as cancellation:
            remaining = max(
                0.0,
                self._CLEANUP_TIMEOUT_SECONDS - (time.monotonic() - started),
            )
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=remaining)
            except BaseException as cleanup_error:
                if not task.done():
                    task.cancel()
                raise BaseExceptionGroup(
                    "cancellation and cleanup both failed",
                    [cancellation, cleanup_error],
                )
            raise
        except BaseException:
            if not task.done():
                task.cancel()
                try:
                    await task
                except BaseException:
                    pass
            raise

    async def _trial_observation(
        self,
        run_id: str,
        cell: dict[str, Any],
        trial_id: str,
        warmup: bool,
        sequence_in_cell: int,
        outcome: TrialOutcome,
    ) -> None:
        reportable = (
            not warmup
            and outcome.status == "success"
            and outcome.product_succeeded
            and outcome.checks_passed
            and not outcome.infrastructure_failed
            and outcome.cleanup_baseline_restored
        )
        self._observation(
            run_id,
            {
                "record": "trial",
                "data": {
                    "operation_id": cell["operation"]["operation"],
                    "cell_id": cell["cell_id"],
                    "trial_id": trial_id,
                    "warmup": warmup,
                    "kind": "warmup" if warmup else "measured",
                    "sequence_in_cell": sequence_in_cell,
                    "reportable": reportable,
                    "latency_ns": outcome.batch_makespan_ns or None,
                    "request_count": len(outcome.responses),
                    "status": outcome.status,
                    "product_succeeded": outcome.product_succeeded,
                    "infrastructure_failed": outcome.infrastructure_failed,
                    "cleanup_baseline_restored": outcome.cleanup_baseline_restored,
                    "checks_passed": outcome.checks_passed,
                    "setup_ns": outcome.setup_ns,
                    "operation_ns": outcome.operation_ns,
                    "verify_ns": outcome.verify_ns,
                    "teardown_ns": outcome.teardown_ns,
                    "artifacts": [outcome.artifact]
                    if outcome.artifact is not None
                    else [],
                },
            },
        )


def _operation_evidence(
    cell: dict[str, Any],
    responses: list[TimedGatewayResponse],
    context: TrialContext,
) -> dict[str, Any]:
    operation = cell["operation"]["operation"]
    body = cell["operation"]["cell"]
    values = [response.value for response in responses]
    if operation == "exec_command":
        output = values[0].get("output", "")
        detail = {
            "command_case": body["command_case"],
            "template_revision": 1,
            "command_sha256": _sha_text(body["command"]),
            "exit_code": values[0].get("exit_code"),
            "stdout": _content_summary(output),
            "stderr": _content_summary(""),
        }
    elif operation == "create_sandbox":
        created = context.data["created_sandbox"]
        verified = context.data["verified_sandbox"]
        detail = {
            "workspace_profile": body["workspace_profile"],
            "network_profile": body["network_profile"],
            "sandbox_id": created.id,
            "create_state": created.state,
            "verified_state": verified.state,
            "workspace_root": str(context.workspace),
            "ready": verified.state == "ready",
        }
    elif operation == "file_read":
        content = context.data["contents"][0]
        detail = {
            "requested_bytes": body["returned_bytes"],
            "returned_bytes": len(content.encode()),
            "returned_lines": content.count("\n") + 1,
            "content_sha256": _sha_text(content),
        }
    elif operation == "file_write":
        content = context.data["request_contents"][0]
        detail = {
            "requested_bytes": body["content_bytes"],
            "observed_bytes": len(content.encode()),
            "expected_sha256": _sha_text(content),
            "observed_sha256": _sha_text(content),
            "attribution": "workspace_session"
            if body["destination"] == "session"
            else "published_layer",
            "attributed_layer_count": context.data["attributed_layer_count"],
        }
    elif operation == "file_edit":
        detail = {
            "file_bytes": body["file_bytes"],
            "match_density": body["match_density"],
            "requested_replacements": body["replacement_count"],
            "applied_replacements": values[0].get("edits_applied"),
            "before_sha256": _sha_text("\n".join(context.data["before"])),
            "expected_sha256": _sha_text("\n".join(context.data["expected"])),
            "observed_sha256": context.data["observed_sha256"],
            "attribution": "workspace_session"
            if body["destination"] == "session"
            else "published_layer",
            "attributed_layer_count": context.data["attributed_layer_count"],
        }
    elif operation == "file_blame":
        ranges = values[0].get("ranges", [])
        detail = {
            "line_count": body["line_count"],
            "ownership_segments": body["ownership_segments"],
            "returned_range_count": len(ranges),
            "covered_lines": sum(
                item.get("line_count", 0) for item in ranges if isinstance(item, dict)
            ),
        }
    elif operation == "create_workspace":
        detail = {
            "requested_count": body["workspace_count"],
            "created_count": len(values),
            "ready_count": len(values),
            "network_profile_matches": sum(
                value.get("network_profile") == body["network_profile"]
                for value in values
            ),
        }
    elif operation == "squash_layerstack":
        source_ids = context.data["source_layer_ids"]
        baseline_layers = {
            layer.layer_id: layer for layer in context.data["s0_view"].layers
        }
        if any(layer_id not in baseline_layers for layer_id in source_ids):
            raise CampaignError("squash response references a layer absent from S0")
        settled_ids = {layer.layer_id for layer in context.data["s3_view"].layers}
        retained = [layer_id for layer_id in source_ids if layer_id in settled_ids]
        allocations = [
            {
                "layer_id": layer_id,
                "logical_bytes": _optional_available(
                    baseline_layers[layer_id].bytes,
                    "product_observability.layerstack",
                    "layer bytes unavailable",
                ),
                "allocated_bytes": _optional_available(
                    baseline_layers[layer_id].allocated_bytes,
                    "product_observability.layerstack",
                    "layer allocated_bytes unavailable",
                ),
            }
            for layer_id in source_ids
        ]
        reclaimed_layers = [
            baseline_layers[layer_id]
            for layer_id in source_ids
            if layer_id not in settled_ids
        ]
        if any(layer.allocated_bytes is None for layer in reclaimed_layers):
            reclaimed_bytes = _unavailable(
                "product_observability.layerstack",
                "one or more reclaimed source allocations are unavailable",
            )
        else:
            reclaimed_bytes = _available(
                sum(layer.allocated_bytes or 0 for layer in reclaimed_layers)
            )
        baseline = context.data["s0_view"]
        settled = context.data["s3_view"]
        manifest_reduced = settled.manifest_version > baseline.manifest_version and len(
            settled.layers
        ) < len(baseline.layers)
        if not manifest_reduced:
            raise CampaignError("squash did not produce a reduced settled manifest")
        detail = {
            "requested_live_sessions": body["live_sessions"],
            "observed_migrated_sessions": context.data["dispositions"]["migrated"],
            "observed_non_migrated_sessions": body["live_sessions"]
            - context.data["dispositions"]["migrated"],
            "dispositions": context.data["dispositions"],
            "effective_remount_parallelism": body["remount_parallelism"],
            "observed_squashed_block_count": context.data[
                "observed_squashed_block_count"
            ],
            "observed_replaced_layer_count": len(source_ids),
            "source_layer_ids": source_ids,
            "retained_source_layer_ids": retained,
            "source_layer_allocations": allocations,
            "reclaimed_bytes": reclaimed_bytes,
            "s0_baseline": context.data["s0_baseline"],
            "s1_sampled_peak": context.data["s1_sampled_peak"],
            "s2_post_commit": context.data["s2_post_commit"],
            "s3_settled": context.data["s3_settled"],
            "manifest_reduced": manifest_reduced,
            "content_equivalent": context.data.get("content_equivalent") is True,
            "usable_session_count": len(context.sessions),
        }
    else:  # pragma: no cover - closed by planning and _operate
        raise CampaignError(f"operation {operation} has no evidence contract")
    result = {"operation": operation, "evidence": detail}
    transport = [
        response.transport_evidence
        for response in responses
        if response.transport_evidence is not None
    ]
    if transport:
        if len(transport) != len(responses):
            raise CampaignError("operation mixed product transport cohorts")
        result["transport"] = transport
    return result


def _content_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        raise CampaignError("command output is not text")
    return {
        "byte_count": len(value.encode()),
        "truncated": False,
        "sha256": _sha_text(value),
    }


def _available(value: Any) -> dict[str, Any]:
    return {"availability": "available", "value": value}


def _unavailable(source: str, reason: str) -> dict[str, Any]:
    return {"availability": "unavailable", "source": source, "reason": reason}


def _optional_available(value: Any, source: str, reason: str) -> dict[str, Any]:
    return _available(value) if value is not None else _unavailable(source, reason)


def _layerstack_evidence(view: Any, offset_ns: int, *, sampled: bool) -> dict[str, Any]:
    source = "product_observability.layerstack"
    return {
        "monotonic_offset_ns": _available(offset_ns),
        "sampled": sampled,
        "manifest_version": _available(view.manifest_version),
        "root_hash": _available(view.root_hash),
        "active_layer_count": _available(len(view.layers)),
        "active_lease_count": _available(view.active_lease_count),
        "active_logical_bytes": _optional_available(
            view.total_bytes, source, "total_bytes unavailable"
        ),
        "active_allocated_bytes": _optional_available(
            view.total_allocated_bytes, source, "total_allocated_bytes unavailable"
        ),
        "storage_logical_bytes": _optional_available(
            view.storage_logical_bytes, source, "storage_logical_bytes unavailable"
        ),
        "storage_allocated_bytes": _optional_available(
            view.storage_allocated_bytes, source, "storage_allocated_bytes unavailable"
        ),
        "staging_entry_count": _optional_available(
            view.staging_entry_count, source, "staging_entry_count unavailable"
        ),
    }


def _trace_layerstack_evidence(
    attrs: dict[str, Any], offset_ns: int, *, sampled: bool
) -> dict[str, Any]:
    mandatory = {
        "manifest_version": attrs.get("manifest_version"),
        "root_hash": attrs.get("s2_root_hash"),
        "active_layer_count": attrs.get("s2_layer_count"),
    }
    if (
        type(mandatory["manifest_version"]) is not int
        or mandatory["manifest_version"] < 0
        or not isinstance(mandatory["root_hash"], str)
        or not mandatory["root_hash"]
        or type(mandatory["active_layer_count"]) is not int
        or mandatory["active_layer_count"] < 0
    ):
        raise CampaignError("product squash trace is missing its S2 identity")
    source = "product_observability.trace"

    def optional(attribute: str) -> dict[str, Any]:
        if attribute not in attrs:
            return _unavailable(source, f"trace attribute {attribute} unavailable")
        value = attrs[attribute]
        if type(value) is int and value >= 0:
            return _available(value)
        raise CampaignError(f"product squash trace attribute {attribute} is invalid")

    return {
        "monotonic_offset_ns": _available(offset_ns),
        "sampled": sampled,
        "manifest_version": _available(mandatory["manifest_version"]),
        "root_hash": _available(mandatory["root_hash"]),
        "active_layer_count": _available(mandatory["active_layer_count"]),
        "active_lease_count": _unavailable(
            source, "active lease count is not emitted at the commit boundary"
        ),
        "active_logical_bytes": optional("s2_active_logical_bytes"),
        "active_allocated_bytes": optional("s2_active_allocated_bytes"),
        "storage_logical_bytes": optional("s2_storage_logical_bytes"),
        "storage_allocated_bytes": optional("s2_storage_allocated_bytes"),
        "staging_entry_count": optional("s2_staging_entry_count"),
    }


def _sampled_peak(
    baseline: dict[str, Any], post_commit: dict[str, Any]
) -> dict[str, Any]:
    def score(snapshot: dict[str, Any]) -> tuple[int, int, int, int]:
        values = []
        for name in (
            "storage_allocated_bytes",
            "storage_logical_bytes",
            "active_allocated_bytes",
            "active_logical_bytes",
        ):
            item = snapshot[name]
            values.append(item["value"] if item["availability"] == "available" else -1)
        return tuple(values)  # type: ignore[return-value]

    selected = baseline if score(baseline) >= score(post_commit) else post_commit
    result = json.loads(json.dumps(selected))
    result["sampled"] = True
    return result


def _sha_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _validated_response_end_ns(
    responses: list[TimedGatewayResponse], *, fallback: int | None
) -> int:
    ended = [
        response.started_ns + response.latency_ns
        for response in responses
        if response.started_ns is not None
    ]
    if len(ended) == len(responses) and ended:
        return max(ended)
    if fallback is None:
        raise CampaignError("request batch did not record a validated completion")
    return fallback


def _expected_command_output(command_case: str) -> str:
    if command_case == "fixture_read":
        # The released command API returns a line-window projection. Its
        # `output` joins logical lines without retaining their delimiters.
        return "4096"
    if command_case == "output64_kib":
        return "x" * 65536
    return ""


def _required_string(value: dict[str, Any], *path: str) -> str:
    current: Any = value
    for component in path:
        if not isinstance(current, dict):
            raise CampaignError(f"expanded plan is missing {'.'.join(path)}")
        current = current.get(component)
    if not isinstance(current, str) or not current:
        raise CampaignError(f"expanded plan is missing {'.'.join(path)}")
    return current


def _isolation(cell: dict[str, Any]) -> str:
    try:
        comparison = cell["comparison_key"]["isolation"]
        resolved = cell["operation"]["cell"]["resolved_isolation"]
    except (KeyError, TypeError) as error:
        raise CampaignError(
            "expanded cell is missing its isolation contract"
        ) from error
    if not isinstance(comparison, str) or comparison != resolved:
        raise CampaignError("expanded cell isolation authorities disagree")
    return comparison


def _new_workspace(run_path: Path, name: str) -> Path:
    workspace = run_path / name
    workspace.mkdir(mode=0o700)
    return workspace


def _content(length: int, seed: str) -> str:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return (digest * ((length + len(digest) - 1) // len(digest)))[:length]


def _multiline_content(length: int, seed: str) -> str:
    value = bytearray(_content(length, seed).encode())
    for index in range(126, max(0, len(value) - 1), 127):
        value[index] = 10
    return value.decode()


def _edits(seed: str, request: int, count: int) -> list[dict[str, Any]]:
    return [
        {
            "old_string": hashlib.sha256(
                f"old:{seed}:{request}:{index}".encode()
            ).hexdigest(),
            "new_string": hashlib.sha256(
                f"new:{seed}:{request}:{index}".encode()
            ).hexdigest(),
            "replace_all": True,
        }
        for index in range(count)
    ]


def _edit_content(
    length: int, density: float, edits: list[dict[str, Any]]
) -> tuple[str, str, dict[str, int]]:
    if not edits or not 0 <= density <= 1:
        raise CampaignError("edit fixture factors are invalid")
    width = len(edits[0]["old_string"])
    slots = (length + 1) // (width + 1)
    if slots < len(edits):
        raise CampaignError("edit fixture cannot place every requested replacement")
    matched = int(slots * density)
    if matched < len(edits):
        raise CampaignError("edit density cannot place every requested replacement")
    counts: dict[str, int] = {}
    rows: list[str] = []
    for index in range(slots):
        if index < matched:
            old = edits[index % len(edits)]["old_string"]
            counts[old] = counts.get(old, 0) + 1
            rows.append(old)
        else:
            rows.append("~" * width)
    before = "\n".join(rows)
    before += "~" * (length - len(before))
    expected = before
    for edit in edits:
        expected = expected.replace(edit["old_string"], edit["new_string"])
    return before, expected, counts


def _blame_content(lines: int, segments: int, event: int) -> str:
    base, remainder = divmod(lines, segments)
    output: list[str] = []
    line = 0
    for segment in range(segments):
        for _ in range(base + (segment < remainder)):
            output.append(f"{'A' if segment % 2 == 0 else 'B'}|{event:08x}|{line:08x}")
            line += 1
    return "\n".join(output)


def _read_matches(value: Any, path: str, content: str) -> bool:
    return (
        isinstance(value, dict)
        and value.get("path") == path
        and value.get("content") == content
        and value.get("bytes_read") == len(content.encode())
    )


def _expected_blame_ranges(
    lines: int, segments: int, event_request_ids: list[str]
) -> list[dict[str, Any]]:
    if len(event_request_ids) < 1 or (segments > 1 and len(event_request_ids) < 2):
        raise CampaignError("blame audit fixture has insufficient events")
    final_owner = f"operation:{event_request_ids[-1]}"
    previous_owner = (
        final_owner if segments == 1 else f"operation:{event_request_ids[-2]}"
    )
    base, remainder = divmod(lines, segments)
    start_line = 1
    ranges: list[dict[str, Any]] = []
    for segment in range(segments):
        line_count = base + (segment < remainder)
        ranges.append(
            {
                "start_line": start_line,
                "line_count": line_count,
                "owner": final_owner if segment % 2 == 0 else previous_owner,
            }
        )
        start_line += line_count
    return ranges


def _blame_matches(
    value: Any, path: str, lines: int, expected_ranges: list[dict[str, Any]]
) -> bool:
    if (
        not isinstance(value, dict)
        or value.get("path") != path
        or not isinstance(value.get("ranges"), list)
    ):
        return False
    next_line = 1
    for item in value["ranges"]:
        if (
            not isinstance(item, dict)
            or item.get("start_line") != next_line
            or not isinstance(item.get("line_count"), int)
            or item["line_count"] <= 0
            or not isinstance(item.get("owner"), str)
        ):
            return False
        next_line += item["line_count"]
    return next_line == lines + 1 and value["ranges"] == expected_ranges


def _event_family(family: str) -> str:
    return {
        "sandbox_lifecycle": "sandbox_lifecycle",
        "command": "command",
        "files": "files",
        "workspace_lifecycle": "workspace_lifecycle",
        "layer_stack": "layerstack",
    }[family]


def _gateway_log_summary(records: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for stream in ("stdout", "stderr"):
        lines = [
            record.text
            for record in records
            if getattr(record, "stream", None) == stream
            and isinstance(getattr(record, "text", None), str)
        ]
        payload = "\n".join(lines).encode()
        parts.extend(
            (
                f"{stream}_lines={len(lines)}",
                f"{stream}_bytes={len(payload)}",
                f"{stream}_sha256=sha256:{hashlib.sha256(payload).hexdigest()}",
                f"{stream}_truncated={str('[LOG CAP REACHED]' in lines).lower()}",
            )
        )
    return "gateway logs retained as redacted digests: " + ",".join(parts)


def _is_v11_windows_named_pipe_treatment(
    environment: dict[str, Any],
) -> bool:
    return (
        environment.get("client_cohort") == "product_cli"
        and environment.get("gateway_endpoint_identity")
        == "isolated_windows_named_pipe_per_execution_block"
        and environment.get("gateway_transport")
        == {
            "transport": "windows_named_pipe",
            "scope": "local_only",
            "rotation": "per_execution_block",
        }
    )


def _block_width(block: dict[str, Any], plan: dict[str, Any]) -> int:
    if block["family_id"] != "layer_stack":
        return 1
    cell = next(
        item for item in plan["cells"] if item["cell_id"] == block["cell_ids"][0]
    )
    return cell["operation"]["cell"]["remount_parallelism"]


def _combine_failures(
    current: BaseException | None, added: BaseException, label: str
) -> BaseException:
    if current is None:
        error = CampaignError(f"{label} failed")
        error.__cause__ = added
        return error
    error = CampaignError(f"campaign trial and {label} both failed")
    error.__cause__ = BaseExceptionGroup(label, [current, added])
    return error


async def _gather_complete(awaitables: list[Awaitable[Any]], label: str) -> list[Any]:
    results = await asyncio.gather(*awaitables, return_exceptions=True)
    cancellation = next(
        (result for result in results if isinstance(result, asyncio.CancelledError)),
        None,
    )
    if cancellation is not None:
        raise cancellation
    errors = [result for result in results if isinstance(result, BaseException)]
    if errors:
        raise BaseExceptionGroup(label, errors)
    return results


def _trial_status(failure: BaseException | None, stage: str) -> str:
    if failure is None:
        return "success"
    if isinstance(failure, asyncio.CancelledError):
        return "cancelled"
    if stage == "cleanup":
        return "cleanup_invalid"
    if stage == "verify":
        return "correctness_failed"
    if stage == "operation" and isinstance(failure, GatewayProductError):
        return "product_failed"
    return "infrastructure_failed"
