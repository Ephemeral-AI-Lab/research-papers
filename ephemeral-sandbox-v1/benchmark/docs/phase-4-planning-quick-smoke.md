# Phase 4 deterministic planning and Quick Smoke

Status: complete.

## Files changed

- `backend/benchmark_lab/planning.py`: strict preset/profile loading, deterministic Cartesian expansion and seeded block order, stable cell/plan identities, catalog and safety admission, bounded estimates, and cross-factor validation including blame and squash topology constraints.
- `backend/benchmark_lab/runner.py`: the sole sequential campaign scheduler, isolated family gateway lifecycle, explicit setup/operation/verification/teardown timing, bounded cancellation, shielded cleanup, seven operation implementations, strict product response verification, observations, bounded evidence, and terminal report generation.
- `backend/benchmark_lab/fixtures.py`, `observability.py`, `product.py`, and `derivation.py`: deterministic fixtures, strict public cgroup/snapshot/layerstack/trace readers, authenticated product-access methods, and report derivation for trials, resources, phases, lifecycle timing, correlations, and factor studies.
- `backend/tests/contract/test_planning.py`, `backend/tests/integration/test_runner.py`, and `backend/tests/unit/test_runner_*.py`, `test_observability.py`, and `test_derivation.py`: deterministic/golden planning, lifecycle failure attribution, cancellation at every phase, fixture and response correctness, squash S0–S3 evidence, trace cardinality, and report derivation.
- `presets/*.yml`, `defaults/standard-local.yml`, and `defaults/workspace-profiles/*.yml`: migrated plan inputs and deterministic fixture profiles.

## Behavior and safety results

Plan expansion is deterministic and rejects unknown operations, duplicate factors, invalid controls, missing catalog operations, unsafe image references, out-of-range values, impossible blame shapes, and squash topologies that cannot form requested session boundaries or exceed 4,096 prepared layers. The scheduler is the only runner; pytest verifies it but never schedules campaigns.

All operation latency comes from the authenticated raw JSONL transport's `time.monotonic_ns()` boundary. Setup, resource sampling, correctness verification, phase extraction, evidence/report writes, and cleanup have separate lifecycle durations and are excluded. A measured trial is reportable only when the product succeeds, every registered check passes, infrastructure remains healthy, and cleanup restores the baseline. Infrastructure and cleanup failures retain independent attribution and may overlap.

The squash implementation prepares deterministic layer blocks and live-session boundaries, checks an exact deny-unknown response schema, accounts for every disposition and faulty-session detail, requires exact block width and trace phase/remount cardinality, derives S0 baseline/S1 sampled peak/S2 commit/S3 three-sample settled evidence, verifies content equivalence and manifest reduction, and retains source-allocation/reclamation evidence.

Cancellation is rejected before request admission and is covered during setup, operation, verification, and teardown. Teardown remains shielded and bounded; a cancellation arriving during successful teardown keeps cleanup proof while preventing a successful trial. Recovery covers every nonterminal manifest transition and treats only absent disposable paths as safe without a marker.

## Commands and results

- Focused planning, recovery, runner, squash, and zero-Rust gate: 44 passed in 1.13 seconds.
- Complete offline backend suite before live proof: 115 passed in 36.22 seconds.
- Product-trace compatibility correction gate: 20 passed in 0.89 seconds.
- Final complete offline backend suite after the trace correction: 117 passed in 36.55 seconds.
- Individually retained live Docker proofs: `exec_command`, `file_read`, `file_write`, `file_edit`, `file_blame`, `create_workspace`, squash with zero sessions, and squash with one migrated live session all completed with correctness pass.
- Combined live run `live-quick-smoke-slice-v6`: completed with correctness pass; 8 cells, 8 measured/reportable trials, 16 issued product requests, 8 bounded evidence artifacts, and 2 squash trials with content equivalence and manifest reduction.
- Combined-run cleanup proof: both `.benchmark-state/runs/live-quick-smoke-slice-v6` and `.benchmark-state/runtime/live-quick-smoke-slice-v6` are absent; no benchmark gateway or daemon process remains.

The first combined attempt, `live-quick-smoke-slice-v5`, failed read-only on a current product root trace that omitted its nullable `parent` field. Pydantic had made `str | None` required because it lacked a default. `TraceSpan.parent` and `TraceEvent.parent` now default to `None`; tree validation still rejects explicit wrong parents. The failed corpus and retained run workspace remain as evidence under `.benchmark-state`.

## Gaps and deviations

No migration-spec deviation. Phase 4 proves the backend runner and Quick Smoke slice, but it does not claim the service/web gate or final full Quick Smoke campaign. FastAPI/SSE and React/Vitest/Playwright belong to Phase 5; final parity, live cancellation/failure/recovery proof, commit, and destructive product cutover remain Phase 6 gates.
