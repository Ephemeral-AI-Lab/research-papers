# Next-Agent Research Prompt — *Ephemeral Sandbox v1*

You are the research lead for an evidence-first arXiv preprint about **Ephemeral Sandbox v1**. The paper’s product aim is to **raise the ceiling on parallel coding agents**: enable more agents to work concurrently without sharing mutable workspace state, while making integration controlled and attributable.

This is a systems paper, not a product announcement. Do not invent measurements, security guarantees, citations, or capabilities not present in the final source snapshot.

## Start here

Read these project artifacts first:

- `PRD.md`
- `progress.md`
- the source repository checkout at `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox-v1`

The initial experimental baseline is upstream `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`. This line is mutable for paper-specific fixes and benchmarks. The final paper version will be an annotated `paper-v1-freeze` tag; record the exact commit for every source claim and experiment.

Before modifying source code, read the repository’s `AGENTS.md` and `CLAUDE.md`. Work directly on its `main` as required by those rules; do not create branches or worktrees.

## Established evidence constraints

- The live website is useful for product framing, but it is **not** the frozen v1 interface contract. It currently advertises 8 management, 7 runtime, and 5 observability CLI operations; the initial source baseline contains 8, 10, and 8 respectively. Generate the paper’s CLI reference from the final tagged source and use `crates/sandbox-cli/src/projection/{manager,runtime,observability}.rs` as primary interface evidence.
- Treat the “concurrency ceiling” as a workload- and runtime-dependent **useful-work** limit: added parallel attempts cease to help when conflict, retry, integration, verification, or resource costs grow faster than accepted progress. Do not claim a universal agent-count threshold, generic speedup, or that more agents always increase throughput.
- The closest direct comparisons currently include CAID (asynchronous coding-agent integration), CoAgent and Claim Plane (coordination/control-plane approaches), SWE-MiniSandbox (isolated SWE workspaces), DeltaBox (filesystem and process-state checkpoint/rollback), and Shepherd (reversible traces). The paper’s bounded niche is a runtime integration protocol: private execution views over immutable shared history plus conflict-aware, atomic durable publication.
## Core research question

How can a sandbox runtime raise the practical concurrency ceiling for coding agents by giving each agent a private, executable workspace over shared project history, then reconciling accepted changes through well-defined publication semantics?

The answer must separate:

- **What the runtime implements:** immutable layers/manifests, leases, copy-on-write overlays, namespace-scoped execution, capture, merge/reject behavior, atomic publication, lifecycle operations.
- **What the operational interfaces expose:** separate management, runtime, and read-only observability clients; sandbox scope; request correlation; connection/authentication discovery; JSON/exit-status contracts; catalog-derived help.
- **What needs measurement:** isolation correctness, publication behavior, latency/resource scaling, and any effect on multi-agent workflows.
- **What is explicitly out of scope:** formal sandbox security proof, universal egress denial, process-state rollback, unsupported Windows/reflink claims, and unmeasured productivity/performance claims.

## Required investigation

### 1. System, documentation, and interface inventory

Read the codebase, maintainer architecture documentation, and public documentation carefully:

- https://ephemeral-sandbox.com/
- https://ephemeral-sandbox.com/architecture
- https://ephemeral-sandbox.com/docs/cli
- CLI sub-pages for management, runtime, and observability where relevant

Map source modules and public documentation to these questions:

- What makes a workspace private, and what state is shared?
- How do leases preserve snapshot consistency and constrain compaction?
- How does capture validate changes and decide merge versus reject?
- What exactly becomes durable after publication?
- What operations belong to management, runtime, and observability clients, and why is that division useful for agent orchestration?
- Which documented behavior is source-proven versus merely a public description?

Write or update `project_inventory.md` and `cli_contract_matrix.md`. Each substantive statement must link to a source path, test, or stable documentation URL.

### 2. Problem framing: the concurrency ceiling

Read https://agent-infra-foundation.org/blog/2026/07/the-concurrency-ceiling-of-coding-agents/ closely.

Treat it as a problem-framing source, not empirical proof by itself. Extract its claims and classify each as:

- citation-safe factual claim with corroborating evidence;
- motivation or hypothesis;
- claim that needs a new experiment;
- claim outside the paper’s scope.

Formulate the gap precisely. A useful draft direction is:

> Parallel coding agents eventually become limited by interference in shared mutable state and uncontrolled integration, not merely by model parallelism.

Do not adopt that sentence unless the system model and evidence support its exact wording. Explain what Ephemeral Sandbox can address (workspace interference, execution isolation boundaries, controlled publication) and cannot address (model quality, task decomposition, semantic merge correctness, general agent coordination).

### 3. Related work

Find and verify relevant research papers, authoritative technical blogs, and GitHub projects. Include, but go beyond, DeltaBox, Shepherd, and AgentBay.

Group findings into:

1. agent sandboxes and isolated execution environments;
2. concurrent coding-agent coordination and code integration;
3. versioned filesystems, copy-on-write layers, checkpoint/rollback, and optimistic concurrency control;
4. agent-system benchmarks and evaluations that inform the concurrency framing.

For every candidate, record:

- title/project name, authors/organization, year, and stable URL;
- source type: peer-reviewed paper, preprint, official technical documentation/blog, or GitHub project;
- one-sentence relevance and one-sentence differentiation;
- whether it is safe to cite as scholarly related work, background motivation, or engineering inspiration only;
- any overlap or novelty risk.

Never cite a blog or GitHub README as empirical evidence. Verify every scholarly citation’s metadata and the sentence it supports.

## Required story deliverable

Create or update `paper_story.md` using this structure:

1. **Working titles** — give 3–5 concise candidates, none implying unmeasured performance or security.
2. **Recommended title** — choose one and explain the framing choice.
3. **One-sentence thesis** — artifact + task + mechanism + evidence boundary.
4. **Problem gap** — use a careful concurrency-ceiling framing.
5. **Technical challenges** — 2–4 concrete systems challenges.
6. **Method insight** — one central design principle, not a list of modules.
7. **System stages** — workspace projection, execution, capture, publication, lifecycle/observability.
8. **Contributions** — 3–5 contributions, each paired with its evidence status.
9. **Abstract options** — two 150–200 word drafts: one design-first and one evaluation-ready template. Use `[MEASURED RESULT NEEDED]` placeholders rather than invented numbers.
10. **Claims to make / be careful about / avoid**.
11. **Related-work position** — specific differentiation from the closest work.
12. **Reviewer risks and blockers**.

A likely title direction to test—not to assume—is:

> *Ephemeral Sandbox: Lease-Based Versioned Workspaces for Parallel Coding Agents*

## Evidence rules

- Ground design claims in the final tagged source snapshot, source paths, and relevant tests.
- Preserve raw experiment data, commands, configuration, environment, seeds, binary/image digests, and analysis code before reporting any number.
- Clearly label existing scripted runs as exploratory until rerun with v1 provenance.
- Separate CLI contract tests from runtime correctness tests and performance experiments.
- State limitations early. Do not overclaim that a systems mechanism “solves” parallel-agent coordination.

## Deliverables and handoff format

Update these files under this paper folder:

- `paper_story.md`
- `project_inventory.md`
- `cli_contract_matrix.md`
- `claim_evidence_map.md`
- `references/related_work.md`

Then report:

1. recommended title, thesis, and abstract option;
2. exact evidence supporting each proposed paper contribution;
3. unresolved questions and experiments required before arXiv submission;
4. a compact source/citation list with links;
5. changes made and checks run.

You may launch focused subagents for code/interface inventory, concurrency-problem framing, and related work, but you must integrate their findings, remove duplicate claims, and own the final evidence map.