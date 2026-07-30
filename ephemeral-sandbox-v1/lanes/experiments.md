# Lane 2: experiments

Status: **protocol design required before final source freeze or measurements**

This lane designs, pilots, freezes, runs, and analyzes the evidence required by the paper. It includes any paper-specific source fixes and measurement instrumentation because those changes must be settled before `paper-v1-freeze`.

## Objective

Determine whether Ephemeral Sandbox implements its stated isolation and publication semantics, how its latency and resource costs scale, and whether private sessions with controlled publication move the workload-dependent useful-work concurrency ceiling under defined coding-agent team and swarm workloads.

## Authoritative inputs

- [`PRD.md`](../PRD.md) — correctness, performance, provenance, and submission gates.
- [`paper_skeleton.md`](../paper_skeleton.md) — RQ1–RQ5 and result structure.
- [`claim_evidence_map.md`](../claim_evidence_map.md) — claims that require measurement and required artifacts.
- [`project_inventory.md`](../project_inventory.md) — existing tests, scripts, exploratory assets, and evidence gaps.
- [`progress.md`](../progress.md) — authoritative tracker and blockers.
- Source checkout: `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox`.
- External benchmark checkout: `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox-test`.
- [`paper-writing.md`](./paper-writing.md) — result handoff expected by the manuscript lane.

The source checkout is currently clean on required `main` at baseline commit `b22862550e0a7cb4fe61ce581831e9244cc492b5`. Its `AGENTS.md` and `CLAUDE.md` prohibit side branches and worktrees.

## Research questions

### RQ1. Isolation correctness

Does each session observe a stable private executable workspace while other sessions publish, compact, fail, or close?

Required cases:

- simultaneous sessions from controlled bases;
- cross-session reads and writes;
- process and namespace identity;
- shared and isolated network profiles;
- cleanup and cancellation;
- compaction while a lease is held;
- daemon restart and lease/substitution recovery.

### RQ2. Publication correctness

Does publication implement the source-defined merge/reject and atomic data-visibility behavior?

Required cases:

- disjoint stale-base writes;
- same-path eligible text merge;
- overlapping text conflict;
- binary, oversized, invalid-UTF-8, and structural conflict;
- delete/modify and protected/drop cases;
- concurrent publishers;
- injected storage, audit, and cleanup failures;
- retry, no-op, and published-but-not-closed outcomes.

### RQ3. Latency and resource scaling

How do session projection, execution, capture, publication, compaction, and storage/resource costs change with concurrency, payload size, and layer depth?

Required factors include:

- worker counts;
- payload size;
- layer depth;
- live session count and lease age/boundaries;
- upperdir entry count, fan-out, and path depth;
- changed-path and source-validation count;
- merge file bytes, line count, similarity, and edit distance;
- conflict/no-conflict workload;
- concurrent publisher count, writer-lock wait, and writer-lock hold time;
- logical, allocated, shared, and exclusive bytes for upper/work/staging/layers/history;
- warm/cold or setup state where relevant.

The factor selection and predicted source-level terms are defined in [`../complexity_and_evolution.md`](../complexity_and_evolution.md). The experiment must test those predictions without presenting them as measured complexity guarantees.

### LayerStack 2.0 evidence boundary

The v1 evaluation and the LayerStack 2.0 migration protocol are separate studies. Do not combine their samples, thresholds, or source revisions. The v1 paper may report the pinned negative Windows `FICLONE` feasibility cell as a narrowly scoped limitation/future-work input, but pending A/B/C tables are not results and no v2 mechanism belongs in a v1 performance baseline unless the paper scope, freeze, and claim map are explicitly revised.

### RQ4. Multi-agent useful-work concurrency

Under controlled coding workloads, does Ephemeral change verification-passing, durably accepted progress relative to a shared mutable directory and Git worktrees?

Workload families:

- **Structured team:** roles, explicit dependencies, handoffs, shared interfaces or services, and an integration lane.
- **Exploratory swarm:** redundant or competing proposals, hot-path overlap, rapidly advancing heads, and result selection.

### RQ5. Attribution and recovery

How completely can accept, reject, retry, cleanup failure, cancellation, and restart outcomes be connected to request, base, paths, result, and audit records?

## Protocol lock

Create `../experiment_inventory.md` before final source freeze. It must fix:

1. accepted-work unit and verification rule;
2. repositories, tasks, and initial commits;
3. structured-team and exploratory-swarm workloads;
4. shared-directory, Git-worktree, and Ephemeral baseline behavior;
5. model, prompt, tool, budget, and coordinator configuration;
6. worker-count grid;
7. payload/layer-depth matrix where applicable;
8. timeouts, retries, stopping rules, seeds, and repeats;
9. integration order and acceptance policy;
10. primary and secondary metrics;
11. uncertainty method and exclusions;
12. Linux platform, cgroup, filesystem, hardware, and runtime configuration;
13. raw artifact and analysis layout;
14. required source instrumentation.

Once protocol lock is declared, do not change metrics, exclusions, or acceptance rules in response to desired outcomes. Amendments must be versioned and justified before new final runs.

## Baselines

### Shared mutable directory

Workers operate against one immediately mutable project/workspace and shared execution environment. Record exactly how writes, Git state, services, tests, and cleanup are coordinated.

### Git worktrees

Each worker receives a distinct working tree with a defined integration and verification policy. Record shared Git state, service/resource behavior, base revision, merge order, and cleanup.

### Ephemeral sessions

Each worker receives an implicit or explicit workspace session under the exact v1 contract. Record base manifest/lease, session/network profile, captured changeset, publication outcome, resulting head, and cleanup.

The baselines must use the same model, prompts, budgets, tasks, tool versions, worker counts, test harness, seeds/repeats, and acceptance rule wherever technically possible.

## Metrics

### Primary

Verification-passing, durably accepted contribution units per wall time and resource cost.

### Secondary

- session creation, execution, capture, publication, and end-to-end latency;
- accepted, rejected, no-op, retry, and failed operations;
- stale bases and conflict classes;
- duplicate or superseded work;
- integration and result-selection latency;
- clean textual publications that fail verification;
- CPU, RSS, disk/I/O, storage amplification, and queueing;
- orphaned sessions/processes/resources;
- attribution completeness and `unknown` rate;
- human/lead repair work if the workload includes it.

No universal agent-count threshold or monotonic scaling assumption is permitted.

## Execution phases

### Phase E0: protocol design

- create `experiment_inventory.md`;
- identify missing harness behavior;
- define artifact schemas;
- decide required source instrumentation;
- review fairness and construct validity.

### Phase E1: exploratory pilots

- exercise each workload and failure class at small scale;
- validate commands, logging, cleanup, and analysis;
- fix source or harness issues on their required repositories;
- revise the protocol before lock;
- label every run `exploratory`.

Pilot numbers cannot enter the paper as results.

### Phase E2: source and benchmark freeze

- source behavior and instrumentation stable;
- annotated `paper-v1-freeze` created and recorded;
- final-tag CLI contract regenerated;
- benchmark repository/configuration commit frozen;
- Linux correctness/fault prerequisites pass or failures are disclosed;
- binaries/images built and digested.

### Phase E3: final runs

- run the locked correctness matrix;
- run latency/resource sweeps;
- run structured-team workloads;
- run exploratory-swarm workloads;
- run attribution/recovery cases;
- retain failures, timeouts, exclusions, and partial runs.

### Phase E4: deterministic analysis

- validate raw artifacts;
- compute aggregates and uncertainty;
- decompose conflict, retry, integration, verification, selection, and resource costs;
- identify the workload-specific limiting regime;
- generate tables and plots from versioned analysis code;
- map each result to claim IDs.

### Phase E5: evidence handoff

Deliver a result record to the paper lane for every claim supported, weakened, or rejected.

## Artifact structure

Use:

```text
experiments/
├── protocols/
│   ├── experiment_inventory.md or linked canonical protocol
│   └── workload and baseline configurations
├── runs/
│   └── RUN_ID/
│       ├── manifest
│       ├── commands and environment
│       ├── raw logs, events, and samples
│       ├── source/binary/image digests
│       └── exclusions or failure record
└── analysis/
    ├── deterministic scripts
    ├── recomputed tables
    └── result figures
```

Every final run must preserve source tag and tag object, benchmark commit, dirty status, OS/kernel/filesystem, hardware, cgroup/runtime settings, toolchain, binary/image digests, workload commit, exact commands/environment, seeds/repeats, raw artifacts, exclusions, and analysis commit.

## Source-change rules

1. Read and obey the source repository's `AGENTS.md` and `CLAUDE.md`.
2. Work in the existing `ephemeral-sandbox` checkout on `main`; do not create side branches or worktrees.
3. Touch only behavior or instrumentation required by a locked paper question.
4. Add correctness tests separately from performance experiments.
5. After every source change, update affected claim-map rows and pilot assumptions.
6. Do not create `paper-v1-freeze` until pilots have exposed required fixes/instrumentation.
7. After final freeze, any affecting fix requires a new freeze and rerun of dependent evidence.

## Paper-lane handoff record

For each result, provide:

- `result_id` and contributing `run_id` values;
- RQ and claim IDs;
- exact question and comparison;
- workload, baseline, worker count, and configuration;
- metric definition, aggregate, uncertainty, and sample count;
- raw and analysis paths;
- exclusions and anomalies;
- supported wording;
- wording that remains unsafe;
- negative or limiting interpretation.

## Completion checklist

- [ ] Create and review `experiment_inventory.md`.
- [ ] Lock accepted-work and verification rules.
- [ ] Lock team and swarm workloads.
- [ ] Lock matched baselines.
- [ ] Lock metrics, worker counts, seeds/repeats, stopping rules, and uncertainty.
- [ ] Resolve protected-drop, attribution, and restart/lease blockers.
- [ ] Add required measurement instrumentation.
- [ ] Complete and archive exploratory pilots.
- [ ] Create and record `paper-v1-freeze`.
- [ ] Freeze the benchmark repository/configuration.
- [ ] Run and archive RQ1 isolation cases.
- [ ] Run and archive RQ2 publication/fault cases.
- [ ] Run and archive RQ3 scaling/resource sweeps.
- [ ] Run and archive RQ4 team/swarm workflow comparisons.
- [ ] Run and archive RQ5 attribution/recovery cases.
- [ ] Freeze deterministic analysis and uncertainty.
- [ ] Generate result tables/figures.
- [ ] Deliver claim-mapped evidence records to the paper lane.

## Definition of done

This lane is complete only when the protocol is reproducible, final source and benchmark versions are frozen, every reported sample has full provenance, aggregates are recomputable, negative results are preserved, and each paper result has a claim-mapped handoff record.
