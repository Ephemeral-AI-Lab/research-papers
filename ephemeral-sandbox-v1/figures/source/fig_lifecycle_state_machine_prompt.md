# Figure prompt: Workspace-session lifecycle state machine

## Status

**Provisional until PW3 completes Section 6.** The image generator may produce
a review draft, but the asset must not be treated as manuscript-final until
the lifecycle/recovery prose and D9 boundary are revalidated.

## Figure contract

```yaml
figure_id: fig:lifecycle-state-machine
filename: figures/concept/fig_lifecycle_state_machine.png
figure_class: concept-method
role: method-detail
message: "Precommit failure, rejection, no-op, publication, discard, close, and post-commit cleanup failure are distinct lifecycle outcomes."
core_conclusion: "Data publication and session closure are separate transitions; cleanup failure cannot undo an accepted active-manifest transition."
evidence_hierarchy:
  hero_evidence: "The split between the precommit state region and the post-commit published region."
  supporting_evidence: "Retry, discard, no-op, closed, and published-but-not-closed paths."
layout: "Left-to-right state machine with vertically separated precommit and post-commit regions."
backend: hybrid
source: "C4, D1, D6, D8, D9, Section 3 definitions, and forthcoming PW3 Section 6."
backup: "Deterministic labels and transitions over a generated state-layout base."
caption_takeaway: "A session can be retained before commit or fail to close after commit; only the latter already changed the active head."
evidence_status: illustrative-only
reviewer_risk: "The current Section 6 is still a placeholder; exact transition names and implicit-session cleanup behavior require PW3 verification."
```

## Copy-paste prompt

```text
Create a review-draft lifecycle state-machine diagram for an arXiv systems
paper about Ephemeral Sandbox. The diagram must distinguish precommit session
handling from post-commit cleanup. Its central message is: data publication
and session closure are separate transitions, so a cleanup failure after
publication does not roll back visible data.

This figure is PROVISIONAL until the paper’s Lifecycle and Recovery section is
completed. Do not embellish or infer missing states.

STYLE
Use a flat 2D vector-inspired Classic Academic × Modern Minimal style. White
background, rounded state nodes, thin gray borders, neutral sans-serif labels,
large whitespace, no gradients, no shadows, no 3D, no isometric servers, no
icons except simple state markers, no logos, and no watermarks. Landscape
16:9, at least 3200 x 1800 pixels, 300 DPI or higher. It must be readable at
approximately 6.5 inches wide.

PALETTE
- Active/private session states: sky blue #56B4E9.
- Planning/finalization states: orange #E69F00.
- Published/accepted states: green #009E73.
- Rejection/precommit failure: vermilion #D55E00, dashed arrows.
- Post-commit cleanup states: purple #CC79A7.
- Closed/neutral terminal state: gray #8C8C8C.
- Text: charcoal #222222.
Use labels and line styles in addition to color.

REGIONS
Create two clearly labeled horizontal regions:
1. upper region: “Before data commit”
2. lower or right-side region: “After data commit”
Separate them with a strong green boundary labeled exactly:
“Active manifest replaced”
Do not label the boundary a transaction.

CORE STATE MACHINE
Use these exact state nodes:
- “Active session”
- “Finalizing”
- “Capture”
- “Reconcile”
- “No-op”
- “Published”
- “Destroying”
- “Closed”
- “Finalize failed”

MAIN TRANSITIONS
Draw solid gray arrows:
“Active session” -- “publish requested” --> “Finalizing”
“Finalizing” -- “capture filesystem delta” --> “Capture”
“Capture” -- “candidate changeset” --> “Reconcile”
“Reconcile” -- “all changes resolved” --> the boundary
The boundary “Active manifest replaced” leads to “Published”.
“Published” --> “Destroying” --> “Closed”.

PRECOMMIT BRANCHES
From “Capture” and “Reconcile”, draw dashed vermilion arrows labeled
“precommit failure or rejection” back to “Active session”.
Add a small note beside the return path:
“Explicit session retained for retry or destroy”.
From “Reconcile”, draw a neutral branch labeled “empty changeset” to “No-op”.
From “No-op”, draw a solid gray arrow to “Destroying”.
From “Active session”, draw a separate neutral path labeled
“destroy without publication” to “Destroying”, with a small tag “discard”.
Keep all of these paths before the commit boundary.

POST-COMMIT BRANCHES
From “Published”, add a dotted purple side annotation:
“Best-effort attribution”.
It must not gate the transition to “Destroying”.
From “Destroying”, draw:
- solid gray arrow labeled “cleanup succeeds” to “Closed”;
- dashed purple arrow labeled “cleanup fails” to “Finalize failed”.
Place a callout next to “Finalize failed”:
“Published but not closed”.
Draw no rollback arrow from “Finalize failed” to “Active session” or to the
old manifest.

IMPLICIT-SESSION CALLOUT
Outside the main state machine, add one small neutral callout:
“Implicit session: enters finalization after command ledger drains”.
Connect it with a dotted gray arrow to “Finalizing”.
Do not imply every tool call creates an implicit session.

CONSTRAINTS
Do not add process checkpointing, automatic semantic verification, automatic
task decomposition, transaction rollback, security guarantees, timeouts,
retry counts, performance metrics, or cross-platform claims.
Do not invent recovery transitions beyond the labels above.

OUTPUT
Return a high-resolution review PNG suitable for:
figures/concept/fig_lifecycle_state_machine.png
Also return a label-placement map and explicitly mark the result
“PROVISIONAL — verify after PW3”.
If exact text is unreliable, create a numbered state layout and preserve all
transition geometry for a deterministic label overlay.
```

## Exact label inventory

- Before data commit
- After data commit
- Active manifest replaced
- Active session
- Finalizing
- Capture
- Reconcile
- No-op
- Published
- Destroying
- Closed
- Finalize failed
- publish requested
- capture filesystem delta
- candidate changeset
- all changes resolved
- precommit failure or rejection
- Explicit session retained for retry or destroy
- empty changeset
- destroy without publication
- discard
- Best-effort attribution
- cleanup succeeds
- cleanup fails
- Published but not closed
- Implicit session: enters finalization after command ledger drains

## Post-generation acceptance

- Precommit return paths never cross the commit boundary.
- Only “Active manifest replaced” leads into “Published”.
- Cleanup failure ends at “Finalize failed” with no data rollback.
- No-op and discard are visually distinct from successful publication.
- The asset is visibly marked provisional in its delivery metadata, not as a
  large watermark inside the artwork.
