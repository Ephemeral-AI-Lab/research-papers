# Ephemeral Sandbox paper artifact

This directory contains the source, evidence ledger, and reproducible PDF for
the Ephemeral Sandbox design paper. The claim is intentionally narrow: the
source implements private LayerStack workspace sessions and a controlled
filesystem-delta publication protocol; one frozen local treatment reports
startup, public-CLI, and selected resource observations.

## Start here

- `main.tex` and `main.pdf` — manuscript source and current review build.
- `ARTIFACTS.md` — frozen evidence inventory and integrity anchors.
- `REPRODUCIBILITY.md` — deterministic projection, verification, and build
  commands.
- `REVIEWER_GUIDE.md` — claim-to-artifact reading path.
- `SUBMISSION.md` and `submission_readiness.md` — external authoring and
  publication gate status.

## Evidence and provenance

- `numeric_evidence.json` and `sections/results_numeric_bindings.md` bind each
  displayed result number to the immutable Table-A provenance CSV.
- `citation_requests.json`, `citation_lock.json`, and
  `citation_verification.md` provide terminal primary-source citation records.
- `plan/source_revalidation.md` and `cli_contract_matrix.md` anchor source
  claims to the tagged product snapshot.
- `literature/` records the closest-work audit and the bounded positioning.

## Status

The scientific and build review is complete. The package is not yet
submission-ready because the paper owner must supply confirmed author names,
affiliations, intended venue/category, and disclosure text. No experiment rerun
or pull-request merge is part of this paper artifact.
