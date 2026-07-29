# Product Requirements Document — *Ephemeral Sandbox v1* Paper

**Status:** Draft — evidence-gated  
**Paper folder:** `ephemeral-sandbox-v1/`  
**Initial experimental baseline:** upstream `ephemeral-sandbox` `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5` (2026-07-29)  
**Final paper freeze:** Pending — create an annotated tag after paper-specific fixes and benchmark completion; every run must record its exact commit.

**Primary submission target:** arXiv `cs.OS`; consider `cs.SE` and `cs.AI` cross-lists only after the evaluation supports their relevance.

## 1. Product objective

Produce a reproducible, technically precise arXiv preprint that records the v1 design of Ephemeral Sandbox: a runtime for concurrent coding agents that gives each workspace a private copy-on-write execution view of a shared project, then integrates accepted work through conflict-aware atomic publication.

The paper is a systems-design and evaluation paper. It must let a reader distinguish the implemented v1 mechanisms from hypotheses and from measured results. It is not a journal submission, security certification, or marketing document.

## 2. Research problem and thesis

Parallel coding agents need to make and execute changes without sharing mutable working state, while their useful results still need controlled integration into a common project. Ordinary shared worktrees risk interference; fully independent copies make synchronization, storage, and integration more expensive or less controlled.

**Thesis:** Ephemeral Sandbox realizes concurrent coding-agent workspaces as leased projections of immutable filesystem history. Each workspace mutates a private overlay upper layer and executes in scoped namespaces; capture validates changed paths against a snapshot and atomically publishes a new immutable layer, merging eligible text changes and rejecting incompatible conflicts.

## 3. Scope

The paper must document these v1 mechanisms, tied to the eventual final paper snapshot:

- LayerStack: immutable base, published, and squash layers represented by an active manifest.
- Lease acquisition over a manifest snapshot, with lease lifetime pinning the referenced layers.
- OverlayFS workspaces whose lower layers are shared read-only and whose upper/work directories are private.
- Persistent namespace holders and one-shot runners that enter the holder namespaces for commands and file operations.
- The public CLI contract: separate management, runtime, and read-only observability clients; sandbox-scoped runtime operations; stable request identity; gateway discovery/authentication; JSON output and exit-status behavior; and catalog-derived help.
- Capture and publication: changed-path validation, eligible text three-way merge, rejection of ineligible/binary conflicts, creation of one immutable published layer, and atomic manifest replacement.
- Lease-aware squash/remount behavior, including fail-closed remount gating.
- The implemented layered isolation model and its stated boundaries.

The paper must explain the design invariants before implementation details:

1. A workspace observes the manifest snapshot leased at creation.
2. Workspace writes remain private until successful publication.
3. Publication either creates one new durable layer from a validated result or leaves the active manifest unchanged.
4. Compaction cannot reclaim layers still pinned by leases.

## 4. Explicit non-goals and prohibited claims

Do **not** claim any of the following without new, directly supporting evidence:

- a formal security proof, sandbox-escape resistance, or universal network-egress blocking;
- process-state checkpoint/rollback, CRIU-like restore, or DeltaBox-equivalent execution rollback;
- superior speed, scalability, storage savings, cost, or agent productivity;
- Windows reflink support or Windows performance results;
- a general LLM-agent benchmark result based only on scripted runs;
- test success merely because test code exists.

The current code rejects the `rfc1918_egress=deny` path, so the paper must describe network behavior narrowly and accurately. The isolation discussion is a threat-model and implementation-boundary discussion, not a security evaluation.

## 5. Readers and success criteria

Primary readers are operating-systems, software-engineering, and agent-infrastructure researchers, plus engineers building multi-agent coding platforms.

A successful reader should be able to answer:

- What state is shared, what state is private, and for how long?
- How does a workspace obtain and retain a consistent view?
- What exactly happens when concurrent changes overlap?
- What is durable after publication, and what occurs on rejection or cleanup?
- Which claims have been measured on which platform and configuration?

## 6. Required paper structure

1. **Introduction** — problem, contribution, and precise thesis.
2. **Goals, non-goals, and threat model** — concurrency, durability, and containment boundaries.
3. **System model and invariants** — LayerStack, manifests, leases, workspace state.
4. **Workspace execution** — OverlayFS projection, private writes, holder/runner namespaces.
5. **Capture and publication** — optimistic validation, merge/reject policy, atomic manifest update.
6. **Lifecycle and recovery** — cleanup, squash, and lease-aware remount.
7. **Implementation and CLI boundary** — v1 component map plus the management, runtime, and observability client contracts.
8. **Evaluation** — correctness first; performance only after reproducible measurements.
9. **Limitations and related work** — clear distinctions from DeltaBox, Shepherd, and AgentBay.
10. **Conclusion** — bounded design contribution and open questions.

## 7. Evidence and evaluation requirements

No numeric result may enter the manuscript unless its raw data, command/configuration, environment, source SHA, binary/image digest, and analysis script are retained in this folder or a linked archival artifact.

### 7.1 Correctness gates

Run and record tests for:

- private-write isolation between simultaneous workspaces;
- three isolated namespaces and intended connectivity behavior;
- non-overlapping concurrent publications;
- overlapping changes that exercise merge, conflict rejection, and retry;
- cleanup after destroy/failure and manifest integrity after interrupted paths;
- lease-protected squash and remount behavior;
- CLI contract behavior: role separation, required sandbox scope, request correlation, JSON response/error envelopes, and exit-status classes.

### 7.2 Performance protocol

The primary platform should be Linux with cgroup v2. Freeze kernel, container/runtime versions, filesystem, hardware, configuration, and seeds. Compare against an independently provisioned container/worktree-per-agent baseline.

Sweep at least:

- agents: 1, 5, 20;
- payload sizes: 4 KiB, 256 KiB, 3 MiB;
- layer depths: 1, 10, 50, 100.

Report raw samples plus p50/p95/p99 for workspace creation, command execution, publication, squash, and remount. Also report physical disk use, RSS/CPU, throughput, failures, and confidence intervals. Explain baseline setup and any features it cannot match.

### 7.3 Agent-workload gate

The historical ten-lane scripted run (482/482 planned public operations in 56.4 seconds) is exploratory only: it predates v1 and lacks source/binary digest. Re-run it with full provenance before describing it as a reproducibility demonstration. Treat an LLM-agent benchmark as a later study requiring fixed model, prompt, tasks, budget, coordinator policy, success rubric, cost accounting, and cleanup checks.

### 7.4 Known blocker

The Windows Docker Desktop/WSL 2 reflink experiment failed with `errno=95`. This is a platform limitation to disclose, not a result to generalize. The existing public benchmark preset has no completed data and must not be cited as a measurement.

## 8. Related-work positioning

- **DeltaBox** targets high-frequency coupled filesystem and process-state checkpoint/rollback for search and RL. Ephemeral Sandbox v1 instead focuses on long-lived private filesystem workspaces, leases, and durable conflict-aware publication; it does not implement process-state rollback.
- **Shepherd** models reversible agent/environment traces as Git-like commits, forks, and reversions. Ephemeral Sandbox focuses on the workspace-runtime and integration boundary; the two are potentially complementary layers.
- **AgentBay** provides multi-platform cloud sandboxes with human graphical takeover and adaptive streaming. Its architecture is broader in interaction surface; Ephemeral Sandbox concentrates on versioned filesystem workspaces and publish semantics. Do not use AgentBay's hypothetical evaluation data as empirical comparison.

## 9. Required paper artifacts

Create and maintain the following under this folder:

- `paper_story.md` — one-sentence thesis, reader, contribution, and section arc.
- `project_inventory.md` — source paths, v1 snapshot, test locations, experiments, environment facts.
- `claim_evidence_map.md` — every substantive claim mapped to code, measurement, or qualified limitation.
- `cli_contract_matrix.md` — public command families mapped to runtime operations, state effects, and contract tests.
- `main.tex`, `references.bib`, and a reproducible build command.
- `figures/` — architecture diagram, workspace/publication state sequence, and evaluation figures generated from data.
- `experiments/` — immutable run manifests, raw samples, analysis scripts, and result tables.
- `ARTIFACTS.md` — how to reproduce evaluation and locate binaries/images/data.
- `paper.pdf` — generated release candidate only after all claim gates pass.

## 10. Acceptance criteria

The paper is ready for arXiv submission only when all conditions hold:

- The title, abstract, and conclusion make bounded, evidence-supported claims.
- Every design statement links to the final annotated paper tag or a documented architectural decision.
- Every number is reproducible from retained raw data and scripts.
- Evaluation distinguishes implementation tests, scripted demonstrations, and LLM-agent experiments.
- Related-work citations are verified and describe differences without unsupported performance comparisons.
- CLI behavior in the manuscript is cross-checked against source and the versioned CLI reference.
- Limitations include current network-policy boundaries and the Windows reflink failure.
- The LaTeX source compiles in the arXiv-compatible environment and ships without undeclared generated dependencies.
- A final skeptical pass finds no language implying security, performance, or generality beyond the evidence.

## 11. Milestones

1. Freeze scope, commit SHA, and architecture inventory.
2. Write `paper_story.md`, inventory, and the claim–evidence map.
3. Implement/run correctness experiments and archive results.
4. Run the baseline comparison and analyze results.
5. Draft figures, tables, and main text around validated evidence.
6. Complete citation, reproducibility, and arXiv build checks.
7. Publish the source/artifact repository; submit the LaTeX source to arXiv; link the arXiv record and artifacts from Hugging Face.

## 12. Sources reviewed

- [DeltaBox](https://arxiv.org/pdf/2605.22781)
- [AgentBay](https://arxiv.org/html/2512.04367v1)
- [Shepherd](https://arxiv.org/pdf/2605.10913)
- [Ephemeral Sandbox architecture](https://ephemeral-sandbox.com/architecture)
- [Ephemeral Sandbox CLI reference](https://ephemeral-sandbox.com/docs/cli)
