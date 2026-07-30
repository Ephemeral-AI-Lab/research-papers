# PW3: Lifecycle, Recovery, Implementation, and Operational Interface

## Bounded scope

- Draft Section 6, `Lifecycle and Recovery`.
- Complete Section 7, `Implementation and Operational Interface`, while
  preserving and integrating the existing source-derived cost model.
- Integrate the four supplied concept-method PNGs into Sections 3, 5, and 6
  with evidence-bounded captions.
- Revalidate the lifecycle figure against the completed Section 6 prose.
- Record supplied-asset provenance, review findings, and the author's
  instruction to defer visual/style/resolution changes to PW7.
- Refresh the reproducible manuscript build and workflow records.
- Do not modify the source repository, benchmark implementation, experiment
  protocol, bibliography, or Sections 1--2 and 8--10.

## Target venue and template

- arXiv `cs.OS`.
- Current one-column 10 pt `article` scaffold with 1 inch margins.
- Concept figures are illustrative mechanism diagrams, not correctness,
  performance, security, or cross-platform evidence.

## Authoritative inputs and evidence

- Claims C3--C4, D8--D13, and K1--K5.
- Sections 3--5 and their PW1/PW2 reverse outlines.
- `project_inventory.md`, `claim_evidence_map.md`,
  `cli_contract_matrix.md`, `complexity_and_evolution.md`, and
  `plan/terminology.md`.
- Baseline source checkout on `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- Lifecycle source: finalization policy, explicit publish, implicit finalize,
  guarded destruction, holder-exit reconciliation, bounded recovery artifact,
  shutdown convergence, squash, lease cleanup, and live remount paths.
- Interface source: maintainer component map, three CLI projections, routed
  catalog, request construction, gateway discovery, output rendering,
  catalog-derived help, and contract tests.

## Files allowed to edit

- `main.tex`
- `sections/03-system-model.tex`
- `sections/05-capture-publication.tex`
- `sections/06-lifecycle-recovery.tex`
- `sections/07-implementation-interface.tex`
- `figures/figure_plan.md`
- `figures/concept-figure-review.md`
- `plan/task-packets/pw2-5-figure-generation.md`
- `plan/task-packets/pw3-lifecycle-interface.md`
- `lanes/paper-writing.md`
- `plan/progress.md`
- root `progress.md`
- `paper_state.json`
- `BUILD.md`
- `build_check.md`
- the recorder build log and ignored LaTeX outputs

The four PNG assets are inputs and must remain byte-identical during PW3.

## Section theses and planned paragraph roles

### Section 6 thesis

The runtime makes precommit retry, accepted publication, discard, cleanup
failure, holder loss, and lease-aware compaction distinct lifecycle outcomes
rather than treating workspace finalization as one rollback-capable
transaction.

Planned paragraph roles:

1. Define the lifecycle state and admission boundary.
2. Explain explicit publication, precommit failure, rejection, and retry.
3. Separate commit/no-op from later cleanup and published-but-not-closed.
4. Contrast implicit publish-then-destroy finalization with explicit retry.
5. Explain deliberate discard and convergent resource teardown.
6. Bound holder-exit handling and recovery artifacts without claiming process
   restoration or automatic replay.
7. Explain lease-aware squash, live remount, retained/faulty sessions, and GC.
8. State restart, cancellation, recovery, and platform evidence boundaries.

### Section 7 thesis

The implementation preserves architectural ownership through a role-separated,
catalog-derived operational contract, while its source-derived cost model
identifies scaling variables without converting them into measured results.

Planned paragraph roles:

1. Map the request path and component responsibilities.
2. Describe the management, runtime, and observability client roles and
   baseline operation counts.
3. Define scope, request correlation, connection, and transport behavior.
4. Define JSON streams, exits, and catalog-derived help.
5. Bound role separation as an interface property rather than authorization or
   a complete coordination plane.
6. Preserve and frame the existing source-derived cost model.
7. State the serialized publication and merge-resource hypotheses.
8. Close with Linux, source-freeze, and contract-test evidence boundaries.

## Figure placement and caption plan

- System architecture: Section 3, after shared/private/durable/public state is
  defined.
- Publication sequence: Section 5, before the detailed capture-to-commit prose.
- Reconciliation decision flow: Section 5, next to current-head
  reconciliation.
- Lifecycle state machine: Section 6, after explicit and implicit lifecycle
  outcomes are defined.

Captions must state the takeaway and any omitted boundary. They must not turn
the diagrams into experimental evidence or erase the post-commit boundary.

## Supplied-figure handling

- Preserve exact PNG bytes and record SHA-256, dimensions, and the absence of
  generator/model/seed metadata.
- The author accepts the supplied figures for the drafting-stage manuscript.
- Record topology, layout, resolution, and style-family disparities.
- Defer image redesign, normalization, and replacement to PW7.
- Current acceptance is for manuscript use at the drafting stage, not for
  submission-final figure quality.

## Rejection checks

- Reject wording that lets precommit failure or rejection publish a subset.
- Reject wording that lets post-commit cleanup failure roll back visible data.
- Do not imply that an implicit command session is retained for caller retry
  after publication rejection.
- Do not call a bounded recovery artifact a process checkpoint, restored
  session, or automatic replay.
- Do not claim daemon-restart correctness for in-memory lease/substitution
  registries.
- Do not claim that live remount always succeeds; preserve migrated, retained,
  faulty, and gone outcomes.
- Do not call role-separated clients an authorization or security boundary.
- Do not claim a complete task, intent, resource-lease, service-discovery,
  handoff, scheduling, or coordination plane.
- Keep 8/10/8 operation counts explicitly tied to the provisional baseline and
  final-tag regeneration.
- Keep cost and queueing statements source-derived hypotheses, not measured
  performance results.
- Do not modify or regenerate the four supplied PNG files during PW3.

## Required artifacts

- Complete Sections 6 and 7.
- Four LaTeX figure inclusions with self-contained captions and stable labels.
- A figure provenance and QA record.
- Final paragraph-level reverse outline with evidence and residual risk.
- Synchronized root/lane/skill trackers.
- Fresh recorder-generated build attestation and inspected PDF.

## Validation commands

- `python <skill>/scripts/research_quality_gate.py <paper-folder>`
- `python <skill>/scripts/check_citations.py main.tex references.bib`
- `python <skill>/scripts/record_build.py <paper-folder> --run`
- `python <skill>/scripts/parse_build_log.py main.log`
- JSON parse and `full-paper` / `drafting` assertions.
- Exact ten-section input count/order check.
- Exact Section 6/7 heading and label check.
- Figure-file existence, hash-preservation, and LaTeX-reference check.
- Relative Markdown link check.
- Prohibited-claim and terminology review.
- Scoped and whole-worktree `git diff --check`.
- Read-only source branch, commit, and clean-status check.
- Rendered-PDF visual inspection, including pages containing figures and
  tables.

## Acceptance criteria

1. Sections 6 and 7 satisfy the PW3 lane contract and retain stable headings
   and labels.
2. Every strong sentence maps to C3--C4, D8--D13, K1--K5, or is explicitly a
   boundary or hypothesis.
3. Explicit retry, implicit finalization, no-op, discard, accepted publication,
   published-but-not-closed, holder loss, and cleanup failure remain distinct.
4. Recovery wording does not exceed the implemented bounded-artifact and
   in-process reconciliation mechanisms.
5. Client roles, scopes, request IDs, JSON streams, exits, help derivation, and
   coordination boundary match the baseline contract.
6. The existing cost model remains source-derived and non-numerical in the
   empirical sense.
7. All four supplied figures are integrated unchanged and their disparities
   are recorded as PW7 debt.
8. The lifecycle figure is consistent with the completed prose or any
   discrepancy is explicit in the review record.
9. The recorded build and all declared validation checks pass.
10. The source checkout remains clean at the audited baseline and unrelated
    paper/benchmark/experiment changes remain untouched.

## Final reverse outline

### Section 6

| Paragraph | Message | Evidence | Residual risk |
|---:|---|---|---|
| 1 | Active/finalizing/finalize-failed states, a per-session gate, and the command ledger coordinate in-process lifecycle work without forming a durable transaction log. | C4 | Abrupt restart remains untested. |
| 2 | Explicit precommit capture/publication failure restores an active retained session for deliberate retry or destroy. | C4 | Protected-drop entry-point policy remains nonuniform. |
| 3 | Accepted commit and no-op precede cleanup; committed cleanup failure is published-but-not-closed and cannot roll back the manifest. | C4, D8, D9 | Attribution and cleanup remain outside data commit. |
| 4 | Implicit command sessions publish-then-destroy after ledger drain and do not become caller-managed retry sessions after rejection. | C4 | Capture-after-quiescence and teardown faults still need archived Linux evidence. |
| 5 | Deliberate discard rejects live-command teardown and converges workspace/cgroup cleanup without repeating completed raw teardown. | C4 | Failure interleavings remain source-derived. |
| 6 | Holder-exit handling cancels/joins work and preserves only a bounded diagnostic artifact for eligible implicit sessions, not a restored process/session. | C4 | Partial artifact writes and daemon restart remain unverified. |
| 7 | Squash honors lease boundaries and remount can migrate, retain, fault, disappear, or remain unchanged; GC remains reference-sensitive. | C4, K5 | Physical savings and every substitution ordering are unmeasured. |
| 8 | Shutdown is bounded in-process convergence; in-memory registries prevent a general automatic crash-recovery claim. | C4, K5 | Final fault campaign and source freeze are absent. |

### Section 7

| Paragraph | Message | Evidence | Residual risk |
|---:|---|---|---|
| 1 | Component ownership follows the request path from projected catalog operation through client, gateway, manager, daemon, and low-level crates. | C3 | Baseline links remain provisional. |
| 2 | Three feature-gated clients expose baseline 8/10/8 role-specific operations with projection-integrity coverage. | C3, D10 | Counts require final-tag regeneration. |
| 3 | Request envelopes carry operation, ID, scope, and arguments; only runtime exposes an ID override, and gateway discovery follows explicit precedence. | C3, D11 | Correlation is not causal filesystem attribution. |
| 4 | Help/stdout/stderr/exit behavior forms a machine-readable shell contract, with command exit status remaining response data. | C3, D12 | Final binary fixtures and digests are absent. |
| 5 | Help joins the semantic catalog and projection but does not synchronize external website documentation or prove runtime correctness. | C3, D13 | Live-site drift remains. |
| 6 | Role separation is an orchestration-facing interface property, not authorization, security, or a complete coordination plane. | C3 | External orchestration semantics remain out of scope. |
| 7 | The cost model names manifest, lease, upperdir, changeset, fingerprint, byte, queue, and retained-reference variables without treating them as measurements. | K1--K5 | Empirical validation is absent. |
| 8 | The exclusive publication path creates a queueing/saturation hypothesis while private execution remains parallel. | K3 | No observed limiting regime is claimed. |
| 9 | The 8 MiB input gate does not independently bound Myers trace memory; line count and edit distance remain required stress axes. | K4 | Adversarial CPU/RSS evidence is absent. |
| 10 | Squash can reduce eligible depth but remains constrained by leases and coexistence of old/new representations. | K5 | Latency and physical storage savings are unmeasured. |
| 11 | Linux/OverlayFS, baseline-source, and contract-freeze limits close the implementation account. | C3, C4, K1--K5 | `paper-v1-freeze` and archived final contract tests remain open. |

## Completed validation and outcome

- The full-paper quality gate and citation-key check pass.
- All ten section inputs remain present exactly once and in order; Section 6
  and Section 7 headings and labels are stable.
- All four PNGs exist at the declared paths, retain their recorded SHA-256
  hashes, and are referenced once with stable labels and bounded captions.
- Lifecycle/prose consistency passes with the explicit normal-path qualifier;
  all topology, layout, resolution, grayscale-contrast, and style-family
  exceptions remain recorded for PW7.
- The final recorder run passed with no LaTeX errors, emergency stops,
  undefined citations/references, missing files, or overfull boxes. Seven
  underfull boxes remain in the two narrow source-derived tables, and the
  comment-only bibliography produces the expected empty References warning.
- The 14-page PDF was rendered in color and grayscale. Figures appear on
  pages 3, 6, 8, and 10; the Section 7 tables remain after their introductions;
  no clipping, overlap, broken glyph, or page-number defect was found.
- The read-only source checkout remains clean on `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- PW3 is complete. The four supplied assets remain drafting-stage review
  drafts; their final visual disposition is exclusively a PW7 task.
