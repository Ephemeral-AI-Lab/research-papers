# Paper-local benchmark artifact

This directory is the paper-local, runnable benchmark implementation used by
the Ephemeral Sandbox paper. EXP1 protocol v1.0 was frozen at paper commit
`eb10c26d1bfd632772baf1bc331c985d0231f52d`; the measured product is anchored
by annotated `paper-v1-freeze` tag object
`0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`. The sole final attempt failed and
is ineligible, so this freeze supports provenance but no final performance
claim.

Completed v1.1 work is governed by
[`../experiments/exp1-v1.1-protocol-amendment.md`](../experiments/exp1-v1.1-protocol-amendment.md).
It retains one fresh native CLI subprocess per measured request but replaces
loopback TCP with one isolated Windows named pipe per gateway execution block.
The v1.1 product is clean direct `main` commit
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`, annotated tag object
`834c84534359f37653fb25ac45304091e82c37a6`. Qualification, smoke, pilot,
projection, measurement freeze, sole final, immutable archival, deterministic
analysis, and numeric handoff passed. Final run
`019fb86c-096e-7589-a0a4-a6d6ef5d7f8b` is archive-derived into
`../experiments/analysis/final-v11-019fb86c-tables-a`; its exact identities and
post-freeze Table-1 reader compatibility erratum are in the
[`final Gate report`](../experiments/analysis/exp1-gate0-7-final-report.md).

## Provenance

- Upstream repository: `Ephemeral-AI-Lab/ephemeral-sandbox-test`
- Imported subtree: `benchmark/`
- Upstream commit: `d45618733c8bfe75466947fdb9c47bea67f74b78`
- Import date: 2026-07-30
- Import verification: all 171 upstream files matched by SHA-256 immediately
  after copying

Paper-local additions that are not present in the imported upstream subtree:

- `PAPER_ARTIFACT.md` records the complete paper-local delta and the qualified
  execution shape.
- `defaults/workspace-profiles/paper-100m.yml` defines the fixed 100 MiB,
  4,000-file, depth-100 paper workspace.
- `presets/paper-env-smoke.yml`, `presets/paper-pilot.yml`, and
  `presets/paper-good-pass.yml` define the 19-cell CLI-only smoke, exploratory
  pilot, and final matrices.
- `backend/benchmark_lab/product_cli.py` is the native manager/runtime/
  observability CLI subprocess adapter, including end-to-end timing, exact
  executable selection, response validation, cancellation/timeout reaping,
  pre-staged content-file transfer, canonical `--gateway-endpoint` routing,
  redacted argv, and retained stdout/stderr metadata.
- `backend/benchmark_lab/ipc_qualification.py` implements the preregistered
  qualification-only 25,000-invocation native manager-CLI gate, including
  fixed identity bindings, Windows event/TCP/process sampling, fail-closed
  lifecycle evidence, and deterministic summary/manifest output.
- `backend/tests/conftest.py` supplies a fail-closed Windows symlink helper
  which skips only WinError 1314.
- `backend/tests/unit/test_product_cli.py` covers argument vectors, token
  redaction, executable routing, JSON and product errors, stderr, timeout,
  cancellation, timing, concurrency, canonical endpoint routing, and raw CLI
  evidence.
- `backend/tests/unit/test_ipc_qualification.py` covers the fixed qualifier
  workload, response and identity gates, sampling cadence, exact resource
  bounds, TCP/event failures, manifest retention, cleanup, and CLI exit status.
- `tests/fixtures/golden/artifacts/operation-evidence-v1-squash.json` is the
  explicit frozen schema-v1 squash evidence fixture used for compatibility
  checks.

Paper-local modifications to imported upstream files, including the active
v1.1 prequalification worktree delta, are complete as follows:

- `backend/benchmark_lab/artifacts.py` adds content-addressed, colon-free,
  bounded evidence v2 storage, durable batch journal appends, and retained
  schema-v1 corpus reads.
- `backend/benchmark_lab/catalog.py` validates Windows `.exe` identities and
  falls back from an unavailable catalog exporter to reviewed released-CLI
  help probes.
- `backend/benchmark_lab/cli.py` exposes the fail-closed
  `qualify-exp1-ipc` command and returns a nonzero status for a failed gate.
- `backend/benchmark_lab/derivation.py` raises the derivation revision and
  records the CLI subprocess timing boundary, executable/evidence provenance,
  and unavailable-metric reasons required by numeric evidence v2.
- `backend/benchmark_lab/fixtures.py` admits depth 100, uses extended-length
  native Windows paths and binary-mode low-level writes, validates the cached
  fixture tree and reparse/plain-entry identity before reuse, and materializes
  independent native Windows copies through bounded multithreaded Robocopy
  with a validated Python fallback while preserving fixed fixture bytes and
  identity.
- `backend/benchmark_lab/gateway.py` stages native Windows configuration,
  launches isolated released gateways, performs readiness through the manager
  CLI for `product_cli`, scopes readiness request IDs by gateway instance,
  assigns one unique named-pipe endpoint per v1.1 execution block, preserves
  endpoint ownership evidence, passes arbitrary tokens with parser-safe equals
  syntax, fails fast on deterministic product rejection, and cleans long owned
  paths.
- `backend/benchmark_lab/metadata.py` records native Windows host, product
  source, image, daemon, gateway, three CLI executable identities, and the
  protocol-visible gateway transport/scope/rotation identity.
- `backend/benchmark_lab/models.py` admits the canonical `product_cli` cohort.
- `backend/benchmark_lab/observability.py` validates daemon self-metric
  responses used by resource sampling.
- `backend/benchmark_lab/paths.py` resolves the paper-local source and staged
  native Windows binary layout safely.
- `backend/benchmark_lab/planning.py` validates paper-only `product_cli`,
  expands the distinct manager-CLI sandbox-create/base-mount cell, applies
  `paper-100m` to every cell, derives exact batch/request counts, and persists
  the seeded cell permutation for each sequential family execution block.
- `backend/benchmark_lab/product.py` exposes the product-observability and
  lifecycle protocol used interchangeably by direct test doubles and the CLI
  adapter.
- `backend/benchmark_lab/resource_sampling.py` launches daemon, cgroup,
  snapshot, filesystem, process, and host-volume collection on fixed 100 ms
  deadlines, permits at most one expensive collection in flight to bound
  measurement-induced load, records every missed deadline as explicit
  unavailability with scheduled and observed collection start/completion
  offsets, and defers ordered durable persistence to the trial boundary.
- `backend/benchmark_lab/runner.py` routes all paper operations, verification,
  observability, and cleanup through `product_cli`; measures batch makespan
  from the admitted-task barrier release through the maximum validated CLI
  response end while excluding evidence persistence; commits setup,
  waiting-at-barrier, and all-tasks-ready events as one ordered durable
  transaction before release, then batches timestamped in-flight and terminal
  states after the operation; pre-stages write payloads; emits deterministic
  checks and bounded evidence; distinguishes sandbox create from session
  create; records the v1.1 gateway policy; and durably persists each unique
  execution-block endpoint before client construction or trial timing.
- `backend/benchmark_lab/safety.py` removes only marked owned trees using safe
  native extended-length paths.
- `backend/benchmark_lab/service.py` requires reviewed product catalog/CLI
  availability before validation or execution.
- `backend/benchmark_lab/sessions.py` uses the shared product-access protocol
  without constructing a direct gateway transport.
- `backend/benchmark_lab/transport.py` exposes bounded product rejection
  classification plus strict loopback-TCP/named-pipe endpoint parsing and a
  one-attempt Windows named-pipe request path with no fallback.
- `backend/tests/compatibility/test_artifacts.py` and
  `backend/tests/unit/test_runner_squash.py` verify schema-v1 compatibility
  using the explicit frozen evidence fixture and v2 indexing/download.
- `backend/tests/compatibility/test_reports.py` verifies canonical CSV bytes
  independently of Git checkout newline conversion.
- `backend/tests/contract/test_api.py`, `backend/tests/contract/test_planning.py`,
  and `backend/tests/contract/test_catalog.py` verify public serialization,
  paper-preset rejection/fallback rules, exact 19-cell expansions, request
  counts, `paper-100m`, executable probing, and fail-closed catalog behavior.
- `backend/tests/contract/test_zero_rust_guard.py` excludes the prepared
  virtual environment while retaining the zero-product-source coupling guard.
- `backend/tests/integration/test_gateway_lifecycle.py` covers native Windows
  launch/configuration, CLI readiness, gateway-scoped IDs, leading-hyphen
  rejection behavior, per-block named-pipe uniqueness/ownership, cleanup,
  stale recovery, and symlink refusal.
- `backend/tests/integration/test_gateway_transport.py` covers real and mocked
  named-pipe round trips, concurrent requests, unsafe endpoint rejection, and
  absence of TCP fallback.
- `backend/tests/integration/test_runner.py` keeps its fakes aligned with CLI
  readiness, daemon sampling, explicit gateway cleanup semantics, synchronized
  barrier timing, validated-response makespan, write pre-staging, v1.1 policy
  provenance, endpoint uniqueness, and crash-prefix manifest durability.
- `backend/tests/unit/test_exp1_archive.py` verifies explicit protocol version,
  unique safe named-pipe provenance, v1.1 freeze tags, and the complete frozen
  protocol/analysis/tracker scope.
- `backend/tests/unit/test_exp1_runtime_projection.py` verifies v1.1 protocol
  and named-pipe provenance before any final-runtime projection is accepted.
- `backend/tests/unit/test_metadata.py` verifies the recorded named-pipe
  transport, local scope, and per-execution-block rotation identity.
- `backend/tests/unit/test_resource_sampling.py` verifies fixed-deadline
  collection, deferred ordered persistence, and explicit saturation evidence.
- `backend/tests/unit/test_derivation.py` verifies timing/provenance and
  numeric-evidence derivation.
- `backend/tests/unit/test_fixtures.py` verifies depth-100 generation and the
  revised admission boundary.
- `backend/tests/unit/test_runner_command.py` verifies the released line-window
  command representation and command evidence.
- `backend/tests/unit/test_safety.py` verifies deep Windows cleanup and
  fail-closed symlink behavior.
- `defaults/definition-catalog.json` defines the separate sandbox lifecycle
  create/base-mount operation and EXP1 timing/evidence semantics.
- `presets/paper-env-smoke.yml` and `presets/paper-good-pass.yml` select only
  `product_cli`, retain the fixed 19 cells, and apply `paper-100m`; the final
  preset fixes two warmups and 100 measured trials without retry or outlier
  removal.
- `web/src/api/types.ts`, `web/src/components/DefaultPlanLauncher.tsx`, and
  `web/tests/unit/plan-workflow.test.tsx` expose and verify the `product_cli`
  cohort in the plan UI.

No imported benchmark file outside this list is modified by EXP1.

The upstream test repository remains the engineering source of truth. This
copy is intentionally frozen so that paper results can be tied to an exact
benchmark implementation. If the snapshot is refreshed, replace the complete
upstream subtree, update the commit above, and rerun the benchmark; do not mix
results from different benchmark revisions in one table.

## Directory roles

When this copy is used, the three benchmark roots are:

- Test repository root: the parent paper directory
  `research-papers/ephemeral-sandbox-v1`
- Benchmark source root: this `benchmark` directory
- Product root: a separate checkout of `ephemeral-sandbox`
- Product binary directory: a directory beneath the product root containing
  the prebuilt release executables

Generated fixtures, run workspaces, raw observations, and reports are written
under `ephemeral-sandbox-v1/.benchmark-state/`. That directory is ignored by
Git and must not be treated as benchmark source.

## Prepare and validate on the qualified Windows host

The selected host is native Windows x64. Docker Desktop supplies the Linux
AMD64 engine and the pinned Ubuntu sandbox image; Ubuntu is not the host. The
released native Windows gateway and manager/runtime/observability CLIs are the
only permitted product access path.

The benchmark requires Python 3.13 or newer for its own orchestration. Prepare
its virtual environment and dependencies off-clock. No package installation,
build, image pull, or source mutation may occur during a pilot or final
campaign.

The three paper presets select `product_cli`; `direct_client` and `cli_e2e`
remain prohibited. The frozen v1.1 product is local clean `main` at
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`. It retains the earlier
released-CLI, shared-base-cache, and resource-sampling repairs and adds the
no-fallback local-IPC treatment plus TCP endpoint compatibility. Its staged
native Windows package and archive are:

- `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5c48dae1`
- `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5c48dae1.zip`
- archive SHA-256
  `11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`

From `research-papers\ephemeral-sandbox-v1`, the validated Windows command
shape is:

```powershell
$paper = 'C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1'
$product = 'C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox'
$productBin = "$product\target\windows-exp1-5c48dae1\bin"

Set-Location -LiteralPath $paper
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e '.\benchmark[test]'

& .\.venv\Scripts\sandbox-benchmark.exe validate `
  --test-repository-root $paper `
  --product-root $product `
  --product-bin-dir $productBin `
  --plan paper-env-smoke
```

Validation checks the plan and product catalog but does not establish
performance. A campaign command must not be issued until the preset expands to
`product_cli`, the exact released executables and image digest pass preflight,
and the phase gate in
[`../experiment_inventory.md`](../experiment_inventory.md) authorizes the run.

The paper presets pin the selected Linux AMD64 Ubuntu image by digest. Docker
Desktop must already contain and independently inspect that exact digest before
any pilot or final measurement begins.

At the frozen v1.1 revision, validation produces:

| preset | plan hash | cells | batches | CLI requests |
| --- | --- | ---: | ---: | ---: |
| `paper-env-smoke` | `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937` | 19 | 19 | 55 |
| `paper-pilot` | `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f` | 19 | 133 | 385 |
| `paper-good-pass` | `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b` | 19 | 1,938 | 5,610 |

## Paper base workspace

Use workspace profile `paper-100m` for every final measured cell. It generates
exactly 100 MiB (104,857,600 bytes) across 4,000 deterministic files with a
maximum directory depth of 100. The cached seed is copied into a clean
benchmark-owned per-cell workspace before sandbox creation; operation-specific
file targets are prepared there outside the primary timing interval.
