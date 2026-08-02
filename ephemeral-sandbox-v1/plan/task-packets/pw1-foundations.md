# PW1: Foundations

## Bounded scope

- Draft only Section 2, **Goals, Non-goals, and Threat-model Boundary**, in `sections/02-goals-nongoals.tex`.
- Draft only Section 3, **System Model and Invariants**, in `sections/03-system-model.tex`.
- Preserve every later manuscript section and all experiment, bibliography, figure, and planning work outside the authorized execution records.
- Update only the PW1 task packet, the skill progress log, the root milestone tracker after acceptance, the machine/build records, and recorder-produced build outputs.
- Do not modify, build, test, benchmark, commit, branch, tag, push, or otherwise mutate the `ephemeral-sandbox` source checkout.

## Target venue and template

- Target: arXiv `cs.OS`.
- Template: the existing 10 pt `article` manuscript in `main.tex`.
- Mode and stage: `full-paper` / `drafting`.
- Source evidence status: provisional baseline evidence at `b22862550e0a7cb4fe61ce581831e9244cc492b5` until an annotated `paper-v1-freeze` exists.

## Authoritative inputs and evidence IDs

- Project contract and state: `README.md`, `PRD.md`, root `progress.md`, `paper_state.json`, `plan/progress.md`, and `NEXT_AGENT_PROMPT.md`.
- Story and structure: `paper_story.md`, `paper_skeleton.md`, `lanes/paper-writing.md`, and `lanes/experiments.md`.
- Vocabulary and evidence: `plan/terminology.md`, `project_inventory.md`, `claim_evidence_map.md`, `cli_contract_matrix.md`, `references/related_work.md`, and `complexity_and_evolution.md`.
- Manuscript/build state: `main.tex`, `BUILD.md`, `build_check.md`, and the two target section files.
- Primary claim-map scope:
  - motivation and definitions: M0--M6;
  - implemented contributions: C1--C4;
  - system-design details: D1--D9.
- C5, M4, and measured uses of useful work or the concurrency ceiling remain pending evaluation.

## Files allowed to edit

- `sections/02-goals-nongoals.tex`
- `sections/03-system-model.tex`
- `plan/task-packets/pw1-foundations.md`
- `plan/progress.md`
- root `progress.md`
- `paper_state.json`
- `BUILD.md`
- `build_check.md`
- the recorder-selected build log and ignored build outputs
- only if drafting exposes a real inconsistency: `claim_evidence_map.md` or `plan/terminology.md`

## Section theses and paragraph roles

### Section 2 thesis

Ephemeral Sandbox aims to separate stable private execution from changing shared history and to make publication and lifecycle outcomes explicit, while limiting its claims to a Linux/OverlayFS-centered workspace runtime rather than a security proof, process checkpoint system, semantic coordination layer, or measured scaling result.

Paragraph roles before drafting:

1. State the private-execution and shared-history goal, including stable leased views and faithful filesystem capture. Evidence: C1, D1--D4.
2. State the integration goal: conflict-aware all-or-none reconciliation, **atomic data publication** at the active-manifest visibility boundary, and explicit partial-failure outcomes. Evidence: C2, C4, D5--D9.
3. State the role-separated operational-contract goal without converting client separation into an authorization boundary. Evidence: C3.
4. State isolation, publication, scaling, and useful-work behavior as evaluation goals, not results. Evidence class: C5 pending; M2 and M4 as definitions/hypotheses.
5. Define the bounded meaning of **workspace OS**. Evidence: C1--C4 and `plan/terminology.md`.
6. State the threat-model, platform, coordination, and semantic non-goals plainly, ending with the transition to the system model. Evidence: M6 and the explicit limitations attached to C1--C4 and D1--D9.

### Section 3 thesis

The system model separates leased shared history, session-private execution, durable accepted data, and publicly visible operational state, then states four evidence-bounded invariants governing snapshot observation, private writes, atomic data publication, and lease-safe reclamation.

Paragraph roles before drafting:

1. Define project history, LayerStack, layer, manifest, active head, and lease. Evidence: C1, C2, D3, D7.
2. Define workspace session, implicit session, explicit session, and private overlay; distinguish sessionless command and file-operation paths. Evidence: C1, D1, D2, D2a.
3. Define capture, candidate changeset, current-head reconciliation, publication, rejection, and publication outcomes. Evidence: C2, C4, D4--D9.
4. Classify shared, private, durable, and publicly visible operational state, including the atomic-data boundary around the active manifest. Evidence: C2, C3, C4, D6--D9.
5. Define orchestrator, worker, agent team, exploratory swarm, useful work, and the workload-dependent concurrency ceiling as evaluation roles, workload families, and hypotheses rather than findings. Evidence: M0b, M2, M4, M5, M6.
6. State Invariants 1 and 2: lease-captured observation and private-overlay writes before publication. Evidence: C1, D1--D4.
7. State Invariant 3: one fully resolved changeset becomes visible through a durable active-manifest transition or the active manifest remains unchanged; attribution and cleanup remain outside the atomic data boundary. Evidence: C2, C4, D5--D9.
8. State Invariant 4: live-lease layers require retention or a safe substitute, qualified by the unresolved daemon-restart/substitution boundary; reject transaction and serializability overclaims. Evidence: D3 and its open restart test.

## Planned reverse outline

The final reverse outline will record, for each drafted paragraph, its actual message, evidence IDs, and residual wording risk. Initial risks to control are:

- generalizing the implicit-session path from `exec_command` to every tool call;
- presenting useful work or the concurrency ceiling as a measured finding;
- enlarging atomic data publication to include audit, accounting, or cleanup;
- describing client-role separation as authorization or security;
- importing database transaction, snapshot-isolation, or serializability semantics;
- overstating lease behavior across daemon restart;
- implying Linux mechanisms or durability guarantees are cross-platform;
- implying line-oriented merge establishes semantic correctness.

## Final reverse outline

### Section 2

| Paragraph | Message | Evidence | Residual risk and control |
|---|---|---|---|
| 1 | The first goal is a stable leased view, private OverlayFS writes, and faithful typed filesystem capture. | C1; D1--D4. | “Faithful” is scoped to the implemented entry classes and explicit protected drops; the paragraph disclaims process checkpointing. |
| 2 | Integration resolves the complete candidate or rejects it, and **atomic data publication** ends at the durable active-manifest visibility transition; lifecycle phases can fail separately. | C2, C4; D5--D9. | Atomicity excludes attribution, accounting, and cleanup; semantic correctness is not implied. |
| 3 | The three role-separated client surfaces are orchestration contracts, not authorization or security boundaries. | C3. | Final operation counts and tagged fixtures remain outside PW1 and require the final source freeze. |
| 4 | Isolation, publication, scaling, and useful work are evaluation targets, not demonstrated advantages. | M2, M4, M5; C5 pending. | No result, number, monotonic trend, performance adjective, or raised-ceiling claim is made. |
| 5 | “Workspace OS” denotes only the LayerStack/session/publication/lifecycle/observability substrate. | C1--C4; `plan/terminology.md`. | The paragraph explicitly excludes a general OS, kernel, hypervisor, security monitor, and coordination plane. |
| 6 | The threat model addresses accidental workspace/publication interference but excludes formal security, universal egress denial, process rollback, and semantic correctness. | C1, C2; D1, D4--D7; M6. | Shared networking and selectable isolation are stated; no sandbox-escape claim is made. |
| 7 | Task decomposition, communication, scheduling, intent/ownership, general coordination, and universal cross-platform support are non-goals; isolation alone does not solve collaboration or verification. | M6; limitations attached to C1--C4. | Linux namespaces/OverlayFS scope is explicit, and the paragraph makes no cross-platform durability claim. |

### Section 3

| Paragraph or item | Message | Evidence | Residual risk and control |
|---|---|---|---|
| 1 | Project history is represented as a manifest-selected LayerStack; the active head is shared/durable, and a lease captures one logical view. | C1, C2; D3, D7. | Runtime-treated immutability is distinguished from filesystem-enforced immutability. |
| 2 | Workspace, implicit, and explicit sessions share the lease/private-overlay model, while sessionless file operations use separate paths. | C1; D1, D2, D2a. | “Implicit session” is restricted to sessionless `exec_command`; no “every tool call” generalization remains. |
| 3 | Capture produces a candidate; reconciliation resolves or rejects it; publication and lifecycle outcomes are phase-specific. | C2, C4; D4--D9. | Candidate data is not called accepted, durable, or semantically valid; published-but-not-closed is not rollback. |
| 4 | Shared/private and durable/public are independent state classifications, with accepted filesystem visibility at the active-manifest transition. | C2--C4; D6--D9. | Public means exposed through shared runtime views, not Internet-public; audit/accounting/cleanup have separate persistence. |
| 5 | Orchestrator/worker roles and the agent-team/exploratory-swarm workload families frame useful work and the concurrency ceiling as definitions and hypotheses. | M0b, M2, M4--M6. | The paragraph explicitly disclaims a universal taxonomy and an achieved change in the ceiling. |
| Invariant 1 | A session observes the manifest and ordered layer set captured by its creation lease. | C1; D1, D3. | Physical substitution is allowed only if it preserves the logical view. |
| Invariant 2 | Session filesystem writes remain private until successful publication; capture alone does not expose them. | C1; D2, D4. | The invariant is scoped to workspace-session writes, not sessionless direct file operations. |
| Invariant 3 | Publication makes one fully resolved changeset visible through a durable active-manifest transition or leaves the active manifest unchanged. | C2, C4; D5--D9. | Attribution/accounting/cleanup are explicitly outside the all-or-none data boundary. |
| Invariant 4 | Live-lease layers cannot be reclaimed without retention or a safe logical substitute. | D3. | The daemon-restart/substitution boundary is stated as untested rather than generalized from in-process tests. |
| Closing paragraph | The four properties are not a full transaction, serializable snapshot isolation, a cross-platform crash proof, or a process snapshot. | Boundaries attached to C1, C2, D3, D7. | Prevents importing database or checkpoint semantics. |

No inconsistency in `claim_evidence_map.md` or `plan/terminology.md` was exposed by drafting, so neither file was edited.

## Required artifacts

- Complete drafts of Sections 2 and 3 with exact headings and labels.
- A final paragraph-level reverse outline in this task packet.
- PW1 start/completion records in `plan/progress.md`.
- A root milestone update only after every acceptance check succeeds.
- A fresh recorder-generated build attestation in `paper_state.json`, `BUILD.md`, and `build_check.md`.
- Recorder build log and `main.pdf`.

## Rejection checks

- Reject wording that claims formal security, complete noninterference, universal egress denial, process rollback, semantic merge correctness, general coordination, cross-platform support, performance, productivity, resource savings, or a universal concurrency threshold.
- Reject “every tool call creates a session”; reserve **implicit session** for sessionless `exec_command`.
- Reject unqualified “atomic transaction,” “serializable snapshot isolation,” “immutable filesystem,” or durability claims beyond the implemented active-manifest data boundary.
- Reject any statement that treats source test definitions as a fresh test run or turns C5 into a result.
- Reject any edit to later manuscript sections or source/experiment artifacts.
- Reject completion if the build recorder, full-paper quality gate, citation check, links, JSON, section structure/order, headings/labels, whitespace, or source-baseline checks fail.

## Validation commands

- Declared manuscript command: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
- Skill build recorder: `python <skill>/scripts/record_build.py <paper-folder> --run`.
- Full-paper gate: `python <skill>/scripts/research_quality_gate.py <paper-folder>`.
- Citation checker: `python <skill>/scripts/check_citations.py main.tex references.bib`.
- JSON parse and `full-paper` / `drafting` assertions.
- Exact ten-section `main.tex` input count/order check.
- Exact Section 2/3 heading and label check.
- Relative-Markdown-link resolution check.
- Prohibited-claim scan and manual skeptical review.
- `git diff --check`.
- Paper/source `git status`, source branch, and source-commit verification.

## Acceptance criteria

1. Both target sections satisfy the bounded content requirements and preserve their headings and labels.
2. Every strong sentence maps to M0--M6, C1--C4, or D1--D9, or is visibly a definition, hypothesis, boundary, or non-goal.
3. The four invariants do not overstate transaction, isolation, durability, or restart behavior.
4. The shared/private and durable/public distinctions are explicit.
5. Later sections and experiment artifacts are untouched.
6. This task packet contains the pre-draft plan and final reverse outline.
7. The declared build succeeds through the skill recorder with a fresh attestation.
8. All required quality, citation, link, JSON, section, claim, whitespace, and source checks pass.
9. Root and skill progress records agree.
10. The source checkout remains clean on `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`.

## Final outcome and remaining scientific risk

- Outcome: complete. Both sections satisfy the bounded content requirements; the recorder-generated build and every declared quality, citation, structure, link, JSON, claim, whitespace, hash, and source-baseline check passed.
- Build: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`, exit 0; input SHA-256 `8a9d0f97487ccf937efd82eb6a5726b2c7c8b5e3e31be1434945826a00731708`; PDF SHA-256 `ba4963d3d5f6352e1829946290265671599432e9984e301d5626de7316435327`; build-log SHA-256 `719696c0aa0efb9fce4796efaab3cce5b27dd17563c4b60d7f4951b539aa7f30`.
- Remaining scientific risk: source links remain provisional until `paper-v1-freeze`; no frozen evaluation establishes isolation strength, publication fault behavior, scaling, resource behavior, useful work, or a concurrency ceiling; publication attribution is best-effort after data commit; protected-drop policy and daemon-restart lease/substitution behavior remain unresolved.
