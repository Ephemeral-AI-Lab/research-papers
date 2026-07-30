# PW0 task packet: manuscript scaffold and vocabulary

**Status:** Complete.

## Bounded objective

Create the minimal arXiv-compatible LaTeX package, full-paper execution records, canonical terminology, and non-numerical figure/table plan for PW0. The package must encode the current ten-section structure and provisional framing without drafting the evidence-bearing body assigned to PW1--PW6.

## Authoritative inputs

- `README.md`, `PRD.md`, and root `progress.md`
- `paper_story.md` and `paper_skeleton.md`
- `lanes/paper-writing.md` and `lanes/experiments.md`
- `project_inventory.md`, `claim_evidence_map.md`, and `cli_contract_matrix.md`
- `references/related_work.md`
- `NEXT_AGENT_PROMPT.md`
- Read-only source checkout `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox` on clean `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`
- `ai-research-writing-skill` full-paper workflow, artifact contract, figure workflow, and figure specification

## Allowed files

- `paper_state.json`
- `main.tex`, `references.bib`, `BUILD.md`, `build_check.md`, and `citation_verification.md`
- `sections/01-introduction.tex` through `sections/10-conclusion.tex`
- `plan/task-packets/pw0-manuscript-scaffold.md`, `plan/progress.md`, and `plan/terminology.md`
- `figures/figure_plan.md`
- Root `progress.md`, only to mark the PW0 outcome accurately
- Build outputs and logs produced by the declared local LaTeX command or the skill build recorder

## Non-goals

- No source-code changes, source commits, branches, worktrees, tags, or benchmark runs.
- No invented author metadata, citations, numbers, results, security guarantees, or final contribution wording.
- No PW1--PW6 body prose, generated figures, result tables, final title, final Abstract, final Introduction, or final Conclusion.
- No global toolchain installation or system configuration change.

## Acceptance checks

- [x] All required state, planning, terminology, bibliography, build, and figure-plan artifacts exist.
- [x] `main.tex` uses the provisional recommended title and draft author marker.
- [x] The design-first Abstract is present verbatim in substance and visibly marked provisional.
- [x] At the PW0 scaffold checkpoint, all ten section files contained only a section heading, stable label, and minimal visible draft marker. This is a historical checkpoint condition, not a current manuscript invariant: later PW3/PW4 work has intentionally advanced Sections 7--9 with source-derived complexity, evaluation, limitations, and evolution prose.
- [x] `main.tex` inputs the ten sections in order and references `references.bib`.
- [x] No experimental-result asset is required to compile.
- [x] No unverified BibTeX entry or manuscript citation is introduced.
- [x] The source checkout remains clean at the required baseline commit.
- [x] An executed build and exact tool versions are recorded.
- [x] The skill quality gate was run before and after scaffold creation.
- [x] The declared LaTeX command completes successfully and produces an attested `main.pdf`.

## Final outcome and blockers

All requested PW0 source and planning artifacts were created without modifying the read-only source checkout or overwriting prior paper work. The early quality gate exposed the seven expected missing scaffold artifacts; after creation, the full-paper quality gate passed at stage `drafting`. Citation, section-structure, section-order, terminology, JSON-state, and source-baseline checks also passed.

PW0's build gate was closed on 2026-07-30 using a user-local TinyTeX/TeX Live 2026 installation. The skill recorder executed `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`, produced `main.pdf`, and recorded the command, exact tool versions, exit code, run time, input hash, PDF hash, and build-log hash in `paper_state.json`. The mode-aware full-paper quality gate passed after the attestation.

Other full-paper blockers carried in `paper_state.json` include the missing `paper-v1-freeze`, missing `experiment_inventory.md`, absent final measurements, unresolved author metadata, best-effort attribution, protected-drop and restart questions, source-derived cost-model validation, LayerStack 2.0 evidence, and the Claim Plane novelty audit.

The checklist above records the PW0 scaffold as it existed at that checkpoint. Subsequent source-derived work in Sections 7--9 is expected manuscript evolution and does not retroactively fail PW0's heading-only scaffold acceptance check.
