# Full-paper workflow execution log

Root [`progress.md`](../progress.md) is the authoritative project milestone tracker. This file records executions of the `ai-research-writing-skill` workflow and does not replace the root tracker.

## EXP0: focused performance protocol

- **2026-07-30 -- scope:** Defined a bounded RQ3 practical-performance slice
  for workspace readiness and public command/read/write/edit operations. The
  protocol explicitly avoids competitive-superiority and multi-agent-quality
  claims.
- **2026-07-30 -- reproducibility package:** Created the phase-gated
  `experiment_inventory.md`, environment staging and first-step verification
  guide, four expected table schemas with separated simulated previews, and an
  append-only experiment log.
- **2026-07-30 -- executable configuration:** Added a pinned-image two-cell
  smoke preset, an 18-cell good-pass preset, and a network-free preflight that
  requires prebuilt product artifacts and performs no build, install, pull, or
  source mutation.
- **2026-07-30 -- deterministic checks:** Both presets passed planner
  expansion; the good pass expands to 1,836 trial batches and 5,508 operation
  requests. The preflight passed `bash -n`. No live sandbox or performance
  measurement was run.
- **2026-07-30 -- blockers:** Final native Ubuntu verification, live smoke,
  file-operation base-workspace policy, explicit sandbox-create timing, pilot
  duration, source/benchmark freeze, and protocol approval remain open.

## PW0: manuscript scaffold and vocabulary

- **2026-07-30 -- started:** Loaded the complete skill instructions, full-paper workflow, artifact contract, deterministic-check instructions, figure workflow, and figure specification.
- **2026-07-30 -- input audit:** Read all twelve PW0 input artifacts completely. Confirmed that no `research_handoff.json`, prior `paper_state.json`, LaTeX scaffold, bibliography, section tree, plan tree, or build record existed.
- **2026-07-30 -- provenance check:** Confirmed the read-only source checkout is clean on `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`. Confirmed the paper checkout already contains uncommitted project work that must be preserved.
- **2026-07-30 -- build preflight:** `latexmk`, `tectonic`, `pdflatex`, `xelatex`, `lualatex`, and `bibtex` were not available on `PATH`. No installation or system reconfiguration was attempted.
- **2026-07-30 -- early quality gate:** The full-paper quality gate reported the seven expected missing artifacts: `main.tex`, `references.bib`, `BUILD.md`, `build_check.md`, `citation_verification.md`, `figures/figure_plan.md`, and `plan/terminology.md`.
- **2026-07-30 -- scaffold and vocabulary:** Created the provisional-title/draft-Abstract `main.tex`, ten heading-only section files, comment-only bibliography, canonical terminology record, non-numerical figure/table plan, build instructions, citation record, and build record. No PW1--PW6 body prose or figure/result asset was generated.
- **2026-07-30 -- build attempt:** Ran the skill `record_build.py --run` against the declared `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` command. The recorder returned exit code 2 because `latexmk` does not exist; no compatible alternative or tool version was available and no `main.pdf` was produced. The attempt is recorded in `pw0-build-attempt.log`, `build_check.md`, `BUILD.md`, and `paper_state.json`.
- **2026-07-30 -- checks:** The final skill quality gate passed at stage `drafting`. Citation-key, exact section-structure, section-input-order, required-terminology, paper-state, and read-only source-baseline checks passed.
- **2026-07-30 -- outcome:** PW0 is incomplete at the build gate. All scaffold/vocabulary outputs exist, but completion requires a compatible LaTeX toolchain and a successful recorded build. Full-paper evidence and author blockers remain carried in `paper_state.json`.

## Cross-lane complexity and evolution audit

- **2026-07-30 -- source audit:** Read the v1 lease, overlay setup, merged-view lookup, capture, publish plan/resolve/merge/commit, squash, and lease-GC paths at baseline commit `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **2026-07-30 -- migration audit:** Read the LayerStack 2.0 Windows experiment at commit `6e486fca75cf3afebd091f5ba8a2e48e77d9d05e`, including its A/B/C protocol and sealed negative Windows feasibility conclusion.
- **2026-07-30 -- outputs:** Created `complexity_and_evolution.md`; updated the evidence map, inventory, paper skeleton, writing/experiment lanes, root progress tracker, paper state, and manuscript Sections 7--9.
- **2026-07-30 -- evidence boundary:** Recorded source-derived complexity terms as hypotheses/implementation analysis, not measurements. Recorded LayerStack 2.0 as future work, not a v1 capability; preserved the narrow `FICLONE errno=95` Windows result and copy-fallback requirement.

## PW0 maintenance follow-up

- **2026-07-30 -- later-phase preservation:** Confirmed that Sections 7--9 now contain intentional PW3/PW4 source-derived prose. Updated the PW0 task packet so its heading-only acceptance check is explicitly historical; no manuscript section was reverted or edited.
- **2026-07-30 -- toolchain recheck:** Rechecked `PATH`, conventional local MiKTeX/TeX Live/TinyTeX locations, and WSL. `latexmk`, a compatible TeX engine, and BibTeX remain unavailable. No toolchain was installed or reconfigured, the declared build was not rerun, and the existing precise build blocker and hashes were retained.
- **2026-07-30 -- verification:** The full-paper quality gate passed at the current `drafting` stage before and after the maintenance edit. Section input order, later-work preservation in Sections 7--9, relative links, Git diff whitespace, follow-up-file whitespace, paper state, prior build-log hash, and the read-only source baseline all passed. `main.pdf` remains absent.

## PW0 build closure

- **2026-07-30 -- user-local toolchain:** Installed the official self-contained TinyTeX distribution under `C:\Users\yifan\AppData\Roaming\TinyTeX` and added its bin directory to the user `PATH`. No administrator or system-wide installation was used.
- **2026-07-30 -- recorded build:** Ran the declared `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` command through the skill build recorder. Latexmk 4.88, pdfTeX 1.40.29 from TeX Live 2026, and BibTeX 0.99e produced `main.pdf` with exit code 0.
- **2026-07-30 -- attestation:** Recorded input SHA-256 `e0c64365a445533c8efdb74068d5d5d28945871853d26c06692d0f791b48868e`, PDF SHA-256 `dd63976a4714299aa99f564e2669c1e8a438dad6fe6eeaf1f4eeaadd50ef4406`, and build-log SHA-256 `b0ad2eb77266611365f2af42a8b146fa25d8fdbd29d4cce599d7106b8b1d1e94`.
- **2026-07-30 -- log and visual QA:** The log contains no errors, undefined citations/references, missing files, or overfull boxes. Five underfull boxes remain in the provisional cost table, and the comment-only bibliography intentionally yields an empty References page. All four rendered pages were inspected with no clipping, overlap, or broken glyphs.
- **2026-07-30 -- outcome:** PW0 is complete. Remaining full-paper blockers are scientific, provenance, author, literature, and evaluation blockers carried in `paper_state.json`.

## PW1: foundations

- **2026-07-30 -- started:** Loaded the complete `ai-research-writing-skill` instructions, full-paper workflow, artifact contract, section-writing method, task-management rules, and reference map. Created `plan/task-packets/pw1-foundations.md` with the bounded scope, pre-draft theses, paragraph roles, evidence IDs, rejection checks, validation plan, and acceptance criteria.
- **2026-07-30 -- input audit:** Read all 21 required PW1 paper artifacts completely. Confirmed the paper checkout is clean on `agent/pw0-build-pw1-prompt`; confirmed the read-only source checkout is clean on `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`. No source, experiment, later-section, bibliography, or figure artifact was changed.
- **2026-07-30 -- evidence boundary:** PW1 uses M0--M6, C1--C4, and D1--D9. C5 and measured useful-work or concurrency-ceiling language remain pending evaluation; source-derived wording remains provisional until `paper-v1-freeze`.
