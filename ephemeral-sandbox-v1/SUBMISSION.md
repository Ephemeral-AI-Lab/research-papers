# Submission handoff

## Package state

The manuscript source, results projection, citation lock, bibliography, and
PDF build are complete for editorial review. `main.tex` deliberately uses
`Anonymous authors`: real author names, affiliations, and any required
conflict/disclosure metadata have not been supplied by the paper owner.
Therefore this package is **not submission-ready** and must not be uploaded as
a final non-anonymous arXiv record or submitted to a venue as-is.

## Before authoring a submission

- Replace `Anonymous authors` in `main.tex` with the confirmed author list and
  affiliations.
- Confirm the intended venue, license, category, acknowledgements, and any
  conflict/disclosure text.
- Rebuild, record hashes, rerender the PDF, and rerun every command in
  `REPRODUCIBILITY.md`.
- Recheck citations if the lock is older than the requested submission window.
- Confirm that the paper's intentionally narrow evidence boundary remains
  acceptable for the selected venue.

## Do not change without reopening evidence review

Do not add performance/comparison claims, replace numerical displays, alter
the frozen source/tag references, or use new experiment outputs without a new
claim-evidence review. Do not mutate the archive or frozen Table-A output.

## Git and hosting

The paper branch and its draft pull request are review context only. Merging a
paper or product pull request remains a separate user-authorized action; this
campaign does not merge either pull request.
