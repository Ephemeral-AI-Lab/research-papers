# Ephemeral Sandbox v1 claim-evidence map

**Scope date:** 2026-08-02. Source claims are revalidated against measured
product commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8` and tag
`paper-v1.1-freeze`. Quantitative claims are bound to final EXP1 v1.1 numeric
evidence only.

## Evidence classes

- **Source:** visible in the measured source snapshot.
- **Contract-tested:** interface test existence; not empirical correctness.
- **Final RQ3:** one numeric-evidence v2 selector from the immutable archive.
- **Limitation:** intentionally not claimed as a measured result.

## Retained contributions

| ID | Claim | Evidence | Allowed wording and boundary |
|---|---|---|---|
| C1 | Leased LayerStack workspaces provide private overlay views; sessionless `exec_command` uses an implicit session and explicit sessions retain selected multi-call private state. | Source: workspace/layer/session paths at `5c48dae`; prior tests are contract/correctness-test context only. | Describe implementation, not measured isolation, security, or every-operation behavior. Sessionless file paths are different. |
| C2 | Capture and current-head reconciliation implement source-defined candidate handling, bounded eligible text merge, whole-candidate rejection, and active-manifest data visibility. | Source: capture, publish plan/resolve/merge, layer writer at `5c48dae`. | `Atomic` applies only to resolved data visibility, not semantic validity, audit, accounting, cleanup, or every crash model. |
| C3 | The public interface contains 8 management, 10 runtime, and 8 observability operations. | Regenerated [`cli_contract_matrix.md`](cli_contract_matrix.md), measured projection sources, and contract tests. | All three clients support optional validated request IDs; Windows default is local named pipe, with TCP compatibility. This is not a security boundary. |
| C4 | Lifecycle distinguishes retryable precommit failure, discard, no-op, committed publication, and published-but-not-closed cleanup failure. | Source: session finalization/publish paths at `5c48dae`. | Do not claim automatic crash recovery, consistent post-commit attribution, or tested restart semantics. |
| C5 | EXP1 v1.1 describes startup, public-CLI operations, and seven resource rows for one treatment. | Final archive plus 153 selector-bound entries in `experiments/analysis/final-v11-019fb86c-tables-a/numeric-evidence.json`. | Descriptive only; not comparative, causal, reliable-in-general, or useful-work evidence. |

## Eligible quantitative claims

| ID | Sentence family | Numeric evidence binding | Boundary |
|---|---|---|---|
| E1 | Sandbox create plus base mount had the Table 2 p50/p95/p99 values in the tested environment. | `table2.create_sandbox.none.c1.{p50_ms,p95_ms,p99_ms}` | Native Windows/Docker Desktop, pinned image, `paper-100m`, `product_cli`, concurrency 1. |
| E2 | A public CLI row had the Table 3 p50/p95/p99 and mean throughput values for its fixed payload and concurrency. | `table3.*` selectors used by deterministic table source | Throughput change is not individual-latency improvement, linear scaling, or superiority. |
| E3 | Table 4 reports available sampled resource metrics for seven preregistered rows. | `table4.*` selectors | `upperdir_bytes` is not unavailable host workspace allocated blocks; unavailable values remain unavailable. |
| E4 | The sole final completed 1,900/1,900 reportable measured trials without a classified campaign failure. | campaign/report provenance recorded in final handoff; numerical table claims remain selector-bound | Campaign completeness only, not product-wide reliability. |

## Explicit limitations and removed claims

| Area | Status |
|---|---|
| RQ1 private-view/isolation correctness | No eligible final empirical matrix; source and test existence are not results. |
| RQ2 publication, fault, and semantic correctness | No eligible paper-platform fault matrix; source protocol only. |
| RQ4 competitive baseline, deeper scaling, useful work, productivity | Not measured; removed from Results and framing. |
| RQ5 attribution and restart recovery | Best-effort post-commit attribution and in-memory lease/restart gap remain limitations. |
| Security, egress, rollback, serializability | Out of scope. |
| Reflink/LayerStack 2.0 | Future work; recorded Windows `FICLONE errno=95` feasibility result is narrow and non-performance evidence. |
| Merge resource bound | The 8 MiB input gate does not independently bound line/edit-distance trace memory. |

## Mandatory wording guards

- Never pool v1.0, qualifier, smoke, pilot, projection, setup, verification,
  teardown, partial, simulated, or unavailable values with final results.
- Never imply that a source link or test implies observed correctness.
- Never claim broad speed, scalability, superiority, production readiness,
  security, or multi-agent productivity.
- Retain the local named-pipe change as preregistered treatment remediation and
  disclose the Table-1 analysis compatibility erratum as numeric-neutral.
