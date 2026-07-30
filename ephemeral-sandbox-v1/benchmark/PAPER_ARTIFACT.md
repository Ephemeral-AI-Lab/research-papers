# Paper-local benchmark artifact

This directory is a frozen, runnable snapshot of the benchmark implementation
used by the Ephemeral Sandbox paper.

## Provenance

- Upstream repository: `Ephemeral-AI-Lab/ephemeral-sandbox-test`
- Imported subtree: `benchmark/`
- Upstream commit: `d45618733c8bfe75466947fdb9c47bea67f74b78`
- Import date: 2026-07-30
- Import verification: all 171 upstream files matched by SHA-256 immediately
  after copying

Paper-local additions that are not present in the upstream benchmark subtree:

- `PAPER_ARTIFACT.md`
- `defaults/workspace-profiles/paper-100m.yml`

Paper-local modifications to the upstream snapshot:

- `backend/benchmark_lab/fixtures.py` raises the admitted maximum fixture depth
  from 64 to the product ceiling of 499 so that the depth-100 paper profile is
  valid.
- `backend/tests/unit/test_fixtures.py` verifies admission at depth 100, exact
  generated path depth, and rejection beyond the new limit.

All other files copied from the upstream snapshot remain unchanged.

The upstream test repository remains the engineering source of truth. This
copy is intentionally frozen so that paper results can be tied to an exact
benchmark implementation. If the snapshot is refreshed, replace the complete
upstream subtree, update the commit above, and rerun the benchmark; do not mix
results from different benchmark revisions in one table.

## Directory roles

When this copy is used, the three benchmark roots are:

- Test repository root: the parent paper directory
  `research-papers/ephemeral-sandbox-v1`
- Benchmark source root: this `benchmark` directory
- Product root: a separate checkout of `ephemeral-sandbox`
- Product binary directory: a directory beneath the product root containing
  the prebuilt release executables

Generated fixtures, run workspaces, raw observations, and reports are written
under `ephemeral-sandbox-v1/.benchmark-state/`. That directory is ignored by
Git and must not be treated as benchmark source.

## Install and validate on the Linux benchmark host

From `research-papers/ephemeral-sandbox-v1`:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "./benchmark[test]"

sandbox-benchmark validate \
  --test-repository-root "$PWD" \
  --product-root /absolute/path/to/ephemeral-sandbox \
  --product-bin-dir /absolute/path/to/ephemeral-sandbox/target/release \
  --plan quick-smoke
```

Validation checks the plan and the product catalog but does not establish
performance. Run the smoke campaign before a measured campaign:

```sh
sandbox-benchmark run \
  --test-repository-root "$PWD" \
  --product-root /absolute/path/to/ephemeral-sandbox \
  --product-bin-dir /absolute/path/to/ephemeral-sandbox/target/release \
  --plan quick-smoke
```

Pin the container image by digest in the measured preset before collecting
numbers intended for the paper.

## Paper base workspace

Use workspace profile `paper-100m` for the paper's depth-stress measurements.
It generates exactly 100 MiB (104,857,600 bytes) across 4,000 deterministic
files with a maximum directory depth of 100. The cached seed is copied into a
clean per-cell workspace before sandbox creation.
