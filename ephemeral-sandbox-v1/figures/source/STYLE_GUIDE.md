# Ephemeral Sandbox concept-figure style guide

## Preferred style

Use a flat, vector-inspired academic systems-diagram style that combines
**Classic Academic** precision with **Modern Minimal** spacing. The diagrams
should look like polished architecture figures, not product marketing art.

Why this style fits the paper:

- precise boundaries matter more than visual spectacle;
- the figures must remain readable at the manuscript's approximately
  6.5-inch text width;
- flat geometry is easier to verify against source and terminology;
- restrained color avoids implying performance, security, or maturity that
  the paper has not measured;
- the same visual grammar can cover architecture, sequence, state, and
  decision diagrams.

Avoid isometric servers, 3D stacks, glossy gradients, shadows, glassmorphism,
cartoon robots, brains, clouds, shields, locks, speed lines, dashboards, fake
terminal text, and decorative infrastructure icons.

## Canvas and output

- Full-width figure for a 10 pt, single-column `article` manuscript.
- Preferred landscape canvas: 16:9, at least 3200 x 1800 pixels.
- Decision flow may use 4:3, at least 2800 x 2100 pixels.
- Raster output: PNG, 300 DPI or higher.
- Preserve generous outer margins and at least 3% spacing between groups.
- Do not place the paper caption or a large title inside the artwork.
- Keep text equivalent to at least 8 pt when the figure is rendered at
  6.5 inches wide.

## Typography and geometry

- Neutral sans serif: Inter, Helvetica, Arial, or a close equivalent.
- Sentence case, not all caps.
- Short labels, normally one to four words.
- Charcoal text `#222222`.
- White background `#FFFFFF`; optional group bands `#F8FAFC`.
- Thin neutral borders `#6B7280`, consistent 1.5--2 px visual weight.
- Rounded rectangles with a small, consistent corner radius.
- Use alignment, whitespace, and bands before using icons.
- If icons are necessary, use only simple monochrome geometric glyphs.

## Semantic palette

Use color together with labels, border styles, or shapes so the figure remains
interpretable in grayscale.

| Meaning | Color | Usage |
|---|---|---|
| Shared/durable state | Navy `#0072B2` | Active manifest, LayerStack, promoted layer |
| Private/session state | Sky blue `#56B4E9` | Private overlay, upper/work, session |
| Planning/reconciliation | Orange `#E69F00` | Capture plan, fingerprint, merge |
| Accepted publication | Green `#009E73` | Resolved changeset, commit path |
| Rejection/failure | Vermilion `#D55E00` | Dashed rejection and failure paths |
| Post-commit/non-atomic work | Purple `#CC79A7` | Audit attribution and cleanup boundary |
| Neutral/control | Gray `#8C8C8C` | Control arrows, inactive structure |

Do not use green and red as the only distinction. Pair them with the words
“accepted” and “rejected,” and use solid versus dashed lines.

## Arrow grammar

- Solid navy/blue arrow: data or filesystem-view flow.
- Solid gray arrow: control flow or state transition.
- Solid green arrow: accepted publication path.
- Dashed vermilion arrow: rejection, retry, or failure.
- Dotted gray arrow: optional or semantically separate path.
- Purple dotted or dashed arrow: post-commit attribution/cleanup.
- Avoid crossing arrows; route connections orthogonally when possible.

## Terminology rules

Use exact canonical terms:

- LayerStack
- active manifest
- active head
- lease
- workspace session
- private overlay
- implicit session
- explicit session
- capture
- candidate changeset
- current-head reconciliation
- rejection
- atomic data publication

Never label the mechanism:

- transaction;
- serializable snapshot;
- VM;
- secure sandbox;
- semantic merge;
- Git commit;
- universal network isolation;
- cross-platform;
- faster, scalable, efficient, or higher throughput.

## Generated-text fallback

Exact text is part of the scientific content. If the image generator cannot
render every required label faithfully:

1. generate the same composition with numbered nodes and no prose;
2. return a label-placement map;
3. add exact labels later with a deterministic SVG, PDF, or LaTeX overlay;
4. never accept misspelled or substituted terminology.

## Family consistency

All four figures should reuse:

- the same palette and semantic meanings;
- the same border radius and line weight;
- the same typography;
- the same arrow grammar;
- the same visual representation of the active manifest, LayerStack, private
  overlay, rejection, and post-commit boundary.
