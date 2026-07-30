# Experiment log

**Protocol:** [`../experiment_inventory.md`](../experiment_inventory.md)  
**Policy:** append-only; never rewrite a failed attempt into a successful one  
**Evidence status:** no paper-eligible measurements have been collected

## Logging rules

1. Add one entry for every preflight, smoke, pilot, final run, analysis run, or
   protocol amendment.
2. Use UTC timestamps.
3. Preserve failures, partial output, exclusions, and cleanup problems.
4. Never put credentials, gateway tokens, or other secrets in this file.
5. Exact numerical results remain in machine-readable artifacts; this log
   records their identifiers, disposition, and interpretation.
6. "Completed" means the stated acceptance gate passed, not merely that a
   process exited.

## Current phase status

| Phase | Status | Evidence |
|---|---|---|
| 0 - Reproducibility package | In progress | Spec, table schema, environment guide, log, scripts, presets |
| 1 - Final environment verification | Not started | Final Ubuntu host not selected/verified |
| 2 - Minimal live smoke | Not started | Blocked by Phase 1 |
| 3 - Instrumentation and pilot | Not started | Blocked by Phase 2 |
| 4 - Protocol lock and freeze | Not started | Blocked by Phase 3 |
| 5 - Good pass | Not started | Blocked by Phase 4 |
| 6 - Analysis and tables | Not started | No measured corpus |
| 7 - Paper handoff | Not started | No tables |

## Entries

### 2026-07-30 (time not recorded) - Paper-local benchmark snapshot

- **Entry ID:** `planning-benchmark-snapshot-001`
- **Phase:** 0
- **Kind:** reproducibility setup
- **Source:** `ephemeral-sandbox-test@d45618733c8bfe75466947fdb9c47bea67f74b78`
- **Action:** copied the complete `benchmark/` subtree into the paper project.
- **Verification:** 171 copied files; zero SHA-256 mismatches immediately after
  import.
- **Paper-local additions:** provenance document and paper workspace profile.
- **Disposition:** completed; not a measurement.

### 2026-07-30 (time not recorded) - Paper workspace profile

- **Entry ID:** `planning-workspace-profile-001`
- **Phase:** 0
- **Kind:** protocol setup
- **Profile:** `paper-100m`
- **Fixture:** 4,000 files, 104,857,600 logical bytes, depth range 1-100.
- **Depth ceiling:** aligned to the product ceiling of 499; 500 is rejected.
- **Seed:** `20260712`
- **Fixture identity:** `sha256:9484b132c8a35afd18bc37383759d0fe6d45dd4700b42a99336aed535e651cc7`
- **Verification:** two focused depth-bound tests passed under Python 3.13.
- **Known issue:** the complete upstream fixture test file is Linux-oriented
  and uses `sha256:` in cache directory names, which is not a valid Windows
  directory name. Final validation remains on Linux.
- **Disposition:** completed; not a measurement.

### 2026-07-30 (time not recorded) - Local environment readiness check

- **Entry ID:** `preflight-windows-local-001`
- **Phase:** 1 exploratory check
- **Host:** Windows development workstation, not the selected final host.
- **Docker client:** 29.0.1.
- **Docker server:** unavailable.
- **WSL state:** Docker Desktop and Ubuntu distributions stopped at the time of
  inspection.
- **Disposition:** failed and ineligible. This confirms that the workstation
  cannot supply final measurements in its current state.
- **Next action:** provision and verify the selected native Ubuntu host.

### 2026-07-30 (time not recorded) - Ubuntu image digest resolution

- **Entry ID:** `planning-image-pin-001`
- **Phase:** 0
- **Kind:** external artifact pin
- **Command:** `docker manifest inspect --verbose ubuntu:24.04`
- **Selected platform:** `linux/amd64`
- **Manifest digest:** `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
- **Disposition:** registry identity recorded. Local pull and inspection on the
  final host remain Gate 1 acceptance items.

### 2026-07-30 (time not recorded) - Focused protocol package

- **Entry ID:** `planning-protocol-v0.1-001`
- **Phase:** 0
- **Kind:** protocol draft
- **Scope:** practical startup and public operation performance, without
  competitive baselines.
- **Artifacts:** experiment specification, expected tables, environment setup,
  experiment log, preflight script, smoke preset, and good-pass preset.
- **Open decisions:** file-operation base-workspace boundary and explicit
  sandbox-create timing.
- **Disposition:** draft; requires review before protocol lock.

## Entry template

Copy this section for every new action.

```text
### YYYY-MM-DDTHH:MM:SSZ - Short title

- Entry ID:
- Phase:
- Kind: preflight | smoke | pilot | final-run | analysis | amendment
- Operator:
- Host identity:
- Product branch/commit/tag:
- Product dirty state:
- Benchmark commit/plan hash:
- Image reference/digest:
- Binary hashes:
- Workspace profile/fixture hash:
- Exact command:
- Start/end/elapsed:
- Run ID:
- Raw artifact path:
- Log path:
- Report path:
- Acceptance items checked:
- Failures/anomalies/exclusions:
- Cleanup result:
- Disposition: passed | failed | partial | invalidated
- Supported interpretation:
- Unsafe interpretation:
- Next action:
```

## Protocol amendment template

```text
### YYYY-MM-DDTHH:MM:SSZ - Protocol amendment vX.Y

- Reason:
- Decision made before or after viewing measured results:
- Files changed:
- Metrics/cells/rules affected:
- Prior runs invalidated:
- Required reruns:
- Reviewer/author approval:
```

An amendment made after viewing final results must be disclosed explicitly and
must not be used to selectively remove unfavorable cells.
