# Figure prompt: Workspace-to-publication sequence

## Figure contract

```yaml
figure_id: fig:publication-sequence
filename: figures/concept/fig_publication_sequence.png
figure_class: concept-method
role: method-detail
message: "A workspace delta remains private through capture and reconciliation; accepted data becomes public at active-manifest replacement, before best-effort attribution and cleanup."
core_conclusion: "The sequence has a precise data-commit boundary and separate precommit rejection and post-commit phases."
evidence_hierarchy:
  hero_evidence: "The highlighted active-manifest replacement line."
  supporting_evidence: "Lease/mount/execute/capture flow, whole-candidate rejection, and downstream audit/cleanup."
layout: "Five-lane sequence diagram with time flowing downward."
backend: hybrid
source: "C1/C2, D1--D8, Sections 4--5, and plan/terminology.md"
backup: "Deterministic labels and arrows over a generated background."
caption_takeaway: "Execution and capture stay private; only the accepted manifest transition exposes data, while attribution and cleanup occur afterward."
evidence_status: illustrative-only
reviewer_risk: "Do not make command response equal publication completion, include audit in the commit, or imply every file operation creates a session."
```

## Copy-paste prompt

```text
Create a publication-quality sequence diagram for an arXiv systems paper. The
figure must show how an Ephemeral Sandbox workspace moves from a leased private
execution view to one durable public head. The most important visual fact is
that public data visibility begins at active-manifest replacement; audit
attribution and cleanup occur afterward and are not part of atomic data
publication.

STYLE
Use a flat 2D vector-inspired Classic Academic × Modern Minimal style. White
background, no gradients, no shadows, no 3D, no isometric objects, no logos,
no watermarks, no cartoon agents, and no fake numeric data. Use thin neutral
lines, rounded message boxes, generous whitespace, and neutral sans-serif
text. Landscape 16:9 or 16:10, at least 3200 pixels wide, 300 DPI or higher.
The diagram must remain readable at approximately 6.5 inches wide.

PALETTE AND LINES
- Shared/durable LayerStack: navy #0072B2.
- Private workspace activity: sky blue #56B4E9.
- Planning/reconciliation: orange #E69F00.
- Accepted commit path: green #009E73.
- Rejection/failure: vermilion #D55E00 with dashed arrows.
- Post-commit work: purple #CC79A7 with dotted arrows.
- Neutral control: gray #8C8C8C.
- Text: charcoal #222222.
Do not rely on color alone.

SWIMLANES
Create five vertical swimlanes with these exact headers, left to right:
1. “Caller”
2. “Session service”
3. “Workspace / OverlayFS”
4. “LayerStack”
5. “Post-commit services”
Use subtle alternating lane backgrounds and a downward time direction.
Do not put a large title inside the figure.

SEQUENCE
Show the following numbered conceptual phases without fake timings:

1. Caller → Session service:
   message label “Create or admit session”.

2. Session service → LayerStack:
   message label “Acquire lease”.
   LayerStack returns “Manifest + ordered layers”.

3. Session service → Workspace / OverlayFS:
   message label “Mount leased lowers”.
   Inside the workspace lane show a compact blue state box:
   “Private upper / work”.

4. Caller → Session service:
   message label “Execute command(s)”.
   Session service → Workspace / OverlayFS:
   message label “Holder + runner”.
   Add a small note in the session lane:
   “Implicit: auto-finalize after ledger drains”
   and a second note:
   “Explicit: multiple calls until publish or destroy”.
   Do not equate returning an initial command response with publication.

5. Workspace / OverlayFS → Session service:
   message label “Command ledger drained”.

6. Session service → Workspace / OverlayFS:
   message label “Capture upper tree”.
   Workspace returns an orange object labeled “Candidate changeset”.
   Add a small note: “filesystem delta, not process state”.

7. Session service → LayerStack:
   message label “Plan against leased base”.
   Add a compact orange note in the LayerStack lane:
   “route + protect + fingerprint”.

8. Inside LayerStack, show a narrow orange critical region labeled:
   “Writer lock: reread active manifest”.
   Then show “Current-head reconciliation”.
   From reconciliation draw two branches:
   - dashed vermilion branch left, label “Rejected”, ending at
     “Active manifest unchanged”;
   - solid green branch downward, label “All changes resolved”.
   Add a tiny no-op branch labeled “No-op” that also leaves the current head
   selected.

9. On the accepted branch, inside the LayerStack lane show these exact boxes
   in order:
   “Stage changes”
   → “Sync staging tree”
   → “Promote layer”
   → “Write layer digest”
   → “Recheck manifest”
   → “Replace active manifest”.

COMMIT BOUNDARY
Across all lanes, draw a strong horizontal green line immediately after
“Replace active manifest”. Label the line exactly:
“Atomic data publication — public visibility begins”
This is the hero element of the figure.
Everything above it is private or precommit. Everything below it is
post-commit. Do not place audit or cleanup above this line.

POST-COMMIT PHASE
Below the green line:
- LayerStack → Post-commit services:
  dotted purple message “Best-effort audit attribution”.
- Session service → Workspace / OverlayFS:
  purple/gray message “Destroy workspace”.
- Session service → LayerStack:
  purple/gray message “Release lease”.
Group these steps in a pale region labeled exactly:
“Outside atomic data publication”.

FAILURE SEMANTICS
Use dashed vermilion only for precommit rejection or failure.
Use a separate purple dashed annotation below the commit line:
“Cleanup failure does not roll back visible data”.
Do not draw a rollback arrow from post-commit cleanup to the active manifest.

CONSTRAINTS
Use only the requested terminology. Do not add performance numbers, duration
bars, throughput arrows, security shields, Git commits, database transactions,
semantic merge claims, universal network isolation, or cross-platform icons.
Do not imply that sessionless file read/write/edit follows this exact session
sequence; add a small neutral footnote:
“Sequence shown for workspace-session publication.”

OUTPUT
Return a high-resolution PNG suitable for:
figures/concept/fig_publication_sequence.png
Also return a label-placement map. If exact text is unreliable, preserve the
five-lane layout using numbered message markers and provide a deterministic
overlay plan instead of hallucinating text.
```

## Exact label inventory

- Caller
- Session service
- Workspace / OverlayFS
- LayerStack
- Post-commit services
- Create or admit session
- Acquire lease
- Manifest + ordered layers
- Mount leased lowers
- Private upper / work
- Execute command(s)
- Holder + runner
- Implicit: auto-finalize after ledger drains
- Explicit: multiple calls until publish or destroy
- Command ledger drained
- Capture upper tree
- Candidate changeset
- filesystem delta, not process state
- Plan against leased base
- route + protect + fingerprint
- Writer lock: reread active manifest
- Current-head reconciliation
- Rejected
- Active manifest unchanged
- All changes resolved
- No-op
- Stage changes
- Sync staging tree
- Promote layer
- Write layer digest
- Recheck manifest
- Replace active manifest
- Atomic data publication — public visibility begins
- Best-effort audit attribution
- Destroy workspace
- Release lease
- Outside atomic data publication
- Cleanup failure does not roll back visible data
- Sequence shown for workspace-session publication.

## Post-generation acceptance

- Time and arrows read unambiguously from top to bottom.
- The green commit boundary follows manifest replacement exactly.
- Rejection ends with the active manifest unchanged.
- Audit, destruction, and lease release are below the commit boundary.
- No post-commit rollback arrow exists.
- The caption can explain the sequence without relying on color alone.
