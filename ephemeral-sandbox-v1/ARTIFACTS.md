# Artifact guide

## Scope

This artifact package supports a narrow source-and-treatment claim: Ephemeral
Sandbox implements private LayerStack workspace sessions and controlled
filesystem-delta publication; the paper reports a single frozen local treatment
of startup, public-CLI, and selected resource observations. It is not a
comparative benchmark or a general coding-agent productivity evaluation.

## Immutable evidence

| Artifact | Location | Integrity anchor | Use |
| --- | --- | --- | --- |
| Eligible experiment archive | `experiments/runs/019fb86c-096e-7589-a0a4-a6d6ef5d7f8b/` | content tree `606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986` | Raw reports, manifests, and run facts. |
| Frozen table output | `experiments/analysis/final-v11-019fb86c-tables-a/` | output tree `27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04` | Source for manuscript displays. |
| Numeric registry | `numeric_evidence.json` | Project-side selector projection of the frozen provenance CSV | Verifies every manuscript number in result tables. |
| Tagged product source | `plan/source_revalidation.md` | `paper-v1.1-freeze` peeled commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8` | Source-defined mechanism and interface. |
| Citation lock | `citation_requests.json`, `citation_lock.json` | Terminal arXiv/Crossref metadata checks | Scholarly bibliography provenance. |

The archive and frozen table output are read-only evidence. The manuscript
generator reads them but never writes inside either directory.

## Paper-facing outputs

- `main.tex` and `sections/` — buildable manuscript source.
- `sections/generated_results_tables.tex` — generated LaTeX tables; do not edit
  it directly.
- `scripts/generate_latex_results.py` — deterministic table and numeric-registry
  projection.
- `scripts/generate_bibliography.py` — bibliography projection from the verified
  citation lock.
- `main.pdf` — locally built review PDF.
- `literature/` — inventory, comparison matrix, and claim-positioning record.
- `figures/concept-figure-review.md` — final figure QA and explicit waivers.

## Deliberate exclusions

No experiment rerun, new benchmark, external baseline, fault campaign,
security evaluation, or multi-agent productivity study was performed during
paper completion. Qualification, smoke, pilot, earlier protocol, and broader
research-plan material remain excluded from result claims.
