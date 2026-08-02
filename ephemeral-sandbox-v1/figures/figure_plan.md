# Figure and table plan

No figure or table asset was generated in PW0. PW2.5 now provides four
self-contained concept-figure prompts under `figures/source/` and four
author-supplied PNG review drafts under `figures/concept/`. Their hashes,
provenance boundary, and drafting-stage QA are recorded in
[`concept-figure-review.md`](concept-figure-review.md). The author accepted the
supplied files unchanged for the drafting manuscript and deferred visual,
resolution, topology, and style-family repair to PW7. Concept-method assets are
illustrative only and must still be checked against final terminology and tagged
source before submission. Every evidence-result asset remains blocked until its
named frozen source or experimental data exists.

## PW2.5 prompt package

All four prompts use the shared visual language in
[`source/STYLE_GUIDE.md`](source/STYLE_GUIDE.md), while repeating the relevant
style instructions so each prompt can be sent independently to an image
generator.

| Figure ID | Diagram | Separate prompt | Figure-specific composition | Status |
|---|---|---|---|---|
| `fig:system-architecture` | LayerStack and workspace-session architecture | [`fig_system_architecture_prompt.md`](source/fig_system_architecture_prompt.md) | Three semantic bands with parallel private sessions and one publication boundary | Final color/grayscale review passed; topology/layout waiver recorded. |
| `fig:publication-sequence` | Workspace-to-publication sequence | [`fig_publication_sequence_prompt.md`](source/fig_publication_sequence_prompt.md) | Five vertical swimlanes with a highlighted active-manifest commit line | Final color/grayscale review passed; non-swimlane composition waived. |
| `fig:lifecycle-state-machine` | Workspace-session lifecycle state machine | [`fig_lifecycle_state_machine_prompt.md`](source/fig_lifecycle_state_machine_prompt.md) | Precommit/post-commit state regions with retry and cleanup-failure branches | Final color/grayscale review passed; qualified normal-path abstraction retained. |
| `fig:reconciliation-decision` | Current-head reconciliation decision flow | [`fig_reconciliation_decision_prompt.md`](source/fig_reconciliation_decision_prompt.md) | Source/ignored branches, narrow merge gates, and shared whole-candidate terminals | Final color/grayscale review passed; portrait layout and style-family variation waived. |

Review and finalization order:

1. integrated all four review drafts unchanged during PW3;
2. revalidated lifecycle terminology against completed Section 6;
3. inspected compiled placement, captions, final-size color, and grayscale;
4. repair or explicitly accept all recorded visual disparities during PW7.

## Planned assets

| ID | Asset | Class | Role | Evidence status | PW0 disposition |
|---|---|---|---|---|---|
| F1 | Problem/concurrency-ceiling teaser | `concept-method` | Teaser | Illustrative only | Planned; do not generate in PW0. |
| F2 | LayerStack/session architecture | `concept-method` | Overview | Baseline-source-grounded concept | Planned; source must be revalidated at `paper-v1-freeze`. |
| F3 | Session/publication state machine | `concept-method` | Method detail | Baseline-source-grounded concept | Planned; source must be revalidated at `paper-v1-freeze`. |
| T1 | Shared-directory/worktree/Ephemeral design comparison | `concept-method` | Method comparison | Mechanism comparison only | Planned; no performance cells or implied ranking. |
| T2 | Final-tag CLI contract table | `evidence-result` | Source-evidence summary | Blocked | Regenerate from tagged catalogs/help and archived contract-test outputs. |
| T3 | Publication behavior table | `evidence-result` | Correctness summary | Blocked | Requires frozen source plus archived final correctness/fault outcomes. |
| T4 | Experimental setup and provenance table | `evidence-result` | Result context | Blocked | Requires protocol lock, `experiment_inventory.md`, and frozen run manifests. |
| T5 | Isolation/publication/fault result table | `evidence-result` | Result summary | Blocked | Requires frozen RQ1/RQ2/RQ5 data and deterministic table generation. |
| F4 | Useful-work scaling figure | `evidence-result` | Result summary | Blocked | Requires frozen RQ4 data and deterministic plotting. |
| F5 | Conflict/retry/integration/resource cost figure | `evidence-result` | Failure and limiting-regime analysis | Blocked | Requires frozen RQ3/RQ4 data and deterministic plotting. |

## F1: problem/concurrency-ceiling teaser

- **Message:** Teams and exploratory swarms can fan out attempts, while workspace, integration, verification, and resource costs can limit durably accepted useful work; private sessions add a controlled publication boundary without claiming a measured improvement.
- **Entities:** agent team, exploratory swarm, shared mutable project, private workspace sessions, publication boundary, accepted project head, conflict/retry/verification/resource costs.
- **Relationships:** fan-out from work to workers; private execution views converge through capture/reconciliation; dashed failure paths return rejection/retry.
- **Layout:** two-row left-to-right teaser, with team and swarm workload families above a common publication boundary.
- **Backend:** `generated-image`, with deterministic text overlay if exact labels are not reliable.
- **Source:** future `figures/fig_teaser_prompt.md`; terminology from `plan/terminology.md`.
- **Fallback:** omit the figure; the manuscript must compile without it.
- **Reviewer risk:** A rising curve or agent-count marker could imply an unmeasured ceiling result; use no axes, numbers, or performance encoding.

## F2: LayerStack/session architecture

- **Message:** One active LayerStack history supplies leased read-only lower views to many session-private overlays, and only accepted publication advances the shared active head.
- **Entities:** active manifest, base/published/squash layers, lease, private upper/work directories, namespace holder/runners, capture, reconciliation, promoted layer.
- **Relationships:** manifest selects ordered layers; lease pins a logical view; lower layers feed session projections; capture flows to reconciliation; accepted publication prepends a promoted layer and replaces the manifest.
- **Layout:** horizontal architecture with a shared-history band, parallel private-session band, and publication path.
- **Backend:** `generated-image` or `hybrid` with exact deterministic labels.
- **Source:** future `figures/fig_architecture_prompt.md`; baseline paths and C1/C2/D1--D7.
- **Fallback:** omit the figure; no manuscript dependency before the asset exists.
- **Reviewer risk:** Do not depict layers as filesystem-enforced immutable, networking as universally isolated, or audit/cleanup inside the atomic data boundary.

## F3: session/publication state machine

- **Message:** Explicit lifecycle outcomes distinguish active execution, capture, rejection/precommit retry, accepted publication, discard, close, and published-but-not-closed cleanup failure.
- **Entities:** active session, draining command ledger, capture, reconcile, rejected, retry, no-op, published, destroy, closed, published-but-not-closed.
- **Relationships:** solid state transitions for success; dashed retry/failure transitions; data commit precedes audit and cleanup.
- **Layout:** left-to-right state machine with a separate post-commit cleanup branch.
- **Backend:** `hybrid` generated diagram plus deterministic labels.
- **Source:** future `figures/fig_state_machine_prompt.md`; C4 and D1/D6/D8/D9.
- **Fallback:** omit the figure.
- **Reviewer risk:** A single transaction box would overstate atomicity; data publication and later cleanup must remain visually separate.

## T1: shared-directory/worktree/Ephemeral design comparison

- **Message:** The three workspace strategies differ in live write visibility, base identity, execution-state sharing, reconciliation boundary, lifecycle outcomes, and attribution surface; the table makes no performance ranking.
- **Entities:** shared mutable directory, Git worktree, Ephemeral workspace session; comparison dimensions from `paper_skeleton.md`.
- **Relationships:** side-by-side mechanism comparison.
- **Layout:** deterministic text table.
- **Backend:** `latex-table`.
- **Source:** final mechanism definitions, authoritative Git worktree documentation, tagged Ephemeral source, and locked baseline protocol.
- **Fallback:** omit until every cell has a verified basis.
- **Reviewer risk:** Do not imply worktrees cannot be orchestrated safely or that Ephemeral is faster, cheaper, or semantically safer.

## T2: final-tag CLI contract table

- **Message:** The tagged v1 interface separates management, sandbox-scoped runtime, and read-only observability operations with explicit scopes and state effects.
- **Entities:** operation, client, scope, state effect, request correlation, JSON/exit contract.
- **Relationships:** exact mapping from tagged catalog/projection entries to paper rows.
- **Layout:** multi-page deterministic LaTeX table if needed.
- **Backend:** `latex-table`.
- **Source:** archived final-tag catalogs/help, contract-test logs, and regenerated `cli_contract_matrix.md`.
- **Fallback:** omit; the PW0 manuscript does not depend on it.
- **Reviewer risk:** Baseline counts are provisional and live-site counts drift; no row may be copied into final evidence before tag regeneration.

## T3: publication behavior table

- **Message:** Each candidate path/change class has a source-defined accept, bounded-merge, reject, or protected-drop outcome, and unresolved change rejects the whole data changeset.
- **Entities:** unchanged current path, eligible text divergence, binary/oversized/invalid UTF-8 input, structural conflict, delete/modify, protected path, unsupported entry, fault phase.
- **Relationships:** change class to resolution and active-manifest effect.
- **Layout:** deterministic matrix.
- **Backend:** `latex-table`.
- **Source:** tagged plan/resolve/merge/publish sources and archived RQ2 correctness/fault results.
- **Fallback:** omit until frozen evidence exists.
- **Reviewer risk:** Source rules and observed test results must be distinct columns; no semantic merge claim.

## T4--T5 and F4--F5: future experimental results

- **Message:** Report the exact frozen setup, correctness/fault outcomes, useful-work behavior, and limiting cost decomposition without presuming a positive result.
- **Entities:** workloads, baselines, workers, accepted-work unit, metrics, uncertainty, conflicts, retries, integration, verification, selection, CPU/RSS/I/O/storage, failures.
- **Relationships:** experimental factors to measured outcomes, with negative and mixed results retained.
- **Layout:** setup/provenance and correctness matrices for T4/T5; line or small-multiple plots with uncertainty for F4/F5.
- **Backend:** `latex-table` for T4/T5 and `deterministic-plot` for F4/F5.
- **Source:** frozen run manifests, raw data, versioned analysis, and result IDs after evidence lock.
- **Fallback:** omit all result assets; never substitute conceptual graphics or illustrative numbers.
- **Reviewer risk:** Every value needs complete provenance, defined denominator/direction, sample count, uncertainty, exclusions, and workload-specific interpretation.
