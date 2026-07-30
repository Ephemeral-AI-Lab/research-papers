# Related-work audit for Ephemeral Sandbox v1

Metadata and sentence-level support were checked against primary paper records, versioned manuscripts, proceedings pages, or official project documentation on 2026-07-30. Recheck every mutable 2025–2026 preprint immediately before submission.

## Position in one paragraph

Prior work either provisions isolated execution environments, coordinates coding agents through Git or intent/control-plane protocols, makes agent and environment state reversible, or detects integration conflicts around private branches. Ephemeral Sandbox's bounded niche is a **runtime publication protocol**: private executable workspace sessions are derived from leased shared LayerStack history; captured changes are validated against the current head; and an accepted data changeset becomes visible through a new layer and active-manifest transition. Private copy-on-write views, mount namespaces, leases, optimistic validation, and three-way merge are not individually novel. The potential contribution is their source-defined composition and lifecycle/operational contract for coding-agent tool calls and sessions. The final tagged source and evaluation must establish that composition.

Closest novelty risks: Claim Plane, CAID, Shepherd, CoAgent, DeltaBox, classic union mounts, and optimistic concurrency control. Do not claim that v1 invents isolated workspaces, copy-on-write views, immutable histories, or validate-before-commit.

## 1. Agent sandboxes and isolated execution environments

### SWE-MiniSandbox

- **Record:** Danlong Yuan, Wei Wu, Enhan Zhao, Zhengren Wang, Xueliang Zhao, Huishuai Zhang, and Dongyan Zhao. “SWE-MiniSandbox: Container-Free Reinforcement Learning for Building Software Engineering Agents.” 2026. [arXiv:2602.11210v5](https://arxiv.org/abs/2602.11210v5).
- **Type/organization:** arXiv preprint; affiliations are not clearly stated in the current manuscript.
- **Relevance:** Runs software-engineering tasks in private directories using mount namespaces and chroot-based isolation, with environment pre-caching aimed at concurrent RL workloads.
- **Differentiation:** It focuses on provisioning and execution isolation, not reconciliation or atomic durable publication into shared version history.
- **Citation use:** Scholarly related work, explicitly qualified as a preprint.
- **Overlap/novelty risk:** High for lightweight private executable workspaces; low for publication semantics.

### SWE-ReX

- **Record:** SWE-agent project contributors. “SWE-agent Remote Execution Framework (SWE-ReX).” Public 1.x releases, 2025. [GitHub project](https://github.com/SWE-agent/SWE-ReX); [official architecture](https://swe-rex.com/latest/architecture/).
- **Type/organization:** Official open-source project and technical documentation; SWE-agent.
- **Relevance:** Provides a backend-independent shell, command-session, and file-operation interface across local, Docker, Modal, AWS, and other backends.
- **Differentiation:** It abstracts execution backends and parallel runs but does not define shared version history or capture/reconciliation/publication semantics.
- **Citation use:** Engineering comparison/inspiration only, never empirical evidence. Pin a release or commit if retained.
- **Overlap/novelty risk:** Medium for runtime-client abstraction; low for publication.

### AgentBay

- **Record:** Yun Piao et al. (31 authors), Alibaba Cloud Computing. “AgentBay: A Hybrid Interaction Sandbox for Seamless Human-AI Intervention in Agentic Systems.” 2025. [arXiv:2512.04367v1](https://arxiv.org/abs/2512.04367v1).
- **Type/organization:** arXiv preprint; Alibaba Cloud Computing.
- **Relevance:** Provides isolated multi-platform sessions with programmatic agent control and graphical human takeover.
- **Differentiation:** Its central concern is hybrid agent/human interaction and streaming, not immutable project history, capture, conflict validation, or publication.
- **Citation use:** Design-landscape background only.
- **Overlap/novelty risk:** Low.
- **Evidence hazard:** The manuscript explicitly labels its evaluation contribution as using hypothetical data. Do not cite its security, latency, bandwidth, or success numbers as empirical results.

## 2. Reversible and versioned agent state

### DeltaBox

- **Record:** Yunpeng Dong, Jingkai He, Shiqi Liu, Yuze Hou, Dong Du, Zhonghu Xu, Si Yu, Baochuan Yang, Yubin Xia, and Haibo Chen. “DeltaBox: Scaling Stateful AI Agents with Millisecond-Level Sandbox Checkpoint/Rollback.” 2026. [arXiv:2605.22781v2](https://arxiv.org/abs/2605.22781v2).
- **Type/organization:** arXiv preprint; Shanghai Jiao Tong University and Huawei.
- **Relevance:** DeltaFS freezes writable layers and inserts new copy-on-write layers; DeltaCR couples filesystem state to process checkpoint/rollback for tree search and RL.
- **Differentiation:** Ephemeral concerns reconciling multiple private filesystem views into durable shared history and explicitly does not claim process-state rollback.
- **Citation use:** Scholarly systems related work, qualified as a preprint.
- **Overlap/novelty risk:** Very high for layered filesystem-state management; low-to-medium for multiwriter publication.
- **Evidence hazard:** The v2 landing abstract and v2 manuscript report inconsistent checkpoint/rollback timings. Do not cite a number until the versioned PDF table and artifact are reconciled.

### Shepherd

- **Record:** Simon Yu, Derek Chong, Ananjan Nandi, Dilara Soylu, Jiuding Sun, Christopher D. Manning, and Weiyan Shi. “Shepherd: Enabling Programmable Meta-Agents via Reversible Agentic Execution Traces.” 2026. [arXiv:2605.10913v3](https://arxiv.org/abs/2605.10913v3).
- **Type/organization:** arXiv preprint; Northeastern University and Stanford University.
- **Relevance:** Represents agent actions and environmental effects as reversible Git-like traces; scopes can fork, merge, or discard isolated agent-plus-environment state.
- **Differentiation:** Shepherd's object is a replayable execution trace for intervention and meta-agents. Ephemeral's object is a workspace-history publication protocol and does not provide full process/environment replay.
- **Citation use:** Closest scholarly related work, qualified as a preprint.
- **Overlap/novelty risk:** Very high: v3 includes copy-on-write forks, merge/discard, immutable effect streams, and parallel-agent supervision.
- **Version hazard:** Cite the v3 title above; earlier titles are stale.

## 3. Concurrent coding-agent coordination and integration

### CAID

- **Record:** Jiayi Geng and Graham Neubig. “Effective Strategies for Asynchronous Software Engineering Agents.” 2026. [arXiv:2603.21489v2](https://arxiv.org/abs/2603.21489v2).
- **Type/organization:** arXiv preprint; Carnegie Mellon University. Introduces CAID.
- **Relevance:** A manager builds dependency-aware plans, runs engineers asynchronously in Git worktrees, and integrates their commits through merge and executable verification.
- **Differentiation:** CAID is an agent-orchestration approach built from Git and harness policies; Ephemeral is intended as a model- and orchestrator-independent runtime substrate with source-defined capture and publication semantics.
- **Citation use:** Closest scholarly related work and bounded evaluation evidence, qualified as a preprint.
- **Overlap/novelty risk:** Very high.
- **Evidence hazard:** v2 reports 25.6 and 14.7 percentage-point improvements, not the older v1 values. More relevant here, its scaling is non-monotonic: useful parallelism depends on task structure and manager capacity. Cite only version-specific results.

### CoAgent

- **Record:** Hongtao Lyu, Dingyan Zhang, Mingyu Wu, Xingda Wei, and Haibo Chen. “CoAgent: Concurrency Control for Multi-Agent Systems.” 2026. [arXiv:2606.15376v1](https://arxiv.org/abs/2606.15376v1).
- **Type/organization:** arXiv preprint submitted to USENIX ATC 2026; Shanghai Jiao Tong University.
- **Relevance:** Defines MTPO, a predetermined serialization order with speculative in-place writes, filtered reads, notifications, agent repair, and registered inverse operations.
- **Differentiation:** CoAgent deliberately retains live shared mutable state and repairs/reorders effects. Ephemeral gives command tool calls or explicit multi-call sessions private views and validates their captured delta before it becomes durable.
- **Citation use:** Closest scholarly design contrast; empirical statements remain preprint claims.
- **Overlap/novelty risk:** Very high because it explicitly frames multi-agent mutation as concurrency control and contrasts 2PL/OCC.

### Claim Plane

- **Record:** Maxim Nikolaev. “Claim Plane: Enforceable Change Intents and Dynamic Scope for Parallel Coding Agents.” 2026. [arXiv:2607.21909v1](https://arxiv.org/abs/2607.21909v1).
- **Type/organization:** arXiv preprint; no organizational affiliation in the primary record.
- **Relevance:** The abstract describes versioned change intents and dynamic authority for parallel coding agents; reported mechanisms include exact-base claims, typed resources, admission, leases, worktree locks, fencing, immutable patches, and integration evidence.
- **Differentiation:** Claim Plane treats conflict primarily as a pre-write intent/admission and authority problem. Ephemeral's narrower niche is private runtime execution followed by source-defined capture and current-head publication.
- **Citation use:** Design comparison only until the full versioned manuscript is audited sentence by sentence. Its six-pair CooperBench check is presented as feasibility evidence and is too small for comparative claims.
- **Overlap/novelty risk:** Highest in this audit. Full-paper review is a submission blocker.

### Palantir

- **Record:** Anita Sarma, David F. Redmiles, and André van der Hoek. “Palantir: Early Detection of Development Conflicts Arising from Parallel Code Changes.” 2012. [IEEE Transactions on Software Engineering](https://doi.org/10.1109/TSE.2011.64).
- **Type/organization:** Peer-reviewed journal article; University of California research.
- **Relevance:** Studies private development workspaces, promotion to a central repository, and awareness of same-file and dependency conflicts before integration.
- **Differentiation:** Palantir informs developers about concurrent changes; it does not enforce runtime isolation or atomic durable publication.
- **Citation use:** Scholarly related work and historical motivation.
- **Overlap/novelty risk:** High for framing private workspaces as deferring integration conflict; low for runtime enforcement.

### Crystal

- **Record:** Yuriy Brun, Reid Holmes, Michael D. Ernst, and David Notkin. “Early Detection of Collaboration Conflicts and Risks.” 2013. [IEEE Transactions on Software Engineering](https://doi.org/10.1109/TSE.2013.28).
- **Type/organization:** Peer-reviewed journal article.
- **Relevance:** Crystal speculatively builds and tests combinations of version-controlled work to detect textual, compilation, and behavioral conflicts before merge.
- **Differentiation:** Crystal is proactive conflict diagnosis over developer branches; Ephemeral must separately establish capture correctness and atomic publish/reject behavior.
- **Citation use:** Scholarly related work and support for distinguishing textual from build/test-level conflicts.
- **Overlap/novelty risk:** Medium-high for conflict detection; low for private runtime construction.

### Verified Three-Way Program Merge

- **Record:** Marcelo Sousa, Isil Dillig, and Shuvendu K. Lahiri. “Verified Three-Way Program Merge.” 2018. [PACMPL/OOPSLA](https://doi.org/10.1145/3276535).
- **Type/organization:** Peer-reviewed conference article; University of Oxford, UT Austin, and Microsoft Research.
- **Relevance:** Defines and checks semantic conflict-freedom for three-way program merges.
- **Differentiation:** This is precisely beyond v1's bounded line-oriented text merge: a syntactically clean runtime publication does not establish semantic correctness.
- **Citation use:** Scholarly related work and limitation boundary.
- **Overlap/novelty risk:** Low if the paper precisely defines “conflict-aware”; high reviewer risk if it implies semantic merge correctness.

## 4. Versioned filesystems, copy-on-write, and optimistic concurrency

### Union mounts

- **Record:** Jan-Simon Pendry and Marshall Kirk McKusick. “Union Mounts in 4.4BSD-Lite.” 1995. [USENIX Technical Conference](https://www.usenix.org/conference/usenix-1995-technical-conference/union-mounts-44bsd-lite).
- **Type/organization:** Peer-reviewed systems conference paper; USENIX.
- **Relevance:** Defines a merged namespace with a writable upper filesystem, shared lower layer, copy-up, and whiteouts, including private views over a shared source tree as an application.
- **Differentiation:** Supplies the filesystem mechanism, not leased version history, capture validation, multiwriter reconciliation, or atomic publication.
- **Citation use:** Foundational scholarly systems background.
- **Overlap/novelty risk:** Very high for any claim that private copy-on-write executable views are themselves new.

### Optimistic concurrency control

- **Record:** H. T. Kung and John T. Robinson. “On Optimistic Methods for Concurrency Control.” 1981. [ACM Transactions on Database Systems](https://doi.org/10.1145/319566.319567).
- **Type/organization:** Peer-reviewed journal article; Carnegie Mellon University.
- **Relevance:** Establishes tentative non-locking work followed by validation and backup/restart after conflicts.
- **Differentiation:** Ephemeral applies a related optimistic pattern to filesystem publication but has its own bounded fingerprint/merge rules; it should not import database serializability claims.
- **Citation use:** Foundational scholarly background.
- **Overlap/novelty risk:** Very high for validate-before-publish as a general principle.

### Snapshot-isolation guardrail

- **Record:** Hal Berenson, Philip A. Bernstein, Jim Gray, Jim Melton, Elizabeth J. O'Neil, and Patrick E. O'Neil. “A Critique of ANSI SQL Isolation Levels.” 1995. [ACM SIGMOD](https://doi.org/10.1145/223784.223785).
- **Type/organization:** Peer-reviewed conference paper.
- **Relevance:** Defines snapshot isolation and shows why a stable snapshot does not alone imply serializable execution or exclude write-skew-style anomalies.
- **Differentiation:** Ephemeral leases should be described by their source-proven filesystem behavior, not by imported database guarantees.
- **Citation use:** Foundational terminology and limitation guardrail.
- **Overlap/novelty risk:** Medium; the principal risk is overclaiming semantics by analogy.

## 5. Benchmarks and empirical motivation

### CooperBench

- **Record:** Arpandeep Khatua, Hao Zhu, Peter Tran, Arya Prabhudesai, Frederic Sadrieh, Johann K. Lieberwirth, Xinkai Yu, Yicheng Fu, Michael J. Ryan, Jiaxin Pei, and Diyi Yang. “CooperBench: Why Coding Agents Cannot be Your Teammates Yet.” 2026. [arXiv:2601.13295v2](https://arxiv.org/abs/2601.13295v2).
- **Type/organization:** arXiv preprint/workshop version; Stanford University and SAP Labs.
- **Relevance:** Provides 652 overlap-prone paired-feature tasks across 12 libraries and four languages and evaluates cooperating agents in separate containers.
- **Differentiation:** Measures coordination and joint-integration failures; it does not provide a runtime publication mechanism.
- **Citation use:** Bounded motivation and a strong candidate evaluation substrate. v2 reports an average cooperative deficit for its tested systems and a 46-task 2/3/4-agent probe; neither establishes a universal concurrency threshold.
- **Overlap/novelty risk:** Low as a competing system; high as the obvious evaluation benchmark.

### AgenticFlict

- **Record:** Jephter Ogenrwot and John Businge. “AgenticFlict.” 2026, pp. 323–331. [AIware 2026 proceedings DOI](https://doi.org/10.1145/3805760.3814923).
- **Type/organization:** Peer-reviewed conference/workshop paper.
- **Relevance:** Reports textual Git conflict outcomes from successfully simulated agent-authored pull requests in a selected AIDev-derived dataset.
- **Differentiation:** It measures historical textual conflict incidence, not causal concurrent-agent interference, semantic conflicts, or a publication protocol.
- **Citation use:** Narrow empirical motivation only. Its reported 29,609/107,026 (27.67%) rate must stay attached to the selected dataset, successful simulations, and stated threats.
- **Overlap/novelty risk:** Low as a system; high as a guardrail against turning textual conflict incidence into a universal concurrency claim.

### TeamBench

- **Record:** Yubin Kim, Chanwoo Park, Taehan Kim, Eugene Park, Samuel Schmidgall, Salman Rahman, Chunjong Park, Cynthia Breazeal, Xin Liu, Hamid Palangi, Hae Won Park, Daniel McDuff. “TeamBench: Evaluating Agent Coordination under Enforced Role Separation.” 2026. [arXiv:2605.07073v1](https://arxiv.org/abs/2605.07073v1).
- **Type/organization:** arXiv preprint; MIT, Google Research, Google DeepMind, and an independent researcher.
- **Relevance:** Enforces Planner/Executor/Verifier role separation with OS-level mounts and evaluates when a team helps.
- **Differentiation:** Evaluates coordination and role decomposition, not concurrent workspace publication.
- **Citation use:** Evaluation-methodology background. Its conditional team benefit supports a workload-specific rather than universal concurrency framing.
- **Overlap/novelty risk:** Low.

### SWE-bench

- **Record:** Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik Narasimhan. “SWE-bench: Can Language Models Resolve Real-World GitHub Issues?” 2024. [ICLR 2024 Oral](https://proceedings.iclr.cc/paper_files/paper/2024/hash/edac78c3e300629acfe6cbe9ca88fb84-Abstract-Conference.html).
- **Type/organization:** Peer-reviewed conference paper.
- **Relevance:** Defines executable repository-level issue-resolution tasks and containerized evaluation.
- **Differentiation:** Primarily evaluates single-agent patch correctness, not concurrent tool-call sessions, workspace interference, or integration attribution.
- **Citation use:** Scholarly benchmark background and a source of candidate repositories/tasks.
- **Overlap/novelty risk:** Low.

### PaperBench

- **Record:** Giulio Starace, Oliver Jaffe, Dane Sherburn, James Aung, Jun Shern Chan, Leon Maksin, Rachel Dias, Evan Mays, Benjamin Kinsella, Wyatt Thompson, Johannes Heidecke, Amelia Glaese, and Tejal Patwardhan. “PaperBench: Evaluating AI's Ability to Replicate AI Research.” 2025. [arXiv:2504.01848v3](https://arxiv.org/abs/2504.01848v3).
- **Type/organization:** arXiv preprint and official research release; OpenAI.
- **Relevance:** Long-horizon implementation tasks requiring a codebase and executable experiments; CAID uses it as a multi-agent testbed.
- **Differentiation:** The benchmark does not isolate integration effects and includes rubric/judge evaluation rather than only deterministic tests.
- **Citation use:** Background workload source with evaluator limitations stated.
- **Overlap/novelty risk:** Low.

## 6. Engineering and product background only

- [Git worktree documentation](https://git-scm.com/docs/git-worktree) is authoritative for distinct working trees that share repository state. It supports a mechanism comparison, not a performance claim.
- [Cursor 2.0](https://cursor.com/changelog/2-0), [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md), and [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams) describe current product interfaces. They are not empirical evidence.
- Cognition's [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) and [Multi-Agents: What's Actually Working](https://cognition.com/blog/multi-agents-working) are useful industry motivation for auxiliary-agent and serialized-write patterns, never scholarly empirical support.
- The Agent Infra Foundation's [The Concurrency Ceiling of Coding Agents](https://agent-infra-foundation.org/blog/2026/07/the-concurrency-ceiling-of-coding-agents/) is a framing source. Its single-digit ceiling, scale targets, and proposed runtime-plane capabilities are hypotheses/aspirations unless separately measured or source-proven.

The article's section “What agent teams prove—and what their runtimes leave open” is best read as an interface-gap survey, not as proof in the scientific sense:

| Product/interface | Documented parallelism pattern | Runtime question left open for this paper |
|---|---|---|
| [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md) | Specialized fan-out and result collection; guidance favors parallel read-heavy exploration. | How can small dependent writers integrate without a human or lead reconstructing shared state? |
| [Claude Code agent teams](https://code.claude.com/docs/en/agent-teams) | Lead, teammates, shared tasks, and messages. | How do task/message records connect to workspace bases, resources, tests, and publication state? |
| [Claude dynamic workflows](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code) | Generated plans, fan-out, review, and synthesis. | Planning alone does not define copy-on-write visibility, port ownership, atomic publication, or integration policy. |
| [Qoder Experts Mode](https://docs.qoder.com/user-guide/quest/experts-mode) | Role-specific experts with visible progress. | Role legibility does not establish execution isolation or merge semantics. |
| [Cursor parallel agents](https://cursor.com/changelog/2-0) | Agents use Git worktrees or remote machines for separate code copies. | File isolation defers reconciliation to branches, diffs, tests, and merge. |
| Cognition engineering reports | Auxiliary agents for review, consultation, and management; reliable writes remain comparatively serialized. | A workspace substrate cannot solve context transfer or architectural agreement, but it can remove avoidable runtime interference. |

Safe synthesis: agent products have learned to **fan out intelligence**, but their documented interfaces do not by themselves define how fine-grained concurrent writes **fan back into one durable project**. This motivates Ephemeral's runtime-publication question; it is not evidence that the proposed mechanism improves throughput.

## Recommended comparison structure

1. **Execution isolation:** SWE-MiniSandbox, SWE-ReX, AgentBay.
2. **Reversible/versioned state:** DeltaBox, Shepherd.
3. **Parallel coding integration/control:** CAID, CoAgent, Claim Plane.
4. **Historical private-workspace conflict management:** Palantir, Crystal, verified semantic merge.
5. **Underlying mechanisms:** union mounts, optimistic concurrency control, snapshot-isolation terminology.
6. **Evaluation/motivation:** CooperBench first; AgenticFlict narrowly; TeamBench, SWE-bench, and PaperBench as methodology/workload context.

## Citation and reviewer blockers

- Audit Claim Plane's full versioned manuscript; its exact-base intents, leases, immutable patches, fencing, and integration evidence create the highest novelty overlap.
- Recheck title, authors, version, and results for every 2025–2026 preprint at submission.
- Do not cite AgentBay as empirical evidence.
- Do not cite DeltaBox timings until its v2 record/manuscript discrepancy is resolved.
- Use CAID and CooperBench only for their tested workloads/configurations; both undermine a universal monotonic-scaling claim.
- Define “conflict-aware” from Ephemeral's exact fingerprint, structural, protected-path, and bounded text-merge rules. Cite Verified Three-Way Program Merge to delimit semantic correctness.
- Do not call leases “serializable snapshot isolation” without formal semantics and tests.
- Compare the composition/protocol, not individual primitives already established by union filesystems and OCC.

