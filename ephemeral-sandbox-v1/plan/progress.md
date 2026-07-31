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
- **2026-07-30 -- environment-qualification continuation:** Exhausted bounded
  local discovery for `eos-benchmark-ubuntu24`; no DNS, SSH, hosts-file,
  Docker-context, Hyper-V, or eligible Multipass route exists. The only local
  Multipass instance is Ubuntu 22.04 and remains ineligible.
- **2026-07-30 -- final-host automation:** Added a reproducible Windows bundle
  builder, hash-locked Linux CPython 3.13 dependency input/lock, off-clock host
  staging script, strict network-free preflight, and an archival smoke
  qualification wrapper with before/after leak comparison.
- **2026-07-30 -- transfer readiness:** Generated and integrity-checked the
  final-host transfer bundle at
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\ephemeral-sandbox-v1-20260730-ready-v2`.
  The strict verifier also failed closed on WSL at the exact-hostname gate. No
  benchmark run or measurement was performed.
- **2026-07-30 -- CLI-only correction:** Replaced the direct-client environment
  smoke with two independent product-CLI-controlled lifecycles. The final WSL
  diagnostic completed 2/2 batches and 20 validated CLI calls with correctness
  pass, empty CLI stderr, no gateway warnings/errors, and zero Docker resources
  remaining for its unique gateway instance. This is automation evidence only;
  the native-host gate remains unpassed.
- **2026-07-30 -- handoff boundary:** Corrected the external action: SSH and new
  provisioning are optional. Completion requires running the supplied handoff
  on an existing eligible native host, or provisioning one only if none exists,
  and returning an all-pass qualification artifact set.
- **2026-07-30 -- host correction:** User clarification established native
  Windows plus Docker Desktop as the final host. Ubuntu 24.04 is the sandbox
  image. The earlier native-Ubuntu/SSH/CPython/ext4 handoff is superseded.
- **2026-07-30 -- Windows package and qualifier:** Checksum-verified and staged
  the official `v0.1.4` Windows AMD64 package under ignored product `target/`.
  Added a PowerShell-only strict host/package/Docker/image qualifier using the
  native gateway and manager/runtime/observability CLIs.
- **2026-07-30 -- environment completion:** Accepted
  `qualification-windows-docker-20260730-final-6`: native Windows/Docker
  Desktop preflight pass, 2/2 independent batches, 20 validated product-CLI
  calls, correctness pass, empty CLI stderr, zero warnings/failures, unchanged
  EOS baseline, and zero resources remaining for the qualifier gateway. The
  environment-only task is complete.

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
- **2026-07-30 -- artifacts produced:** Drafted Sections 2 and 3 and completed the paragraph-level reverse outline in `plan/task-packets/pw1-foundations.md`. Updated only the authorized task, progress, machine-state, and build records; no claim-map or terminology correction was needed.
- **2026-07-30 -- recorded build:** The skill recorder executed `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` with exit code 0 using Latexmk 4.88, pdfTeX 1.40.29, and BibTeX 0.99e from TeX Live 2026. It recorded input SHA-256 `8a9d0f97487ccf937efd82eb6a5726b2c7c8b5e3e31be1434945826a00731708`, PDF SHA-256 `ba4963d3d5f6352e1829946290265671599432e9984e301d5626de7316435327`, and build-log SHA-256 `719696c0aa0efb9fce4796efaab3cce5b27dd17563c4b60d7f4951b539aa7f30`.
- **2026-07-30 -- verification:** The full-paper quality gate, citation-key check, JSON/mode/stage check, exact section-count/order check, Section 2/3 heading/label check, 115-target relative-link check, prohibited-claim review, PDF/log hash check, and Git whitespace check passed. The source checkout remains clean on `main` at the audited baseline. The build log has no errors, undefined citations/references, missing files, or overfull boxes; five pre-existing underfull boxes remain in the Section 7 cost table.
- **2026-07-30 -- outcome:** PW1 is complete. Remaining scientific risks are the missing source freeze and frozen evaluation, best-effort post-commit attribution, unresolved explicit/implicit protected-drop policy, and untested lease/substitution behavior across daemon restart.

## PW2: workspace execution and capture/publication

- **2026-07-30 -- started:** Reloaded the complete `ai-research-writing-skill` instructions and the required workflow, artifact, section-writing, and task-management references. Created `plan/task-packets/pw2-workspace-publication.md` before manuscript drafting with the bounded scope, section theses, paragraph roles, evidence IDs, rejection checks, validation plan, and acceptance criteria.
- **2026-07-30 -- input audit:** Read the authoritative PW2 lane contract, C1/C2 and D1--D8 evidence, canonical terminology, story/skeleton/inventory/interface records, Sections 2--5, and the relevant read-only baseline source for workspace creation, execution, capture, reconciliation, commit, attribution, and cleanup. No standalone `lanes/prompts/pw2.md` exists, so the task packet records the lane charter as authoritative.
- **2026-07-30 -- worktree boundary:** Preserved the authorized PW1 record updates and unrelated pre-existing benchmark/experiment modifications. Recorded protected-file hashes before drafting; no source, benchmark, experiment, bibliography, figure, or non-target manuscript edit is authorized.
- **2026-07-30 -- artifacts produced:** Drafted Sections 4 and 5 from C1/C2 and D1--D8 and completed their paragraph-level reverse outlines. The drafts distinguish implicit commands, explicit sessions, session and sessionless file paths, source and ignored publication routes, merge eligibility, the active-manifest visibility point, and post-commit attribution/cleanup boundaries.
- **2026-07-30 -- recorded build:** The skill recorder executed `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` with exit code 0 using Latexmk 4.88, pdfTeX 1.40.29, and BibTeX 0.99e from TeX Live 2026. It recorded input SHA-256 `36877891dbce1e066589d8a295e436654ccb097970620003cdaf45871f74311b`, PDF SHA-256 `801ac91c302ae3ea7d5827d34dd4da09278e8f537409e3426fd4ff30c8ed36e7`, and build-log SHA-256 `9fc4261ab327472e004f4f62466bf2266218d1b17a66cc5b852ee5dbe7b23265`.
- **2026-07-30 -- verification:** The full-paper quality gate, citation-key check, JSON/mode/stage check, exact section-count/order check, Section 4/5 heading/label check, 115-target relative-link check, prohibited-claim review, attested input/PDF/log hash check, protected-file hash review, and scoped and whole-worktree Git whitespace checks passed. The source checkout remains clean on `main` at the audited baseline. The build log has no errors, undefined citations/references, missing files, or overfull boxes; five pre-existing underfull boxes remain in the Section 7 cost table.
- **2026-07-30 -- outcome:** PW2 is complete. Remaining scientific risks are the missing source freeze and frozen fault/resource evidence, best-effort post-commit attribution, nonuniform protected-drop entry-point policy, unvalidated worst-case text-diff resource behavior, and lifecycle/recovery outcomes deferred to PW3.

## PW2.5: concept-figure prompt package

- **2026-07-30 -- started:** Loaded the figure workflow, figure-specification contract, venue/style presets, canonical terminology, current figure plan, and Sections 3--6. Created `plan/task-packets/pw2-5-figure-prompts.md` before authoring prompt sources.
- **2026-07-30 -- scope boundary:** This package creates prompts/specifications only. It does not generate images, edit manuscript inputs, refresh the PDF build, or treat a concept diagram as experimental evidence. Pre-existing paper, benchmark, and experiment changes remain untouched.
- **2026-07-30 -- artifacts produced:** Created one shared Classic Academic × Modern Minimal style guide and four separate, self-contained prompt/spec files for the system architecture, publication sequence, lifecycle state machine, and reconciliation decision flow. Updated `figures/figure_plan.md` with direct links, distinct compositions, generation order, and asset status.
- **2026-07-30 -- verification and outcome:** Confirmed all four prompts independently include style, palette, output, exact labels, and acceptance criteria. The 121-target relative-link check, full-paper quality gate, and scoped whitespace check pass. Prompt preparation is complete; image generation and visual QA remain pending, and the lifecycle asset is provisional until PW3.

## PW2.5: concept-figure generation and review

- **2026-07-30 -- started:** Loaded the image-generation and paper-figure workflows, created `plan/task-packets/pw2-5-figure-generation.md`, and delegated architecture, publication-sequence, and reconciliation assets to non-overlapping subagents. The lifecycle asset will use the next available agent slot.
- **2026-07-30 -- review contract:** Every PNG must pass visual inspection for exact labels, final-width readability, semantic palette, shared/private and commit/post-commit boundaries, and unsupported-claim avoidance. Failed assets receive targeted regeneration or editing rather than automatic acceptance.
- **2026-07-30 -- supplied assets:** The author supplied four PNGs, which were
  moved to the expected `figures/concept/` paths. Generator/model/seed metadata
  and label-placement maps were not supplied; prompt/spec sources remain the
  available regeneration contract.
- **2026-07-30 -- drafting-stage review:** Recorded hashes, dimensions,
  strengths, topology/layout/resolution/style disparities, and the
  concept-only evidence boundary in `figures/concept-figure-review.md`.
  The author accepted all four files unchanged for the drafting manuscript and
  deferred visual repair and normalization to PW7.
- **2026-07-30 -- outcome:** Draft asset generation and review are complete;
  submission-final visual acceptance remains open. Lifecycle/prose consistency
  is carried into PW3.

## PW3: lifecycle, recovery, implementation, and interface

- **2026-07-30 -- started:** Loaded the full-paper, section-writing, figure,
  task-management, and build contracts; created
  `plan/task-packets/pw3-lifecycle-interface.md`; and passed the early
  full-paper quality gate.
- **2026-07-30 -- evidence audit:** Confirmed the read-only source checkout is
  clean on `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
  Audited explicit and implicit finalization, guarded destruction, holder-exit
  reconciliation, bounded recovery artifacts, shutdown, remount, role-separated
  client projections, request construction, output/help behavior, and the
  existing cost model.
- **2026-07-30 -- figure boundary:** PW3 will integrate the four author-supplied
  PNGs without modifying their bytes. Recorded visual disparities are PW7 debt,
  not hidden as passed final-quality gates.
- **2026-07-30 -- artifacts produced:** Replaced the Section 6 placeholder with
  the explicit/implicit lifecycle, partial-failure, holder-exit, recovery,
  shutdown, remount, and lease-aware compaction account. Completed Section 7's
  role-separated operational contract while preserving the source-derived cost
  model. Added four evidence-bounded figure inclusions and one baseline CLI
  contract table.
- **2026-07-30 -- figure revalidation:** Passed the lifecycle image as a
  qualified normal-path abstraction. Recorded its omitted holder-exit,
  shutdown, and remount branches and shared cleanup-node ambiguity, plus all
  architecture, publication, reconciliation, resolution, grayscale, and
  style-family disparities, as PW7-only repair work. Rechecked all four hashes;
  the PNG bytes remain unchanged.
- **2026-07-30 -- recorded build:** The final recorder run executed
  `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` with exit
  code 0 using Latexmk 4.88, pdfTeX 1.40.29, and BibTeX 0.99e from TeX Live
  2026. It recorded input SHA-256
  `e31aa83e7db9c45cdf0c3c1f731fe66670fc6641dc20d755704a7673a552e18a`,
  PDF SHA-256
  `bf893a5ac17e396233232b18d552e77ddddfc2bcba50786d457fd58db71604eb`,
  and build-log SHA-256
  `39a836a6226fc9b8007dd23fda5deb9e2cd8bf3c453faf17539c9b356871e59f`.
- **2026-07-30 -- verification:** The full-paper quality gate, citation-key
  check, structure/label/figure/hash/link checks, source-baseline check, and
  whitespace checks pass. The final log has no errors, emergency stops,
  undefined citations/references, missing files, or overfull boxes; seven
  underfull boxes remain in the two narrow Section 7 tables.
- **2026-07-30 -- PDF inspection and outcome:** Rendered all 14 pages in color
  and grayscale. Figures appear on pages 3, 6, 8, and 10; both Section 7
  tables follow their introductions; no clipping, overlap, broken glyph, or
  page-number defect was found. PW3 is complete. Submission-final figure
  repair/waiver remains PW7, and scientific/source-freeze/evaluation blockers
  remain open.

## EXP1: CLI-only focused performance campaign specification

- **2026-07-30 -- tracker reconciliation:** Updated the authoritative root
  tracker to record the accepted native Windows/Docker Desktop environment and
  remove the stale native-Linux-host experiment gate. Gates 1 and 2 remain
  complete; no performance measurement was run.
- **2026-07-30 -- pre-measurement decisions:** Fixed the focused RQ3 primary
  timing boundary as end-to-end native product-CLI subprocess latency, selected
  `paper-100m` for every operation family, and retained sandbox-create-to-ready
  as a distinct manager-CLI metric. These decisions were recorded before
  viewing performance results.
- **2026-07-30 -- next-agent contract:** Created
  `plan/task-packets/exp1-cli-performance-campaign.md` with exact environment,
  image, executable, hash, cohort, timing, workspace, implementation, test,
  pilot, freeze, final-run, analysis, stop, artifact, and handoff requirements.
  The final focused matrix is 19 cells after the required sandbox-create cell
  is implemented.
- **2026-07-30 -- outcome:** Documentation/specification work is complete.
  The immediate executable task is the reviewed `product_cli` benchmark cohort.
  `paper-env-smoke`, `paper-pilot`, and `paper-good-pass` remain prohibited
  until the implementation and validation gates in the EXP1 packet pass.
- **2026-07-31 -- implementation and qualification:** Implemented and reviewed
  the native Windows `product_cli` cohort, fixed all 19 cells to `paper-100m`,
  added manager-CLI sandbox-create timing, passed the full backend suite, and
  completed clean CLI-only smoke and five-sample pilot runs. The conservative
  final projection was 1,307.100411100 seconds against the author-approved
  1,400-second Gate-3 limit.
- **2026-07-31 -- freeze:** Froze protocol v1.0 at paper commit
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`, product commit
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`, and annotated product tag
  object `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`. No object was pushed.
- **2026-07-31 -- final stop condition:** The sole eligible final run
  `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4` stopped after 853 of 1,938 batches.
  The product file-read request succeeded, but the mandatory post-response
  snapshot CLI failed to connect with WSAEADDRINUSE 10048. Windows TCP/IP
  Event 4227 at the same instant confirms local endpoint-reuse pressure from
  high-rate connection churn.
- **2026-07-31 -- preservation and outcome:** Explicit cleanup completed, and
  the 620,311,242-byte failed corpus was archived and independently verified at
  `experiments/runs/019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`, content-tree
  `sha256:7efa643b12aba09f0ba5ecfbed5b5692a166a5c12931490402d3992d92f3ae6a`.
  It is permanently `failed_ineligible`; Gates 5--7 fail and no partial,
  pilot, or smoke number may enter the paper. A future attempt requires a
  protocol amendment, new freeze, and explicit author authorization.
