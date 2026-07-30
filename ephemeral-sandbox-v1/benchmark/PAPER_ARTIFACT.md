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
- `presets/paper-env-smoke.yml`
- `presets/paper-good-pass.yml`

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

## Prepare and validate on the qualified Windows host

The selected host is native Windows x64. Docker Desktop supplies the Linux
AMD64 engine and the pinned Ubuntu sandbox image; Ubuntu is not the host. The
released native Windows gateway and manager/runtime/observability CLIs are the
only permitted product access path.

The benchmark requires Python 3.13 or newer for its own orchestration. Prepare
its virtual environment and dependencies off-clock. No package installation,
build, image pull, or source mutation may occur during a pilot or final
campaign.

The current `paper-env-smoke` and `paper-good-pass` files still select
`direct_client` and are therefore prohibited. After the `product_cli` cohort
and presets pass the EXP1 implementation and review gates, the Windows command
shape from `research-papers\ephemeral-sandbox-v1` is:

```powershell
$paper = 'C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1'
$product = 'C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox'
$productBin = "$product\target\windows-v0.1.4\bin"

Set-Location -LiteralPath $paper
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e '.\benchmark[test]'

& .\.venv\Scripts\sandbox-benchmark.exe validate `
  --test-repository-root $paper `
  --product-root $product `
  --product-bin-dir $productBin `
  --plan paper-env-smoke
```

Validation checks the plan and product catalog but does not establish
performance. A campaign command must not be issued until the preset expands to
`product_cli`, the exact released executables and image digest pass preflight,
and the phase gate in
[`../experiment_inventory.md`](../experiment_inventory.md) authorizes the run.

The paper presets pin the selected Linux AMD64 Ubuntu image by digest. Docker
Desktop must already contain and independently inspect that exact digest before
any pilot or final measurement begins.

## Paper base workspace

Use workspace profile `paper-100m` for the paper's depth-stress measurements.
It generates exactly 100 MiB (104,857,600 bytes) across 4,000 deterministic
files with a maximum directory depth of 100. The cached seed is copied into a
clean per-cell workspace before sandbox creation.
