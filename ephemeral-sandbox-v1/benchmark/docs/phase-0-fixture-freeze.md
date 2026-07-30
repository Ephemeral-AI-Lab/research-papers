# Phase 0 fixture freeze

Status: complete (reader verification is deliberately assigned to Phase 2).

## Authority and revisions

- Product/source revision: `4077e9e4133a457b356e4e25da87c173f0641d2b`
- Target starting revision: `b52aa1e579451a789e9647c6376f87a05e284e99`
- Evidence production date: 2026-07-12
- Freeze date: 2026-07-13

## Frozen evidence

`tests/fixtures/golden/rust/quick-smoke-completed` is a complete Rust-produced Quick Smoke run: 8 cells, 48 trial batches, the standard `small` workspace profile, and `create_workspace`, `exec_command`, `file_read`, `file_write`, and `squash_layerstack`. It includes schema envelopes, event and observation journals, bounded evidence, summary, report, and JSON/CSV exports.

`quick-smoke-cancelled` and `quick-smoke-failed` retain top-level journals and artifacts for cancellation and infrastructure-failure behavior. `observations` preserves the oldest supported observation schemas without promotion or rewriting. The catalog fixture was emitted by the already-built `sandbox-catalog-export`; no build tool was invoked.

Compact vectors cover exact Type-7 quantiles, sample standard deviation, MAD, Tukey outliers, small-sample omissions, histogram/ECDF projection, deterministic bootstrap cases, compatible and blocked comparison responses, torn tails, and interior corruption.

## Sanitization

Only two mechanical substitutions were made:

- the evidence machine's test root became `/benchmark-fixture/test-repository`;
- loopback endpoint ports became `0`.

Schemas, run identifiers, measurements, ordering, terminal state, correctness results, and report statistics were not changed. Embedded hashes of diagnostic gateway log chunks may describe the original unsanitized diagnostic text; authoritative plan and definition hashes remain the historical values. Tests must treat this corpus as immutable read-only input.

## Commands and results

- Read the migration authority in full and inspected artifact, recovery, report, comparison, planning, and statistics contracts.
- Invoked the prebuilt `sandbox-catalog-export`: schema 1, three product domains, 29,042 bytes.
- Indexed 113 historical runs: 11 full Quick Smoke, plus command, file, workspace, and LayerStack slices.
- Frozen corpus: 87 files, 14,708,736 bytes after compact vector additions.
- JSON/NDJSON validation and redaction/path scans are recorded by the Phase 0 fixture tests added in Phase 1.

## Gaps and deviations

No migration-spec deviation. The frozen standard/preset representative is the full Quick Smoke preset itself, which uses the standard `small` workspace profile. Compatibility readers are not implemented in this freeze phase and remain explicitly unchecked until Phase 2.
