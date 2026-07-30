# Paper story: Ephemeral Sandbox v1

Status: design story grounded in source baseline [`b22862550e0a7cb4fe61ce581831e9244cc492b5`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5), audited 2026-07-30. The final paper must use the annotated `paper-v1-freeze` commit. No performance or multi-agent workflow result is yet paper-ready.

The section-by-section execution plan, evidence dependencies, figure/table plan, and work packages are in [`paper_skeleton.md`](./paper_skeleton.md).

## Working titles

1. **Ephemeral Sandbox: A LayerStack Workspace OS for Parallel Coding Agents**
2. **Ephemeral Sandbox: LayerStack Sessions for Parallel Coding Agents**
3. **Ephemeral Sandbox: Private Sessions over LayerStack**
4. **Ephemeral Sandbox: LayerStack Isolation and Controlled Publication**
5. **Ephemeral Sandbox: Raising Coding-Agent Concurrency with a LayerStack OS** — use only if the final evaluation demonstrates this result.

None claims measured speedup, a universal concurrency threshold, security, or semantic merge correctness.

## Recommended title

**Ephemeral Sandbox: A LayerStack Workspace OS for Parallel Coding Agents**

Three independent reviewers audited the options from source-accuracy, concurrency-evidence, and related-work perspectives. The source reviewer preferred “Private LayerStack Workspace Sessions and Controlled Publication for Parallel Coding Agents”; the other two independently proposed the near-identical “Private LayerStack Workspaces with Controlled Publication for Parallel Coding Agents.” All three rejected an unconditional “raising the ceiling” title before measurement and warned that “OS” can invite broader kernel/security expectations.

The recommendation synthesizes that consensus with the desired systems identity without forcing every mechanism into the title. It names the artifact, LayerStack substrate, workspace-OS role, and parallel-agent domain in ten words. The thesis and abstract carry the private-session and controlled-publication details. Options 2–4 are progressively more mechanism-specific; option 5 becomes eligible only if frozen experiments show higher workload-specific useful-work concurrency against named baselines.

## One-sentence thesis

Ephemeral Sandbox is a LayerStack workspace OS that executes each sessionless command tool call in an isolated workspace session, optionally groups multiple tool calls in an explicit session, and returns accepted filesystem changes to shared history only through capture, current-head reconciliation, and atomic data publication; source and tests establish the mechanism, while whether it raises the useful-work concurrency ceiling remains unmeasured.

## Problem gap

Conventional operating systems expose collaboration primitives for human-operated applications and cooperative processes: users, files, descriptors, locks, process identifiers, ports, permissions, and mutable namespaces. They do not expose a first-class coding-agent role, delegated task, workspace-session boundary, base revision, resource ownership record, or publish/reject event. A human developer can often reconstruct these relationships from a terminal, editor, Git history, and team conversation. An autonomous multi-agent runtime must establish them explicitly and repeatedly at machine speed.

This abstraction mismatch matters because concurrent coding-agent tool calls do more than write independent patches. They inspect a changing project, perform multi-file edits, run builds and tests, start services, consume shared resources, and return results that may have been produced against different project states. In one native mutable workspace, intermediate edits and execution side effects can leak across agents. Separate copies or Git worktrees reduce direct file interference but leave service ownership, resource admission, stale-base detection, integration ordering, verification, and attribution to external coordination.

Two multi-agent regimes expose different limits. In an **agent team**, workers have relatively stable roles, delegated tasks, and an orchestrator or lead. Its concurrency ceiling can be dominated by dependency-aware scheduling, ownership and handoff delays, shared-service conflicts, and a serial integration/verification lane. In an **agent swarm**, many workers explore or implement concurrently with weaker central coordination. Its ceiling can be dominated by duplicated work, hot-path collisions, rapidly stale bases, resource saturation, publication contention, and the cost of attributing and selecting among competing results. These are workload models for evaluation, not claims that every product implements one regime cleanly or that either has a fixed agent-count threshold.

The product survey in [“What agent teams prove—and what their runtimes leave open”](https://agent-infra-foundation.org/blog/2026/07/the-concurrency-ceiling-of-coding-agents/) supports a narrower, useful observation: current agent-team interfaces make parallel research, review, planning, and separated modules legible, while their own guidance remains cautious about interdependent concurrent writes. Task lists, messages, role canvases, dynamic plans, worktrees, and remote machines organize workers, but do not by themselves define private copy-on-write visibility, resource ownership, current-head reconciliation, atomic data publication, or an integration policy. These product documents establish engineering motivation, not scholarly evidence that a particular runtime raises coding concurrency.

Existing evidence shows coordination and textual-integration failures in overlap-prone workloads, but it does not identify a universal agent-count ceiling or prove that the runtime substrate is the dominant cause. CooperBench v2 is especially instructive: agents operate in separate containers yet still suffer coordination and joint-integration failures. Isolation is therefore necessary for one class of interference, not sufficient for collaboration.

For workload \(W\), runtime \(R\), agent configuration \(A\), and worker count \(n\), define useful-work rate \(U(W,R,A,n)\) as verification-passing, durably accepted contribution units per unit wall time or cost. A practical concurrency ceiling is a workload- and runtime-specific region where increasing \(n\) no longer improves \(U\) because conflict, retry, integration, verification, or resource costs dominate marginal accepted progress. There is no universal threshold and no presumption that \(U\) is monotonic.

The systems gap studied here is narrower: a coding-agent runtime needs a private workspace-session boundary for tool execution and a defined path for merging captured session changes back into recorded project history. Ephemeral Sandbox can address direct workspace interference, namespace-scoped execution boundaries, stale/overlapping publication, and typed lifecycle outcomes. It cannot fix model quality, task decomposition, architectural disagreement, semantic merge correctness, general agent communication/scheduling, or verification design.

Problem-framing sources and their bounded uses are audited in [`references/related_work.md`](./references/related_work.md) and [`claim_evidence_map.md`](./claim_evidence_map.md). The Agent Infra Foundation's [concurrency-ceiling article](https://agent-infra-foundation.org/blog/2026/07/the-concurrency-ceiling-of-coding-agents/) is motivation, not empirical proof.

## Introduction opening (working draft)

Agent systems have learned to fan out intelligence; their runtimes still lack a principled way to fan concurrent writes back into one durable project. Current agent teams are effective at research, review, planning, and work that can be divided into separated modules. Fine-grained coding is harder. Workers edit related files, run commands against changing dependencies, start services, and produce locally successful results that must eventually coexist at one project head.

Multi-agent coding remains an immature systems setting. Agents can miscommunicate, choose poor decompositions, duplicate work, make incompatible architectural assumptions, and produce changes that merge textually but fail together. A workspace runtime cannot solve those problems. They are also not a reason to accept avoidable interference from a substrate that has no agent-level session or publication abstraction. The runtime should remove the conflicts it creates itself, so the measured limit reflects the coding workload, agents, and coordination method rather than a shared mutable checkout and an improvised merge procedure.

Conventional operating systems were organized around human-operated applications and cooperative processes, not autonomous teams of coding agents. Their first-class units are users, processes, files, descriptors, locks, and ports. They do not represent an agent's delegated task, the project revision it observed, the lifetime of its private execution state, the resources it owns, or the decision that makes its result durable. Human developers reconstruct this context through editors, terminals, Git, and conversation. At multi-agent speed, leaving it implicit turns concurrent coding into a collection of filesystem, process, service, and integration races.

Structured agent teams and exploratory swarms encounter this limit differently. Teams can stall at dependency handoffs, shared services, and a serial integration lane; swarms can saturate the same code paths and resources with duplicated or rapidly stale work. In both cases, adding workers can stop improving verification-passing, durably accepted progress when conflicts, retries, integration, verification, or resource costs dominate. This workload-dependent point is the concurrency ceiling—not a universal agent count and not a claim that more agents always help.

Ephemeral Sandbox treats this ceiling as a runtime-systems problem. Its central abstraction is a private workspace session over a leased LayerStack base: one durable project history, many private executable views, and one controlled boundary for capture, current-head reconciliation, and atomic data publication. The mechanism isolates uncertain work without treating isolation as collaboration itself. It does not make agents agree on architecture, decompose tasks correctly, or validate semantic compatibility. The paper therefore asks whether explicit workspace sessions and controlled publication can move the measured useful-work ceiling under stated coding workloads, rather than assuming that result.

## Technical challenges

1. **Stable execution over changing history.** A session must retain an executable snapshot while other publications advance the head and compaction changes the physical layer representation. The baseline uses a manifest/layer lease and lease-aware squash/GC ([LayerStack](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack)).
2. **Faithful capture at the filesystem boundary.** The runtime must recover writes, deletes, symlinks, empty directories, and opaque directories from OverlayFS metadata without confusing ordinary `.wh.*` names for kernel whiteouts, and it must make unsupported entries explicit ([capture](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/capture.rs), [tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/tests/unit/overlay_capture.rs)).
3. **Current-head reconciliation without partial visibility.** A delta produced against a leased base must be compared with the active head, merged only under defined rules, rejected as a whole when unresolved, and made visible through one durable manifest transition ([publish resolver](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/resolve.rs), [commit path](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs)).
4. **Lifecycle and failure attribution across non-atomic phases.** Capture, data commit, best-effort audit, and session destruction have distinct failure points. The interface must distinguish retryable precommit failure from published-but-not-closed cleanup failure ([publish service](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/impls/publish_session.rs), [tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session_publish.rs)).

## Method insight

**Make the workspace session the boundary between a tool call and shared LayerStack history.** Execute a sessionless command tool call in a private session—or group related tool calls in one explicit session—then cross back into shared history only by capturing and validating the session's complete filesystem delta against the current head.

In compact form: **one durable project truth, many private executable sessions, controlled publication.** This makes coding concurrency an explicit runtime concern rather than an improvised consequence of task prompts, worktree conventions, and lead-agent merge repair.

This is deliberately not described as a full transaction: the resolved data changeset is atomic at the active-manifest visibility boundary, while audit attribution, accounting, and post-publication cleanup are later, fallible phases.

## System stages

1. **Workspace projection.** The initial project is copied into a base layer. Session creation acquires an exact LayerStack manifest/layer lease and mounts those shared lowers with a fresh private upper/work pair ([workspace creation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/lifecycle/create.rs), [overlay mount](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/overlay/src/kernel_mount.rs)).
2. **Tool-call execution.** A sessionless `exec_command` call creates one implicit workspace session with `publish_then_destroy`; an explicit session can host multiple command and file calls until the caller publishes or destroys it ([command path](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/command/service/exec_command.rs), [finalization model](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/model.rs)). A holder owns user, mount, PID, and optionally network namespaces; runners join the stored handles without moving the daemon itself into the session ([namespace holder](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-process/src/holder/namespace.rs), [setns](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-process/src/runner/setns/namespaces.rs)).
3. **Capture.** The runtime walks the private upperdir and translates kernel OverlayFS metadata into typed layer changes and protected drops ([capture](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/capture.rs)).
4. **Publication.** Planning validates the base and routes paths; the exclusive commit phase rereads the active head, resolves fingerprints/eligible text merges, rejects the whole data changeset on unresolved conflict, or stages/syncs/promotes one layer and atomically replaces the active manifest ([plan](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/plan.rs), [resolve](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/resolve.rs), [publish](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs)). Audit attribution is best-effort after commit.
5. **Merge-back lifecycle and observability.** When an implicit command session drains, it captures, publishes or rejects, and destroys; an explicit session supports deliberate publish/retry or discard. Three catalog-derived clients separate management, sandbox runtime, and read-only observability operations ([CLI matrix](./cli_contract_matrix.md)).

## Proposed contributions and evidence status

1. **LayerStack-backed workspace-session protocol.** A sessionless command tool call receives an implicit private workspace over an exact LayerStack lease, while an explicit session can group multiple command/file calls before publication or discard. **Evidence:** implemented at the baseline; session lifecycle, capture, and squash/lease behavior have correctness tests; final-tag isolation and restart tests still need to run. See C1 in [`claim_evidence_map.md`](./claim_evidence_map.md).
2. **Conflict-aware atomic data publication.** A whole-changeset protocol with base validation, path fingerprints, structural rejection, bounded eligible text merge, staged layer promotion, and atomic active-manifest replacement. **Evidence:** implemented and covered by LayerStack and explicit-session publication tests; paper-platform fault testing still needed. This excludes semantic correctness, audit, accounting, and cleanup. See C2.
3. **Role-separated operational contract.** Separate management, sandbox-runtime, and read-only observability clients with catalog-derived help, typed scope, request IDs, connection/token discovery, and JSON/exit contracts. **Evidence:** implemented and contract-tested at 8/10/8 baseline operations; must be regenerated from the final tag. See C3.
4. **Explicit lifecycle and partial-failure semantics.** Persistent and implicit workspaces distinguish retryable precommit failure, discard, successful publication, and published-but-not-closed cleanup failure. **Evidence:** implemented and correctness-tested; protected-drop policy and daemon-restart recovery remain open. See C4.
5. **A concurrency-ceiling evaluation methodology.** Measure accepted verified progress, conflict/retry/integration costs, and runtime resources across worker counts and workspace strategies. **Evidence:** external presets and exploratory demos exist, but no final dataset. This is a planned contribution, not yet a result. Drop or demote it if the freeze evaluation is not completed. See C5.

## Abstract option A: design-first

Agent systems can fan out intelligence, but conventional operating-system workspaces provide no agent-level protocol for fanning concurrent writes back into one durable project. Coding-agent teams and swarms inspect changing code, perform multi-file edits, run tests, and start services; sharing one mutable workspace permits live-state interference, while copying workspaces alone defers integration. We present Ephemeral Sandbox, a workspace OS organized around LayerStack: one durable project history, many private executable sessions, and controlled publication. A sessionless `exec_command` tool call receives an implicit isolated session over a leased LayerStack snapshot. When its command ledger drains, the runtime captures the private overlay, reconciles the complete delta against the current head, and either publishes one new layer or returns a structured rejection. Eligible text divergence can use a bounded three-way merge; structural, binary, oversized, or conflicting changes reject. Explicit sessions let multiple command and file tool calls share private state before publication or discard. Source and correctness tests establish these mechanisms, but not formal security, semantic merge correctness, process-state rollback, resource coordination, or improved multi-agent throughput. Whether Ephemeral Sandbox raises the workload-dependent useful-work concurrency ceiling remains an empirical question.

## Abstract option B: evaluation-ready template

Conventional operating-system workspaces provide process- and file-level concurrency, but no agent-level unit connecting a delegated task, private execution state, resource ownership, and a controlled publication decision. Coding-agent teams and swarms can therefore lose useful work through mutable-state interference, stale results, resource collisions, and deferred integration. We present Ephemeral Sandbox, a LayerStack workspace OS in which each sessionless command tool call executes inside an implicit isolated workspace session, while explicit sessions can group multiple command and file calls. Merge-back captures the private overlay, validates its complete delta against the current LayerStack head, and either performs bounded eligible text reconciliation, publishes one layer through an atomic manifest transition, or rejects the data changeset. We evaluate isolation and publication using [MEASURED RESULT NEEDED] adversarial cases, then compare shared-directory, Git-worktree, and Ephemeral-session baselines across structured-team and exploratory-swarm workloads with [MEASURED RESULT NEEDED] workers. We report verification-passing durably accepted work, conflicts, retries, integration latency, resource cost, and attribution completeness. Ephemeral Sandbox achieves [MEASURED RESULT NEEDED] under [EXACT CONDITIONS NEEDED], while [LIMITING RESULT NEEDED] identifies when coordination, verification, conflicts, or resources dominate marginal progress. The result is workload-specific, not a universal speedup, security guarantee, or solution to semantic coordination.

## Claims to make

- v1 implements private writable Linux overlay views over leased recorded history, with namespace-scoped command/file execution.
- a sessionless `exec_command` call creates an implicit isolated workspace session and uses `publish_then_destroy` after its command ledger drains.
- an explicit workspace session can carry private state across multiple command and file tool calls before explicit publication or discard.
- leases retain a captured logical snapshot and constrain compaction/GC.
- capture translates kernel OverlayFS state into typed filesystem changes and protected drops.
- publication applies defined current-head validation, bounded text merge, structured reject, and all-or-none data-changeset behavior.
- successful data publication promotes a layer/digest and changes active-manifest visibility atomically in the implemented commit path.
- the baseline source contract contains 8 management, 10 runtime, and 8 observability operations, with the exact scopes in [`cli_contract_matrix.md`](./cli_contract_matrix.md).
- explicit lifecycle states distinguish precommit retry from post-commit cleanup failure.

## Claims to be careful about

- **Immutable history:** call layers append-oriented/content-digested and treated as immutable after promotion; do not claim filesystem-enforced immutability against external mutation.
- **Isolation:** specify private upperdir and namespace profile. Default/shared networking is not egress isolation.
- **Workspace OS:** define it as the runtime substrate for workspace-session execution, LayerStack history, publication, lifecycle, and observability; do not imply a general-purpose OS, kernel, or security monitor.
- **Per-tool-call sessions:** this is exact for sessionless `exec_command`. Sessionless `file_read` projects the active LayerStack, while sessionless `file_write` and `file_edit` amend the current head directly; do not claim that every runtime operation creates a workspace session.
- **Atomic:** scope it to one resolved data changeset and the active-manifest visibility boundary.
- **Attributable:** request correlation and a best-effort audit log exist, but audit is not transactionally coupled and may be `unknown`.
- **Conflict-aware:** enumerate fingerprints, structural checks, protected paths, and bounded line merge; do not imply semantic conflict detection.
- **Durable:** bind it to the tested Linux/filesystem/fault model; the source alone is not a cross-platform crash proof.
- **Concurrency ceiling:** define workload, runtime, agents, metric, cost basis, and uncertainty for every result.
- **Observability:** source-prove which views exist; do not imply that agents necessarily use them effectively.
- **Complexity:** present a stage-specific operational cost model, not one context-free runtime bound. Separate source-derived \(L,S,U,C,F,B,Q,R\) terms from measured latency, RSS, queueing, and physical allocation.
- **Bounded merge:** the 8 MiB byte gate bounds file inputs, not the current Myers trace's practical line/edit-distance memory envelope.
- **LayerStack 2.0:** describe it only as a candidate future response to v1 byte-copy/storage amplification; capability detection, extent-dependent cost, semantic preservation, and copy fallback are mandatory qualifiers.

## Claims to avoid

- a universal concurrency ceiling or a single-digit threshold;
- generic speedup, cheapness, scalability, productivity, or monotonic benefit from more agents;
- “solves” parallel-agent coordination;
- formal sandbox security, complete noninterference, or universal egress denial;
- process-state checkpoint/rollback;
- semantic merge correctness or serializable snapshot isolation;
- unsupported Windows overlay, reflink, locking, or durability claims;
- \(O(1)\), universally available, or already implemented reflink publication;
- atomic coupling of data, line attribution, accounting, and cleanup;
- current v1 support for intent negotiation, service/port ownership, scheduling, handoffs, or resource budgets unless added and source-proven before freeze.

## Related-work position

- **CAID:** orchestrates asynchronous engineers in Git worktrees and performs harness-level merge/verification; Ephemeral supplies a lower-level model/orchestrator-independent capture/publication runtime.
- **CoAgent:** speculates on shared mutable state and repairs/reorders effects; Ephemeral isolates writes and validates before durable visibility.
- **Claim Plane:** admits typed change intents and authority before work; Ephemeral's niche begins with private execution and ends with current-head publication. This is the highest novelty risk.
- **SWE-MiniSandbox:** optimizes isolated task environments; it does not reconcile results into shared history.
- **DeltaBox:** couples layered filesystem state with process checkpoint/rollback for tree search; Ephemeral does not roll back process state and instead focuses on multiwriter durable publication.
- **Shepherd:** records reversible agent/environment traces for meta-agent replay and intervention; Ephemeral records workspace history and publication outcomes, not full reversible execution.
- **Union mounts and OCC:** establish the primitives. Novelty, if any, lies in the composition and source-defined lifecycle/operational protocol.
- **Palantir, Crystal, and Verified Three-Way Program Merge:** show that private workspaces defer integration issues and that textual cleanliness is not semantic correctness.

Full metadata, citation safety, and overlap risks are in [`references/related_work.md`](./references/related_work.md).

## Complexity and evolution position

The manuscript should include a compact source-derived cost table in Implementation and test its variables in Evaluation. The strongest current hypotheses are that history depth multiplies session/validation metadata, upperdir structure controls capture, published bytes and reconciliation work extend the serialized writer path, and long-lived leases trade stable views for retained history. These are mechanisms to measure, not performance conclusions. The derivation and experiment matrix are in [`complexity_and_evolution.md`](./complexity_and_evolution.md).

LayerStack 2.0 belongs in Limitations/Future Work, not the abstract or v1 contributions. Its single-storage-domain/reflink protocol targets publication and allocation amplification while requiring unchanged blame, squash, remount, active execution, crash, memory, image, and privilege behavior. The only completed Windows evidence is negative and narrow: direct `FICLONE` failed with `errno=95` in the pinned stock Docker Desktop/WSL 2 cell, so the integrated candidate was not run and a copy fallback remains necessary.

## Reviewer risks and blockers

1. **Freeze/provenance:** `paper-v1-freeze` is absent. All current source citations are provisional.
2. **Evaluation gap:** no paper-ready isolation, fault, scaling, resource, or multi-agent workflow results exist.
3. **Novelty:** Claim Plane, CAID, Shepherd, CoAgent, DeltaBox, union mounts, and OCC substantially overlap individual ideas. The paper must make a composition/protocol claim and audit Claim Plane fully.
4. **Attribution mismatch:** the product aim says attributable integration, but source audit is best-effort after data commit. Either state this plainly, strengthen and test the implementation before freeze, or narrow the contribution.
5. **Failure model:** restart ordering for in-memory leases/substitutions and explicit/implicit protected-drop asymmetry need resolution.
6. **Atomicity wording:** reviewers will object if data, audit, and cleanup are described as one transaction.
7. **Semantic boundary:** clean text merge can still fail build/tests; evaluation should measure this rather than hide it.
8. **Platform scope:** core overlay/namespace behavior is Linux-only; Windows/reflink claims are unsupported.
9. **Cost-model validation:** layer-depth, live-lease, upperdir-shape, changed-path/byte, writer-queue, merge-shape, and retained-history predictions have not been validated on the freeze.
10. **Merge resource risk:** the current byte gate does not independently bound the retained diff trace; add adversarial CPU/RSS evidence or change the implementation before freeze.
11. **Benchmark validity:** compare matched agent/model/budget/workloads, preserve raw provenance, report uncertainty, and avoid treating deterministic demos or ignored benches as final evidence.
