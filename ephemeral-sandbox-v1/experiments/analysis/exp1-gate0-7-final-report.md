# EXP1 CLI-only performance campaign: final Gate 0–7 report

Report date: 2026-07-31.

Protocol: `ephemeral-sandbox-v1-practical-performance-v1.0`.

Execution-progress estimate: 88%. Implementation, qualification, freeze, the
single final attempt, failure preservation, diagnosis, cleanup, and evidence
handoff are complete. Scientific completion is not 88% successful: the final
corpus is ineligible, so the campaign has no paper-eligible performance result.

## Gate decisions

| Gate | Phase | Decision | Evidence |
|---|---|---:|---|
| Gate 0 | Audit and protocol review | PASS | Cross-links, configuration, operation ownership, timing boundaries, correctness, resource policy, and table schemas were reconciled before live work. |
| Gate 1 | Native-Windows `product_cli` implementation | PASS | Offline implementation/tests passed; final expansion is exactly 19 cells, 1,938 batches, and 5,610 product requests with no `direct_client` fallback. |
| Gate 2 | CLI integration smoke | PASS | Run `019fb6c5-dab0-7958-b7ba-94f2a9eda944` completed all 19 cells with zero failures/warnings and clean teardown. |
| Gate 3 | Five-sample exploratory pilot | PASS | Run `019fb6cf-6021-76d5-ab4f-c6ed53e1d293` completed all 19 cells; central/envelope projections were 1,170.818322650/1,307.100411100 seconds, both below the author-approved 1,400-second limit. These are qualification values, not manuscript results. |
| Gate 4 | Protocol/source/treatment freeze | PASS | Paper commit `eb10c26d1bfd632772baf1bc331c985d0231f52d`, product commit `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`, annotated product tag object `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`, exact plan, package, image, fixture, schema, metrics, exclusions, seed, and analysis identities were frozen. |
| Gate 5 | Sole frozen final | FAIL | Run `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4` stopped after 853/1,938 batches. A required post-response snapshot connection failed; therefore the failed cell and all remaining cells lack 100 reportable trials. |
| Gate 6 | Deterministic final aggregation | FAIL | Protocol forbids aggregation of a partial failed final. No final tables or numeric-evidence v2 record were generated. |
| Gate 7 | Numeric paper handoff | FAIL | There is no eligible numeric selector or recomputable final aggregate to place in LaTeX. Failure provenance and safe/unsafe wording were handed off instead. |

## Frozen identities

- Paper source commit:
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`
  (`feat(benchmark): freeze EXP1 CLI protocol v1.0`).
- Product commit:
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`
  (`perf(docker): reuse executor and compress daemon archive`), clean direct
  local `main`.
- Annotated product tag: `paper-v1-freeze`; tag object
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`; peeled commit
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`.
- Frozen paper-source content tree:
  `sha256:1efeff548dd664580dcb452829d86e1ae114477828a1af65589b7e34cc311b67`.
- Freeze record:
  `experiments/analysis/exp1-freeze-record-eb10c26-0392b299.json`,
  `sha256:38608c306476ce19cd63f1e42808aaa45cd030e3e160a88dd6defd1189aa3429`.
- Final plan:
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`;
  seed 20260712; two warmups and 100 measured trials; 19 cells; 1,938
  batches; 5,610 product requests; `product_cli` and `paper-100m` only.
- Windows candidate ZIP:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-0392b299.zip`;
  5,685,130 bytes;
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`.
- No commit or tag was pushed.

## Code and documentation changed

Product commit `0392b299` contains the following exact paths:

```text
Cargo.lock
Cargo.toml
crates/sandbox-provider-docker/Cargo.toml
crates/sandbox-provider-docker/src/archive.rs
crates/sandbox-provider-docker/src/engine.rs
crates/sandbox-provider-docker/src/installer.rs
crates/sandbox-provider-docker/tests/archive.rs
crates/sandbox-provider-docker/tests/runtime.rs
```

Paper freeze commit `eb10c26` contains the following exact paths:

```text
ephemeral-sandbox-v1/benchmark/PAPER_ARTIFACT.md
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/artifacts.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/catalog.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/derivation.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/fixtures.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/gateway.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/metadata.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/models.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/observability.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/paths.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/planning.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/product.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/product_cli.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/recovery.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/resource_sampling.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/runner.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/safety.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/service.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/sessions.py
ephemeral-sandbox-v1/benchmark/backend/benchmark_lab/transport.py
ephemeral-sandbox-v1/benchmark/backend/tests/compatibility/test_artifacts.py
ephemeral-sandbox-v1/benchmark/backend/tests/compatibility/test_reports.py
ephemeral-sandbox-v1/benchmark/backend/tests/conftest.py
ephemeral-sandbox-v1/benchmark/backend/tests/contract/test_api.py
ephemeral-sandbox-v1/benchmark/backend/tests/contract/test_catalog.py
ephemeral-sandbox-v1/benchmark/backend/tests/contract/test_planning.py
ephemeral-sandbox-v1/benchmark/backend/tests/contract/test_zero_rust_guard.py
ephemeral-sandbox-v1/benchmark/backend/tests/integration/test_gateway_lifecycle.py
ephemeral-sandbox-v1/benchmark/backend/tests/integration/test_recovery.py
ephemeral-sandbox-v1/benchmark/backend/tests/integration/test_runner.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_derivation.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_exp1_archive.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_exp1_runtime_projection.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_fixtures.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_metadata.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_observability.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_product_cli.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_resource_sampling.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_runner_command.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_runner_squash.py
ephemeral-sandbox-v1/benchmark/backend/tests/unit/test_safety.py
ephemeral-sandbox-v1/benchmark/defaults/definition-catalog.json
ephemeral-sandbox-v1/benchmark/presets/paper-env-smoke.yml
ephemeral-sandbox-v1/benchmark/presets/paper-good-pass.yml
ephemeral-sandbox-v1/benchmark/presets/paper-pilot.yml
ephemeral-sandbox-v1/benchmark/tests/fixtures/golden/artifacts/operation-evidence-v1-squash.json
ephemeral-sandbox-v1/benchmark/uv.lock
ephemeral-sandbox-v1/benchmark/web/src/api/types.ts
ephemeral-sandbox-v1/benchmark/web/src/components/DefaultPlanLauncher.tsx
ephemeral-sandbox-v1/benchmark/web/tests/unit/plan-workflow.test.tsx
ephemeral-sandbox-v1/experiment_inventory.md
ephemeral-sandbox-v1/experiments/analysis/scripts/generate_exp1_tables.py
ephemeral-sandbox-v1/experiments/analysis/tests/test_generate_exp1_tables.py
ephemeral-sandbox-v1/experiments/expected_tables.md
ephemeral-sandbox-v1/experiments/experiment_log.md
ephemeral-sandbox-v1/experiments/scripts/archive_exp1_run.py
ephemeral-sandbox-v1/experiments/scripts/capture_exp1_baseline.py
ephemeral-sandbox-v1/experiments/scripts/probe_exp1_windows_cli_content_file.py
ephemeral-sandbox-v1/experiments/scripts/probe_exp1_windows_cli_payload.py
ephemeral-sandbox-v1/experiments/scripts/project_exp1_final_runtime.py
ephemeral-sandbox-v1/plan/task-packets/exp0-focused-performance-protocol.md
ephemeral-sandbox-v1/plan/task-packets/exp1-cli-performance-campaign.md
```

Post-run evidence and tracker updates, intentionally outside the immutable
freeze commit, are:

```text
ephemeral-sandbox-v1/benchmark/PAPER_ARTIFACT.md
ephemeral-sandbox-v1/claim_evidence_map.md
ephemeral-sandbox-v1/experiment_inventory.md
ephemeral-sandbox-v1/experiments/analysis/exp1-final-failure-diagnostic.json
ephemeral-sandbox-v1/experiments/analysis/exp1-final-handoff.md
ephemeral-sandbox-v1/experiments/analysis/exp1-final-system-event-4227.json
ephemeral-sandbox-v1/experiments/analysis/exp1-gate0-7-final-report.md
ephemeral-sandbox-v1/experiments/experiment_log.md
ephemeral-sandbox-v1/paper_state.json
ephemeral-sandbox-v1/plan/progress.md
ephemeral-sandbox-v1/progress.md
```

Run archives, captures, caches, and temporary diagnostics were preserved
outside the scoped source/evidence commits unless explicitly listed above.

## Tests and material commands

The append-only experiment log records every validation attempt, including
corrected command mistakes. Material terminal results are:

| Command or command class | Exit/status |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1; .\.venv\Scripts\python.exe -m pytest .\benchmark\backend\tests -q` | Exit 0: 277 passed, five expected Windows symlink-privilege skips. |
| Focused resource, runner, and projection pytest selection | Exit 0: 55 passed. |
| Cached Ruff 0.16.1 scoped format/import checks | Exit 0 after mechanical line-ending/import correction. |
| Paper scoped `git diff --check` | Exit 0. |
| `cargo test -p sandbox-provider-docker` | Exit 0: 17 passed, one live-Docker test ignored. |
| `cargo fmt --all -- --check` | Exit 0. |
| Provider all-target Clippy with warnings denied | Exit 0. |
| `cargo check -p sandbox-gateway` | Exit 0. |
| Windows release packaging script with explicit `-ExecutionPolicy Bypass -File` | Exit 0. The first policy-blocked launch did not execute. |
| Fresh `benchmark_lab validate` for smoke, pilot, and final presets | Exit 0 with empty stderr and zero findings/warnings. |
| Smoke benchmark/wrapper, archive creation, independent verify-only, and cleanup | Exit 0; terminal run `completed`. |
| Pilot benchmark/wrapper, archive creation, independent verify-only, cleanup, two table generations, and two structural projections | Exit 0; terminal run `completed`; repeated outputs byte-identical. |
| Paper source commit and annotated product tag creation/peel verification | Exit 0. |
| Final benchmark process/wrapper | Process exit 0, but the preserved run manifest is terminal `failed`; process exit is not a Gate-5 pass. |
| First final archive attempt | Nonzero: cleanup proof correctly rejected the still-present owned run workspace. |
| Explicit exact-run cleanup | Exit 0, `cleaned: true`; runtime and run workspace absent afterward. |
| Second final archive creation and independent verify-only invocation | Exit 0 with identical archive identity. |
| Post-run JSON parsing and scoped diff checks | Exit 0 after four Markdown trailing-space defects were corrected. |
| Read-only `Get-WinEvent` capture for System/Tcpip event 4227, record 88385 | Exit 0; primary post-run capture preserved without modifying the run archive. |

Other recorded non-result attempts include an accidental one-second pytest
runner timeout, unavailable venv-local Ruff, broad pre-existing lint/style
findings, one malformed PowerShell tag-peel expression, one mismatched orphan
projection filename, and an unavailable static `SHA256.HashData` method. Each
was corrected or bounded; none consumed an extra live final attempt or changed
the frozen treatment.

## Runs and absolute artifact paths

| Disposition | Run ID | Absolute archive path | Archive content tree |
|---|---|---|---|
| Smoke, qualification only | `019fb6c5-dab0-7958-b7ba-94f2a9eda944` | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb6c5-dab0-7958-b7ba-94f2a9eda944` | `sha256:3ad6e3aba681cfdf257939df79a0561a5b73b710a73d46686146bc5780fe8a6b` |
| Pilot, exploratory only | `019fb6cf-6021-76d5-ab4f-c6ed53e1d293` | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb6cf-6021-76d5-ab4f-c6ed53e1d293` | `sha256:f81cf711bbb734f04201c7fdc09652e0d59c7cbdecd50fe3676370b1df77b93c` |
| Final, failed/ineligible | `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4` | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb6e5-c00b-7b02-8a3c-d76bd1346eb4` | `sha256:7efa643b12aba09f0ba5ecfbed5b5692a166a5c12931490402d3992d92f3ae6a` |

Final archive details:

- 24,867 files; 620,311,242 bytes.
- Archive manifest:
  `sha256:5e0a3c4f7c864df8070a668d2f373b75bece3c2a57cc4340cd89ece292cc7927`.
- Campaign manifest:
  `sha256:8eefbec9772406943bb1baa2476b181c7436a6fafd7a6d7984874e8889f96982`.
- Raw subtree: 24,841 files; 547,911,783 bytes;
  `sha256:1cc85e7883136ede15e342aa6f2ac50d72bdf6d4eace340dc0e6dba9e992f5b5`.
- Independent verify output:
  `sha256:13b4b44f9a6f2e8835fd85b81d73de0bba7a65ac0eb7c110a57ad21168f43630`.
- Generated final tables: unavailable by protocol; none were generated and
  therefore no table hash exists.

## Failure, partial evidence, exclusions, and unavailable fields

The final started at `2026-07-31T06:39:01.112787Z` and terminalized at
`2026-07-31T06:50:13.449078Z`, after 672.336291 seconds. It reached 853 of
1,938 trial batches and 2,077 of 5,610 product requests. These counts describe
completion/failure provenance only, not performance.

Measured file-read trial
`trial-242749a59d59cc16-measured-000034` had a successful product request, but
its mandatory post-response observability snapshot could not connect.
Invocation
`trial-242749a59d59cc16-measured-000034.observe.snapshot.1.boundary.0`
returned WSAEADDRINUSE 10048 and failed response validation as a transport
connection error. The trial retained one of two required resource boundaries,
was classified `infrastructure_failed`, and is not reportable.

The independently captured Windows System/Tcpip event 4227, record 88385, at
`2026-07-31T06:50:09.9652511Z` states that the selected local endpoint had
recently been used for the same remote endpoint and identifies high-rate
connection open/close churn as the typical cause. The primary capture is
`experiments/analysis/exp1-final-system-event-4227.json`,
`sha256:b6eac476b6ecf8c20de529be5c5ca8de297874ae9273c65a4baaf6ffc34ac89d`.
It was captured read-only after the run and is not represented as an
in-run artifact.

The archive has 7,992 committed CLI invocation records and one additional
incomplete raw cgroup projection group with valid stdout and empty stderr but
no metadata commit marker. The group is consistent with a concurrent sibling
finishing while the snapshot exception unwound the boundary, but the exact
persistence race is not logged and is not claimed as proven.

Smoke and pilot data are permanently excluded from manuscript tables. All
partial-final latency, throughput, tail-latency, resource, I/O, storage, and
scaling aggregates are excluded. Expected Windows allocated-byte values and
unreported LayerStack fields remain explicitly unavailable rather than zero.

Cleanup restored the exact baseline: the benchmark runtime and owned run
workspace are absent, no matching benchmark process remains, the protected
gateway PID 62980 remains running, the pre-existing exited container and five
pre-existing volumes remain, and the product checkout is clean direct `main`
at `0392b299`.

## Supported claim wording

- “EXP1 v1.0 did not produce a paper-eligible final performance result.”
- “The frozen native-Windows `product_cli` smoke and five-sample pilot
  completed, but both remain qualification/exploratory evidence.”
- “The sole final attempt stopped during a required resource observation
  after the measured file-read request itself succeeded.”
- “The failed snapshot connection recorded WSAEADDRINUSE 10048; a
  contemporaneous post-run-captured TCP/IP Event 4227 attributes the host
  condition to local-endpoint reuse under high-rate connection churn.”
- “The failed corpus and cleanup proof were preserved and independently
  verified.”

## Wording that remains unsafe

- Any latency, throughput, p99, RSS, CPU, I/O, storage, or scaling number from
  the smoke, pilot, or failed partial final.
- Any claim that Ephemeral Sandbox is fast, scales, is cheap, beats a baseline,
  or has broader superiority.
- Any claim that the file-read product operation failed, returned incorrect
  content, or that the gateway globally died.
- Any claim that all 16,384 dynamic ports were simultaneously occupied, that
  Windows has a universal ceiling at the observed invocation count, or that an
  exact TIME_WAIT/port-occupancy mechanism was captured.
- Any implication that preserving the failed corpus makes it eligible.

## Remaining blocker and next external action

The sole frozen v1.0 final is permanently failed/ineligible, and the protocol
prohibits relaunching or replacing it. Gates 5–7 cannot be recovered inside
v1.0.

The single next external action is an author decision authorizing a new EXP1
protocol version after selecting a scientifically acceptable connection-churn
remedy; that decision must require a new source/environment freeze and a new
explicitly authorized final attempt while preserving this failed archive.
