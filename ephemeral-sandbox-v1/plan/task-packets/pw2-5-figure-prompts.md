# PW2.5: Concept-Figure Prompt Package

## Bounded scope

- Create reusable prompt/spec sources for four concept-method figures:
  1. LayerStack and workspace-session architecture;
  2. workspace-to-publication sequence;
  3. session lifecycle state machine;
  4. current-head reconciliation decision flow.
- Define one shared visual style so the four assets form a coherent paper figure family.
- Update only figure planning/prompt sources and this workflow record.
- Do not generate final images, edit manuscript TeX, refresh the PDF attestation, run experiments, or modify source/benchmark artifacts.

## Evidence and terminology

- Architecture and execution: C1, D1--D3, Sections 3--4, and `plan/terminology.md`.
- Capture, reconciliation, and publication: C2, D4--D8, Section 5, and `plan/terminology.md`.
- Lifecycle: C4, D1, D6, D8, and D9; the prompt is provisional until PW3 completes Section 6.
- Generated concept figures are explanatory only. They are not correctness, performance, security, or cross-platform evidence.

## Files allowed to edit

- `figures/figure_plan.md`
- `figures/source/STYLE_GUIDE.md`
- `figures/source/fig_system_architecture_prompt.md`
- `figures/source/fig_publication_sequence_prompt.md`
- `figures/source/fig_lifecycle_state_machine_prompt.md`
- `figures/source/fig_reconciliation_decision_prompt.md`
- `plan/task-packets/pw2-5-figure-prompts.md`
- `plan/progress.md`

## Prompt requirements

Each figure source must contain:

- the figure contract: class, role, message, conclusion, evidence hierarchy, entities, relationships, layout, backend, source, caption takeaway, and reviewer risk;
- one self-contained copy-paste prompt;
- exact label inventory;
- forbidden visual claims and terminology;
- expected output dimensions and file name;
- a deterministic-label fallback when generated text is unreliable.

## Acceptance checks

1. All four prompt files and the shared style guide exist.
2. Every prompt uses canonical manuscript terminology.
3. No prompt requests fake numbers, axes, performance trends, security imagery, or an oversized transaction boundary.
4. Architecture and publication prompts visibly separate shared/private state and data commit/post-commit activity.
5. Lifecycle is marked provisional until PW3.
6. Markdown links resolve and edited files pass whitespace checks.

## Outcome

- Complete. One shared style guide and four self-contained prompt/spec files
  exist. Each prompt repeats its own style, palette, layout, exact labels,
  constraints, output contract, and acceptance checklist, so it can be sent
  independently to an image-generator agent.
- Validation passed: four-file existence and structure, shared/self-contained
  style checks, canonical-boundary review, 121 relative Markdown links,
  full-paper quality gate, and scoped Git whitespace check.
- Remaining boundary: no image asset has been generated or visually inspected.
  The lifecycle state-machine prompt remains provisional until PW3 completes
  Section 6.
