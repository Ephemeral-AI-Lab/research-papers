# Phase 1 Python foundation and safety

Status: complete.

## Files changed

- `pyproject.toml`, `README.md`: Python 3.13 project, declared runtime/test dependencies, and one `sandbox-benchmark` entry point.
- `backend/benchmark_lab/models.py`: strict Pydantic v2 marker, schema, run-state, and manifest-core contracts.
- `backend/benchmark_lab/paths.py`: three explicit canonical roots, disjoint repository checks, derived source/state roots, exact state marker, and state-role validation.
- `backend/benchmark_lab/safety.py`: create-only owned markers, active ledger/adoption, path containment, symlink/device checks, and fail-closed deletion.
- `backend/tests/unit` and `backend/tests/contract`: path, ownership, strict-model, and source-policy coverage.

## Commands and results

- Zero-native/tooling/product-coupling guard: 3 passed.
- Focused Phase 1 pytest: 12 passed in 0.42 seconds.
- Python module CLI help: exposed exactly `serve`, `validate`, `run`, `compare`, `recover`, and `cleanup` with shared explicit roots.
- Native source/manifest filesystem scan: zero files.

Tests use Python 3.13 in an isolated external environment. No product executable or container was launched. The product repository remained unchanged.

## Gaps and deviations

No spec deviation. Subcommand behavior is intentionally not wired until its owning phase; the shared parser and root validation are present. Public models are split progressively as later artifact/API contracts are implemented, rather than creating empty modules.
