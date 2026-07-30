# Concept-figure provenance and drafting-stage review

Review date: 2026-07-30.

## Provenance boundary

The four PNGs were supplied by the author from
`C:\Users\yifan\Downloads` and moved into `figures/concept/` with filenames
matching the approved prompt/spec sources. The external generator, model,
seed, source session, and label-placement maps were not supplied. The prompt
files under `figures/source/` are the available regeneration specifications;
they do not prove that the supplied PNGs were generated exactly from those
prompts.

The author directed that the four files be used unchanged in the drafting-stage
manuscript. Visual redesign, resolution normalization, topology repair, and
style-family harmonization are deferred to PW7. These assets are explanatory
concept diagrams and are not experimental evidence.

## File inventory

| Asset | Dimensions and metadata | Bytes | SHA-256 |
|---|---:|---:|---|
| `concept/fig_system_architecture.png` | 1536 x 1024, 96 x 96 dpi | 1,356,038 | `bef02bc0fc10e475dce7c75647e1efcf964e9f40ca46985055ae7442a2f7467a` |
| `concept/fig_publication_sequence.png` | 1672 x 941, 96 x 96 dpi | 1,367,977 | `08bb7881f356946553d1f7e34704f4b7d6791e8f939897db21f1226111efec82` |
| `concept/fig_lifecycle_state_machine.png` | 3200 x 1800, 300 x 300 dpi | 212,531 | `dd0c2f719c788072d45e52519e2b15850457caa97eaa0e5743ec9fce4f37464f` |
| `concept/fig_reconciliation_decision.png` | 1024 x 1536, 96 x 96 dpi | 1,389,136 | `b0445f2d0c93439270d649d3c51e2d002722b8b445cdd5e84c561b52d46feb2d` |

## Drafting-stage QA

### System architecture

- Strengths: names the shared LayerStack, two private sessions, capture and
  reconciliation, the active-manifest visibility boundary, post-commit work,
  and sessionless file paths.
- Deferred disparities: the two private-session publication paths do not
  converge as cleanly as the prompt requires; one orange route visually
  approaches the resolved-changeset area; the green return path does not
  clearly originate at the promoted layer; the shared-state band overlaps the
  publication column; resolution and aspect ratio differ from the prompt.
- Current gate: accepted unchanged for drafting; topology and resolution review
  required at PW7.

### Publication sequence

- Strengths: separates private execution, precommit planning, accepted
  publication, and post-commit services; the active-manifest boundary and
  cleanup non-rollback note are prominent.
- Deferred disparities: the supplied composition uses horizontal phase groups
  and per-step owner tags rather than the requested five vertical swimlanes;
  some requested caller/session labels are absent or reorganized; icon density
  and raster resolution differ from the shared specification.
- Current gate: accepted unchanged for drafting; layout, label inventory, and
  resolution review required at PW7.

### Lifecycle state machine

- Strengths: distinguishes precommit and post-commit regions, explicit retry,
  no-op, discard, published, destroying, closed, and finalize-failed outcomes.
  The file satisfies the requested 3200 x 1800 and 300 dpi delivery target.
- Lifecycle qualifier: the diagram is a normal-path abstraction. It omits
  holder-exit recovery artifacts, shutdown convergence, and lease-aware
  remount outcomes. The shared `Destroying` node does not encode whether its
  predecessor was publication, no-op, or discard; therefore
  `Published but not closed` must be read only for the committed-publication
  path.
- PW3 revalidation: pass as a qualified normal-path abstraction. Section 6
  separately describes the omitted holder-exit recovery artifact, shutdown
  convergence, and lease-aware remount outcomes, and the caption prevents the
  shared `Destroying` node from extending `Published but not closed` to the
  no-op or discard paths. Submission-final topology review remains PW7.

### Reconciliation decision flow

- Strengths: exposes base validation, protected-drop handling, source and
  ignored routes, fingerprint checks, narrow text-merge eligibility,
  whole-candidate rejection, no-op, and accepted publication.
- Deferred disparities: the portrait 1024 x 1536 raster differs from the
  requested wide high-resolution layout; lower rejection routing is visually
  close to the active-manifest replacement terminal; the no-op and commit
  terminals require careful caption interpretation; style differs from the
  more icon-heavy architecture and sequence figures.
- Current gate: accepted unchanged for drafting; terminal routing, layout,
  resolution, and family-style review required at PW7.

## Gate summary

| Gate | Drafting-stage result | Final requirement |
|---|---|---|
| File existence and hashes | Pass | Recheck after any PW7 replacement |
| Prompt/spec source present | Pass | Preserve with final assets |
| Concept-only evidence boundary | Pass | Keep captions non-empirical |
| Label/topology review | Completed with recorded disparities | Repair or explicitly accept at PW7 |
| Final-width and raster review | Exceptions recorded | Reassess at PW7 |
| Style-family consistency | Deferred by author | Resolve or explicitly waive at PW7 |
| Lifecycle/prose consistency | Pass with an explicit normal-path qualifier | Repeat after any PW7 replacement |
| Manuscript placement and captions | Pass in the final PW3 render | Repeat after any PW7 replacement |

## PW7 final-phase queue

No PNG is to be changed during PW3. The final paper-polish phase must revisit:

1. the architecture figure's route convergence, promoted-layer return edge,
   band overlap, aspect ratio, and raster resolution;
2. the publication figure's requested swimlane layout, missing or reorganized
   labels, icon density, and raster resolution;
3. the lifecycle figure's omitted exceptional branches and shared
   `Destroying`-node ambiguity;
4. the reconciliation figure's portrait layout, terminal-edge separation,
   no-op/commit interpretation, and raster resolution; and
5. cross-figure typography, palette, stroke, icon, spacing, final-size,
   grayscale, and family-style consistency.

PW7 may repair these items or explicitly accept an item with a recorded
submission-stage waiver. The current author waiver permits drafting-stage use
only.

## PW3 compiled-PDF review

- The successful recorded build preserves the four asset hashes above.
- The 14-page US-letter PDF places the architecture on page 3, publication
  sequence on page 6, reconciliation flow on page 8 immediately before
  Section 6, and lifecycle state machine on page 10 immediately before
  Section 7.
- Figure and table boundaries have no clipping, overlap, missing glyphs,
  broken labels, or unresolved references. The two Section 7 tables remain
  after their introducing prose.
- All four figures are readable at their compiled color size for drafting.
  The grayscale render preserves the core topology and primary labels, but
  pale dashed annotations and category cues lose contrast, especially the
  lifecycle figure's pink post-commit/failure notes. That contrast weakness,
  together with final typography and style-family consistency, remains PW7
  debt rather than a PW3 image edit.
- The final PDF-wide color and grayscale contact sheets show consistent
  margins, page numbering, and section transitions. The sparse final
  References page is expected while `references.bib` remains comment-only.
