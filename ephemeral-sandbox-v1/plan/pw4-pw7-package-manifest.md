# PW4--PW7 package manifest

## Included review artifacts

- Manuscript: `main.tex`, `sections/`, `references.bib`, `main.pdf`.
- Evidence: `ARTIFACTS.md`, `numeric_evidence.json`, frozen archive and Table-A
  paths named in `ARTIFACTS.md`, and `sections/results_numeric_bindings.md`.
- Reproduction: `scripts/generate_latex_results.py`,
  `scripts/generate_bibliography.py`, `REPRODUCIBILITY.md`, and
  `build_check.md`.
- Literature: `citation_requests.json`, `citation_lock.json`,
  `citation_verification.md`, `literature/`, and `references/related_work.md`.
- Review and handoff: `REVIEWER_GUIDE.md`, `SUBMISSION.md`,
  `submission_readiness.md`, `plan/reviewer_report.md`, and figure review
  records.

## Excluded material

- Temporary PDF page renders under `plan/pw4-pw7-render/` are QA intermediates
  only and are not submission artifacts.
- LaTeX auxiliary files, build caches, editor files, and prior draft prompts
  are not release artifacts.
- Qualification, smoke, pilot, exploratory, and superseded experiment outputs
  are not result evidence.
- The task packet and user-owned progress edits are planning context and are
  not automatically staged for a paper commit.

## Gate disposition

**FAIL/GATED.** The declared review artifacts are complete and verified, but
author/affiliation/venue/disclosure metadata remains an external owner input.
Neither a pull-request merge nor external submission is performed by this
package.
