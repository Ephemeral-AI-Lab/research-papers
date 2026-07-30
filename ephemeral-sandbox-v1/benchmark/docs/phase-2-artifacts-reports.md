# Phase 2 artifacts, recovery, statistics, reports, and comparison

Status: complete.

## Files changed

- `backend/benchmark_lab/artifacts.py`: closed artifact registry, historical schema readers, observation v1/v2 in-memory promotion, durable journals, content-addressed bounded evidence, same-filesystem atomic staging, partial-tail quarantine, and opaque artifact downloads.
- `backend/benchmark_lab/recovery.py`: startup scanning, fatal read-only interior-corruption handling, manifest-plus-marker ownership proof, aggregated recovery health, and fail-safe interrupted-run finalization.
- `backend/benchmark_lab/statistics.py`: Type-7 statistics, sample standard deviation, MAD, Tukey flags, raw-point/histogram-ECDF projections, and deterministic SplitMix64 bootstrap intervals.
- `backend/benchmark_lab/reports.py`: strict historical run corpus validation, v4 summary projection, compatible JSON/CSV exports, atomic report-bundle persistence, and provenance normalization.
- `backend/benchmark_lab/comparison.py`: revision-2 historical reader and revision-3 comparison writer with phase deltas, compatibility gates, treatment declarations, deterministic intervals, and descriptive override.
- `backend/benchmark_lab/models.py`: strict event, report-v4, and summary-v4 wire contracts.
- `backend/tests/compatibility`, `backend/tests/integration`, and `backend/tests/unit`: frozen corpus, artifact boundary, recovery, report/export, comparison, and statistical coverage.

## Compatibility and safety results

The backend opens completed, cancelled, and failed Rust-produced runs without a product process. Observation schemas 1, 2, and 3 normalize to the same current in-memory representation; historical files are never rewritten. Existing report v4 remains field-compatible, CSV v3 regenerates byte-for-byte, and JSON/summary outputs regenerate semantically. Historical comparison derivation revision 2 remains readable; Python writes revision 3 because phase comparisons add an incompatible field.

Immutable artifacts are staged under `.benchmark-state/tmp`, flushed and fsynced, then atomically linked into place without overwrite. Snapshots use atomic replacement from the same filesystem. Downloads resolve only fixed IDs or opaque IDs discovered through the bounded-evidence directory grammar. Evidence size, JSON media type, filename/content digest, schema, symlink, and caller-supplied runtime-secret checks fail closed.

Recovery validates both journals before mutation. It quarantines only an incomplete final line, never interior corruption, and requires an exact marker for every `runs` or `runtime` directory that exists at the persisted crash transition; a directory not yet created or already removed is a valid absent resource. Cleanup failures or marker mismatches leave execution unavailable and the manifest nonterminal, and recovery never promotes a run to completed.

## Commands and results

- Focused comparison/report/artifact/statistics/guard suite: 24 passed in 26.40 seconds.
- Atomic artifact/download guard suite: 13 passed in 0.28 seconds.
- Recovery failure matrix after the injected-callback correction: 18 passed in 0.32 seconds.
- Report bundle, artifacts, recovery, and guard: 25 passed in 1.08 seconds.
- Complete offline backend suite from unrelated working directory `/tmp`: 41 passed in 27.22 seconds.
- Frozen corpus inventory: 87 files; deterministic inventory digest `93f21fa3e3f7a07c65634b1fa1102c0794ac91ef263b1eaa6647873460a830c7`.
- `git diff --check`: clean. Product repository status: clean.

The first recovery-vector draft accidentally ended its supposed partial record with a newline and used an invented event payload. The fixture was corrected to a genuine event-v1 envelope with no final newline before compatibility implementation. Removing that final byte required a one-byte `truncate` because a textual patch cannot encode a missing final newline; no source or product file was touched.

## Gaps and deviations

No migration-spec deviation. Phase 2 owns generic report derivation, persistence, exports, and compatibility. Operation-specific cell assembly is deliberately integrated one operation at a time in Phase 4, where setup, timing, verification, teardown, and observations become available; it will use this single report path rather than a second runner or report implementation.
