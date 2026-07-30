# EXP0 task packet: focused performance protocol

**Status:** Documentation and configuration complete; final-host gates pending.

## Bounded objective

Create a runnable, phase-gated protocol package for a short practical
performance characterization of workspace readiness, `exec_command`, read,
write, and edit. Include acceptance tracking, expected real and simulated table
layouts, a fast prebuilt-only environment workflow, an executable preflight,
and an append-only experiment log.

## Authoritative inputs

- `lanes/experiments.md`, `PRD.md`, `paper_skeleton.md`
- `claim_evidence_map.md`, `complexity_and_evolution.md`
- Paper-local benchmark snapshot derived from
  `ephemeral-sandbox-test@d45618733c8bfe75466947fdb9c47bea67f74b78`
- Product baseline
  `ephemeral-sandbox@b22862550e0a7cb4fe61ce581831e9244cc492b5`
- User decisions: descriptive performance rather than competitive
  superiority; one environment; 100 MiB base; maximum depth 100; no
  verification column
- `ai-research-writing-skill` artifact, table, and evidence rules

## Outputs

- `experiment_inventory.md`
- `experiments/environment_setup.md`
- `experiments/expected_tables.md`
- `experiments/experiment_log.md`
- `experiments/scripts/verify_environment.sh`
- `benchmark/presets/paper-env-smoke.yml`
- `benchmark/presets/paper-good-pass.yml`
- Updated experiment README, paper README, progress, benchmark provenance, and
  paper state

## Acceptance checks

- [x] The protocol is explicitly scoped to descriptive RQ3 performance.
- [x] Environment verification is Gate 1 and precedes every sandbox run.
- [x] Measurement-host workflow consumes prebuilt binaries and a pre-pulled
  pinned image.
- [x] The fast preflight has a 60-second warm target and performs no build,
  install, or pull.
- [x] Workspace profile is exactly 4,000 files, 100 MiB, maximum depth 100.
- [x] Generator admits the product ceiling of 499 and rejects 500.
- [x] Four expected table schemas exist.
- [x] Simulated tables are visibly non-evidence and separated from real table
  templates.
- [x] The CLI table has per-operation rows and no verification/pass column.
- [x] Smoke and good-pass presets validate through the planner.
- [x] Shell preflight passes `bash -n`.
- [x] Experiment log records existing checks and unresolved gates without
  invented measurements.
- [ ] Final Ubuntu environment passes the preflight.
- [ ] Minimal live smoke passes.
- [ ] Instrumentation boundary decisions are resolved.
- [ ] Protocol is reviewed and locked before final measurement.

## Verification record

- `paper-env-smoke`: 2 cells, 2 trial batches, 2 operation requests.
- `paper-good-pass`: 18 cells, 1,836 trial batches, 5,508 operation requests.
- Focused depth tests: 2 passed under Python 3.13.
- Preflight shell syntax: passed under Ubuntu WSL `bash -n`.
- Live Docker campaign: not run; final host remains Gate 1.

## Scientific risks carried forward

- Current file-operation cells use operation-specific prepared fixtures rather
  than an explicitly selected `paper-100m` base.
- Initial sandbox creation/mount timing is not yet a first-class preserved
  operation metric.
- The 20-minute good-pass budget is a pilot acceptance target, not a verified
  runtime.
- Depth 100 is stress-shaped and must not be described as a typical code
  repository.
