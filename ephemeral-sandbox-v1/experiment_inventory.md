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
| Product source baseline | `b22862550e0a7cb4fe61ce581831e9244cc492b5`; final clean commit/tag pending |
| Upstream benchmark snapshot | `d45618733c8bfe75466947fdb9c47bea67f74b78` |
| Paper-local benchmark | [`benchmark/`](benchmark/) plus documented paper-local changes |
| Host | Ubuntu Server 24.04 LTS, Linux x86-64 |
| Host minimum | 8 vCPU, 16 GiB RAM, 100 GiB local NVMe-backed ext4 |
| Runtime | Docker Engine, cgroup v2 |
| Sandbox image | `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf` |
| Sandbox resource profile | `standard`: 1 vCPU, 512 MiB memory maximum, 256 PIDs |
| Network profile | `shared` |
| Client cohort | `direct_client` |
| Base workspace profile | `paper-100m` |
| Base workspace | 4,000 deterministic files, 100 MiB logical content, maximum depth 100 |
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
`linux/amd64` on 2026-07-30. Phase 1 must independently pull and inspect the
same digest on the final host before it is accepted.

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

The current benchmark schema applies the selected base-workspace profile
directly to command and workspace-readiness cells. File-operation cells create
their deterministic target files during untimed setup. Before protocol lock,
we must either:

1. extend file-operation cells to mount the same `paper-100m` base; or
2. state in the paper that the 100 MiB base applies only to startup/command
   cells and that file-operation rows use operation-specific clean fixtures.

No final run may proceed while this boundary is ambiguous.

## Measured operations and boundaries

| Operation | Timed boundary | Untimed work |
|---|---|---|
| Workspace/session create | Concurrent internal no-op session requests until ready, against a prepared sandbox and base fixture | Base generation, sandbox creation, verification, teardown |
| `exec_command` | One public command request against a prepared explicit session | Sandbox/session setup, result verification, teardown |
| File read | One public `file_read` request over a prepared snapshot target | Target generation and content verification |
| File write | One public `file_write` request in a fresh prepared session | Target/session setup, read-back verification, teardown |
| File edit | One public `file_edit` request in a fresh prepared session | Target/session setup, read-back verification, teardown |

Initial sandbox creation and mounting are not currently a first-class measured
operation: the runner invokes `create_sandbox` during setup and discards its
timed response. If the paper reports "sandbox create + mount" latency, Phase 3
must add an explicit metric with request-to-ready timing. Session-create
latency must not be relabeled as sandbox-create latency.

## Draft good-pass matrix

The executable draft is
[`paper-good-pass.yml`](benchmark/presets/paper-good-pass.yml).

| Operation | Cases | Concurrency | Measured cells |
|---|---|---:|---:|
| Workspace/session create | `paper-100m`, shared network | 1, 5 | 2 |
| `exec_command` | no-op, 4 KiB fixture read | 1, 5 | 4 |
| File read | 4 KiB, 256 KiB | 1, 5 | 4 |
| File write | 4 KiB, 256 KiB, session-local | 1, 5 | 4 |
| File edit | 4 KiB, 256 KiB, one exact replacement | 1, 5 | 4 |
| **Total** |  |  | **18** |

Each cell has 2 warmups and 100 measured trials. This sample count permits a
reported empirical p99 without silently treating a smaller sample's maximum as
a stable tail estimate.

## Metrics

### Primary

- client-observed batch makespan latency in milliseconds;
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

- A trial's latency is its timed operation boundary, excluding setup,
  verification, and teardown.
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

- [ ] Provision the single Ubuntu 24.04 x86-64 host.
- [ ] Place prebuilt product binaries; do not build on the measurement host.
- [ ] Pull the pinned image before the measurement window.
- [ ] Run `experiments/scripts/verify_environment.sh`.
- [ ] Confirm ext4, cgroup v2, Docker server, CPU/RAM/free-space thresholds.
- [ ] Confirm clean product `main` and record the exact commit.
- [ ] Confirm binary, daemon, toolchain-archive, and image digests.
- [ ] Archive the preflight output in the run directory.
- [ ] Complete the preflight in 60 seconds or less with a warm local image.

**Gate 1:** every environment acceptance item passes. Any failure stops work;
do not compensate by building, installing, or changing the host mid-run.

### Phase 2 - Minimal live smoke

- [ ] Run the `paper-env-smoke` preset.
- [ ] Confirm one sandbox/session lifecycle completes.
- [ ] Confirm one `exec_command` completes and verifies.
- [ ] Confirm cleanup leaves no owned sandbox, process, or runtime residue.
- [ ] Record elapsed time and keep the smoke below 3 minutes.
- [ ] Mark all smoke samples exploratory and ineligible for paper tables.

**Gate 2:** live create, execute, observe, and cleanup succeed once.

### Phase 3 - Instrumentation and five-sample pilot

- [ ] Decide and implement the file-operation base-workspace boundary.
- [ ] Add explicit sandbox-create + mount timing if Table 2 will report it.
- [ ] Confirm p99, throughput, and resource fields are emitted by analysis.
- [ ] Run a five-sample pilot over every final cell.
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
- [ ] Confirm all 18 cells have 100 reportable measured trials.

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
