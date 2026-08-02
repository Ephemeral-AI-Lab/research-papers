# PW2.5: Concept-Figure Generation and Review

## Bounded scope

- Generate four concept-method PNG assets from the approved prompt package:
  - `figures/concept/fig_system_architecture.png`;
  - `figures/concept/fig_publication_sequence.png`;
  - `figures/concept/fig_lifecycle_state_machine.png`;
  - `figures/concept/fig_reconciliation_decision.png`.
- Delegate generation to non-overlapping subagents.
- Inspect every output for scientific boundaries, exact terminology, layout,
  label readability, and style consistency.
- Request targeted edits or redesigns when an output fails review.
- Update figure planning and review records only after selected assets exist.
- Do not edit manuscript TeX or treat the images as experimental evidence.

## Shared style

- Classic Academic precision with Modern Minimal spacing.
- Flat 2D, vector-inspired geometry on white.
- Consistent semantic palette and arrow grammar from
  `figures/source/STYLE_GUIDE.md`.
- No isometric art, 3D, gradients, marketing decoration, fake metrics,
  security imagery, or performance implications.

## Review gates

1. The intended message is readable without the manuscript paragraph.
2. Labels are exact, legible at final-paper scale, and not hallucinated.
3. Shared/private and precommit/post-commit boundaries are visually correct.
4. Active-manifest replacement is the data-visibility point wherever shown.
5. Rejection never becomes partial publication.
6. Audit and cleanup remain outside atomic data publication.
7. The four assets look like one visual family.
8. Lifecycle remains marked provisional until PW3.

## Delegation

- Architecture: `/root/architecture_figure`.
- Publication sequence: `/root/publication_sequence_figure`.
- Reconciliation flow: `/root/reconciliation_figure`.
- Lifecycle state machine: assigned when one concurrency slot becomes free.

The three delegated generation attempts were interrupted and did not supply
the selected assets. The author subsequently supplied four PNGs from
`C:\Users\yifan\Downloads`; generator/model/seed metadata was not available.
Their dimensions, hashes, provenance boundary, and review findings are recorded
in [`../../figures/concept-figure-review.md`](../../figures/concept-figure-review.md).

## Outcome

- Draft-generation outcome complete: all four expected PNG paths exist.
- Drafting-stage review complete with recorded disparities. The author directed
  that the images be integrated unchanged and that redesign, topology repair,
  resolution normalization, and style-family harmonization be deferred to PW7.
- This outcome does not declare the figures submission-final. PW3 later passed
  lifecycle/prose consistency with an explicit normal-path caption qualifier,
  integrated all four files unchanged, and inspected the compiled color and
  grayscale pages. Final visual acceptance remains a PW7 gate.
