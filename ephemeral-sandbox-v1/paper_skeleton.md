# Ephemeral Sandbox v1: paper and work skeleton

Status: working manuscript skeleton. Design claims are provisionally grounded in source baseline [`b22862550e0a7cb4fe61ce581831e9244cc492b5`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5). No experiment may become a paper result until rerun against the annotated `paper-v1-freeze` tag with complete provenance.

Current readiness, active lanes, synchronization gates, and immediate actions are tracked in [`progress.md`](./progress.md).

## Core paper contract

**Recommended title:** *Ephemeral Sandbox: A LayerStack Workspace OS for Parallel Coding Agents*

**Research question:** How can a sandbox runtime raise the practical concurrency ceiling for coding agents by giving each agent a private, executable workspace over shared project history, then reconciling accepted changes through well-defined publication semantics?

**Thesis:** Agent products can fan out intelligence, but conventional operating-system workspaces provide no agent-level protocol for fanning concurrent writes back into one durable project. Ephemeral Sandbox makes the workspace session the boundary between private execution and shared LayerStack history, with capture, current-head reconciliation, and atomic data publication. Source and correctness tests can establish the mechanism; whether it raises useful-work concurrency requires measurement.

**Method phrase:** **One durable project truth, many private executable sessions, controlled publication.**

**Evidence boundary:** The paper does not claim a universal concurrency threshold, generic speedup, formal sandbox security, universal egress denial, process-state rollback, semantic merge correctness, or a complete agent coordination/resource plane.

## Manuscript skeleton

### 0. Title and abstract

**Purpose:** State the artifact, systems problem, mechanism, and evidence boundary in 150–200 words.

**Include:**

- OS/runtime abstraction mismatch for autonomous agent teams and swarms;
- private LayerStack workspace sessions;
- capture, merge/reject, and atomic data publication;
- explicit statement that concurrency-ceiling improvement is measured, not assumed.

**Evidence:** [`paper_story.md`](./paper_story.md), C1–C5 in [`claim_evidence_map.md`](./claim_evidence_map.md).

**Gate:** Rewrite last, after frozen evaluation results and limitations are complete.

### 1. Introduction

**Purpose:** Make the situation, issue, and bounded opportunity unmistakable.

**Paragraph plan:**

1. Agent systems can fan out research, review, planning, and separated modules, but fine-grained interdependent writers remain difficult to integrate.
2. Multi-agent coding is immature for model and coordination reasons; runtime-created interference should not become an artificial ceiling.
3. Conventional OS units—users, processes, files, descriptors, locks, and ports—do not encode agent task, project base, private session, resource ownership, or publish/reject state.
4. Structured teams and exploratory swarms encounter different dependency, conflict, staleness, resource, and integration limits.
5. Define useful-work rate and the workload-dependent concurrency ceiling.
6. Introduce the LayerStack workspace-session insight and state the limitations.
7. List contributions, each paired with its evidence type.

**Evidence:** Motivation claims M0–M6; source contributions C1–C4; evaluation contribution C5.

**Gate:** Do not say “raises the ceiling” in past tense until C5 has frozen results.

### 2. Problem statement and system model

**Purpose:** Define precisely what is shared, what is private, and what success means.

**Entities:**

- durable project head and ordered LayerStack history;
- leased base manifest/layers;
- implicit or explicit workspace session;
- private filesystem overlay and namespace-scoped execution;
- captured candidate changeset;
- publish, reject, retry, discard, and published-but-not-closed outcomes;
- management, runtime, and observability clients;
- coding worker, structured team, exploratory swarm, and orchestrator.

**State split:**

- **Private execution state:** uncommitted files, commands, processes, and experiments within a session.
- **Shared durable state:** accepted LayerStack history and active manifest.
- **Public operational state exposed by v1:** request/scope, lifecycle results, bounded traces/events/resources/topology/LayerStack views.
- **Coordination state not established by v1:** task intent, agent ownership, handoffs, port/service leases, resource budgets, and integration scheduling.

**Useful-work definition:** For workload \(W\), runtime \(R\), agent configuration \(A\), and worker count \(n\), measure verification-passing, durably accepted contribution units per wall time or cost. The concurrency ceiling is the workload-specific region in which marginal workers no longer improve that rate.

**Failure taxonomy:** shared-file visibility, multi-file inconsistency, stale bases, Git/worktree state, service/port collisions, compute/I/O saturation, lifecycle residue, audit gaps, lossy filesystem observation, and semantic integration.

**Gate:** Separate source-proven runtime properties from workload hypotheses.

### 3. Design goals and non-goals

**Goals:**

1. Stable private execution over changing shared history.
2. Faithful filesystem change capture.
3. Conflict-aware all-or-none data publication.
4. Atomic visibility of an accepted LayerStack head transition.
5. Explicit lifecycle and partial-failure outcomes.
6. Role-separated operational contracts for orchestration.
7. Measurable isolation, publication, scaling, and useful-work behavior.

**Non-goals:**

- formal security proof or complete noninterference;
- universal network-egress denial;
- process checkpoint/rollback;
- semantic merge correctness;
- general task decomposition, communication, or scheduling;
- current v1 port leases, service discovery, intent negotiation, handoffs, or resource budgets;
- Windows OverlayFS/reflink or generic cross-platform durability.

### 4. Design overview

**Purpose:** Explain the whole mechanism before implementation detail.

**Pipeline:**

1. Select and lease a LayerStack base.
2. Project shared lower layers with a unique private upper/work pair.
3. Execute tool calls in the session's namespace-scoped workspace.
4. Capture the complete private filesystem delta.
5. Reconcile the delta against the current durable head.
6. Merge eligible text or reject the unresolved data changeset as a whole.
7. Stage, sync, promote, and atomically replace the active manifest.
8. Attribute best-effort, close, retry, or report partial cleanup failure.

**Key distinction:** Data publication is atomic at the active-manifest visibility boundary; audit, accounting, and cleanup are later fallible phases.

**Evidence:** System stages in [`paper_story.md`](./paper_story.md); source map in [`project_inventory.md`](./project_inventory.md).

### 5. LayerStack and workspace-session design

#### 5.1 Shared version history

- layer/manifest representation;
- content digests and append-oriented history;
- active head and base selection;
- exact immutability wording.

#### 5.2 Leases, compaction, and snapshot stability

- manifest/layer lease acquisition;
- leased logical snapshot;
- squash/GC constraints;
- remount/substitution and restart questions.

#### 5.3 Private workspace projection

- shared lower layers;
- unique upper/work directories;
- OverlayFS whiteouts and opaque directories;
- Linux/platform boundary.

#### 5.4 Tool-call execution

- implicit session for sessionless `exec_command`;
- explicit session for multiple command/file calls;
- user, mount, PID, and optional network namespaces;
- shared-network default for implicit command sessions;
- sessionless file-operation qualifier.

#### 5.5 Capture

- writes, deletions, symlinks, empty and opaque directories;
- ordinary `.wh.*` names versus kernel whiteouts;
- protected drops and unsupported entry behavior.

**Evidence:** C1, D1–D4 in [`claim_evidence_map.md`](./claim_evidence_map.md).

### 6. Conflict-aware publication

#### 6.1 Planning and validation

- verify base and changeset;
- route/protect paths;
- fingerprint base/current/candidate states.

#### 6.2 Reconciliation

- unchanged-current fast path;
- eligible bounded three-way text merge;
- binary, oversized, invalid-UTF-8, structural, delete/modify, and conflicting-edit rejection;
- no semantic compatibility claim.

#### 6.3 Durable commit

- stage layer;
- sync and promote;
- construct manifest;
- atomic active-manifest replacement;
- no partial data changeset visibility.

#### 6.4 Partial failures

- precommit failure and retry;
- reject and retry;
- no-op publication;
- commit followed by audit failure;
- published-but-not-closed cleanup failure.

**Evidence:** C2, C4, D5–D9.

### 7. Operational interface

**Purpose:** Show how an orchestrator invokes and observes the runtime without conflating the CLI contract with runtime correctness.

#### 7.1 Management client

- host/fleet lifecycle, selection, compaction, and export;
- 8 baseline operations, regenerated at freeze.

#### 7.2 Runtime client

- sandbox-scoped command, file, attribution, and session lifecycle;
- 10 baseline operations, regenerated at freeze.

#### 7.3 Read-only observability client

- snapshot, trace, events, resources, daemon, topology, cgroup, and LayerStack;
- 8 baseline operations, regenerated at freeze.

#### 7.4 Shared protocol

- sandbox scope;
- request IDs;
- connection and token discovery;
- newline-framed JSON;
- stdout/stderr and exit-status contracts;
- catalog-derived help.

#### 7.5 Boundary

- smaller role-specific surfaces are an interface/least-exposure property;
- they are not alone an authorization or security guarantee;
- v1 is not a full task, intent, resource-lease, service-discovery, or handoff plane.

**Evidence:** [`cli_contract_matrix.md`](./cli_contract_matrix.md), C3, D10–D13.

### 8. Implementation

**Purpose:** Record source organization and engineering choices without turning modules into contributions.

**Cover:**

- Rust crates and process boundaries;
- LayerStack storage and publish locking;
- workspace and OverlayFS lifecycle;
- namespace holder/runner pattern;
- operation services and command ledger;
- catalog/projection/help generation;
- observability and audit storage;
- source-derived operational complexity and the distinction between logical and physically allocated storage;
- platform assumptions and dependencies.

**Gate:** Every source citation must be changed from the baseline commit to `paper-v1-freeze`.

#### 8.1 Operational cost model

Define \(L\) layers, \(S\) live sessions, \(U\) upperdir entries, \(C\) captured changes, \(F\) validated paths, \(B_p\) published bytes, \(Q\) concurrent publishers, and \(R\) layer references retained across leases. Summarize:

- \(O(L)\) lease/session setup metadata and \(O(R)\), commonly \(O(SL)\), live lease-manifest metadata;
- metadata-only capture over the private upperdir, including per-directory sorting;
- repeated layer/path/fingerprint work during planning and resolution;
- byte-proportional hashing/copy/sync plus manifest work inside the serialized publication path;
- the current line-merge algorithm's edit-distance-dependent time and retained-trace space;
- squash/GC costs and lease-induced history retention.

These are source-derived drivers, not latency or storage results. The authoritative working analysis is [`complexity_and_evolution.md`](./complexity_and_evolution.md).

### 9. Evaluation methodology

#### RQ1: Does each session observe a stable private executable workspace?

**Protocol:** concurrent leased sessions, controlled bases, cross-session file/process/network probes, compaction during leases, cleanup and restart.

**Measures:** visibility matrix, namespace identities, escaped-state failures, exact base/manifest/lease IDs, cleanup outcomes.

#### RQ2: Does publication implement the documented merge/reject and visibility semantics?

**Protocol:** disjoint stale writes, same-path merge, binary/structural conflicts, delete/modify, protected paths, concurrent publishers, storage and cleanup fault injection.

**Measures:** accept/reject class, changed paths, unrelated-path leakage, pre/post manifest, layer digest, retry outcome, partial failures.

#### RQ3: How do latency, storage, and resources scale?

**Protocol:** 1/2/4/8/... workers on fixed no-op, command, capture, publish, and conflict workloads with warmups and repeated measured runs. Independently vary layer depth, live-lease count and age, upperdir entry structure, changed-path count, payload bytes, merge line/edit-distance shape, and storage backend.

**Measures:** session start, execution, capture, publish, squash/GC, and end-to-end latency distributions; CPU, RSS/PSS, I/O, logical/allocated/shared/exclusive storage, writer wait/hold time, queueing, failures, and residual history after lease release.

#### RQ4: Does the runtime move useful-work concurrency under controlled coding workloads?

**Baselines:** shared mutable directory, Git worktrees, Ephemeral sessions.

**Workload families:**

- **Structured team:** explicit roles, task dependencies, handoffs, shared interfaces/services, and an integration lane.
- **Exploratory swarm:** redundant or competing proposals, hot-path overlap, rapidly changing heads, and result selection.

**Controls:** same model, prompts, budgets, repositories, tool versions, test harness, initial commits, worker counts, seeds/repeats, and integration acceptance.

**Primary measure:** verification-passing, durably accepted contribution units per wall time and resource cost.

**Secondary measures:** conflicts, retries, stale bases, duplicate work, integration/selection latency, clean textual publishes that fail tests, resource saturation, and human/lead repair if present.

#### RQ5: How complete is operational attribution and recovery?

**Protocol:** correlated accept, reject, retry, audit failure, cleanup failure, cancellation, and daemon restart.

**Measures:** request/base/path/result linkage, missing or `unknown` attribution, recovery time, residual sessions/processes/resources.

**Provenance required for every number:** source tag/commit, benchmark commit, dirty status, OS/kernel/filesystem, hardware, cgroup/runtime settings, toolchain, binary/image digests, workload commit, exact command/environment, seeds/repeats, raw events/logs, exclusions, and analysis commit.

### 10. Results

Do not draft numerical prose until frozen data exists. Reserve the following result structure:

1. isolation correctness matrix;
2. publication and injected-failure matrix;
3. latency/resource scaling curves;
4. useful-work curves by baseline and workload family;
5. conflict, retry, integration, and selection decomposition;
6. audit/recovery completeness;
7. negative results and the observed limiting regime.

Every result paragraph must state workload, runtime, model/agent configuration, worker range, metric, uncertainty, and exact evidence artifact.

### 11. Related work

Organize by:

1. agent sandboxes and isolated execution;
2. concurrent coding-agent coordination and integration;
3. reversible and versioned agent state;
4. private-workspace awareness and semantic merge;
5. union filesystems, copy-on-write, leases, and optimistic concurrency;
6. multi-agent coding benchmarks and product motivation.

**Position:** Ephemeral's bounded niche is a model- and orchestrator-independent runtime publication protocol: private executable sessions over leased shared history, followed by source-defined capture, current-head reconciliation, and atomic data publication.

**Evidence:** [`references/related_work.md`](./references/related_work.md).

### 12. Limitations and discussion

State prominently:

- workspace isolation is necessary for one failure class, not sufficient for collaboration;
- clean text reconciliation is not semantic correctness;
- shared networking remains possible and no universal egress guarantee is made;
- filesystem capture is not process rollback;
- audit is best-effort and not transactionally coupled to data publication;
- resource ownership/admission and general agent coordination remain open;
- publication is serialized and v1 keeps reconciliation plus byte hashing/copy/sync inside the writer critical section;
- per-lease manifest metadata scales with retained layer references, and long-lived leases can retain obsolete history;
- the 8 MiB text-merge byte limit does not eliminate the current diff trace's pathological line/edit-distance memory envelope;
- logical copy-on-write behavior is not a claim about physical extent sharing or cheap publication;
- the platform and crash claims are limited to the tested Linux environment;
- any concurrency result is workload- and runtime-specific.

Discuss the larger ambition separately from demonstrated results: the runtime should not force agent teams or swarms into low concurrency before task dependencies, agent quality, verification, or physical resources become the actual limit.

#### 12.1 Future evolution

Present LayerStack 2.0 only as a candidate response to the byte-copy/storage term: a qualified same-filesystem storage domain plus capability-gated reflink publication/copy-up, with a correctness-preserving copy fallback. Do not call reflink \(O(1)\), do not import preregistered thresholds as results, and disclose the pinned stock Windows Docker Desktop/WSL 2 feasibility failure (`FICLONE` `errno=95`). Also identify shorter writer critical sections, shared/compact lease metadata, indexed layered lookups, and independently bounded merge CPU/RSS as future targets. Evidence and wording boundaries are in [`complexity_and_evolution.md`](./complexity_and_evolution.md).

### 13. Conclusion

Return to the evidence:

- what the tagged source implements;
- what correctness and fault tests establish;
- what the measured workloads show;
- which limits remain.

Closing direction: multi-agent coding should be limited by the work and the agents, not prematurely by a shared mutable workspace and an undefined merge-back procedure.

## Figure and table skeleton

| ID | Type | Message | Evidence class | Status |
|---|---|---|---|---|
| Figure 1 | Teaser/problem diagram | Teams and swarms can fan out work but collide at workspace, resource, and integration planes; LayerStack sessions introduce a controlled publication boundary. | Concept-method | Planned |
| Figure 2 | Architecture | One durable LayerStack history, many leased private session views, capture, reconciliation, and one accepted head transition. | Concept-method | Planned |
| Figure 3 | State machine | Create → execute → capture → publish/reject → retry/discard/close, including published-but-not-closed. | Concept-method grounded in source | Planned |
| Table 1 | Design comparison | Shared directory vs worktree vs Ephemeral session across visibility, base identity, services/resources, merge-back, and attribution. | Mechanism comparison | Planned |
| Table 2 | CLI contract | Final management/runtime/observability operations and scopes from the tagged projections. | Source evidence | Baseline matrix exists; regenerate |
| Table 3 | Publication matrix | Exact merge/reject behavior by path/change class. | Source plus correctness tests | Planned |
| Table 4 | Operational cost model | Source-derived stage, scaling variables, critical section, live/peak space, and required measurement. | Source analysis, not a measured result | Drafted in `complexity_and_evolution.md` |
| Table 5 | Experimental setup | Hardware, software, workloads, agents, worker counts, controls, seeds, and metrics. | Experimental provenance | Blocked on freeze |
| Table 6 | Correctness/fault results | Isolation, publication, restart, audit, and cleanup outcomes. | Experimental result | Not run |
| Figure 4 | Useful-work scaling | Accepted verified progress versus workers for each baseline and workload family. | Experimental result | Not run |
| Figure 5 | Cost decomposition | Conflict, retry, integration, verification, and resource costs across concurrency. | Experimental result | Not run |

Generated concept figures communicate the mechanism only; they cannot serve as experimental evidence. Numerical figures and tables must be generated deterministically from preserved raw data and analysis code.

## Work packages

### WP1. Freeze and provenance

**Tasks:** resolve paper-specific source fixes, create annotated `paper-v1-freeze`, record commit/tag object/dirty status/toolchain/lockfile/binary digests, and relink all source claims.

**Done when:** every source claim names the freeze commit and the checkout/build provenance is archived.

### WP2. Interface freeze

**Tasks:** regenerate the three CLI catalogs/help snapshots, update operation counts and scopes, archive raw outputs, and document website drift.

**Done when:** [`cli_contract_matrix.md`](./cli_contract_matrix.md) matches the tagged binaries and contract tests pass separately from runtime tests.

### WP3. Runtime correctness and fault testing

**Tasks:** run the isolation, lease/compaction, capture, publication, concurrent-publisher, injected-storage-fault, audit, cleanup, cancellation, and restart matrices on the paper Linux platform.

**Done when:** commands, logs, configurations, and exact outcomes are archived and mapped to C1, C2, and C4.

### WP4. Scaling and resource evaluation

**Tasks:** run controlled session/start/capture/publish/conflict microbenchmarks across worker counts and collect latency, CPU, memory, I/O, storage, queueing, and failures.

**Done when:** repeatable raw runs, uncertainty analysis, and deterministic plots exist.

### WP5. Multi-agent workflow evaluation

**Tasks:** finalize structured-team and exploratory-swarm workloads; run shared-directory, Git-worktree, and Ephemeral baselines with matched models, budgets, prompts, tools, worker counts, and seeds.

**Done when:** useful-work, conflict, retry, integration, selection, verification, and resource results have complete provenance.

### WP6. Analysis and claim update

**Tasks:** compute metrics, uncertainty, negative results, cost decomposition, and the observed workload-specific ceiling; update C5 and every quantitative manuscript sentence.

**Done when:** every number is recomputable from raw data and the claim map labels its strength correctly.

### WP7. Manuscript, figures, and citations

**Tasks:** draft evidence-bearing core sections first; create source-grounded system figures and deterministic result plots; verify scholarly metadata and sentence-level support; then rewrite Introduction, Abstract, title, and Conclusion.

**Done when:** all citations and claims pass review and no placeholder is presented as a result.

### WP8. Skeptical review and release

**Tasks:** run source/evidence, systems novelty, experimental methodology, statistics, limitations, and reproducibility reviews; build the final paper and archive submission artifacts.

**Done when:** high-severity objections are resolved or recorded as explicit blockers and the final package builds from the frozen inputs.

## Dependency order

1. Fix source blockers and freeze v1.
2. Freeze the operational contract.
3. Run runtime correctness/fault tests.
4. Run scaling and workflow experiments.
5. Analyze results and update claims.
6. Draft the evidence-bearing system/evaluation/results sections.
7. Produce figures/tables and verify citations.
8. Rewrite title, abstract, introduction, limitations, and conclusion.
9. Conduct skeptical review, build, and package.

## Current blockers

1. `paper-v1-freeze` does not exist.
2. No paper-ready isolation, publication/fault, scaling/resource, or multi-agent workflow dataset exists.
3. Attribution is best-effort after data commit rather than atomically coupled to publication.
4. Explicit/implicit protected-drop behavior needs maintainer confirmation.
5. Lease/substitution and daemon-restart behavior needs fault testing.
6. Claim Plane requires deeper sentence-level novelty comparison.
7. Final structured-team and exploratory-swarm workloads, acceptance units, and integration policy must be fixed before measurement.

## Document map

- Current readiness, workflow lanes, gates, and next actions: [`progress.md`](./progress.md)
- Paper-writing execution contract: [`lanes/paper-writing.md`](./lanes/paper-writing.md)
- Experiment protocol, freeze, run, and evidence-handoff contract: [`lanes/experiments.md`](./lanes/experiments.md)
- Story, title, abstracts, introduction, contributions, and claim boundaries: [`paper_story.md`](./paper_story.md)
- Source, tests, documentation, and evidence inventory: [`project_inventory.md`](./project_inventory.md)
- Source-derived operational interface: [`cli_contract_matrix.md`](./cli_contract_matrix.md)
- Claim strength and evidence requirements: [`claim_evidence_map.md`](./claim_evidence_map.md)
- Related-work metadata and positioning: [`references/related_work.md`](./references/related_work.md)
