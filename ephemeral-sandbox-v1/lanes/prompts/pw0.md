# Execution prompt: PW0 manuscript scaffold and vocabulary

You are executing **PW0: Manuscript Scaffold and Vocabulary** for the evidence-first arXiv systems paper *Ephemeral Sandbox v1*.

## Required skill

You **must use the `ai-research-writing-skill`** for this task.

Before taking any task action:

1. Read the skill's `SKILL.md` completely.
2. Because PW0 starts the full-paper artifact, read the complete full-paper workflow and artifact contract referenced by that skill:
   - `references/workflow.md`
   - `references/artifacts.md`
3. Follow their evidence, story, build, and completion gates.
4. Announce in commentary that the skill is being used and identify any action or pause caused by it.

Do not treat this prompt as a replacement for the skill. If the skill requires an additional directly linked instruction for a step you perform, read it before that step.

## Authoritative working locations

Paper repository:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers`

Paper folder:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1`

Read-only source reference for PW0:

`C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox`

The source checkout should be clean on required `main` at baseline commit:

`b22862550e0a7cb4fe61ce581831e9244cc492b5`

PW0 does not authorize source-code changes, source commits, source branches, worktrees, tags, or benchmark runs.

Work in the existing `research-papers` checkout on its current branch. Do not commit or push unless the user separately requests it.

## Read first

Read these paper artifacts completely before editing:

1. `README.md`
2. `PRD.md`
3. `progress.md`
4. `paper_story.md`
5. `paper_skeleton.md`
6. `lanes/paper-writing.md`
7. `lanes/experiments.md`
8. `project_inventory.md`
9. `claim_evidence_map.md`
10. `cli_contract_matrix.md`
11. `references/related_work.md`
12. `NEXT_AGENT_PROMPT.md`

Check whether `research_handoff.json`, `paper_state.json`, `main.tex`, `references.bib`, `sections/`, `plan/`, or an existing build record already exists. Preserve and extend existing artifacts; do not overwrite user work or regenerate unrelated documents.

## PW0 objective

Create a minimal, arXiv-compatible, reproducibly buildable manuscript scaffold and a canonical terminology record. Do not draft the evidence-bearing body sections assigned to PW1–PW6.

The scaffold must encode the current paper structure and evidence boundaries without inventing:

- author names or affiliations;
- experimental results;
- performance, resource, or productivity claims;
- security guarantees;
- final contribution wording;
- final title, Abstract, Introduction, or Conclusion.

Use the current recommended title and design-first Abstract from `paper_story.md` only as explicitly provisional framing. Preserve all evidence-boundary language.

## Required outputs

Create or update the following under the paper folder.

### Full-paper state and execution records

1. `paper_state.json`
   - schema version: `ai-research-writing/paper-state-v1`;
   - mode: `full-paper`;
   - stage: `drafting`;
   - target venue: `arXiv cs.OS`;
   - main TeX: `main.tex`;
   - bibliography: `references.bib`;
   - record current blockers, including the missing `paper-v1-freeze`, missing `experiment_inventory.md`, absent final measurements, unresolved author metadata, and any unavailable build tool;
   - build status must reflect the actual PW0 build attempt.

2. `plan/task-packets/pw0-manuscript-scaffold.md`
   - bounded objective;
   - authoritative inputs;
   - allowed files;
   - non-goals;
   - acceptance checks;
   - final outcome and blockers.

3. `plan/progress.md`
   - execution log for the skill workflow;
   - point to root `progress.md` as the authoritative project milestone tracker;
   - record PW0 start, checks, build attempt, completion or blocker.

4. `plan/terminology.md`
   - canonical term;
   - precise paper definition;
   - source/claim-map basis;
   - unsafe synonyms or overclaims;
   - include at least LayerStack, layer, manifest, active head, lease, workspace session, implicit session, explicit session, private overlay, capture, candidate changeset, current-head reconciliation, publication, rejection, atomic data publication, useful work, concurrency ceiling, agent team, exploratory swarm, and workspace OS.

### LaTeX scaffold

5. `main.tex`

Use an arXiv-compatible standard LaTeX setup with conservative, commonly supported packages. It must:

- use the provisional recommended title from `paper_story.md`;
- use explicit draft author metadata such as `[AUTHOR INFORMATION NEEDED]`; never invent names or affiliations;
- include the provisional design-first Abstract from `paper_story.md`, marked as a draft in a way that cannot be mistaken for final submission text;
- `\input` each section file below in order;
- reference `references.bib`;
- avoid unavailable generated assets;
- compile without requiring experimental result files.

6. Create these section files:

- `sections/01-introduction.tex`
- `sections/02-goals-nongoals.tex`
- `sections/03-system-model.tex`
- `sections/04-workspace-execution.tex`
- `sections/05-capture-publication.tex`
- `sections/06-lifecycle-recovery.tex`
- `sections/07-implementation-interface.tex`
- `sections/08-evaluation.tex`
- `sections/09-limitations-related-work.tex`
- `sections/10-conclusion.tex`

Each file should contain only:

- its final planned `\section{...}` heading;
- a stable `\label{...}`;
- the smallest visible draft marker needed to prevent an empty-section build warning.

Do not draft PW1–PW6 prose in PW0. Keep process instructions in planning documents rather than manuscript prose.

7. `references.bib`

- create the file if absent;
- include no citation written from memory;
- retain only verified entries if entries already exist;
- an empty/comment-only bibliography is acceptable for PW0.

8. `BUILD.md`

Record:

- required LaTeX tools;
- exact local build command;
- clean-build command;
- output paths;
- tool version used in the PW0 build;
- current build limitations.

Do not install a new global toolchain or change system configuration merely to satisfy PW0. If no compatible LaTeX tool exists, leave a precise blocker and keep PW0 incomplete.

### Figure/table planning

9. `figures/figure_plan.md`

Create or update a non-numerical plan for:

- problem/concurrency-ceiling teaser;
- LayerStack/session architecture;
- session/publication state machine;
- shared-directory/worktree/Ephemeral design comparison;
- final-tag CLI contract table;
- publication behavior table;
- future experimental result figures and tables.

Classify every item as `concept-method` or `evidence-result`. Mark result assets blocked on frozen data. Do not generate figures during PW0.

## Exact section mapping

The scaffold must use:

1. Introduction
2. Goals, Non-goals, and Threat-model Boundary
3. System Model and Invariants
4. Workspace Execution
5. Capture and Publication
6. Lifecycle and Recovery
7. Implementation and Operational Interface
8. Evaluation
9. Limitations and Related Work
10. Conclusion

Do not silently rename or combine sections without updating `lanes/paper-writing.md`, `paper_skeleton.md`, and `progress.md`.

## Build and verification

1. Inspect available LaTeX builders in this order or choose an equivalent justified order:
   - `latexmk`
   - `tectonic`
   - `pdflatex` plus required bibliography pass
2. Record the exact builder and version.
3. Attempt a clean build.
4. If the skill's `record_build.py` is applicable, run it against the paper project and record the actual command, exit code, log, source-input hash, and PDF hash.
5. Run the skill's quality gate early. Expected missing evaluation artifacts remain blockers; do not hide or fabricate them to force a pass.
6. Check:
   - JSON validity of `paper_state.json`;
   - all ten section files are included exactly once and in order;
   - all relative Markdown links resolve;
   - LaTeX has no undefined `\input` paths;
   - no invented citation or numeric result exists;
   - no generated PDF or auxiliary build file is presented as final;
   - source repository commit and dirty status remain unchanged.

If a generated PDF or auxiliary file is not intended for version control, respect the repository's ignore policy. Do not delete pre-existing artifacts.

## Progress updates

Update root `progress.md` only after verifying the actual outcome:

- Check `Paper PW0` only if the complete scaffold exists and the clean build succeeds.
- If the scaffold exists but no compatible builder is available or the build fails, leave PW0 unchecked and add the exact blocker.
- Do not check PW1 or any later phase.
- Do not change experiment-lane completion states.

Update the PW0 task packet and `plan/progress.md` at the end.

## Acceptance criteria

PW0 is complete only if:

1. `paper_state.json` accurately records drafting state and blockers.
2. `main.tex` includes all ten planned sections.
3. Every section has one file, heading, and stable label.
4. The provisional title and Abstract are evidence-bounded and visibly non-final.
5. No author identity, citation, capability, or result is invented.
6. `plan/terminology.md` establishes canonical terms and unsafe alternatives.
7. `figures/figure_plan.md` separates concept assets from result assets.
8. `BUILD.md` records a reproducible command and tool version.
9. A clean manuscript build succeeds and its result is recorded.
10. Root and skill progress records agree.
11. The source repository remains clean at its starting commit.

If any criterion is unmet, report PW0 as **blocked or partial**, not complete.

## Final report

Report:

1. files created or changed;
2. exact title/author-placeholder/Abstract treatment;
3. section mapping;
4. terminology artifact;
5. build command, tool version, exit status, log, and PDF path/hash if produced;
6. quality-gate result and expected blockers;
7. progress updates;
8. repository status for both paper and source checkouts;
9. the single next action for PW1.

Do not commit, push, tag, modify source code, run paper benchmarks, or begin PW1 without a separate instruction.
