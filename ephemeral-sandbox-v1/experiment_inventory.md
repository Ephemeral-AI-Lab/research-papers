# Focused sandbox performance experiment specification

**Protocol ID:** `ephemeral-sandbox-v1-practical-performance-v0.1`  
**Status:** Draft; not protocol-locked and not approved for final measurement  
**Last updated:** 2026-07-30  
**Primary tracker:** the phase checklists in this document  
**Run log:** [`experiments/experiment_log.md`](experiments/experiment_log.md)

## Purpose and claim boundary

This experiment characterizes whether Ephemeral Sandbox has practically useful
startup and public-operation performance in one disclosed Linux environment.
It does not attempt to show that Ephemeral beats another sandbox, shared
directory, Git worktree, or agent framework.

The permitted result language is descriptive:

- "In the tested environment, operation X had p50/p95/p99 latency of ..."
- "Throughput changed from ... to ... between concurrency 1 and 5."
- "Peak measured resource use remained within ... for this workload."

The following claims are outside this protocol:

- competitive superiority;
- a universal concurrency ceiling;
- general security or isolation correctness;
- multi-agent task-quality improvement;
- performance on Windows, macOS, another filesystem, another image, or
  untested hardware.

This is a bounded RQ3 performance slice. It does not replace the broader RQ1-RQ5
charter in [`lanes/experiments.md`](lanes/experiments.md).

## Fixed study configuration

| Item | Locked choice for this protocol |
|---|---|
| Product branch | `main` |
| Product source baseline | clean `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`, annotated tag `v0.1.4` |
| Upstream benchmark snapshot | `d45618733c8bfe75466947fdb9c47bea67f74b78` |
| Paper-local benchmark | [`benchmark/`](benchmark/) plus documented paper-local changes |
| Computer name | `DESKTOP-OLP1ADS` |
| Host | Native 64-bit Windows build 26200 |
| Qualified host capacity | 48 logical CPUs, 137,438,953,472 bytes memory, NTFS |
| Runtime | Docker Desktop 29.0.1; Linux AMD64 engine, `overlayfs`, cgroup v2 |
| Product path | `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox` |
| Paper path | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1` |
| Environment qualifier | Native PowerShell; no Python dependency |
| Sandbox image | `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf` |
| Sandbox resource profile | `standard`: 1 vCPU, 512 MiB memory maximum, 256 PIDs |
| Network profile | `shared` |
| Client cohort | `product_cli`; manager, runtime, and observability subprocesses |
| Environment qualification workspace | Two tiny isolated fixtures inside the qualification artifact directory |
| Canonical repo-backed workspace | `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\workspace-base\ephemeral-sandbox-v0.1.4` |
| Performance-only workspace profile | `paper-100m` (outside the environment task) |
| Performance-only base workspace | 4,000 deterministic files, 100 MiB logical content, maximum depth 100 |
| Generator ceiling | Maximum depth 499 |
| Seed | `20260712` |
| Operation concurrency | 1 and 5 |
| File payloads | 4 KiB and 256 KiB |
| Warmups | 2 per measured cell |
| Measured trials | 100 per measured cell |
| Scheduling | Seeded randomized blocks |
| Resource sampling | 100 ms |
| Retries | None |

The image digest above was resolved from the Docker registry for
`linux/amd64` on 2026-07-30 and inspected through Docker Desktop during the
accepted Windows qualification.

## Workspace construction

The benchmark generates and caches a deterministic artificial seed workspace.
Before a sandbox cell is prepared, the seed is copied into a new empty
benchmark-owned directory. The sandbox mounts that per-cell copy, never the
product source checkout or paper checkout.

The primary profile is
[`paper-100m.yml`](benchmark/defaults/workspace-profiles/paper-100m.yml):

```text
logical bytes:   104,857,600
files:           4,000
depth range:     1..100
files per depth: approximately 40
maximum depth:   100
seed:            20260712
```

The selected `paper-100m` base applies to every final measured cell, including
file read, write, and edit. Operation-specific targets are created during
untimed setup inside a fresh per-cell copy of that base. The current benchmark
schema applies the selected profile only to command and workspace-readiness
cells, so Phase 3 must extend the file-operation preparation path before any
pilot or final run. Neither the product checkout, paper checkout, canonical
repository-backed qualification workspace, nor a clean empty fixture is a
substitute for the performance base.

## Measured operations and boundaries

| Operation | Timed boundary | Untimed work |
|---|---|---|
| Sandbox create + base mount | One native manager-CLI subprocess from process launch through successful validated ready response | Base generation/copy, gateway start, verification, teardown |
| Workspace/session create | Concurrent native runtime-CLI `create_workspace_session` subprocesses against a prepared sandbox and `paper-100m` base | Base generation/copy, sandbox creation, verification, teardown |
| `exec_command` | One native runtime-CLI subprocess against a prepared explicit session | Sandbox/session setup, result verification, teardown |
| File read | One native runtime-CLI `file_read` subprocess over a prepared target in the `paper-100m` base | Target generation and content verification |
| File write | One native runtime-CLI `file_write` subprocess in a fresh prepared session over the `paper-100m` base | Target/session setup, read-back verification, teardown |
| File edit | One native runtime-CLI `file_edit` subprocess in a fresh prepared session over the `paper-100m` base | Target/session setup, read-back verification, teardown |

The focused campaign includes explicit manager-CLI sandbox-create-to-ready
timing. The current runner invokes `create_sandbox` during setup and discards
its response timing, so Phase 3 must add this separate metric. Session-create
latency remains a distinct runtime-CLI operation and must never be relabeled as
sandbox-create latency.

### CLI timing contract

- A measured operation begins immediately before the native Windows CLI
  subprocess is created and ends only after it exits and its stdout and stderr
  have been captured, parsed, and validated.
- Primary latency therefore includes executable launch, argument parsing,
  CLI-to-gateway transport, gateway execution, response serialization, and
  subprocess exit. This is the user-visible cost of the required public CLI
  boundary.
- Product-reported internal command or gateway durations may be archived as
  separate secondary observations when available. They must not replace,
  subtract from, or be mixed with the primary end-to-end CLI latency.
- Concurrent batches release their CLI subprocesses from one benchmark barrier
  and measure makespan until every subprocess has produced a valid result.
- Setup, correctness verification, observability sampling, and teardown also
  use released product CLIs where they are sandbox operations, but remain
  outside the measured operation interval.

## Draft good-pass matrix

The executable draft is
[`paper-good-pass.yml`](benchmark/presets/paper-good-pass.yml).

| Operation | Cases | Concurrency | Measured cells |
|---|---|---:|---:|
| Sandbox create + base mount | `paper-100m`, shared network | 1 | 1 |
| Workspace/session create | `paper-100m`, shared network | 1, 5 | 2 |
| `exec_command` | no-op, 4 KiB fixture read | 1, 5 | 4 |
| File read | 4 KiB, 256 KiB | 1, 5 | 4 |
| File write | 4 KiB, 256 KiB, session-local | 1, 5 | 4 |
| File edit | 4 KiB, 256 KiB, one exact replacement | 1, 5 | 4 |
| **Total** |  |  | **19** |

Each cell has 2 warmups and 100 measured trials. This sample count permits a
reported empirical p99 without silently treating a smaller sample's maximum as
a stable tail estimate.

## Metrics

### Primary

- end-to-end native product-CLI subprocess latency and concurrent-batch
  makespan in milliseconds;
- p50, p95, and p99 over the 100 measured trials;
- throughput in completed operation requests per second.

### Secondary

- daemon CPU-time delta;
- sandbox CPU-time delta;
- peak daemon RSS;
- peak sandbox memory;
- sandbox block-read and block-write byte deltas;
- workspace logical and allocated bytes;
- host free-space minimum.

### Metric definitions

- A trial's latency follows the CLI timing contract above. It includes native
  CLI process launch and exit while excluding separate setup, verification, and
  teardown operations.
- For a concurrent batch, throughput is
  `completed_requests / batch_makespan_seconds`.
- Warmups never contribute to aggregates.
- Percentiles use the deterministic implementation recorded by the benchmark
  report generator.
- Verification is an inclusion gate, not a result-table column. Every displayed
  sample must have succeeded, passed correctness checks, and restored its
  cleanup baseline.

## Inclusion, failure, and stopping rules

1. There are no automatic retries.
2. Every attempted run, including failed and partial runs, is retained and
   logged.
3. A sample is reportable only when the product operation succeeded, internal
   checks passed, infrastructure did not fail, and cleanup restored baseline.
4. If any measured cell has fewer than 100 reportable samples, its p99 row is
   withheld until the cause is resolved and the complete cell is rerun.
5. Do not silently remove outliers. Retain the raw sample and use the
   benchmark's preregistered descriptive/outlier annotations.
6. Stop the campaign on environment drift, image/binary hash mismatch, disk
   pressure below the preflight threshold, repeated cleanup leakage, or daemon
   instability.
7. A failed environment or smoke gate blocks all pilot and measured runs.
8. Protocol changes after Phase 4 require a version bump, a log entry, and
   rerunning every affected final cell.

## Runtime budget

The targets below are acceptance budgets, not measured claims:

| Activity | Target |
|---|---:|
| Warm, network-free environment preflight | <= 60 seconds |
| Minimal live environment smoke | <= 3 minutes |
| Five-sample exploratory pilot | <= 5 minutes |
| Complete good pass | <= 20 minutes |
| Deterministic analysis and table generation | <= 2 minutes |

If the good pass exceeds 20 minutes during the pilot, reduce the matrix before
protocol lock. Do not reduce trials or remove slow cells after seeing final
results.

## Phases and acceptance tracker

### Environment decision

The native Windows workstation with Docker Desktop is the selected and
qualified environment. Windows launches the released gateway and CLIs; Docker
Desktop supplies the Linux engine and runs the pinned Ubuntu sandbox image.
The exact qualification command and evidence are fixed in
[`experiments/environment_setup.md`](experiments/environment_setup.md).

Every sandbox lifecycle, command, file, and observation operation used for
qualification or a future experiment must execute through
`sandbox-manager-cli`, `sandbox-runtime-cli`, or
`sandbox-observability-cli`. The imported benchmark currently implements only
`direct_client`; its performance presets are therefore prohibited until a
product-CLI subprocess cohort is implemented and reviewed. The complete
execution contract is
[`plan/task-packets/exp1-cli-performance-campaign.md`](plan/task-packets/exp1-cli-performance-campaign.md).

### Phase 0 - Reproducibility package

- [x] Create the paper-local benchmark snapshot.
- [x] Record upstream benchmark commit and paper-local modifications.
- [x] Create the deterministic 100 MiB/depth-100 profile.
- [x] Define the environment, table schemas, and append-only log.
- [x] Create a network-free fast preflight script.
- [x] Create minimal-smoke and good-pass presets.
- [ ] Review and approve this draft protocol.

**Gate 0:** all files exist and cross-links/configuration validate.

### Phase 1 - Verify the final environment first

- [x] Confirm native Windows x64 host identity and build.
- [x] Stage the official `v0.1.4` Windows AMD64 package under ignored `target/`.
- [x] Confirm NTFS, CPU/RAM/free-space thresholds.
- [x] Confirm Docker Desktop 29.0.1, Linux AMD64, `overlayfs`, and cgroup v2.
- [x] Confirm the pinned Ubuntu image is present locally.
- [x] Confirm clean product `main` and the exact commit.
- [x] Confirm archive, gateway, CLI, config, daemon, and image digests.
- [x] Archive the complete native Windows preflight output.

**Gate 1:** every environment acceptance item passes. Any failure stops work;
do not compensate by building, installing, or changing the host mid-run.

### Phase 2 - Minimal live smoke

- [x] Run the native Windows CLI-only environment smoke.
- [x] Confirm two independent sandbox lifecycles complete.
- [x] Confirm command and file-operation correctness in both batches.
- [x] Confirm cleanup leaves no qualifier-owned container, volume, or process.
- [x] Record elapsed time and keep the smoke below 3 minutes.
- [x] Mark the elapsed time as environment evidence, ineligible for paper tables.

**Gate 2:** both product-CLI-controlled lifecycles complete, all 20 expected
CLI calls pass strict response checks, and the unique gateway instance leaves
no containers, volumes, processes, or runtime state.

The earlier 2026-07-30 WSL smoke used the now-disallowed `direct_client`
cohort. It remains diagnostic implementation evidence but is not
Gate 2-equivalent under the product-CLI-only contract.

A later WSL/Docker Desktop diagnostic executed the replacement product-CLI
smoke successfully for two lifecycles. Because WSL is ineligible, this validates
the automation only and still does not satisfy Gate 1 or Gate 2.

The accepted native Windows run is
`qualification-windows-docker-20260730-final-6`. It satisfies Gate 1 and Gate 2
with the official Windows release gateway and CLIs controlling Docker Desktop.

### Phase 3 - Instrumentation and five-sample pilot

- [ ] Implement and review the `product_cli` subprocess cohort for manager,
  runtime, and observability operations; make paper presets reject
  `direct_client`.
- [ ] Apply `paper-100m` to command, lifecycle, read, write, and edit cells.
- [ ] Add explicit manager-CLI sandbox-create + base-mount timing for Table 2.
- [ ] Enforce the end-to-end CLI timing contract and retain any internal
  product timing only as separate secondary evidence.
- [ ] Confirm p99, throughput, and resource fields are emitted by analysis.
- [ ] Run a five-sample pilot over all 19 final cells with the final two
  warmups retained.
- [ ] Confirm operation setup is excluded from operation latency.
- [ ] Confirm all correctness checks and cleanup gates pass.
- [ ] Confirm raw observations deterministically regenerate draft tables.
- [ ] Confirm the projected good-pass duration is <= 20 minutes.

**Gate 3:** measurement boundaries, outputs, and runtime are demonstrated.

### Phase 4 - Protocol lock and freeze

- [ ] Resolve every Gate 0-3 item.
- [ ] Freeze the product commit/tag and record a clean tree.
- [ ] Freeze the paper-local benchmark commit and plan hash.
- [ ] Freeze image and binary digests.
- [ ] Freeze table columns, metric definitions, seed, trials, and exclusions.
- [ ] Record protocol version `v1.0` in the log.

**Gate 4:** no scientific decision remains conditional or ambiguous.

### Phase 5 - Good pass

- [ ] Re-run the fast environment preflight.
- [ ] Confirm no build, image pull, package install, or source mutation occurs.
- [ ] Run `paper-good-pass` once with the frozen plan.
- [ ] Preserve run manifest, raw observations, traces, resources, and logs.
- [ ] Preserve failed or partial evidence if the run does not complete.
- [ ] Confirm all 19 cells have 100 reportable measured trials.

**Gate 5:** one complete, provenance-rich measured corpus exists.

### Phase 6 - Deterministic analysis and tables

- [ ] Validate the raw corpus before aggregation.
- [ ] Generate all four expected tables from archived data.
- [ ] Confirm every displayed value traces to a run/cell/metric selector.
- [ ] Confirm no verification/pass column appears in the CLI table.
- [ ] Confirm negative or unavailable resource fields are disclosed.
- [ ] Record analysis command, commit, and output hashes.

**Gate 6:** tables regenerate exactly and contain no manual numeric edits.

### Phase 7 - Paper handoff

- [ ] Map each table to the exact supported descriptive claim.
- [ ] Record wording that remains unsafe.
- [ ] Update the claim-evidence map with run and table identifiers.
- [ ] Add numeric-evidence selectors before inserting numbers into LaTeX.
- [ ] Obtain author review of environment, boundaries, and interpretation.

**Gate 7:** the paper uses only reproducible, scoped evidence.

## Artifact layout

```text
experiments/
|-- environment_setup.md
|-- expected_tables.md
|-- experiment_log.md
|-- scripts/
|   `-- verify_environment.sh
|-- runs/
|   `-- RUN_ID/
|       |-- environment-preflight.txt
|       |-- run-manifest.json
|       |-- raw/
|       |-- logs/
|       `-- failures.md
`-- analysis/
    |-- tables/
    `-- generation-log.txt
```

Generated state may initially reside under `.benchmark-state`, but the final
run package must be copied or linked into the immutable `experiments/runs`
layout before numbers enter the manuscript.

## Definition of done

This focused experiment is complete only when Gates 0-7 pass, all four tables
regenerate from preserved raw data, the final host and every digest are
recorded, failures are retained, and the paper makes only descriptive claims
within the tested environment.
