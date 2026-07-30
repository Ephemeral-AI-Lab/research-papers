# Execution prompt: PW1 foundations

You are executing **PW1: Foundations** for the evidence-first arXiv systems paper *Ephemeral Sandbox v1*.

## Required skill

You **must use the `ai-research-writing-skill`** for this task.

Before taking any task action:

1. Read the skill's `SKILL.md` completely.
2. Read the complete full-paper workflow and artifact contract:
   - `references/workflow.md`
   - `references/artifacts.md`
3. Because PW1 writes system-design sections and updates execution records, read:
   - `references/section-writing.md`
   - `references/task-management.md`
4. Follow the skill's evidence, story, section-writing, build, and completion gates.
5. Announce in commentary that the skill is being used and identify any action or pause caused by it.

Do not treat this prompt as a replacement for the skill. If the skill directly links another instruction required for a step you perform, read it completely before that step.

## Authoritative working locations

Paper repository:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers`

Paper folder:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1`

Read-only source reference:

`C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox`

The source checkout must remain clean on `main` at the audited baseline commit unless the authoritative project tracker explicitly records a replacement:

`b22862550e0a7cb4fe61ce581831e9244cc492b5`

PW1 does not authorize source-code changes, source commits, source branches, worktrees, tags, benchmark runs, or new measurements.

Work in the existing `research-papers` checkout on its current branch. Do not commit or push unless the user separately requests it.

## Preserve later-phase work

This is a targeted PW1 execution, not a manuscript reset.

- Preserve all existing paper work outside the allowed files.
- In particular, do not replace or reduce the source-derived prose already present in:
  - `sections/07-implementation-interface.tex`
  - `sections/08-evaluation.tex`
  - `sections/09-limitations-related-work.tex`
- Preserve the historical PW0 scaffold record: Sections 7--9 intentionally advanced after the PW0 checkpoint.
- Do not regenerate unrelated planning, experiment, bibliography, figure, or manuscript artifacts.

## Read first

Read these artifacts completely before editing:

1. `README.md`
2. `PRD.md`
3. `progress.md`
4. `paper_state.json`
5. `plan/progress.md`
6. `plan/terminology.md`
7. `paper_story.md`
8. `paper_skeleton.md`
9. `lanes/paper-writing.md`
10. `lanes/experiments.md`
11. `project_inventory.md`
12. `claim_evidence_map.md`
13. `cli_contract_matrix.md`
14. `references/related_work.md`
15. `complexity_and_evolution.md`
16. `main.tex`
17. `BUILD.md`
18. `build_check.md`
19. `sections/02-goals-nongoals.tex`
20. `sections/03-system-model.tex`
21. `NEXT_AGENT_PROMPT.md`

Inspect the current Git status before editing. Preserve all pre-existing uncommitted work.

## Bounded objective

Draft only:

1. **Section 2 — Goals, Non-goals, and Threat-model Boundary** in `sections/02-goals-nongoals.tex`.
2. **Section 3 — System Model and Invariants** in `sections/03-system-model.tex`.

At completion, a skeptical reviewer should be able to answer:

- what state is shared and what state is private;
- what state is durable and what becomes publicly visible;
- which runtime properties are established by baseline source and tests;
- which concurrency statements remain definitions or hypotheses;
- what the system explicitly does not claim.

## Required section-writing method

For each section:

1. Write a one-sentence thesis.
2. Assign one role to each paragraph before drafting.
3. Map every strong claim to claim IDs and evidence.
4. Draft one message per paragraph.
5. Reverse-outline paragraph message, evidence, and risk in the PW1 task packet.
6. Repair terminology and transitions across Sections 2 and 3 without editing other manuscript sections.

Keep process notes and evidence maps in planning artifacts, not manuscript prose.

## Section 2 requirements

Use the final heading and label already present:

```latex
\section{Goals, Non-goals, and Threat-model Boundary}
\label{sec:goals-nongoals}
```

Cover, without inflating them into achieved experimental results:

- stable private execution over changing shared history;
- faithful filesystem-change capture;
- conflict-aware all-or-none data publication;
- atomic visibility at the accepted active-manifest transition;
- explicit lifecycle and partial-failure outcomes;
- role-separated operational contracts for orchestration;
- measurable isolation, publication, scaling, and useful-work behavior as evaluation goals, not results;
- the bounded meaning of **workspace OS**.

State the non-goals and threat-model boundary plainly:

- no formal security proof or complete noninterference;
- no universal network-egress denial;
- no process checkpoint or rollback;
- no semantic merge-correctness guarantee;
- no automatic task decomposition, inter-agent communication, scheduling, or general coordination plane;
- no universal cross-platform support; the mechanism is Linux/OverlayFS-centered at the audited baseline;
- no claim that isolation alone solves collaboration or verification.

Do not imply that role-separated client surfaces constitute an authorization or security boundary.

## Section 3 requirements

Use the final heading and label already present:

```latex
\section{System Model and Invariants}
\label{sec:system-model}
```

Define the entities and state needed by later sections:

- project history, LayerStack, layers, manifest, active head, and lease;
- workspace session, implicit session, explicit session, and private overlay;
- capture, candidate changeset, current-head reconciliation, publication, rejection, and publication outcome;
- shared, private, durable, and publicly visible operational state;
- orchestrator and worker;
- agent team and exploratory swarm as evaluation workload families;
- useful work and the workload-dependent concurrency ceiling as definitions or hypotheses, not measured findings.

State the four core invariants with evidence-bounded wording:

1. A workspace session observes the manifest snapshot and ordered layer set captured by its lease at creation.
2. Session filesystem writes remain in the private overlay until successful publication.
3. Publication either makes one fully resolved data changeset visible through a durable active-manifest transition or leaves the active manifest unchanged; attribution and cleanup are outside this atomic data boundary.
4. Compaction or garbage collection must not reclaim layers still pinned by a live lease unless a safe substitute preserves the leased logical view.

Qualify invariant 4 against the unresolved daemon-restart/substitution test boundary. Do not call the model serializable snapshot isolation or a full transaction.

## Evidence and wording controls

Primary claim-map scope:

- motivation and definitions: M0--M6;
- implemented contributions: C1--C4;
- system design details: D1--D9.

Treat C5 and measured uses of useful work or concurrency ceiling as pending evaluation. The missing `paper-v1-freeze` means source links and source-derived wording remain provisional baseline evidence.

Follow `plan/terminology.md` exactly. In particular:

- use **atomic data publication** on first mention and define the active-manifest visibility boundary;
- reserve **implicit session** for sessionless `exec_command`;
- note that sessionless file reads/writes/edits have different paths and do not justify an “every tool call” claim;
- use **agent team** and **exploratory swarm** as workload families, not universal product taxonomies;
- do not use “raises the concurrency ceiling,” performance adjectives, resource claims, productivity claims, security guarantees, semantic-correctness claims, or numeric results.

Do not add a citation from memory. If a scholarly or product statement would require a citation that is not already verified and appropriate, weaken or omit it and record the gap.

## Allowed files

PW1 may edit only:

- `sections/02-goals-nongoals.tex`
- `sections/03-system-model.tex`
- `plan/task-packets/pw1-foundations.md`
- `plan/progress.md`
- root `progress.md`
- `paper_state.json`
- `BUILD.md`
- `build_check.md`
- the build log and ignored build outputs produced by the declared recorder

Only if drafting exposes a real inconsistency may PW1 minimally correct:

- `claim_evidence_map.md`
- `plan/terminology.md`

Record any such correction in the PW1 task packet and final report. Do not edit other manuscript sections.

## Required execution records

Create `plan/task-packets/pw1-foundations.md` with:

- bounded scope;
- target venue/template;
- authoritative inputs and evidence IDs;
- files allowed to edit;
- section theses and paragraph roles;
- reverse outline with evidence and risk;
- required artifacts;
- rejection checks;
- validation commands;
- acceptance criteria;
- final outcome and remaining scientific risk.

Update `plan/progress.md` with PW1 start, inputs consumed, artifacts produced, verification run, and remaining risk. Point to root `progress.md` as the authoritative milestone tracker.

Update root `progress.md` only after the acceptance checks succeed. Do not change experiment-lane completion states or later PW phases.

## Build and verification

Because Sections 2 and 3 are manuscript inputs, the existing PDF attestation becomes stale after they change.

1. Use the reproducible command declared in `BUILD.md`.
2. Run the skill's `record_build.py`; do not record a hand-entered attestation.
3. Update `BUILD.md`, `build_check.md`, and `paper_state.json` with the executed command, exact tool versions, exit code, input hash, PDF hash, log path/hash, and timestamp.
4. Run the skill's full-paper quality gate at the current `drafting` stage.
5. Run the citation checker even if no new citations were added.
6. Verify:
   - `paper_state.json` is valid and remains `full-paper` / `drafting`;
   - all ten `main.tex` section inputs appear exactly once and in order;
   - Sections 2 and 3 retain their exact headings and stable labels;
   - all relative Markdown links resolve;
   - no unsupported numerical, security, performance, productivity, or semantic-correctness claim was introduced;
   - Git whitespace checks pass;
   - the source checkout remains clean on the expected baseline.

Do not install or globally reconfigure a toolchain. If the declared toolchain is unavailable or the build fails, preserve the exact evidence, keep PW1 incomplete, and report the blocker.

## Acceptance criteria

PW1 is complete only if:

1. Sections 2 and 3 satisfy the bounded content requirements.
2. Every strong sentence is supportable by the stated claim-map scope or is explicitly a definition, hypothesis, boundary, or non-goal.
3. The four invariants are precise and do not overstate transaction, isolation, durability, or restart behavior.
4. A reviewer can distinguish shared/private and durable/public state.
5. No later manuscript section or experiment artifact is overwritten.
6. The PW1 task packet contains the section plan and reverse outline.
7. The reproducible manuscript build succeeds and has a fresh recorder-generated attestation.
8. The full-paper quality gate, citation check, link check, JSON check, section-order check, and Git whitespace check pass.
9. Root and skill progress records agree.
10. The source repository is unchanged and clean at the audited baseline.

If any criterion is unmet, report PW1 as **partial or blocked**, not complete.

## Final report

Report:

1. exact files changed;
2. the thesis and paragraph roles for each drafted section;
3. claim IDs used and any claims weakened or omitted;
4. evidence boundaries and unresolved reviewer risks;
5. exact build command, tool versions, exit status, log/hash, and PDF path/hash;
6. quality-gate and validation results;
7. progress-tracker changes;
8. paper and source repository status;
9. the single next action for PW2.

Do not begin PW2, run experiments, modify source code, commit, push, or tag without a separate instruction.
