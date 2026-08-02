# Figure prompt: Current-head reconciliation decision flow

## Figure contract

```yaml
figure_id: fig:reconciliation-decision
filename: figures/concept/fig_reconciliation_decision.png
figure_class: concept-method
role: method-detail
message: "Publication resolves every planned change through explicit route, fingerprint, structure, and merge gates, or rejects the whole candidate."
core_conclusion: "Only eligible exact-file text divergence is merged; ignored-route behavior and whole-candidate rejection remain explicit."
evidence_hierarchy:
  hero_evidence: "Source-route fingerprint divergence leading to a narrowly eligible merge gate."
  supporting_evidence: "Protected-path/base checks, ignored-route branch, opaque-directory checks, and whole-candidate commit/reject outcomes."
layout: "Top-down decision flow with source and ignored branches that rejoin at whole-candidate resolution."
backend: hybrid
source: "C2, D4--D6, Section 5, and plan/terminology.md"
backup: "Deterministic labels over a generated flowchart layout."
caption_takeaway: "A candidate is committed only after every change resolves; required binary, oversized, structural, or conflicting merges reject rather than partially publish."
evidence_status: illustrative-only
reviewer_risk: "Do not imply all binary/oversized writes reject: the restriction applies only when divergence requires a merge."
```

## Copy-paste prompt

```text
Create a publication-quality decision-flow diagram for the Current-head
reconciliation method in an arXiv systems paper about Ephemeral Sandbox. The
reader should understand that every planned change must resolve, only a narrow
class of concurrent exact-file text divergence can merge, and one unresolved
change rejects the whole candidate changeset.

STYLE
Use a flat 2D vector-inspired Classic Academic × Modern Minimal flowchart.
White background, no gradients, no shadows, no 3D, no isometric objects, no
logos, no watermarks, no fake code, and no fake numeric results. Use rounded
rectangles for actions, diamonds for decisions, thin neutral borders, short
exact labels, and orthogonal arrows with minimal crossings. Use a neutral
sans-serif font. Preferred canvas 4:3 at least 2800 x 2100 pixels, or a roomy
16:9 landscape if needed, 300 DPI or higher. Text must remain readable at
approximately 6.5 inches wide.

PALETTE
- Input/shared state: navy #0072B2.
- Planning and decisions: orange #E69F00.
- Accepted/resolved path: green #009E73.
- Rejection: vermilion #D55E00 with dashed arrows.
- Ignored-route branch: neutral gray #8C8C8C.
- Notes/boundaries: purple #CC79A7.
- Text: charcoal #222222.
Use words and line styles in addition to color.

TOP INPUT
At the top center, draw a navy rounded rectangle:
“Candidate changeset”
Then an orange action:
“Validate leased base”
Then a decision diamond:
“Base identity valid?”
The “no” branch goes by dashed vermilion arrow to:
“Reject whole candidate”
with a small result tag:
“Active manifest unchanged”.

PROTECTION AND PLANNING
The “yes” branch continues to:
“Protected path or drop?”
For an explicit-session figure, the “yes” branch goes to
“Reject whole candidate”.
Add a compact purple footnote:
“Unsupported-special-file drop policy differs by entry point”.
The “no” branch goes to:
“Plan route”.
Beside planning, add a small orange callout:
“Opaque directory: protected descendant, mixed route, or expansion bound
violation → reject”.

ROUTE SPLIT
From “Plan route”, split into two clearly labeled branches:

LEFT NEUTRAL BRANCH — “Ignored route”
Action box:
“Carry wholesale change”
Small note:
“No source fingerprint merge”.

RIGHT ORANGE BRANCH — “Source route”
Action box:
“Fingerprint leased base”
Then show a critical-region label:
“Writer lock: reread active manifest”.
Then a decision:
“Current fingerprint matches base?”
The “yes” branch goes to:
“Accept planned change”.
Add a small compatibility note:
“Compatible directory create may pass”.

SOURCE DIVERGENCE
The “no” branch from fingerprint comparison goes to:
“Structural descendant changed?”
The “yes” branch goes to “Reject whole candidate”.
The “no” branch continues to:
“Exact regular-file write?”
The “no” branch goes to “Reject whole candidate”.
The “yes” branch continues to:
“Merge inputs eligible?”
Place a concise note next to this diamond:
“base + current + command:
UTF-8, no NUL, each ≤ 8 MiB”.
The “no” branch goes to “Reject whole candidate”.
The “yes” branch continues to:
“Three-way line merge clean?”
The “no” branch goes to “Reject whole candidate”.
The “yes” branch goes to:
“Resolved merged write”.

IMPORTANT QUALIFIER
Add a clearly visible purple note near the merge path:
“Binary or oversized writes are not categorically rejected.
They reject only when concurrent divergence requires this merge.”
Add another short note:
“Clean merge ≠ semantic correctness”.

WHOLE-CANDIDATE JOIN
Join these green/neutral success nodes:
- “Carry wholesale change”
- “Accept planned change”
- “Resolved merged write”
into one action:
“Record resolved change”.
Then draw a decision:
“Every planned change resolved?”
The “no” branch goes to “Reject whole candidate”.
The “yes” branch goes to:
“Resolved changeset”.
From there:
- if empty, branch to “No-op; current head remains”;
- if nonempty, branch to “Stage and commit whole changeset”.
End the accepted branch at:
“Active manifest replacement”.

VISUAL EMPHASIS
Make “Reject whole candidate” one shared terminal node reached by all dashed
vermilion rejection paths. Do not draw partial-commit arrows.
Make “Active manifest replacement” the accepted green terminal node.
The decision tree must communicate all-or-none data handling, not a full
database transaction.

CONSTRAINTS
Do not add performance claims, runtime graphs, security imagery, Git merge
terminology, arbitrary binary merge, semantic verification, automatic tests,
partial publication, or rollback after active-manifest replacement.
Do not simplify the qualifier into “binary files reject” or “files above 8 MiB
reject”.

OUTPUT
Return a high-resolution PNG suitable for:
figures/concept/fig_reconciliation_decision.png
Also return a label-placement map. If exact text cannot be guaranteed, produce
a numbered-node base with the same branch topology for a deterministic text
overlay; do not paraphrase the technical labels.
```

## Exact label inventory

- Candidate changeset
- Validate leased base
- Base identity valid?
- Reject whole candidate
- Active manifest unchanged
- Protected path or drop?
- Unsupported-special-file drop policy differs by entry point
- Plan route
- Opaque directory: protected descendant, mixed route, or expansion bound violation → reject
- Ignored route
- Carry wholesale change
- No source fingerprint merge
- Source route
- Fingerprint leased base
- Writer lock: reread active manifest
- Current fingerprint matches base?
- Accept planned change
- Compatible directory create may pass
- Structural descendant changed?
- Exact regular-file write?
- Merge inputs eligible?
- base + current + command: UTF-8, no NUL, each ≤ 8 MiB
- Three-way line merge clean?
- Resolved merged write
- Binary or oversized writes are not categorically rejected. They reject only when concurrent divergence requires this merge.
- Clean merge ≠ semantic correctness
- Record resolved change
- Every planned change resolved?
- Resolved changeset
- No-op; current head remains
- Stage and commit whole changeset
- Active manifest replacement

## Post-generation acceptance

- Source and ignored routes are distinct.
- All rejection paths converge on one whole-candidate rejection terminal.
- Merge is available only after exact-file and eligibility gates.
- The binary/oversized qualifier is readable and unambiguous.
- No partial publication path exists.
- Accepted visibility ends at active-manifest replacement.
