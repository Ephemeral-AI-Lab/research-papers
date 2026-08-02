# Reviewer guide

## Fast path

Read the abstract, Sections 3--5 for the mechanism boundary, Section 8 for
the frozen treatment, and Section 9 for the claim exclusions. Then run the
commands in `REPRODUCIBILITY.md`.

## What each evidence class supports

| Question | Evidence to inspect | Supported conclusion |
| --- | --- | --- |
| What is the mechanism? | `plan/source_revalidation.md`, Sections 3--7 | Source-defined private workspace and publication behavior. |
| Which numbers are reportable? | `sections/results_numeric_bindings.md`, `numeric_evidence.json`, frozen Table-A output | Only the rendered local-treatment values. |
| Can values be traced to raw data? | Frozen `numeric-provenance.csv` and archive manifest | Selector-level provenance for the numerical tables. |
| Are citations current? | `citation_requests.json`, `citation_lock.json`, `citation_verification.md` | Terminal metadata and sentence-level support records. |
| Are visuals evidence? | `figures/concept-figure-review.md` | No; they explain the mechanism only. |

## Negative evidence boundary

The package does not support comparative performance, a useful-work concurrency
ceiling, semantic merge correctness, crash recovery, security, process-state
rollback, cross-platform behavior, or team productivity. Those omissions are
intentional and are not hidden as unresolved result claims.
