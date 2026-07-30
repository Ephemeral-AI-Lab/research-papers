# Figure prompt: LayerStack and workspace-session architecture

## Figure contract

```yaml
figure_id: fig:system-architecture
filename: figures/concept/fig_system_architecture.png
figure_class: concept-method
role: overview
message: "One active LayerStack supplies leased read-only views to multiple private workspace sessions, and only accepted active-manifest replacement advances the shared head."
core_conclusion: "Shared history and session-private execution are separated until atomic data publication."
evidence_hierarchy:
  hero_evidence: "Shared LayerStack feeding two private overlays that converge through one publication boundary."
  supporting_evidence: "Holder/runner execution, lease pinning, rejection, and post-commit audit/cleanup."
layout: "Three horizontal semantic bands in a left-to-right architecture."
backend: hybrid
source: "C1/C2, D1--D8, Sections 3--5, and plan/terminology.md"
backup: "Deterministic SVG or LaTeX label overlay if generated text is unreliable."
caption_takeaway: "Sessions share leased lower history but keep writable state private; accepted data becomes public only when the active manifest is replaced."
evidence_status: illustrative-only
reviewer_risk: "Do not depict filesystem-enforced immutability, universal network isolation, a security boundary, or audit/cleanup inside atomic publication."
```

## Copy-paste prompt

```text
Create a publication-quality concept-method architecture diagram for an arXiv
systems paper titled “Ephemeral Sandbox.” The reader should understand one
idea immediately: one shared LayerStack provides leased read-only views to
multiple private workspace sessions, and only accepted active-manifest
replacement advances the shared active head.

STYLE
Use a flat 2D vector-inspired academic systems-diagram style: Classic Academic
precision combined with Modern Minimal spacing. White background, no gradients,
no shadows, no 3D, no isometric perspective, no clip art, no logos, no
watermarks, no fake terminal text. Use clean rounded rectangles, thin neutral
borders, generous whitespace, and a neutral sans-serif font. The final figure
will be printed approximately 6.5 inches wide, so all labels must remain
readable at that size. Landscape 16:9 canvas, at least 3200 x 1800 pixels,
300 DPI or higher.

SEMANTIC PALETTE
- Shared/durable state: navy #0072B2.
- Private/session state: sky blue #56B4E9.
- Capture and reconciliation: orange #E69F00.
- Accepted publication: green #009E73.
- Rejection/failure: vermilion #D55E00.
- Post-commit/non-atomic work: purple #CC79A7.
- Neutral control structure: gray #8C8C8C.
- Text: charcoal #222222.
Do not rely on color alone; pair color with exact labels and line styles.

LAYOUT
Create three clearly separated horizontal bands with a left-to-right reading
order. Do not add a large title inside the artwork.

TOP BAND — SHARED DURABLE STATE
Label the pale band “Shared durable state.”
At the left, draw a small box labeled exactly “Active manifest.”
It points to a horizontal ordered stack labeled exactly “LayerStack.”
Inside the stack show three flat layer slabs labeled, from highest precedence
to lowest: “Newest layer”, “Earlier layer”, and “Base”.
Add a small directional annotation “newest first”.
From the active manifest and layer stack, draw two navy lease connections
downward. Each connection has a small tag labeled exactly “Lease”.
The leases must visually pin a logical view; do not depict them as global locks.

MIDDLE BAND — PRIVATE SESSION STATE
Label the pale blue band “Private session state.”
Place two parallel session groups to show multiplicity:
“Workspace session A” and “Workspace session B”.
Inside each group, show:
1. a read-only lower stack labeled “Leased lowers”;
2. a distinct writable block labeled “Upper / work”;
3. the combined mounted view labeled “Private overlay”;
4. a small process box labeled “Namespace holder”;
5. one or two small process nodes labeled “Runner”.
Use solid blue arrows from each leased lower stack into its private overlay.
Use a separate blue writable connection from “Upper / work” into the same
overlay. Connect “Namespace holder” to “Runner” with a neutral control arrow.
Add one short annotation beneath the two sessions: “Shared lowers; unique
writable state”.
Do not draw virtual machines, security shields, locks, or claims of complete
isolation.

RIGHT-SIDE PUBLICATION PATH
From each private overlay, allow an orange path to converge into one box
labeled exactly “Capture”.
Then draw boxes in this exact order:
“Candidate changeset” → “Current-head reconciliation” → “Resolved changeset”.
Use orange for capture and reconciliation, then green for the resolved
changeset.
From reconciliation, draw one dashed vermilion branch labeled “Rejected” that
ends at a box labeled “Active manifest unchanged”.
From “Resolved changeset”, draw a solid green path through:
“Stage + sync” → “Promoted layer” → “Active manifest replacement”.
Make “Active manifest replacement” the strongest visual boundary, using a
green outlined box and a thin vertical marker labeled exactly
“Public data visibility”.
Draw a green arrow from the promoted layer into the top-band LayerStack,
showing that the accepted layer is prepended to shared history.

POST-COMMIT BOUNDARY
After “Active manifest replacement”, draw a visually separate pale region
labeled exactly “Outside atomic data publication”.
Inside it place two small boxes: “Audit attribution” and “Session cleanup”.
Connect them with purple dotted arrows from the manifest replacement.
They must appear downstream and outside the green publication boundary.

SESSIONLESS FILE-OPERATION CALLOUT
Add a small neutral inset in the bottom-left corner labeled exactly
“Sessionless file operations”.
Inside it show:
“read” → “Active LayerStack”
“write / edit” → “Direct head amendment”
Use dotted gray arrows and keep this inset visually separate from the workspace
sessions. This prevents the diagram from implying that every tool call creates
a session.

ARROW GRAMMAR
- Solid navy/blue: filesystem-view or private-state flow.
- Solid gray: process/control relationship.
- Solid green: accepted publication.
- Dashed vermilion: rejection.
- Dotted purple: post-commit work outside atomic publication.
- Dotted gray: separate sessionless paths.
Avoid crossing arrows.

EXACTNESS AND CONSTRAINTS
Use only the labels requested above. Do not add numbers, axes, performance
curves, speed symbols, security claims, semantic correctness claims, Git
terminology, cross-platform claims, or decorative infrastructure.
Do not label the system a transaction, VM, secure sandbox, or serializable
snapshot.

OUTPUT
Return a high-resolution PNG suitable for:
figures/concept/fig_system_architecture.png
Also return a short label-placement map. If exact text cannot be rendered
faithfully, generate a numbered text-light base composition and preserve the
same layout for a deterministic label overlay; never invent or misspell labels.
```

## Exact label inventory

- Shared durable state
- Active manifest
- LayerStack
- Newest layer
- Earlier layer
- Base
- newest first
- Lease
- Private session state
- Workspace session A
- Workspace session B
- Leased lowers
- Upper / work
- Private overlay
- Namespace holder
- Runner
- Shared lowers; unique writable state
- Capture
- Candidate changeset
- Current-head reconciliation
- Resolved changeset
- Rejected
- Active manifest unchanged
- Stage + sync
- Promoted layer
- Active manifest replacement
- Public data visibility
- Outside atomic data publication
- Audit attribution
- Session cleanup
- Sessionless file operations
- read
- Active LayerStack
- write / edit
- Direct head amendment

## Post-generation acceptance

- Shared and private bands are visually distinct.
- Both sessions share lower history but have separate upper/work state.
- Rejection leaves the active manifest unchanged.
- Public visibility is marked only at active-manifest replacement.
- Audit and cleanup are visibly outside atomic data publication.
- Sessionless file operations are not routed through an implicit session.
- No text is misspelled or smaller than final-paper readability permits.
