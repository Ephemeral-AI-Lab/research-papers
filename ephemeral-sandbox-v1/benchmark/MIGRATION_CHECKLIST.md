# EphemeralOS benchmark migration checklist

Authority: `ephemeral-sandbox-docs/implementation-plan/benchmark_test/python-benchmark-migration-spec.md`

The source benchmark and product repository are read-only until the final, separately gated cutover. Every phase must run the zero-Rust/zero-Cargo/product-coupling guard.

## Phase 0 — freeze parity evidence

- [x] Record source and target revisions.
- [x] Freeze a successful full Quick Smoke preset using the standard `small` profile.
- [x] Freeze cancelled and infrastructure-failed terminal runs.
- [x] Freeze schema versions 1–3 of historical observations.
- [x] Freeze report, summary, JSON/CSV export, bounded evidence, and journals.
- [x] Freeze deterministic statistics, comparison, and recovery vectors.
- [x] Freeze product catalog schema 1 from the prebuilt exporter.
- [x] Sanitize machine paths and volatile loopback ports.
- [x] Verify every frozen fixture with the Python compatibility readers (Phase 2).

## Phase 1 — Python foundation and safety

- [x] Create the Python 3.13+ project and one CLI entry point.
- [x] Implement canonical repository roots and strict state ownership.
- [x] Implement fail-closed deletion and path-containment checks.
- [x] Add strict Pydantic public models.
- [x] Add and run the zero-Rust/zero-Cargo/product-coupling guard.

## Phase 2 — artifacts, recovery, statistics, and reports

- [x] Read all frozen historical artifacts without rewriting them.
- [x] Implement atomic JSON writes and durable NDJSON append journals.
- [x] Implement partial-tail quarantine and reject interior corruption.
- [x] Implement deterministic statistics and comparison parity.
- [x] Implement summary, report, JSON export, and CSV export parity.

## Phase 3 — catalog, gateway, transport, and cleanup

- [x] Consume `sandbox-catalog-export` schema 1 from a prebuilt executable.
- [x] Launch isolated gateways from prebuilt binaries only.
- [x] Time authenticated raw JSONL over `asyncio` sockets with `monotonic_ns`.
- [x] Track resources, redact secrets, and aggregate cleanup failures.
- [x] Cover fake process/socket failures before Docker.

## Phase 4 — planning and Quick Smoke operations

- [x] Implement deterministic plan expansion and campaign scheduling.
- [x] Implement each Quick Smoke operation individually.
- [x] Prove setup, timing, verification, teardown, artifacts, and reports per operation.
- [x] Prove one complete Quick Smoke slice.

## Phase 5 — FastAPI and web migration

- [x] Implement `/api/v1`, SSE replay/resume, cancellation, and artifact routes.
- [x] Preserve origin, nonce, JSON content-type, and path security.
- [x] Move React/TypeScript while preserving Vitest and fixture Playwright.
- [x] Replace every Rust/Cargo launcher assumption with Python/Uvicorn.

Gate evidence: 43 Vitest tests passed; 40 fixture Playwright tests passed; the
production build passed; the Python/Uvicorn small real-backend proof completed
LayerStack with all artifacts and zero teardown violations. Python manifests now
write schema v2 with explicit implementation provenance while readers and
recovery retain historical Rust schema v1.

## Phase 6 — parity, live proof, and gated cutover

- [x] Run offline parity, Vitest, fixture Playwright, and zero-Rust guard.
- [x] Run feature-by-feature live Docker proof and retain append-only evidence.
- [x] Run final Quick Smoke, cancellation, failure, recovery, SSE, and cleanup proof.
- [x] Commit and verify the external implementation.
- [x] Only then remove the product Cargo member and old benchmark tree.

Pre-cutover evidence: 131 offline pytest tests, 43 Vitest tests, and 40 fixture
Playwright tests passed; the production web build passed. Fake process/socket,
failure, cancellation, recovery, corrupt-journal, path-escape, redaction,
historical-artifact, and SSE contract coverage is included in those suites.
Feature-by-feature live Docker campaigns and a complete Quick Smoke slice passed
before the final proof.

The retained full real-backend proof is
`.benchmark-state/evidence/real-backend-full-2026-07-12T23-51-55-118Z`.
It passed seven browser-driven campaigns covering each family, sequential Run
All, exact SSE resume, cancellation, complete and cancelled artifacts, reports,
comparison, accessibility, and cleanup. Its proof ledger recorded an unchanged
source digest, identical baseline/final owned run and runtime entries, identical
Docker container/network/volume sets, zero violations, and 37/37 authenticated
mutations carrying both the same-origin header and mutation nonce.

Cutover evidence: external implementation commit
`5e8b023aba42d3b791442f39a82282e4df927b15` was clean and readable before
the product cutover. Product commit
`1ac36033e0e993b1e446c1db1e4ac803f02ac6fb` removed the Cargo member,
lockfile package, and old benchmark tree, and added a CI boundary check that
rejects their return without invoking Cargo or Rust tooling.
