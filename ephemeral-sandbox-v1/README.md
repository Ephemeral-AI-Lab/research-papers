# Ephemeral Sandbox v1

Design paper for the v1 implementation of [ephemeral-sandbox](https://github.com/Ephemeral-AI-Lab/Ephemeral-AI-Lab).

## Project management

- [PRD](PRD.md) — evidence-gated requirements and submission criteria
- [Progress tracker](progress.md) — current milestones, parallel work lanes, evidence gates, and blockers
- [Paper and work skeleton](paper_skeleton.md) — section plan, research questions, figures/tables, work packages, and dependencies
- [Paper-writing lane](lanes/paper-writing.md) — source-grounded drafting order, evidence contract, and completion gates
- [Experiment lane](lanes/experiments.md) — protocol lock, pilots, freeze, final runs, analysis, and manuscript handoff
- [Focused performance protocol](experiment_inventory.md) — phase gates,
  acceptance tracker, workload, metrics, and stopping rules
- [Environment setup](experiments/environment_setup.md) — prebuilt staging,
  first-step verification, smoke, and good-pass commands
- [Expected tables](experiments/expected_tables.md) — final schemas and
  clearly labeled simulated previews
- [Experiment log](experiments/experiment_log.md) — append-only attempts,
  failures, amendments, and dispositions

## Evidence and story documents

- [Paper story](paper_story.md) — title, thesis, abstracts, introduction opening, contributions, and claim boundaries
- [Project inventory](project_inventory.md) — source, test, documentation, experiment, and environment evidence
- [Claim–evidence map](claim_evidence_map.md) — intended claims mapped to source, tests, measurements, or limitations
- [Complexity and evolution](complexity_and_evolution.md) — source-derived time/space cost model, scaling risks, limitations, and LayerStack 2.0 targets
- [CLI contract matrix](cli_contract_matrix.md) — source-derived management, runtime, and observability interfaces
- [Related-work audit](references/related_work.md) — verified metadata, citation safety, differentiation, and novelty risks

## Folder structure

```text
ephemeral-sandbox-v1/
├── README.md, PRD.md, progress.md, NEXT_AGENT_PROMPT.md
├── paper_skeleton.md
├── paper_story.md, project_inventory.md
├── claim_evidence_map.md, complexity_and_evolution.md, cli_contract_matrix.md
├── lanes/                                # paper-writing and experiment charters
├── main.tex, references.bib              # created when manuscript drafting begins
├── sections/                             # LaTeX section files
├── references/                           # related-work and citation-verification records
├── figures/                              # concept sources and generated/result assets
├── experiments/                          # protocols, immutable runs, and analysis
├── ARTIFACTS.md
└── paper.pdf                             # generated only after evidence gates pass
```

The required evidence documents remain at the paper-folder root so the PRD, progress tracker, and handoff links stay stable. Large or generated assets belong in the dedicated subdirectories.

Status: baseline discovery and paper-story work are complete; protocol lock, frozen evidence collection, and LaTeX drafting are next.
