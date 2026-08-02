# PW2: Workspace Execution and Capture/Publication

## Bounded scope

- Draft only Section 4, **Workspace Execution**, in `sections/04-workspace-execution.tex`.
- Draft only Section 5, **Capture and Publication**, in `sections/05-capture-publication.tex`.
- Preserve Sections 1--3 and 6--10, all experiment artifacts, the bibliography, figures, and planning work outside the authorized execution records.
- Update only this task packet, the skill progress log, the root milestone tracker after acceptance, the machine/build records, and recorder-produced build outputs.
- Do not modify, build, test, benchmark, commit, branch, tag, push, or otherwise mutate the `ephemeral-sandbox` source checkout.

The paper-writing lane fully specifies PW2, but no standalone `lanes/prompts/pw2.md` exists. This execution therefore treats the PW2 block in `lanes/paper-writing.md` as the authoritative work-package contract and records the missing prompt as a planning inconsistency rather than inventing one.

## Target venue and template

- Target: arXiv `cs.OS`.
- Template: the existing 10 pt `article` manuscript in `main.tex`.
- Mode and stage: `full-paper` / `drafting`.
- Source evidence status: provisional baseline evidence at `b22862550e0a7cb4fe61ce581831e9244cc492b5` until an annotated `paper-v1-freeze` exists.

## Authoritative inputs and evidence IDs

- Project contract and state: `README.md`, `PRD.md`, root `progress.md`, `paper_state.json`, `plan/progress.md`, and `NEXT_AGENT_PROMPT.md`.
- Story and structure: `paper_story.md`, `paper_skeleton.md`, `lanes/paper-writing.md`, and `lanes/experiments.md`.
- Vocabulary and evidence: `plan/terminology.md`, `project_inventory.md`, `claim_evidence_map.md`, `cli_contract_matrix.md`, `references/related_work.md`, and `complexity_and_evolution.md`.
- Manuscript/build continuity: `main.tex`, `BUILD.md`, `build_check.md`, Sections 2--5, and the PW1 task packet.
- Primary PW2 claim-map scope: C1, C2, and D1--D8.
- Source evidence inspected in the read-only baseline:
  - command and workspace-session services;
  - workspace construction, snapshot leasing, OverlayFS projection, and namespace-holder/runner paths;
  - session and sessionless file-operation paths;
  - upper-directory capture;
  - publication route, plan, fingerprint, opaque-directory expansion, resolve, and merge modules;
  - layer staging, promotion, digest, manifest replacement, post-commit audit attribution, and session finalization.

No source test was run. Test definitions remain source-derived evidence rather than fresh execution results.

## Files allowed to edit

- `sections/04-workspace-execution.tex`
- `sections/05-capture-publication.tex`
- `plan/task-packets/pw2-workspace-publication.md`
- `plan/progress.md`
- root `progress.md`
- `paper_state.json`
- `BUILD.md`
- `build_check.md`
- the recorder-selected build log and ignored build outputs
- only if drafting exposes a real inconsistency: `claim_evidence_map.md` or `plan/terminology.md`

## Pre-existing worktree state

PW2 began with authorized PW1 record updates already present in `BUILD.md`, `build_check.md`, `paper_state.json`, `plan/progress.md`, `plan/task-packets/pw1-foundations.md`, and root `progress.md`. It also found unrelated benchmark/experiment modifications and generated Python bytecode under `benchmark/` and `experiments/`. PW2 will preserve all of these changes and validate its own edit scope separately.

## Section theses and paragraph roles

### Section 4 thesis

A workspace session projects the exact LayerStack view held by its creation lease into a Linux OverlayFS with private writable state, then runs commands and file operations through holder-owned namespaces while keeping implicit commands, explicit multi-call sessions, and sessionless file paths semantically distinct.

Paragraph roles before drafting:

1. Define workspace creation as the projection of a leased manifest and ordered LayerStack into a session-specific runtime view. Evidence: C1, D3.
2. Explain newest-first lower layers, private upper/work directories, and the Linux/OverlayFS platform boundary. Evidence: C1, D2, D3.
3. Explain the long-lived namespace holder and short-lived runner control path, including namespace join order and the daemon's position outside the command namespaces. Evidence: C1.
4. Explain the implicit-session path for sessionless `exec_command`, including shared networking and publish-then-destroy only after the command ledger drains. Evidence: D1.
5. Explain explicit sessions as multi-call containers whose commands and file operations share one private overlay until explicit publication or destruction. Evidence: D2.
6. Qualify session file operations, sessionless reads, sessionless direct write/edit paths, and selectable network behavior so no “every tool call” or universal-egress claim is made. Evidence: D1, D2, D2a.
7. State creation/finalization failure boundaries and transition from a complete private filesystem delta to capture; explicitly exclude process checkpointing, rollback, and a formal security guarantee. Evidence: C1, D1--D3.

### Section 5 thesis

Publication converts a complete private upper-directory delta into a typed candidate changeset, validates and reconciles the entire candidate against the current head, and exposes accepted data only through durable layer promotion followed by atomic active-manifest replacement, with attribution and cleanup outside that atomic data boundary.

Paragraph roles before drafting:

1. Explain capture as a typed filesystem delta covering writes, deletions, symlinks, directories, opaque directories, and OverlayFS whiteouts, while preserving literal `.wh.*` names for later rejection and reporting unsupported entries as protected drops. Evidence: C2, D4.
2. Explain planning against the leased base: base identity, protected-path and source/ignored routing, bounded opaque-directory expansion, and base fingerprints. Evidence: D5.
3. Explain current-head reconciliation under the writer lock: re-read the active manifest, accept unchanged fingerprints, reject structural divergence, and admit only eligible exact-file source writes to merge. Evidence: C2, D5.
4. Bound conflict-merge behavior to clean line-oriented text no larger than 8 MiB; when a concurrent source-path change requires merging, reject binary, invalid-UTF-8, oversized, non-file, structurally divergent, or text-conflicting cases. Distinguish this from an unchanged-fingerprint binary or oversized write, which can publish without merging, and do not claim semantic correctness or a fully resource-bounded diff. Evidence: C2, D5.
5. State whole-candidate resolution and rejection: no conflicting subset becomes visible, a no-op leaves the current head in place, and lifecycle handling after pre-commit failure is deferred to Section 6. Evidence: C2, D6.
6. Explain the durable commit sequence: write and sync a staging tree, rename it into the layer store, persist its digest, revalidate the active manifest, and atomically replace the active manifest. Evidence: C2, D7.
7. Delimit atomic data publication from best-effort post-commit attribution and later session cleanup, leaving cleanup-failure outcomes to Section 6. Evidence: C2, D7, D8.
8. State the baseline and platform qualifiers and transition to lifecycle/recovery: source inspection is provisional, no cross-platform crash proof or oversized-transaction claim is made, and cleanup/recovery are separate phases. Evidence: D7, D8.

## Planned reverse outline

The final reverse outline will record each paragraph's actual message, evidence IDs, and residual risk. Initial controls are:

- do not generalize implicit sessions beyond sessionless `exec_command`;
- do not describe sessionless direct file writes/edits as private workspace activity;
- do not call namespace isolation a formal security boundary or claim universal network-egress denial;
- do not describe capture as process-state capture;
- do not interpret ordinary `.wh.*` filenames as capture-time whiteout markers;
- do not hide the explicit-session protected-drop fail-closed behavior or generalize it into an unverified uniform policy;
- do not call optimistic reconciliation serializable snapshot isolation or a full transaction;
- do not claim that a clean textual merge is semantically correct;
- do not claim that binary or oversized writes are categorically rejected: the restriction applies when concurrent source-path divergence requires a merge;
- do not describe the 8 MiB text limit as a complete CPU/RSS bound;
- do not extend atomic data publication to audit attribution, accounting, autosquash notification, session destruction, or cleanup;
- do not claim universal cross-platform crash durability;
- do not present source test definitions as freshly executed validation.

## Final reverse outline

### Section 4

| Paragraph | Message | Evidence | Residual risk and control |
|---|---|---|---|
| 1 | Creation acquires a lease before opening the workspace, so a live session retains the selected manifest and ordered layer paths even if the active head advances. | C1, D3. | The paragraph calls this a stable leased view, not serializable snapshot isolation. |
| 2 | Linux OverlayFS projects newest-first shared lower layers beneath a session-unique upper/work pair. | C1, D2, D3. | The non-Linux path is explicitly unsupported; no universal platform claim is made. |
| 3 | A long-lived holder owns namespace handles and short-lived runners join them for commands while the daemon stays outside. | C1. | Namespace separation is described as an implementation boundary, not a hostile-code security proof. |
| 4 | Only sessionless `exec_command` creates an implicit shared-network, publish-then-destroy session, and finalization waits for the command ledger to drain. | D1. | The paragraph distinguishes command completion from an initial response and does not generalize to every tool call. |
| 5 | Explicit sessions preserve one leased overlay across multiple command and file calls until deliberate publication or destruction. | D2. | Publication admission with active commands is stated; process-state rollback is not implied. |
| 6 | Session file operations use the live overlay, sessionless reads project the active head, sessionless writes/edits amend it directly, and network profiles have different boundaries. | D1, D2, D2a. | Shared networking is not called egress containment; direct file amendments are not called implicit sessions. |
| 7 | Creation is a fallible multi-stage admission with rollback attempts, while capture begins only from filesystem state in the private upper tree. | C1, D1--D3. | No claim is made that the runtime snapshots registers, memory, sockets, or arbitrary process state. |

### Section 5

| Paragraph | Message | Evidence | Residual risk and control |
|---|---|---|---|
| 1 | Capture maps upper-tree files, links, directories, kernel whiteouts, and opaque metadata to typed changes and reports invalid or unsupported entries as protected drops. | C2, D4. | Literal `.wh.*` names are preserved until protected-path rejection; the explicit/generic protected-drop policy asymmetry is disclosed. |
| 2 | Planning validates the leased-base identity, routes source versus ignored paths, rejects reserved paths, fingerprints source state, and bounds opaque-directory expansion. | C2, D5. | The paragraph calls this a plan rather than accepted or durable data. |
| 3 | Under the writer lock, source fingerprints are checked against the current head and structural divergence rejects, while ignored-route writes deliberately do not receive source reconciliation. | C2, D5. | The source/ignored distinction prevents an overbroad isolation claim. |
| 4 | Concurrent exact-file source writes may use the eligible 8 MiB line merge; other required merge cases reject. | C2, D5. | Unchanged-path binary/oversized writes remain publishable; clean merge is not semantic correctness and the byte gate is not a complete CPU/RSS bound. |
| 5 | Resolution emits one complete changeset, one no-op, or one rejection; no unrelated resolved subset is passed to the writer. | C2, D6. | Lifecycle behavior after pre-commit failure is deferred rather than imported from D9. |
| 6 | Commit stages and syncs the resolved layer, promotes it, persists its digest, rechecks the manifest, and exposes it only through atomic active-manifest replacement. | C2, D7. | Failures may leave unselected artifacts; the claim concerns manifest-selected data, not zero residual files. |
| 7 | Best-effort attribution and subsequent destruction, accounting, notification, and reclamation lie after the atomic data-publication boundary. | C2, D7, D8. | No atomic coupling between data, audit, or cleanup is claimed; cleanup outcomes are left to Section 6. |
| 8 | The private-to-public path is bounded to the provisional Linux baseline and does not establish semantic merge correctness, cross-platform crash proof, or unlimited transaction size. | Boundaries attached to C2, D5, D7, D8. | Frozen fault and resource evidence remains pending. |

No inconsistency in `claim_evidence_map.md` or `plan/terminology.md` required an edit. The missing standalone PW2 prompt and the protected-drop entry-point asymmetry remain recorded planning/scientific risks.

## Required artifacts

- Complete drafts of Sections 4 and 5 with exact headings and stable labels.
- A final paragraph-level reverse outline in this task packet.
- PW2 start/completion records in `plan/progress.md`.
- A root milestone update only after every acceptance check succeeds.
- A fresh recorder-generated build attestation in `paper_state.json`, `BUILD.md`, and `build_check.md`.
- Recorder build log and `main.pdf`.

## Rejection checks

- Reject performance, productivity, resource-savings, security, universal-egress, semantic-correctness, serializability, full-transaction, process-rollback, and cross-platform durability claims.
- Reject “every tool call creates a session”; reserve **implicit session** for sessionless `exec_command`.
- Reject wording that makes sessionless direct file writes/edits part of an implicit session.
- Reject any atomicity statement that includes post-commit attribution or cleanup.
- Reject any statement that categorically rejects binary or oversized clean-path writes, or presents the 8 MiB merge threshold as sufficient protection from adversarial diff CPU or memory use.
- Reject any edit to non-target manuscript sections or source/experiment artifacts.
- Reject completion if the build recorder, full-paper quality gate, citation check, links, JSON, section structure/order, headings/labels, whitespace, protected-file hashes, or source-baseline checks fail.

## Validation commands

- Declared manuscript command: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
- Skill build recorder: `python <skill>/scripts/record_build.py <paper-folder> --run`.
- Full-paper gate: `python <skill>/scripts/research_quality_gate.py <paper-folder>`.
- Citation checker: `python <skill>/scripts/check_citations.py main.tex references.bib`.
- JSON parse and `full-paper` / `drafting` assertions.
- Exact ten-section `main.tex` input count/order check.
- Exact Section 4/5 heading and label check.
- Relative-Markdown-link resolution check.
- Prohibited-claim scan and manual skeptical review.
- PW2-scoped `git diff --check`, plus whole-worktree whitespace inspection without changing unrelated files.
- Protected-file hash comparison.
- Paper/source `git status`, source branch, and source-commit verification.

## Acceptance criteria

1. Both target sections satisfy the bounded lane requirements and preserve their headings and labels.
2. Every strong sentence maps to C1, C2, or D1--D8, or is visibly a boundary or limitation.
3. The path from private session state to durable public head is complete and distinguishes capture, planning, reconciliation, commit, attribution, and cleanup.
4. Implicit commands, explicit sessions, session file operations, and sessionless file operations remain distinct.
5. Atomic data publication is bounded to the accepted active-manifest transition.
6. No later manuscript section, source file, benchmark artifact, or experiment artifact is overwritten.
7. This task packet contains the pre-draft plan and final reverse outline.
8. The declared build succeeds through the skill recorder with a fresh attestation.
9. All required quality, citation, link, JSON, section, claim, whitespace, hash, and source checks pass.
10. Root and skill progress records agree, and the source checkout remains clean on `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`.

## Final outcome and remaining scientific risk

- Outcome: complete. Sections 4 and 5 satisfy the bounded PW2 contract; the recorder-generated build and every declared quality, citation, structure, link, JSON, claim, whitespace, hash, and source-baseline check passed.
- Build: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`, exit 0; input SHA-256 `36877891dbce1e066589d8a295e436654ccb097970620003cdaf45871f74311b`; PDF SHA-256 `801ac91c302ae3ea7d5827d34dd4da09278e8f537409e3426fd4ff30c8ed36e7`; build-log SHA-256 `9fc4261ab327472e004f4f62466bf2266218d1b17a66cc5b852ee5dbe7b23265`.
- Remaining scientific risk: source links remain provisional until `paper-v1-freeze`; no frozen fault/resource evaluation establishes crash behavior or worst-case merge cost; attribution remains best effort after the data commit; protected-drop policy differs by publication entry point; and lifecycle/recovery failure handling remains for PW3.
