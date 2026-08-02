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
| 1 - Final environment verification | Passed | Native Windows/Docker Desktop strict preflight accepted |
| 2 - Minimal live smoke | Passed | Native Windows product-CLI 2/2 qualification accepted |
| 3 - Instrumentation and pilot | Out of scope | Environment-only task |
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

### 2026-07-30 (time not recorded) - Preset and script validation

- **Entry ID:** `planning-config-validation-001`
- **Phase:** 0
- **Kind:** deterministic configuration check
- **Python:** 3.13 paper-local virtual environment.
- **Smoke preset:** runnable; 2 cells, 2 trial batches, 2 operation requests.
- **Good-pass preset:** runnable; 18 cells, 1,836 trial batches, 5,508
  operation requests.
- **Shell preflight:** `bash -n` passed under the Ubuntu WSL shell.
- **Caveat:** planner validation used a synthetic runtime-environment identity,
  so its provisional plan hashes are not final-host plan hashes.
- **Disposition:** passed as configuration validation; no sandbox was launched
  and no performance evidence was produced.

### 2026-07-30 (time not recorded) - Current workstation Gate 1 audit

- **Entry ID:** `preflight-workstation-audit-002`
- **Phase:** 1 exploratory check
- **Kind:** preflight audit
- **Gate score:** 5 of 15 passed (about 33%); environment not accepted.
- **Passed:** CPU count, memory capacity, cgroup v2, clean product `main`, and
  deterministic workspace profile.
- **Partial:** Linux x86-64 exists through WSL 2, but it is not the selected
  native host.
- **Failed:** Ubuntu version is 26.04 rather than 24.04; paper/product paths
  are WSL `9p` rather than ext4; Docker server and pinned local image are
  unavailable; gateway/catalog binaries and both Git archives are missing;
  Linux-side Python is 3.14 rather than the required 3.13.
- **Disposition:** failed and ineligible for measurements.
- **Interpretation:** benchmark configuration readiness does not establish
  measurement-host readiness.

### 2026-07-30 (time not recorded) - Docker Desktop capability audit

- **Entry ID:** `preflight-docker-capability-003`
- **Phase:** 1 exploratory check
- **Kind:** preflight audit
- **Host/runtime:** Windows workstation; Docker Desktop 29.0.1; Linux AMD64
  engine; kernel `6.6.87.2-microsoft-standard-WSL2`; `overlayfs` storage
  driver; cgroup v2.
- **Capacity reported by engine:** 48 CPUs and 67,414,814,720 bytes of memory.
- **Image:** exact pinned
  `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
  pulled and inspected as `linux/amd64`.
- **Resource-control probe:** passed; disposable container observed
  `memory.max=536870912`, `pids.max=256`, and
  `cpu.max="100000 100000"`.
- **OverlayFS probe:** passed on a separate `tmpfs` backing store, including
  mount, read, copy-up/write, and unmount. A direct nested mount on the
  container's existing overlay root failed, so this probe does not validate the
  product's complete storage path.
- **Bind-mount probe:** passed container write followed by host read.
- **Prebuilt artifact audit:** Linux daemon present with SHA-256
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`;
  release gateway, catalog exporter, and both fixed Git archives missing.
- **Updated strict Gate 1 score:** 7 of 15 passed (about 47%).
- **Disposition:** partial; Docker substrate accepted for development checks,
  but the workstation is ineligible for paper measurements and the live product
  smoke is blocked by the incomplete prebuilt bundle.
- **Supported interpretation:** the selected image, resource controls, nested
  OverlayFS capability on a suitable backing store, and bind mounts can work on
  this machine.
- **Unsafe interpretation:** end-to-end benchmark readiness or performance.
- **Next action:** stage the prebuilt Linux AMD64 bundle on the selected native
  Ubuntu 24.04/ext4 host, then run `verify_environment.sh` and
  `paper-env-smoke`.

### 2026-07-30 (time not recorded) - Product installation-guide execution

- **Entry ID:** `preflight-product-guide-004`
- **Phase:** 1 exploratory check
- **Kind:** preflight
- **Host:** Windows workstation with Docker Desktop 29.0.1 and Ubuntu 26.04
  under WSL 2.
- **Product branch/commit:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Actions:** followed the product's Windows source-build and smoke guide;
  separately built the two required Linux release binaries in WSL ext4
  storage.
- **Windows product smoke:** passed image listing, sandbox creation,
  `exec_command`, snapshot, and destruction.
- **Linux bundle SHA-256:** gateway
  `f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf`;
  catalog exporter
  `c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba`;
  daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Catalog:** schema version 1, three domains, 37,216 bytes, SHA-256
  `5d270c1ac87bad74319f202b127404b5cfd363b185362ceedaece437c88bfef7`.
- **Disposition:** passed for product capability and staging; not a final-host
  preflight and not performance evidence.
- **Next action:** run the benchmark's minimal live smoke with the staged Linux
  bundle.

### 2026-07-30 (time not recorded) - Protocol amendment v0.2

- **Entry ID:** `amendment-current-product-contract-001`
- **Reason:** current product installation/package scripts and runtime source
  no longer use fixed Git toolchain archives; the imported benchmark contract
  predated the current product catalog, response schemas, and daemon profile.
- **Decision timing:** before any pilot or paper-eligible measurements.
- **Files changed:** benchmark gateway preflight, catalog/product/observability
  models, resource sampling, daemon defaults, focused tests, environment
  preflight, product-boundary documentation, and protocol inventory.
- **Changes:** removed the obsolete Git-archive prerequisite; accepted current
  float catalog arguments and strict current product response fields; updated
  resource sampling for explicitly partial initial cgroup snapshots; replaced
  the obsolete daemon thread setting with current standard-profile fields.
- **Verification:** 30 focused unit, contract, and integration tests pass.
- **Prior runs invalidated:** none; no paper-eligible run exists.
- **Required reruns:** environment smoke, five-sample pilot, and good pass.
- **Disposition:** accepted as a pre-measurement compatibility amendment.

### 2026-07-30T01:19:10Z - End-to-end benchmark environment smoke

- **Entry ID:** `smoke-wsl-ext4-005`
- **Phase:** 2 exploratory check
- **Kind:** smoke
- **Host identity:** Windows workstation, Docker Desktop Linux AMD64 engine,
  Ubuntu 26.04 WSL 2 control environment, isolated WSL ext4 execution
  snapshots.
- **Product branch/commit:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Benchmark plan/hash:** `paper-env-smoke`;
  `sha256:de517817323c2017b1daa7029dd3403f40f4ec24394c08a7f8c37b88f7afe13e`.
- **Environment fingerprint:**
  `sha256:de2011d4dcc196ae6b86f28dcd20aa1db5bf0f3b3a4972ad18867384c6aec12b`.
- **Python:** CPython 3.14 in the isolated WSL virtual environment.
- **Run ID:** `019fb09a-9d36-7686-bb51-ab73803daac6`.
- **Start/end/elapsed:** `2026-07-30T01:19:10.773459Z` /
  `2026-07-30T01:19:23.171695Z` / 12.398236 seconds.
- **Result:** completed; correctness passed; 2 of 2 trial batches; two issued
  operation requests; zero failures; zero warnings; report ready.
- **Raw artifact path:**
  `/root/.cache/ephemeral-sandbox-paper/live-smoke-20260730i/test-root/.benchmark-state/results/019fb09a-9d36-7686-bb51-ab73803daac6`.
- **Cleanup:** benchmark-owned smoke resources cleaned; an unrelated
  pre-existing sandbox was intentionally left untouched.
- **Disposition:** passed as an exploratory development/pilot smoke. Final-host
  Gate 2 remains open because Gate 1 has not passed on native Ubuntu 24.04.
- **Supported interpretation:** the documented build/staging path and current
  benchmark-product integration can complete create, execute, observe, and
  cleanup on this computer.
- **Unsafe interpretation:** paper-grade performance, native-host readiness, or
  comparison with another sandbox.
- **Next action:** review the Phase 3 measurement boundaries, then reproduce
  the same preflight and smoke on the selected native Ubuntu 24.04 host.

### 2026-07-30 (time not recorded) - Post-amendment good-pass validation

- **Entry ID:** `planning-good-pass-validation-002`
- **Phase:** 0
- **Kind:** preflight
- **Plan/hash:** `paper-good-pass`;
  `sha256:878e4a68a138d71650a92d381428f71e9e53e0671104a851eadd97c411baeab4`.
- **Result:** runnable; 18 cells, 1,836 trial batches, 5,508 issued operation
  requests, zero planner warnings.
- **Focused regression:** 30 tests passed in 0.46 seconds.
- **Shell verification:** `verify_environment.sh` passed `bash -n`.
- **Disposition:** passed as configuration validation only; no good-pass
  operation was executed and no performance evidence was produced.

### 2026-07-30 (time not recorded) - Protocol amendment v0.3

- **Entry ID:** `amendment-final-environment-specificity-001`
- **Reason:** the environment choice and handoff boundary needed one
  operationally exact interpretation.
- **Decision timing:** before pilot or paper-eligible measurements.
- **Selected environment:** logical host `eos-benchmark-ubuntu24`; native
  Ubuntu Server 24.04 x86-64; Docker Engine 29.0.1; ext4; CPython 3.13; product
  at `/srv/eos-benchmark/product`; paper at `/srv/eos-benchmark/paper`.
- **Product baseline:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Image:** pinned Linux AMD64 Ubuntu 24.04 manifest already recorded by this
  protocol.
- **Decision:** current WSL/Docker Desktop is GO for development smoke and a
  diagnostic pilot, but NO-GO for `paper-good-pass` or paper-table numbers.
- **Prior runs invalidated:** none; the successful smoke remains exploratory.
- **Required reruns:** strict preflight and `paper-env-smoke` on
  `eos-benchmark-ubuntu24`, followed by the Phase 3 pilot.
- **Disposition:** accepted as a pre-measurement specificity amendment.

### 2026-07-30T01:47:01Z - Final-host reachability discovery

- **Entry ID:** `preflight-final-host-discovery-006`
- **Phase:** 1
- **Kind:** preflight
- **Operator:** Codex environment-qualification handoff
- **Host identity:** Windows development workstation; not the selected final
  host.
- **Exact commands/checks:** workspace reference search; Windows hosts-file
  lookup; SSH config/effective-target and known-hosts lookup; DNS resolution
  for `eos-benchmark-ubuntu24`, `.local`, and the active `ctc` suffix; ICMP
  lookup; local virtualization inventory; WSL inventory; Docker context
  inventory; Multipass instance inventory.
- **Attempts:** two broad read-only repository/discovery commands timed out
  before useful output and were repeated as bounded checks.
- **Result:** no hosts-file, SSH, known-hosts, DNS, Docker-context, Hyper-V, or
  Multipass route exists for `eos-benchmark-ubuntu24`. The only Multipass
  instance is `ephemeral-sandbox-2204` on Ubuntu 22.04 and is ineligible. WSL
  Ubuntu and Docker Desktop are running but remain explicitly ineligible.
- **Disposition:** failed because the selected external host is unreachable;
  no system state changed.
- **Supported interpretation:** the final host cannot be qualified from this
  machine until it is provisioned and exposed through a reachable SSH route.
- **Unsafe interpretation:** that no suitable host exists outside locally
  discoverable configuration.
- **Next action:** provision the documented native Ubuntu 24.04 host and make
  `eos-benchmark-ubuntu24` SSH-reachable from this workstation.

### 2026-07-30T01:47:01Z - Canonical Linux bundle audit

- **Entry ID:** `planning-canonical-bundle-audit-003`
- **Phase:** 1 staging
- **Kind:** preflight
- **Product branch/commit:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Canonical layout:** gateway and catalog exporter now exist under
  `target/release`; the daemon exists under `dist`.
- **Binary verification:** all three files are executable x86-64 ELF under
  WSL. SHA-256 values are gateway
  `f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf`,
  catalog exporter
  `c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba`,
  and daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Product dirty state:** clean; `target/` remains ignored.
- **Disposition:** passed for off-clock staging readiness; not a final-host
  preflight.
- **Next action:** transfer this exact bundle to the selected host.

### 2026-07-30T02:06:11Z - Final-host handoff automation validation

- **Entry ID:** `planning-final-host-handoff-validation-004`
- **Phase:** 1 staging
- **Kind:** preflight
- **Operator:** Codex environment-qualification handoff
- **Host identity:** Windows development workstation with WSL used only as an
  ineligible negative-control Linux parser/runtime; not the selected final
  host.
- **Product branch/commit/tag:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`; annotated tag `v0.1.4`
  resolves to that commit.
- **Checks:** PowerShell parsing; `bash -n` for all three Linux scripts;
  deliberate execution of the strict verifier on WSL; bundle-manifest
  size/hash verification; `git bundle verify` and bundled `main` ref
  verification; archive enumeration; archive exclusion checks; archived shell
  parsing; and SHA-256 verification of all three canonical Linux ELF payloads.
- **Negative-control result:** the strict verifier passed Linux and x86-64,
  then failed closed because the logical hostname was not
  `eos-benchmark-ubuntu24`. It did not reach or run the benchmark.
- **Attempts/anomalies:** direct PowerShell script execution was blocked by the
  workstation execution policy; the documented command now uses
  `-ExecutionPolicy Bypass`. One combined archive-check command and one
  negative-control output-capture command had local shell-quoting errors and
  were repeated as bounded checks. A temporary clone-check command was rejected
  before execution by local destructive-action policy; complete-history bundle
  verification and exact ref enumeration passed instead. Three earlier generated
  bundles were superseded after documentation and Windows long-path handling
  were hardened, then removed; they are reproducible with the recorded bundle
  command.
- **Final raw artifact path:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\ephemeral-sandbox-v1-20260730-ready-v2`.
- **Final archive SHA-256:** product Git bundle
  `cbb267a93c0575934b5f0571e057fadbc04ce93e340dbd874f26664eaf5e531a`;
  product artifacts
  `570bbac95bd828fea88d7ce6dfcd03d3f86769126943a4c5e54b25395dff2f21`;
  paper snapshot
  `724ca7e0c5a25880f2045502074d9c12d32ddb6623d583d48c2aec33c276d1b9`.
- **Archived payload SHA-256:** gateway
  `f1f8420bfa6ea6370d90fbf8428c432fe6f1031b0cb7cc7d32ac543dc8be2faf`;
  catalog exporter
  `c841597bab53612a2f424088264a0fce383b54ded480050d99fbed1c529ac8ba`;
  daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Failures/exclusions:** CPython 3.13 and the native-host runtime could not be
  exercised locally; WSL remains excluded. No benchmark run or measurement was
  performed.
- **Disposition:** passed for reproducible transfer readiness; strict final-host
  Gate 1 and Gate 2 remain unrun.
- **Next action:** provision the documented native host and make
  `eos-benchmark-ubuntu24` SSH-reachable from this workstation.

### 2026-07-30T02:39:00Z - v0.1.4 product-CLI artifact staging

- **Entry ID:** `planning-v014-cli-artifacts-005`
- **Phase:** 1 staging
- **Kind:** preflight
- **Product branch/commit/tag:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`; annotated release `v0.1.4`.
- **Release source:** public `v0.1.4` Linux AMD64 archive.
- **Release archive SHA-256:**
  `308563ad38bc7a9c5000acd54251db872e2e6a58bf70846d14760fef2b0d713c`.
- **Staged product CLI SHA-256:** manager
  `0be4f0c26f8f50b76b175d04cfeec61529a605bcda9ffcd6782a09096ba2983f`;
  runtime
  `e9ac5f6c7a5f9c07a3de166b320e7d6065fa9480a7f18d6d59114337d15e28e7`;
  observability
  `6b2dae2369344cbb3960a76f6ccdfa869a7aa9b7a7a255f8a634f4a52d5cfdb5`.
- **Validation:** all three are executable Linux x86-64 ELF files in ignored
  `target/release`; product Git remains clean.
- **Attempt anomaly:** the first release-metadata query requested unsupported
  `isLatest` JSON output and failed; the bounded retry used supported fields.
  One hash loop used the wrong daemon location and one inline WSL loop was
  shell-mangled; both were rerun with explicit paths. No product source changed.
- **Disposition:** passed for transfer staging; not a final-host gate.

### 2026-07-30T02:42:00Z - Protocol amendment v0.4: product-CLI environment gate

- **Entry ID:** `amendment-cli-only-environment-gate-001`
- **Reason:** the imported `paper-env-smoke` invokes `direct_client`, while the
  required public-product boundary is the released manager, runtime, and
  observability CLIs.
- **Decision timing:** before any native-host qualification or performance
  measurement.
- **Change:** the environment smoke now runs two independent sandbox
  lifecycles. Each lifecycle uses ten validated product-CLI calls covering
  image listing, create, execute, write/read/edit/read, snapshot, destroy, and
  post-destroy listing.
- **Cleanup rule:** product CLI performs sandbox destruction. The harness then
  removes only shared-base volumes carrying its unique gateway-instance label
  and requires both a clean initial baseline and clean final state.
- **Prior runs invalidated:** WSL run
  `019fb09a-9d36-7686-bb51-ab73803daac6` remains historical diagnostic
  evidence but is invalid for Gate 2 because it used `direct_client`.
- **Performance boundary:** no performance preset is authorized; the imported
  planner still lacks a product-CLI subprocess cohort.
- **Disposition:** accepted as a pre-qualification environment amendment.

### 2026-07-30T02:49:42Z - Product-CLI smoke automation diagnostics

- **Entry ID:** `smoke-cli-automation-diagnostic-006`
- **Phase:** 2 diagnostic
- **Kind:** smoke
- **Host identity:** Windows workstation, Docker Desktop Linux AMD64 engine,
  Ubuntu 26.04 WSL 2 control environment; ineligible as the final host.
- **Image:** `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`.
- **Attempts:**
  1. The first inline PowerShell/WSL launcher was shell-mangled and failed
     before the smoke script received an artifact directory.
  2. The next attempt failed before gateway startup because the script
     incorrectly rejected a symlinked Python interpreter. The check was
     corrected while keeping non-symlink enforcement for product artifacts.
  3. A one-lifecycle run passed its CLI correctness checks, but its claimed 2/2
     accounting was rejected as unsupported.
  4. A true two-lifecycle run passed 20 CLI calls, but inspection showed two
     shared-base cache volumes owned by that diagnostic gateway. The run was
     rejected for the no-leak gate.
  5. The final implementation added exact-owner volume cleanup and passed two
     independent lifecycles.
- **Additional command anomalies:** one PowerShell glob was invalid for `rg`;
  one Docker volume-inspection loop and the first exact-label cleanup command
  were quoting-mangled. Each failed without deletion and was repeated with
  explicit JSON inspection.
- **Superseded diagnostic cleanup:** one cache volume for gateway instance
  `cli-env-smoke-20260730T024942Z-16705` and two for
  `cli-env-smoke-20260730T025229Z-17455` were removed after exact label
  verification. Older unrelated EOS resources were left untouched.
- **Final diagnostic result:** `product_cli`; 2/2 completed batches; two
  distinct sandboxes; 20 validated product-CLI calls; correctness pass; zero
  failures; zero warnings; empty CLI stderr; six seconds; zero containers and
  zero volumes remaining for gateway instance
  `cli-env-smoke-20260730T025443Z-18897`.
- **Final raw artifact:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\eos-cli-env-diagnostic-cleanup-20260730T120003Z.tar.gz`.
- **Final artifact SHA-256:**
  `9d4c16f059dbe24f61cea470715f39afc41673b6261dc5252595adaaccb4acee`.
- **Disposition:** passed as automation diagnostic only; Gate 1 and Gate 2
  remain open because WSL is ineligible.
- **Unsafe interpretation:** native-host qualification, performance evidence,
  or a paper-table result.

### 2026-07-30T02:55:00Z - CLI final-host verifier negative control

- **Entry ID:** `preflight-cli-final-host-negative-control-007`
- **Phase:** 1
- **Kind:** preflight
- **Host identity:** Ubuntu 26.04 WSL 2; deliberately ineligible.
- **Exact command:** strict `verify_environment.sh` with canonical product
  artifact paths and pinned image.
- **Result:** Linux and x86-64 checks passed, then the verifier failed closed
  at the exact logical-hostname check with exit code 1. It did not start a
  gateway or sandbox.
- **Log:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\verify-environment-wsl-negative-control-20260730.txt`.
- **Disposition:** passed as a negative control; native-host preflight remains
  unrun.

### 2026-07-30T03:00:00Z - Six-artifact transfer-bundle validation

- **Entry ID:** `planning-cli-transfer-bundle-validation-006`
- **Phase:** 1 staging
- **Kind:** preflight
- **Bundle attempt:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\ephemeral-sandbox-v1-cli-final`.
- **Archive SHA-256:** product Git bundle
  `fc5879964c7e54203c52d19dc3a54ae69f76722597bb0870e25d319afc990459`;
  product artifacts
  `0b0d386c2a38618163ab0028c446cdc25ef601dee1904ad0b5777595f3d7eddb`;
  paper snapshot
  `4389e2c9929462880d0722456bb515b3f1c67f2207ebe61eff2beb33c671270e`.
- **Validation:** manifest archive hashes matched; `git bundle verify` reported
  complete history and exact `main` ref
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`; the six extracted artifacts
  matched their pinned hashes; archived Bash and PowerShell scripts parsed;
  the 310-entry paper archive excluded `.venv`, `.benchmark-state`,
  `experiments/runs`, and `__pycache__`.
- **Attempt anomaly:** an initial combined validator was rejected before
  execution because it contained recursive temporary-directory cleanup. The
  validator was rerun without deletion, and the extracted audit directory was
  retained at
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\bundle-validation-cli-final`.
- **Disposition:** validation passed, but this bundle is superseded solely so
  the append-only record of its validation is included in the final paper
  snapshot.
- **Final target:** regenerate as
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\ephemeral-sandbox-v1-cli-final-v2`.
  Its external `bundle-manifest.json` is the authoritative archive-hash record;
  the bundle is not paper or performance evidence.

### 2026-07-30T03:05:00Z - Protocol amendment v0.5: Windows host correction

- **Entry ID:** `amendment-windows-docker-host-001`
- **Reason:** user clarification established that the host is native Windows
  with Docker Desktop; Ubuntu 24.04 is the sandbox image, not the host OS.
- **Decision timing:** before accepting a final environment result.
- **Superseded contract:** native Ubuntu Server 24.04 host,
  `eos-benchmark-ubuntu24`, ext4 host paths, CPython 3.13 qualification
  dependency, SSH exposure, and Linux transfer bundle.
- **Corrected contract:** native Windows x64 host `DESKTOP-OLP1ADS`; Docker
  Desktop 29.0.1 Linux AMD64 engine with `overlayfs` and cgroup v2; native
  Windows gateway and product CLIs; released Linux daemon inside containers;
  pinned Ubuntu sandbox image.
- **Prior runs invalidated:** Linux/WSL runs remain diagnostics but cannot
  establish the corrected native Windows CLI boundary.
- **Required rerun:** strict native Windows preflight plus two independent
  product-CLI sandbox lifecycles.
- **Disposition:** accepted before the final Windows qualification.

### 2026-07-30T03:06:00Z - Official Windows v0.1.4 package staging

- **Entry ID:** `planning-v014-windows-package-007`
- **Phase:** 1 staging
- **Kind:** preflight
- **Release archive:** `ephemeral-sandbox-windows-amd64.zip`.
- **Archive SHA-256:**
  `9f2327578c186897578f0d502893d894aed52be27306f43f75afa3205eba9fdb`.
- **Staged path:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4`.
- **Artifact hashes:** gateway
  `3a96bedcfa9857bd3881155d758ec2d969f6265456ec3b2878eb6dbb26dc9368`;
  manager CLI
  `b43ec520edc2f436adc8aa7e8b2b50680bb9021883fe23d79a85b17afd2e10fe`;
  runtime CLI
  `df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4`;
  observability CLI
  `0e0471e52750805570876a6244868764c44e166ec653627b9ebd490176e2fcbe`;
  config
  `0f0efd15e5111851054e0f7c1ce0f3eaebb3b3047c1b9e2322544036f5daf5db`;
  daemon
  `2da4395cd835e5325bc3e55b9c2f3b67565ea7c698fce5e086167ec4a2092a39`.
- **Validation:** four native binaries are x64 PE; daemon is x86-64 ELF;
  package is under ignored `target/`; product remains clean `main`.
- **Attempt anomaly:** the first GitHub release metadata request ended with a
  transient GraphQL EOF. A bounded retry succeeded before download.
- **Disposition:** passed.

### 2026-07-30T03:10:00Z - Native Windows qualifier development attempts

- **Entry ID:** `smoke-windows-docker-attempts-008`
- **Phase:** 1/2
- **Kind:** preflight and smoke
- **Host:** native Windows x64 `DESKTOP-OLP1ADS`, build 26200.
- **Docker:** Docker Desktop client/server 29.0.1; Linux AMD64,
  `overlayfs`, cgroup v2.
- **Attempts:**
  1. `qualification-windows-docker-20260730-final` passed the host/package/
     Docker/image checks, then strict-mode cleanup hit a scalar `.Count` bug.
     No result was accepted.
  2. `...-final-2` passed the same preflight, then the native gateway rejected
     PowerShell's BOM-bearing generated YAML; the expected startup connection
     refusal also terminated instead of retrying. No sandbox was created.
  3. `...-final-3` used BOM-less YAML and reached a ready native gateway. The
     container daemon correctly rejected Windows host paths in its in-container
     config. The gateway and daemon configs were separated.
  4. `...-final-4` created a ready sandbox, but strict validation rejected the
     returned `\\?\` Windows path form before recording the active sandbox ID.
     The known sandbox was subsequently destroyed through a restarted gateway
     and `sandbox-manager-cli.exe`; its uniquely labeled shared-base volume was
     then removed, leaving zero resources for that gateway instance.
  5. `...-final-5` passed create, execute, write, and read. Windows command-line
     parsing stripped the inner quotes from the `file_edit` JSON argument; the
     active sandbox was destroyed by the product CLI and exact-owner cleanup
     ended at zero resources.
- **Disposition:** all attempts preserved; none accepted as the final
  qualification.
- **Performance boundary:** no benchmark or performance experiment ran.

### 2026-07-30T03:16:21Z - Native Windows Docker Desktop qualification

- **Entry ID:** `qualification-windows-docker-final-009`
- **Phase:** 1 and 2
- **Kind:** preflight and smoke
- **Host:** native Windows x64 `DESKTOP-OLP1ADS`, build 26200; 48 logical
  CPUs; 137,438,953,472 bytes physical memory; qualified paths on NTFS.
- **Product:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`; official `v0.1.4` Windows
  package and hashes recorded above.
- **Docker/image:** Docker Desktop 29.0.1, Linux AMD64, `overlayfs`, cgroup v2;
  exact pinned Ubuntu 24.04 image present.
- **Client cohort:** native Windows `product_cli`.
- **Result:** completed; correctness pass; 2/2 independent batches; 20
  validated CLI calls; zero failures; zero warnings; empty CLI stderr.
- **Sandbox IDs:** `eos-edab92fa-dbbc-4ec1-b0ac-1a8e35cfdb8c` and
  `eos-2311f6bb-328f-4ef7-bc5f-f1b30db6a5b5`.
- **Cleanup:** product CLI destroyed both sandboxes; global EOS-owned baseline
  unchanged; zero containers and zero volumes remained for gateway instance
  `cli-env-windows-20260730T031621Z-34036`.
- **Elapsed:** ten seconds, environment-gate observation only.
- **Artifact directory:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6`.
- **Archive:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6.zip`.
- **Archive SHA-256:**
  `eea981665b031846677046d4c211e71ad144f8a32507c09058923241d4d0f7f9`.
- **Disposition:** passed; the corrected Windows plus Docker Desktop
  environment is qualified.
- **Unsafe interpretation:** a performance result or paper-table number.

### 2026-07-30T03:20:48Z - Windows qualification record validation

- **Entry ID:** `analysis-windows-qualification-validation-010`
- **Phase:** 1 and 2
- **Kind:** analysis
- **Checks:** PowerShell parser; paper-state and qualification-summary JSON;
  strict summary acceptance; exact gateway-owner Docker resource query; archive
  checksum; product branch/commit/dirty state; scoped Git whitespace check.
- **Attempt anomaly:** the first whitespace check found two trailing spaces in
  the rewritten environment status header. They were removed and the check was
  repeated.
- **Result:** all checks passed; product remains clean `main`; accepted gateway
  owner has zero containers and zero volumes; archive SHA-256 remains
  `eea981665b031846677046d4c211e71ad144f8a32507c09058923241d4d0f7f9`.
- **Disposition:** passed; no additional environment action is required.

### 2026-07-30 (time not recorded) - Canonical sandbox workspace base

- **Entry ID:** `planning-windows-workspace-base-008`
- **Phase:** environment staging
- **Kind:** preflight
- **Path:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\workspace-base\ephemeral-sandbox-v0.1.4`.
- **Source:** local clean product checkout.
- **Branch/commit/tag:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`; `v0.1.4` resolves to the same
  commit.
- **Generated-state exclusion:** no `target` directory exists in the clone.
- **Attempt anomaly:** Git emitted non-fatal Windows filename/attribute
  warnings for historical report paths containing long or Windows-incompatible
  names. Clone exit code, branch, commit, tag resolution, and Git status all
  passed.
- **Decision:** this source-only clone is the canonical
  `--workspace-bind-root` for repository-backed sandbox creation. The build
  checkout, paper repository, and parent lab directory are not workspace bases.
- **Qualification distinction:** the accepted environment gate continues to
  use its own tiny isolated fixtures; it does not claim that the full base
  repository was an input to the qualification smoke.
- **Disposition:** passed for explicit workspace-base staging; no performance
  experiment ran.

### 2026-07-30T03:39:00Z - EXP1 CLI performance campaign specification

- **Entry ID:** `planning-exp1-cli-campaign-spec-011`
- **Phase:** 0 and planning for 3--7
- **Kind:** amendment
- **Reason:** the user requested corrected experiment documentation and a
  complete execution specification for the next agent.
- **Decision timing:** all decisions were made before viewing performance
  measurements; no performance preset or pilot was run.
- **Environment decision:** retain the already qualified native Windows x64
  host with Docker Desktop's Linux AMD64 cgroup-v2 engine and pinned Ubuntu
  image. Do not restore superseded native-Ubuntu-host requirements.
- **Client decision:** every paper sandbox operation must use the released
  native Windows manager, runtime, or observability CLI through the canonical
  `product_cli` cohort. `direct_client` and `cli_e2e` are prohibited.
- **Timing decision:** primary latency is end-to-end native CLI subprocess
  latency from process creation through validated process exit, including
  process launch and CLI-to-gateway transport.
- **Workspace decision:** command, lifecycle, read, write, and edit cells all
  use a fresh copy of the deterministic `paper-100m` base.
- **Matrix decision:** add a distinct concurrency-1 manager-CLI sandbox-create
  + base-mount cell. The final focused matrix is 19 cells; session-create
  remains separate.
- **Files changed:** `progress.md`, `experiment_inventory.md`,
  `experiments/expected_tables.md`, `benchmark/PAPER_ARTIFACT.md`,
  `plan/progress.md`, and
  `plan/task-packets/exp1-cli-performance-campaign.md`.
- **Prior runs invalidated:** none. Qualification remains environment evidence;
  no performance measurements exist.
- **Required next action:** implement and review the paper-local benchmark's
  `product_cli` cohort and pass its deterministic tests before any live
  performance preset.
- **Approval boundary:** documentation/specification work was user-authorized;
  Gate 0 protocol approval and any later commit, tag, or push remain explicit
  gates.
- **Disposition:** passed as a planning amendment; no experimental result.
- **Supported interpretation:** the environment is qualified and the next
  experiment work is precisely specified.
- **Unsafe interpretation:** any performance conclusion or claim that the
  current `direct_client` presets are eligible.

### 2026-07-30T03:57:08Z - EXP1-A pre-edit audit and hash baseline

- **Entry ID:** `audit-exp1-cli-campaign-012`
- **Phase:** EXP1-A / Gate 0
- **Kind:** preflight
- **Operator:** Codex EXP1 campaign
- **Host identity:** native Windows x64 `DESKTOP-OLP1ADS`, build 26200.
- **Paper Git state before campaign files were added:** clean branch
  `agent/complete-pw3-and-final-host-prep` at
  `347f32efa3fd19465d43dd40de2c5566404487ff`.
- **Product Git state:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Pre-edit hash artifact:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\exp1-pre-edit-baseline.json`.
- **Pre-edit hash artifact SHA-256:**
  `b408147fd6cf4d826c1e03f2beb10137a35e944b702639abc7fb5be79936f959`.
- **Hash coverage:** every tracked file in both repositories; new campaign
  files are recorded as absent from the pre-edit tree.
- **Required-source review:** the complete EXP1 packet, every item in its
  required read-first sequence, and the research-handoff/artifact references
  required by the AI research-writing evidence workflow were read before any
  existing file was edited.
- **Released CLI contract audit:** manager, runtime, and observability catalog
  and operation help completed successfully. The executables do not implement
  `--version`; one bounded `--version` probe exited 2 with a JSON
  `invalid_request` envelope and produced no state change. Release identity is
  therefore the annotated `v0.1.4` tag plus exact binary hashes.
- **Benchmark audit findings:** the scheduler unconditionally constructs
  `ProductAccess(GatewayClient)`; workspace-session creation uses direct daemon
  transport and Docker credential lookup; paper presets select
  `direct_client`; file operations omit `paper-100m`; sandbox creation is
  untimed setup; no `paper-pilot` exists; raw requests omit CLI subprocess
  provenance; resource sampling omits available daemon self CPU/RSS; and no
  deterministic expected-table generator exists.
- **Native-Windows audit findings:** importing the runner exited 1 because
  `os.killpg` is unavailable; executable resolution omits `.exe`; the released
  Windows package intentionally has no catalog-export binary; process identity
  and runner RSS are Linux-only; the fixture cache uses the Windows-invalid
  `sha256:` directory spelling; directory `fsync` is POSIX-only; and metadata
  resolves Linux package paths instead of the staged Windows release.
- **Measurement boundary review:** primary timing is fixed as native CLI
  process launch through exit, separate stdout/stderr capture, exact single
  JSON parse, and response-schema validation. Setup, CLI verification,
  observability sampling, and cleanup remain untimed.
- **Disposition:** audit completed; Gate 0 remains in progress until the
  implementation, protocol cross-links, and deterministic validation remove
  the listed ambiguities. No live performance preset was run.
- **Supported interpretation:** the qualified environment and released CLI
  contracts are sufficient to implement a paper-local native-Windows cohort.
- **Unsafe interpretation:** any performance result or claim that the imported
  harness is currently runnable on native Windows.
- **Next action:** implement the closed `product_cli` adapter, native-Windows
  lifecycle support, exact 19-cell plans, evidence contract, and tests.

### 2026-07-30T04:02:54Z - Released Windows CLI 256 KiB argv blocker

- **Entry ID:** `diagnostic-exp1-windows-cli-argv-limit-013`
- **Phase:** EXP1-A / EXP1-B contract validation
- **Kind:** preflight
- **Operator:** Codex EXP1 campaign
- **Host identity:** native Windows x64 `DESKTOP-OLP1ADS`, build 26200.
- **Product branch/commit/tag:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`, release `v0.1.4`.
- **Runtime CLI:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4\bin\sandbox-runtime-cli.exe`.
- **Runtime CLI SHA-256:**
  `df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4`.
- **Reviewed released contract:** `file_write` accepts file content only through
  `--content TEXT`; the CLI exposes no stdin, response-file, or content-file
  alternative.
- **Exact diagnostic:** construct 262,144 ASCII characters in memory and invoke
  the released runtime CLI with the required `file_write --content` argument
  against the deliberately unused socket `127.0.0.1:1`.
- **Command host exit status:** PowerShell command process exited 0 after
  recording the failure because the native child never started and
  `$LASTEXITCODE` remained null.
- **Native child exit status:** unavailable; process creation failed before an
  executable instance existed.
- **Observed failure:** PowerShell `ResourceUnavailable` /
  `NativeCommandFailed`: `The filename or extension is too long`.
- **Evidence artifact:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\diagnostics\exp1-windows-cli-argv-limit-20260730.json`.
- **Evidence artifact SHA-256:**
  `41429d69f18de0d0a9426b66cb1dcf841aa7ddd1d9e4dff8dd8ec329b2c19a1c`.
- **Protocol impact:** the fixed 256 KiB `file_write` cells at concurrency 1
  and 5 cannot launch through the released native Windows CLI. Therefore the
  exact 19-cell pilot, its Gate 3 acceptance, protocol freeze, and final pass
  are impossible with the pinned package.
- **Fallback decision:** none. Direct gateway access, `exec_command`,
  host-side mutation, payload reduction, cell removal, or a different cohort
  would violate the preregistered operation boundary.
- **Partial paper-local work retained:** pre-edit hash capture plus preliminary
  native-Windows/catalog/session/observability adapter scaffolding in the
  changed benchmark files. It is intentionally uncommitted and has not passed
  EXP1-B tests.
- **Cleanup result:** the runtime CLI process count is zero; no gateway was
  started; Docker was not contacted; no sandbox, container, volume, runtime
  state, or measurement artifact was created; the product repository remains
  clean `main`.
- **Disposition:** failed; actual EXP1 stop condition reached before any live
  performance preset.
- **Supported interpretation:** the released Windows CLI invocation contract
  cannot carry the preregistered 256 KiB `file_write` payload.
- **Unsafe interpretation:** any performance conclusion, any claim that a pilot
  ran, or any estimate of the missing cells.
- **Single required external action:** publish and stage a checksum-pinned
  Windows release whose runtime CLI can read `file_write` content from stdin or
  a file without placing the payload in the native process command line; then
  log a pre-freeze protocol/product-identity amendment and rerun Gates 0--3.

### 2026-07-30T04:06:43Z - Async benchmark-path reproduction and source-contract audit

- **Entry ID:** `diagnostic-exp1-asyncio-cli-payload-014`
- **Phase:** EXP1-B contract validation
- **Kind:** preflight
- **Operator:** Codex EXP1 campaign
- **Purpose:** independently reproduce the 256 KiB launch failure through the
  exact Python subprocess API required by the benchmark and exhaust released
  CLI content-input alternatives.
- **Python:** native Windows CPython 3.13.14,
  `asyncio.create_subprocess_exec`, argument array, no shell.
- **Small control:** the released runtime CLI process started for a 4,096-byte
  `file_write` payload, received a PID, and exited 1 after the deliberately
  unavailable gateway connection. This proves the diagnostic command shape and
  executable are otherwise launchable.
- **Required payload:** the same API with 262,144 content bytes raised native
  `WinError 206` before assigning a PID. The gateway connection was never
  attempted.
- **Async probe artifact:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\diagnostics\exp1-python-subprocess-payload-probe-20260730.json`.
- **Async probe SHA-256:**
  `6cefe6eea5876b70e0c72a399d5dd10ddce9d236ce01daef2066cb0ca3269beb`.
- **Source contract:** exact `v0.1.4` source at the required commit copies
  string/path values directly from argv. Runtime projection exposes
  `file_write` content only as `--content TEXT`; the separately named
  `write_command_stdin` operation targets an already-running command and
  cannot supply `file_write` content.
- **Source-contract artifact:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\diagnostics\exp1-cli-file-write-contract-20260730.json`.
- **Source-contract SHA-256:**
  `cf5c3c315a9a78f138d5cdfd5593798efe15fc3a3dace18f59233647c4884e9f`.
- **Cleanup:** the control runtime-CLI process exited; zero runtime-CLI
  processes remain. No released campaign gateway was started and Docker was
  not contacted. One debug-build gateway process predating EXP1 remains
  running and was intentionally left untouched as unrelated user state.
- **Product state:** clean `main` at the required commit.
- **Disposition:** failed campaign contract; second independent proof of the
  same released-product stop condition. No performance preset ran.
- **Supported interpretation:** the exact subprocess mechanism required by the
  benchmark cannot create the preregistered 256 KiB `file_write` process.
- **Unsafe interpretation:** an estimate of file-write performance or a claim
  about other product versions/interfaces.
- **Next action:** unchanged; a checksum-pinned Windows release needs a
  non-argv file-content input before the fixed campaign can resume.

### 2026-07-30T04:08:01Z - Third external-state blocker audit

- **Entry ID:** `preflight-exp1-blocker-state-015`
- **Phase:** EXP1-B contract validation
- **Kind:** preflight
- **Operator:** Codex EXP1 campaign
- **Action:** re-inspected the current product repository, staged Windows
  packages, runtime-CLI identity, and retained benchmark-path diagnostic before
  deciding whether the campaign could resume.
- **Product state:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Available Windows packages:** only `windows-v0.1.4`.
- **Runtime CLI SHA-256:**
  `df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4`,
  unchanged from both failed launch proofs.
- **External-state change:** none. No new checksum-pinned release or alternate
  released `file_write` content-input contract is present.
- **Disposition:** blocked. The same product-contract stop condition has now
  recurred across the original campaign turn and two continued blocker audits;
  no further safe in-scope benchmark action can make Gate 3 executable.
- **Measurements:** none; no smoke, pilot, final pass, or analysis command ran.
- **Cleanup:** no new process, gateway, sandbox, container, volume, or runtime
  state was created by this read-only audit.
- **Single required external action:** publish and stage a checksum-pinned
  Windows release whose runtime CLI accepts `file_write` content without
  placing the payload in the native process command line.

### 2026-07-30T04:21:50Z - Protocol amendment v1.1: authorized pre-freeze CLI input fix

- **Entry ID:** `amendment-exp1-cli-content-input-016`
- **Phase:** EXP1-B contract implementation, before smoke, pilot, protocol
  freeze, or final measurement.
- **Kind:** amendment
- **Reason:** the released native Windows runtime CLI accepts `file_write`
  content only through `--content TEXT`; the preregistered 262,144-byte payload
  therefore fails native process creation with `WinError 206` before a CLI
  process exists.
- **Decision timing:** made before viewing any EXP1 smoke, pilot, or final
  performance result. No live performance preset has run.
- **Authorization:** the user explicitly authorized checking out from product
  `main` and fixing bugs on 2026-07-30. Work will remain on the existing
  `ephemeral-sandbox` `main` checkout and will not be pushed.
- **Product starting identity:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`, release baseline `v0.1.4`.
- **Permitted product change:** add a bounded, non-command-line content source
  for runtime-CLI `file_write` while preserving the existing `--content`
  contract; add focused tests and help text; rebuild the native Windows
  executable.
- **Files changed:** to be recorded after implementation. No product source had
  changed when this amendment was written.
- **Metrics/cells/rules affected:** no metric, warmup, repetition, concurrency,
  payload-size, success, retry, timeout, exclusion, or analysis rule changes.
  The two 256 KiB `file_write` cells become launchable through the same required
  CLI process boundary.
- **Identity rule:** the rebuilt runtime CLI is a new pre-freeze product
  identity, not the original `v0.1.4` binary. Its product commit, package path,
  binary SHA-256 values, and CLI contract must be requalified and frozen before
  pilot acceptance.
- **Prior runs invalidated:** none; only preflight diagnostics exist. They remain
  historical evidence for the original released-binary defect.
- **Required reruns:** focused product tests; exact 262,144-byte Windows
  subprocess probe through the new input path; Gates 0--2 for the amended
  package; then the full EXP1 smoke and 5-sample pilot Gate 3.
- **Reviewer/author approval:** direct user authorization in the active Codex
  task.
- **Unsafe interpretation:** describing the amended binary as unmodified
  `v0.1.4`, comparing pre-amendment diagnostics as performance data, or changing
  the fixed EXP1 cell matrix.

### 2026-07-30T04:31:18Z - Authorized runtime-CLI fix and amended Windows package

- **Entry ID:** `product-fix-exp1-content-file-017`
- **Phase:** EXP1-B product-boundary repair before live smoke or measurement.
- **Kind:** amendment
- **Operator:** Codex EXP1 campaign.
- **Product starting identity:** clean `main` at
  `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- **Product resulting identity:** clean local `main` at
  `46593b10faf945807ee6e4ec9f76fe8338cb1d19`, one commit ahead of
  `origin/main`; commit subject `fix(cli): support file-backed write content`.
- **Product change:** runtime `file_write` now accepts
  `--content-file FILE` as an alternative value source for the existing
  semantic `content` argument. The CLI opens the file after process creation,
  caps reads at the 16,777,216-byte gateway request limit, requires UTF-8, and
  preserves the original `--content TEXT` behavior.
- **Boundary decision:** the semantic catalog, operation name, request schema,
  gateway transport, and runtime handler are unchanged. The new input-source
  metadata and help remain owned by `sandbox-cli::projection`.
- **Changed production files:**
  `crates/sandbox-cli/src/projection/mod.rs`,
  `crates/sandbox-cli/src/projection/runtime.rs`,
  `crates/sandbox-cli/src/input.rs`, and
  `crates/sandbox-cli/src/help.rs`.
- **Changed verification files:**
  `crates/sandbox-cli/tests/runtime.rs`,
  `crates/sandbox-cli/tests/projection_integrity.rs`,
  `crates/sandbox-cli/tests/compatibility.rs`,
  `crates/sandbox-cli/tests/manager.rs`,
  `crates/sandbox-cli/tests/observability.rs`, and
  `crates/sandbox-cli/tests/fixtures/observability-help.txt`.
- **Ancillary native-Windows test repairs:** exact text fixtures are compared
  after CRLF-to-LF normalization; the stale observability help fixture now
  matches the already-current semantic catalog wording.
- **Verification commands:**
  `cargo fmt --all -- --check`;
  `cargo test -p sandbox-cli --all-features`;
  `cargo clippy -p sandbox-cli --all-targets --all-features -- -D warnings`.
- **Verification result:** passed; 56 integration tests passed, all feature
  combinations compiled, doc tests passed, and strict clippy reported no
  warning.
- **Package command:**
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  .\bin\package-windows-amd64-release.ps1 -PackageName
  windows-exp1-46593b10 -OutDir target -Profile release`.
- **Package path:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-46593b10`.
- **Package archive SHA-256:**
  `a3550b4464b278ffbc35b398378abd2f649f21ba18e8beb4368c7933d28a892f`.
- **Binary SHA-256 values:** gateway
  `5f50012539f92195f74d3474d9c5c52f9bd0389fa565668094846a97e73a5b94`;
  manager CLI
  `512e93523ddd52e7f2e12e0fe7977dc7b9a4541b40ed9ab25fce844cbad191ac`;
  runtime CLI
  `1cff6dda6934e2bff4562dc2b51c8d82844ca6129095f7e313791c111d5d1c3a`;
  observability CLI
  `6bf7c542cb740c85575da015db55ee02fabb805236d21d4d14731df63bbb3043`;
  Linux daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Release-label rule:** this local package is the amended EXP1 product
  identity and must not be called the unmodified `v0.1.4` release.
- **Push status:** no product commit, branch, tag, or package was pushed.
- **Disposition:** passed focused product verification; exact campaign
  requalification still required.

### 2026-07-30T04:31:00Z - Rebuilt runtime-CLI 256 KiB subprocess proof

- **Entry ID:** `diagnostic-exp1-content-file-018`
- **Phase:** EXP1-B amended-product contract validation.
- **Kind:** preflight
- **Operator:** Codex EXP1 campaign.
- **Runtime CLI:** amended package at product commit
  `46593b10faf945807ee6e4ec9f76fe8338cb1d19`, SHA-256
  `1cff6dda6934e2bff4562dc2b51c8d82844ca6129095f7e313791c111d5d1c3a`.
- **Probe API:** native Windows CPython
  `asyncio.create_subprocess_exec`, argument array, no shell.
- **Probe contract:** prepare an exact payload file before starting the clock,
  then time process creation, the CLI's file read and request construction, and
  its deliberately unsuccessful connection to `127.0.0.1:1`.
- **Payloads:** 4,096 and 262,144 ASCII bytes through
  `file_write --content-file PREPARED-PAYLOAD-FILE`.
- **Observed result:** both processes started, received PIDs, constructed their
  requests, and exited 1 with the expected `connection_error`. The required
  262,144-byte path therefore crossed the prior native process-creation
  boundary and reached gateway transport.
- **Initial diagnostic artifact:**
  `experiments/diagnostics/exp1-windows-cli-content-file-probe-20260730.json`,
  SHA-256
  `f462ed2f294476267bd3f387e0db22151c158e06e763279b445a9e4a5a09334d`.
- **Initial diagnostic disposition:** failed assertion only. Product behavior
  was successful, but the script expected error kind `gateway_error` rather
  than the observed stable `connection_error`. The artifact is retained and
  was not overwritten.
- **Corrected diagnostic artifact:**
  `experiments/diagnostics/exp1-windows-cli-content-file-probe-20260730-v2.json`,
  SHA-256
  `7640f479ca5b24dbfa5db7cd6e64732853de64eac92c7fdc0c3551ba6daa43b0`.
- **Corrected probe script:**
  `experiments/scripts/probe_exp1_windows_cli_content_file.py`, SHA-256
  `c0a6ddf78257f057c500f1a2369075d6178bd16eb25590d06f3b4d1de3870b1d`.
- **Acceptance:** passed. The exact fixed large-payload subprocess can now
  launch without putting content in the native Windows command line.
- **Measurements:** diagnostic elapsed times are not EXP1 performance data and
  must not enter pilot, final, or paper tables.
- **Cleanup:** both diagnostic CLIs exited; temporary payload files were
  deleted by the probe; no campaign gateway, sandbox, container, volume, or
  runtime state was created.
- **Next action:** requalify the amended package and complete the native
  Windows CLI-only cohort before smoke and pilot.

### 2026-07-30T04:55:31Z - Smoke preflight exposed missing manager and observability request IDs

- **Entry ID:** `smoke-preflight-exp1-cli-request-id-019`
- **Phase:** EXP1-B/EXP1-C boundary, before any successful smoke, pilot,
  protocol freeze, or final measurement.
- **Kind:** amendment
- **Operator:** Codex EXP1 campaign.
- **Validated plan:** `paper-env-smoke`, plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  runnable with exactly 19 cells, 19 trial batches, and 55 operation requests.
- **First run ID:** `019fb15d-b8b6-7126-9ecd-637fe75b8e27`.
- **First-run disposition:** failed before any cell or operation request. The
  staged Windows configuration omitted the gateway section; the harness
  failed closed and terminal artifact finalization initially masked that
  startup exception. No performance value was produced.
- **Preserved raw artifacts:**
  `.benchmark-state/results/019fb15d-b8b6-7126-9ecd-637fe75b8e27`;
  the failed manifest, plan, environment, and event journal were not
  overwritten.
- **Harness corrections:** synthesize only the missing per-run gateway keys in
  the staged Windows configuration; permit the readiness and campaign CLI
  adapters to share one verified evidence directory; permit a failed run with
  zero observations to derive a terminal report; register the sandbox
  lifecycle report family.
- **Second preflight finding:** after the configuration correction, the gateway
  started, but every manager-CLI readiness probe rejected
  `--request-id`. Manager and observability CLIs mint UUIDs internally and
  expose no explicit request-ID option, whereas the runtime CLI already
  forwards one. This prevents exact benchmark-to-product request correlation.
- **Retained diagnostic evidence:** the failed run's `cli-subprocesses`
  directory contains each redacted manager invocation and error envelope.
  These readiness attempts are diagnostics, not EXP1 measurements.
- **Authorized product amendment:** extend the runtime CLI's existing bounded
  explicit request-ID contract to the manager and observability CLIs, without
  changing operation semantics, gateway transport, factors, repetitions, or
  analysis. The user already authorized product bug fixes on local `main`;
  the fix remains pre-freeze and will not be pushed.
- **Prior runs invalidated:** no valid run. The failed smoke preflight remains
  negative evidence and is excluded by design because it issued zero planned
  operation requests.
- **Cleanup:** the failed startup paths terminated their gateway processes,
  removed owned runtime state, and found no campaign containers or sandboxes.
- **Disposition:** partial; exact CLI correlation requires the authorized
  product fix, rebuild, and full package requalification before smoke resumes.

### 2026-07-30T04:59:22Z - Cross-domain CLI request-ID fix and second amended package

- **Entry ID:** `product-fix-exp1-request-id-020`
- **Phase:** EXP1-B product-boundary repair before successful smoke or pilot.
- **Kind:** amendment
- **Product starting identity:** clean local `main` at
  `46593b10faf945807ee6e4ec9f76fe8338cb1d19`.
- **Product resulting identity:** clean local `main` at
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, two commits ahead of
  `origin/main`; commit subject
  `fix(cli): preserve request IDs across domains`.
- **Product change:** manager and observability CLIs now accept the same
  global, bounded `--request-id VALUE` option already implemented by the
  runtime CLI and forward it unchanged into the gateway request. Shared
  validation permits 1--128 ASCII letters, digits, period, underscore, colon,
  or dash. Default UUID generation remains unchanged when the option is
  omitted.
- **Changed production files:** `crates/sandbox-cli/src/input.rs`,
  `manager.rs`, `observability.rs`, and `runtime.rs`.
- **Changed verification files:** manager and observability integration tests
  plus their exact help fixtures.
- **Verification:** `cargo fmt --all -- --check`,
  `cargo test -p sandbox-cli --all-features`, and
  `cargo clippy -p sandbox-cli --all-targets --all-features -- -D warnings`
  all passed; 58 sandbox-CLI integration tests passed.
- **Package path:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-8c79217e`.
- **Package archive:** 5,605,345 bytes, SHA-256
  `a2fe0bfcd9103e30a9116d02785ffa47a1bb4894e7c78614ad2a08d642f2b82c`.
- **Binary SHA-256 values:** gateway
  `5f50012539f92195f74d3474d9c5c52f9bd0389fa565668094846a97e73a5b94`;
  manager CLI
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`;
  runtime CLI
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`;
  observability CLI
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`;
  daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Plan revalidation:** `paper-env-smoke` remains runnable at plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`,
  exactly 19 cells, 19 batches, and 55 operation requests.
- **Scientific scope:** request correlation only. No operation, factor, cell,
  payload, repetition, timeout, exclusion, metric, or analysis rule changed.
- **Push status:** neither product commit nor package was pushed.
- **Disposition:** passed focused product verification; live package smoke is
  next.

### 2026-07-30T05:01:55Z - Smoke v2 retained: Windows depth-100 fixture path

- **Entry ID:** `smoke-exp1-windows-depth100-021`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb164-afe0-7e5b-a3d2-f067c3f53a98`.
- **Plan:** `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the isolated gateway started and manager-CLI readiness
  passed with exact request ID. The first sandbox-lifecycle cell then failed
  during fixture materialization before any planned operation request.
- **Cause:** the fixed depth-100 fixture uses paths beyond the legacy Windows
  `MAX_PATH` boundary under the benchmark's absolute state root. The generator
  used ordinary Win32 paths and failed while constructing the cache.
- **Raw artifacts:**
  `.benchmark-state/results/019fb164-afe0-7e5b-a3d2-f067c3f53a98`;
  terminal report, manifest, event journal, and redacted CLI readiness/cleanup
  evidence are retained. Correctness is `fail`; measured batches and planned
  operation requests both equal zero.
- **Harness correction:** use the native Windows extended-length path form for
  fixture construction, cache traversal/copy, failed-staging cleanup, and
  local resource walks. Logical fixture paths and container-visible paths are
  unchanged.
- **Verification:** a depth-100 materialization/copy regression test plus
  CLI-contract and plan/API tests passed, 31 tests total.
- **Cleanup:** gateway terminated; CLI cleanup confirmed an empty isolated
  registry; no campaign container or sandbox remained. The empty failed-run
  workspace and invalid partial-cache parent remain owned evidence.
- **Disposition:** failed smoke retained; rerun the same frozen smoke matrix
  after the host-path correction.

### 2026-07-30T05:04:13Z - Smoke v3 retained: equivalent Windows path forms

- **Entry ID:** `smoke-exp1-windows-path-identity-022`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb166-f100-7482-aac4-a0cdbfe05a8d`.
- **Plan:** `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** depth-100 fixture materialization and copy completed.
  The first measured `create_sandbox` CLI invocation returned exit code zero,
  a schema-valid response, and a ready sandbox after 59,866,856,700 ns. The
  harness then rejected the response before recording a product request.
- **Cause:** the product returned the deep workspace as the native Windows
  extended-length alias `\\?\C:\...`; the harness compared it to the same
  directory in ordinary `C:\...` form using `Path` equality. Python preserves
  those two spellings during resolution, so identical native directories
  compared unequal.
- **Raw artifacts:**
  `.benchmark-state/results/019fb166-f100-7482-aac4-a0cdbfe05a8d`;
  the terminal report, three correctness/trial observations, event journal,
  and all redacted CLI stdout/stderr/metadata are retained. Correctness is
  `fail`; one trial batch and one planned operation attempt occurred, but no
  request observation was admitted.
- **Harness correction:** compare resolved Windows native path identities
  after normalizing case and the `\\?\`/`\\?\UNC\` aliases. Apply the same
  identity rule at CLI ownership admission and create-sandbox verification.
  This changes no workload, product behavior, timing boundary, or analysis
  rule.
- **Cleanup:** the isolated gateway terminated and no campaign sandbox or
  container remained. The unrelated pre-existing exited sandbox container was
  not touched.
- **Disposition:** failed smoke retained; verify the path-identity regression
  and rerun the unchanged smoke matrix.

### 2026-07-30T05:13:57Z - Pre-freeze Windows identity and provenance verification

- **Entry ID:** `pre-freeze-exp1-path-provenance-023`
- **Phase:** EXP1-B/EXP1-C boundary, before successful smoke, pilot, or freeze.
- **Kind:** amendment
- **Path correction verification:** native Windows extended-path fixture and
  CLI tests passed, including the regression proving that `\\?\C:\...` and
  `C:\...` workspace responses are admitted as the same resolved directory.
- **Provenance correction:** report derivation revision 4 now identifies
  `request_latency_ns` for `product_cli` as the monotonic interval from
  immediately before native CLI subprocess creation through process exit,
  pipe collection, and one-line JSON schema validation. Report methods also
  name the barrier-based batch boundary, the per-invocation
  `cli-subprocesses` evidence directory, redaction rule, and all fixed
  executable hashes. Numeric calculations did not change.
- **Count guards:** parameterized contract tests now require the complete
  19-cell matrix and exact counts: smoke 19 batches/55 requests, pilot 133/385,
  and final 1,938/5,610. Every cell must select `paper-100m`.
- **Verification:** 40 focused unit and contract tests passed after the
  changes. One intermediate 13-test invocation failed because the new fake
  sandbox response omitted required schema fields; the fixture was completed
  and the same suite then passed. One earlier command used the wrong relative
  virtual-environment path and did not execute any tests.
- **Plan revalidation:** `paper-env-smoke` is runnable with 19 cells, 19 trial
  batches, and 55 requests at unchanged plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Prior runs invalidated:** none were eligible; all three failed smoke runs
  remain diagnostic evidence.
- **Disposition:** passed; rerun the unchanged smoke matrix.

### 2026-07-30T05:16:57Z - Smoke v4 retained: released snapshot CLI shape

- **Entry ID:** `smoke-exp1-snapshot-shape-024`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb171-e8b7-7b81-8eeb-d80963595865`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the depth-100 fixture copied, `create_sandbox` passed
  ownership admission, and the native manager CLI returned a ready sandbox in
  54,015,576,100 ns. Initial cgroup and daemon observability CLI calls also
  passed. The snapshot CLI then returned exit code zero and its released
  schema, but the harness's shallow pre-parser incorrectly required a `view`
  discriminator that snapshot does not define.
- **Raw artifacts:**
  `.benchmark-state/results/019fb171-e8b7-7b81-8eeb-d80963595865`;
  report derivation revision 4, terminal report, observations, events, and
  seven redacted CLI evidence triplets are retained. The one product request
  succeeded, but the trial is ineligible because required resource sampling
  failed before verification.
- **Harness correction:** validate snapshot's released top-level discriminants
  `sandbox_id`, `lifecycle_state`, and `availability`; the existing strict
  snapshot parser remains authoritative for the complete response.
- **Cleanup:** the owned sandbox was destroyed through the manager CLI, the
  isolated registry was verified empty, the gateway terminated, and no
  campaign container remained.
- **Disposition:** failed smoke retained; add the released-shape regression and
  rerun the unchanged smoke matrix.

### 2026-07-30T05:18:54Z - Smoke v5 retained: portable evidence directories

- **Entry ID:** `smoke-exp1-evidence-path-025`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb175-0d2d-71dc-bcdb-7233c8c33c3d`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the first native CLI create request succeeded in
  55,642,277,100 ns; its request observation was admitted; two complete
  100-ms-contract resource samples were persisted; and manager-CLI inspection
  verified ready state and workspace identity. Persistence of the required
  bounded operation evidence then failed during verification.
- **Cause:** the evidence layout used the scientific cell ID
  `sha256:...` verbatim as a directory name. `:` is legal in the original
  POSIX implementation but illegal in a Windows directory component. The run
  therefore contains an empty `cells` evidence parent and no operation
  evidence record.
- **Raw artifacts:**
  `.benchmark-state/results/019fb175-0d2d-71dc-bcdb-7233c8c33c3d`;
  the terminal report, 32 observations, 52 events, and 11 redacted CLI
  evidence triplets are retained.
- **Harness correction:** store each evidence envelope directly under the
  run-level `bounded-evidence` directory using its content digest. Evidence
  schema version 2 embeds the original cell and trial IDs in the envelope;
  readers continue to accept version 1's nested layout. This keeps paths below
  legacy Windows length limits without weakening content addressing or opaque
  download IDs.
- **Byte-integrity correction:** the first portability-test attempt exposed
  that Windows CRT text mode expanded LF bytes to CRLF in every low-level
  `os.open` writer. That made evidence filename digests disagree with the bytes
  on disk and could alter multiline CLI content files. All benchmark-owned
  low-level byte writers now explicitly use binary mode, including journals,
  immutable artifacts, ownership/config/fixture files, gateway logs, and
  product CLI payload files.
- **Verification:** the first hashed-nested-directory test still exceeded
  Windows path limits; the first flat-layout test then exposed the CRLF
  transformation. After both corrections, 43 focused artifact, CLI, fixture,
  derivation, planning, and API tests passed, including byte-for-byte
  multiline content.
- **Cleanup:** the owned sandbox was destroyed through the manager CLI, the
  isolated registry was empty, the gateway terminated, and no campaign
  container remained.
- **Disposition:** failed smoke retained; verify portable evidence indexing and
  rerun the unchanged smoke matrix.

### 2026-07-30T13:27:05Z - Smoke v6 retained: deep runtime cleanup path

- **Entry ID:** `smoke-exp1-runtime-cleanup-026`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb335-074f-7e6d-918c-cbc31b241019`.
- **Start/end:** `2026-07-30T13:27:05.172932Z` to
  `2026-07-30T13:28:44.500576Z`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the complete sandbox-lifecycle family passed. The
  native manager CLI created a ready sandbox in 58,032,810,900 ns; the
  request observation and 58,049,532,100 ns trial-batch latency were
  admitted; two full resource samples (28 metric readings) were retained;
  strict manager and observability CLI verification passed; schema-v2
  content-addressed operation evidence was written; both correctness checks
  passed; and manager-CLI sandbox destruction passed. The family was marked
  completed before the run failed while closing its isolated gateway.
- **Cause:** the owned gateway runtime contains the cached depth-100 shared
  base, but `OwnershipLedger.remove` passed the ordinary Windows path to
  `shutil.rmtree`. Cleanup reached the legacy `MAX_PATH` boundary after the
  gateway had terminated and its authentication token had been deleted.
- **Raw artifacts:**
  `.benchmark-state/results/019fb335-074f-7e6d-918c-cbc31b241019`;
  the failed terminal report, 33 observations, 55 events, one bounded
  evidence envelope, and 11 redacted CLI evidence triplets are retained.
- **Cleanup:** the manager-CLI registry check was empty, the sandbox was
  destroyed, the gateway process is absent, and no campaign container
  remains. The owned runtime directory and marker remain as negative cleanup
  evidence; its token is absent. The unrelated pre-existing exited container
  from ten days earlier was not touched.
- **Disposition:** failed smoke retained; correct only the host-native
  recursive deletion spelling, verify it independently, and rerun the
  unchanged smoke matrix.

### 2026-07-30T13:35:43Z - Pre-freeze deep cleanup correction

- **Entry ID:** `pre-freeze-exp1-runtime-cleanup-027`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** amendment
- **Harness correction:** after exact marker, active-ledger, role-root,
  symlink, device-boundary, and mutable-path validation is complete,
  `OwnershipLedger.remove` now gives `shutil.rmtree` the existing native
  Windows extended-length spelling. Ownership authority and all scientific
  protocol inputs are unchanged.
- **Regression:** a new test constructs an owned directory tree beyond 280
  characters and proves that ledger removal succeeds. The isolated regression
  passed.
- **Additional verification:** the 53-test artifact, CLI, fixture, derivation,
  planning, API, and cleanup selection produced 52 passes. Its sole failure is
  the pre-existing frozen-golden assertion that expects 48 evidence files from
  a committed fixture containing none. Running all five safety tests produced
  three passes plus the two pre-existing Windows failures that require
  symlink privilege; neither failure exercises the cleanup correction.
- **Plan and scientific scope:** no operation, factor, cell, payload,
  repetition, timeout, exclusion, metric, timing boundary, analysis rule, or
  plan file changed. Plan hash remains
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Prior runs invalidated:** none; all six failed smoke attempts remain
  diagnostic evidence.
- **Disposition:** cleanup regression passed; run the unchanged EXP1-C smoke.

### 2026-07-30T13:37:01Z - Smoke v7 retained: repeated readiness evidence ID

- **Entry ID:** `smoke-exp1-readiness-evidence-id-028`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Preflight anomaly:** the first validation command selected the package
  directory instead of its `bin` child and was rejected before a gateway or
  run was created. The corrected command passed with the unchanged binary
  hashes, clean product `main`, 548.53 GiB free, 19 cells, 19 batches, 55
  requests, and no plan warnings.
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb33e-21fa-7249-926a-25b57577d649`.
- **Start/end:** `2026-07-30T13:37:01.715826Z` to
  `2026-07-30T13:38:28.937442Z`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the sandbox-lifecycle family again passed completely.
  Its gateway then closed, emitted its retained redacted-log digest, and
  removed the depth-100 runtime tree successfully. The command family reached
  `preparing` but its second isolated gateway failed during CLI readiness,
  before the family entered `running` or issued a planned request.
- **Cause:** every newly constructed gateway-local CLI adapter restarted its
  readiness counter at zero and used
  `<run-id>.gateway.ready.0`. CLI evidence IDs are the SHA-256 of executable
  role, operation, and request ID, so the second gateway attempted an
  exclusive write to the first gateway's already-retained evidence triplet.
  The predicted historical ID
  `5e85d67a15b969424eeac5af7bf2150b4ffe89431400fa5c1fa427c6b858dab6`
  exactly matches the first readiness metadata filename.
- **Raw artifacts:**
  `.benchmark-state/results/019fb33e-21fa-7249-926a-25b57577d649`;
  failed report and manifest, 33 observations, 57 events, one bounded
  operation envelope, and the first family's 11 CLI evidence triplets are
  retained.
- **Cleanup:** both gateways terminated, both owned runtime generations were
  removed, the manager registry was empty, and no campaign sandbox,
  container, process, volume, or runtime remains.
- **Disposition:** failed smoke retained; make readiness request/evidence IDs
  unique per isolated gateway instance, verify, and rerun the unchanged smoke.

### 2026-07-30T13:41:01Z - Pre-freeze gateway-scoped readiness identity

- **Entry ID:** `pre-freeze-exp1-readiness-identity-029`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** amendment
- **Harness correction:** CLI readiness request IDs now include the
  cryptographically random isolated `gateway_instance_id` before the local
  attempt number. Repeated gateways in one run therefore retain distinct
  request correlation and immutable CLI evidence while preserving exact
  manager request IDs.
- **Verification:** the gateway-scoped identity regression, native deep-tree
  cleanup regression, and complete product-CLI unit file passed, 11 tests
  total.
- **Scientific scope:** readiness probes are setup-only and excluded from the
  55 planned smoke requests and all primary timing. No operation, factor,
  cell, payload, repetition, timeout, exclusion, metric, timing boundary,
  analysis rule, preset, or plan hash changed.
- **Prior runs invalidated:** none; the seven failed smoke attempts remain
  diagnostic evidence.
- **Disposition:** passed focused verification; rerun the unchanged EXP1-C
  smoke.

### 2026-07-30T13:41:45Z - Smoke v8 retained: command line-window semantics

- **Entry ID:** `smoke-exp1-command-line-window-030`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb342-77ef-7866-a746-f83f1a66dfb3`.
- **Start/end:** `2026-07-30T13:41:45.921519Z` to
  `2026-07-30T13:45:07.847222Z`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** the lifecycle family and first command cell completed
  with all checks passing. The gateway-scoped readiness correction also
  crossed its prior failure boundary. In the second command cell, all five
  concurrent native runtime-CLI calls returned exit code zero, passed JSON
  validation, and returned `output: "4096"`. Verification nevertheless
  rejected the responses and conservatively marked the cell's three
  registered checks failed.
- **Cause:** the harness expected raw terminal bytes `"4096\n"`, while the
  released command contract returns a line-window projection whose logical
  line values omit delimiter bytes. Product tests and all five retained CLI
  responses agree on `"4096"`, with `total_lines: 1`.
- **Raw artifacts:**
  `.benchmark-state/results/019fb342-77ef-7866-a746-f83f1a66dfb3`;
  the failed report/manifest, 111 observations (including 7 successful
  planned requests and 84 resource readings), 163 events, and 40 CLI metadata
  records plus stdout/stderr are retained.
- **Cleanup:** both completed gateways terminated and removed their owned
  runtime trees; the registry was empty; and no campaign container, volume,
  process, or runtime remains.
- **Disposition:** failed smoke retained; align the correctness oracle with
  the released line-window representation, verify, and rerun the unchanged
  smoke.

### 2026-07-30T13:47:08Z - Pre-freeze command oracle correction

- **Entry ID:** `pre-freeze-exp1-command-oracle-031`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** amendment
- **Harness correction:** the fixed `fixture_read` command remains
  `wc -c < .eos-benchmark-fixture/command-read.bin`, but its correctness
  oracle now expects the released line-window value `"4096"` rather than raw
  terminal bytes with a trailing LF. The 64-KiB and no-output cases are
  unchanged.
- **Verification:** the explicit line-window regression, command-evidence
  test, gateway-scoped readiness regression, deep cleanup regression, and
  full product-CLI unit file passed, 13 tests total.
- **Scientific scope:** the command, fixture, concurrency, measured boundary,
  response bytes, request count, timing, checks, and operation evidence are
  unchanged. This correction was made from failed-smoke raw product responses
  before pilot or freeze; no performance value was accepted or excluded.
- **Plan:** no preset or plan field changed; hash remains
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Prior runs invalidated:** none; the eight failed smoke attempts remain
  diagnostic evidence.
- **Disposition:** passed focused verification; rerun the unchanged EXP1-C
  smoke.

### 2026-07-30T13:47:56Z - Smoke v9 retained: leading-hyphen auth token

- **Entry ID:** `smoke-exp1-cli-auth-token-032`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** smoke
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`, package
  `windows-exp1-8c79217e`.
- **Run ID:** `019fb348-1e9f-7937-9d6c-d865ca9c0e76`.
- **Start/end:** `2026-07-30T13:47:56.222188Z` to
  `2026-07-30T14:03:01.225216Z`.
- **Plan:** unchanged `paper-env-smoke`, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Observed result:** all lifecycle, command, and file cells passed: 17 of 19
  cells, 17 reportable trials, 49 planned native CLI requests, and all 42
  registered checks completed successfully. The workspace-lifecycle family
  then failed while preparing its isolated gateway, before entering
  `running` or issuing a workspace request.
- **Cause:** this gateway's randomly generated URL-safe auth token began with
  a hyphen. The CLI adapter supplied the token as the next argv item after
  `--gateway-auth-token`; the released Clap parser interpreted its `-R`
  prefix as another option. All 713 attempts from that gateway returned exit
  code 2 and the retained `product_error:invalid_request` classification,
  after which the 60-second readiness deadline expired.
- **Raw artifacts:**
  `.benchmark-state/results/019fb348-1e9f-7937-9d6c-d865ca9c0e76`;
  the failed report/manifest, 741 observations (49 requests, 616 resource
  readings, 42 checks), 1,045 events, 17 bounded operation envelopes, and
  1,080 redacted CLI metadata/stdout/stderr triplets are retained. No complete
  credential appears in the retained error or metadata.
- **Cleanup:** all four gateway processes terminated and all owned runtime
  generations were removed; registries were empty; no campaign container,
  volume, process, or runtime remains.
- **Disposition:** failed smoke retained; use the parser-safe equals form for
  the auth option, fail immediately on non-transient readiness product
  rejection, verify, and rerun the unchanged smoke.

### 2026-07-30T14:06:16Z - Pre-freeze auth argv and readiness correction

- **Entry ID:** `pre-freeze-exp1-cli-auth-token-033`
- **Phase:** EXP1-C environment smoke, before pilot and freeze.
- **Kind:** amendment
- **Harness correction:** every released CLI invocation now supplies the
  arbitrary URL-safe credential as
  `--gateway-auth-token=<credential>`, which is unambiguous even when the
  value begins with `-`. Persisted argv replaces the entire item with
  `--gateway-auth-token=[REDACTED]`.
- **Failure correction:** a product-level readiness rejection now fails
  gateway startup immediately. Only transport/readiness transients remain
  retryable; deterministic CLI usage errors can no longer produce a
  timeout-sized evidence flood.
- **Verification:** the product-CLI suite now uses a leading-hyphen token and
  proves exact equals-form argv plus redaction. A new readiness regression
  proves a product rejection is attempted once. Together with the
  gateway-scoped ID, deep cleanup, and command-oracle regressions, 14 focused
  tests passed.
- **Scientific scope:** auth and readiness are setup-only and excluded from
  planned requests and primary timing. No operation, factor, cell, payload,
  repetition, timeout, exclusion, metric, timing boundary, analysis rule,
  preset, or plan hash changed.
- **Prior runs invalidated:** none; the nine failed smoke attempts remain
  diagnostic evidence.
- **Disposition:** focused verification passed; rerun the unchanged EXP1-C
  smoke after completing the read-only host audit.

### 2026-07-30T14:26:27Z - Pre-freeze full validation and v9 host audit

- **Entry ID:** `pre-freeze-exp1-full-validation-034`
- **Phase:** EXP1-B/EXP1-C boundary, before pilot and freeze.
- **Kind:** preflight
- **Product identity:** clean local `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`; staged package
  `windows-exp1-8c79217e`.
- **v9 host/Docker audit:** retained CLI metadata contains exactly 713 failed
  readiness attempts for gateway
  `benchmark-gateway-06ae7ec80dd70ceb84daf362eb3ad509`, attempts 0--712
  over 60.0476619 seconds. Every call exited 2 with
  `product_error:invalid_request` and stderr SHA-256
  `4517dcba7692d4b49b792eb70b02c6dfd6c9185eee3210b1362f66e1b6ac6b42`;
  the parser reported `unexpected argument '-R' found`. Docker recovery and
  cleanup queries completed in approximately 2--3 ms. Current inspection
  found no campaign process, listener, container, volume, or runtime tree and
  ample host disk/memory. Docker/host exhaustion is ruled out.
- **Real-parser probe:** the released manager CLI was invoked with a
  leading-hyphen credential using attached
  `--gateway-auth-token=-R-exp1-probe`; it parsed the option and reached the
  deliberately unavailable endpoint, returning a connection error rather
  than `invalid_request`. Bounded logs are retained in
  `experiments/diagnostics/leading-hyphen-token.*.log`; no gateway or sandbox
  was created and no timing value is eligible for analysis.
- **Focused backend verification:** the product-CLI/readiness/command/deep
  cleanup regressions passed 14 tests. Cross-platform safety, catalog,
  gateway, squash-evidence, and artifact compatibility tests then passed
  34 tests with 4 Windows WinError 1314 symlink-privilege skips.
- **Complete backend verification:** with
  `PYTHONDONTWRITEBYTECODE=1`,
  `.\.venv\Scripts\python.exe -m pytest .\benchmark\backend\tests -q`
  exited 0: 152 passed and 4 skipped in 36.37 seconds. The skips are limited
  to attempted symlink creation rejected by Windows with WinError 1314; other
  fail-closed path and ownership checks passed. Test-generated tracked and
  untracked bytecode was restored/removed after validation.
- **Web environment and verification:** `npm` was initially blocked by the
  PowerShell script policy and `npm.cmd test` then reported the absent local
  `vitest` executable. Off-clock `npm.cmd ci` with Node v24.11.1 and npm
  11.6.2 installed the lockfile-pinned dependencies and exited 0. Subsequent
  `npm.cmd test` exited 0 (10 files, 43 tests) and `npm.cmd run build` exited
  0. npm reported two high-severity dependency advisories and Vite reported a
  large output chunk; no automatic dependency mutation was performed, and
  neither warning changes the native CLI measurement path.
- **Plan validation:** an initial preflight accidentally supplied the package
  root rather than its `bin` child and failed closed because the required
  executables were not located. Reissuing the same validation with
  `target\windows-exp1-8c79217e\bin` made all three presets runnable with zero
  validation findings, `product_cli`, and only `paper-100m`:
  `paper-env-smoke` = 19 cells/19 batches/55 requests, hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  `paper-pilot` = 19/133/385, hash
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  `paper-good-pass` = 19/1,938/5,610, hash
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
- **Artifact inventory:** `benchmark/PAPER_ARTIFACT.md` now lists the complete
  paper-local EXP1 delta, exact staged package, and the three validated plan
  expansions.
- **Scientific scope:** no live performance preset ran during this
  verification, and no measured value, operation, factor, cell, payload,
  repetition, timeout, exclusion, metric, or analysis rule changed.
- **Cleanup:** no campaign-owned runtime state or Docker object remains. The
  unrelated old exited `eos-76263...` container and unrelated volumes were
  left untouched.
- **Disposition:** EXP1-B deterministic validation passed; recheck exact
  environment/package hashes and run the unchanged EXP1-C smoke.

### 2026-07-30T14:30:21Z - Historical failed-runtime recovery before smoke

- **Entry ID:** `preflight-exp1-historical-runtime-recovery-035`
- **Phase:** EXP1-C preflight, before smoke v10.
- **Kind:** preflight
- **Finding:** a recursive preflight found four owned runtime directories
  retained from failed smoke runs
  `019fb166-f100-7482-aac4-a0cdbfe05a8d`,
  `019fb171-e8b7-7b81-8eeb-d80963595865`,
  `019fb175-0d2d-71dc-bcdb-7233c8c33c3d`, and
  `019fb335-074f-7e6d-918c-cbc31b241019`. They contained no live gateway
  process or campaign Docker object but had survived the earlier Windows
  long-path cleanup defect. This corrects the narrower prior cleanup checks,
  which proved no live process/container/volume but did not recursively
  enumerate historical runtime directories.
- **Recovery action:** the benchmark's scoped
  `sandbox-benchmark cleanup --run-id RUN_ID` command was issued once for each
  exact terminal failed run with the staged product `bin` directory. All four
  commands exited 0 with `cleaned: true` and `terminalized: false`; all four
  runtime directories were removed through their ownership markers.
- **Postcondition:** `sandbox-benchmark recover` exited 0 with
  `execution_available: true`, no issues, and no recovered run IDs. No
  campaign process, listener, container, volume, or runtime directory remains.
- **Preservation boundary:** immutable failed-run result corpora under
  `.benchmark-state/results` were not changed. Failed-run workspace trees
  under `.benchmark-state/runs` remain intentionally retained as required by
  the runner's failed-run forensic contract and its integration regression;
  they are not live gateway/runtime state and carry exact ownership markers.
- **Unrelated process:** a pre-existing debug gateway on loopback port 7878,
  started before this campaign with a separate debug binary/configuration,
  remains untouched. It has no campaign gateway label or Docker object and is
  not bound to any reserved campaign endpoint.
- **Disposition:** historical runtime leakage safely resolved; EXP1-C smoke
  preflight may proceed.

### 2026-07-30T14:55:33Z - Smoke v10 passed and archived

- **Entry ID:** `smoke-exp1-cli-passed-036`
- **Phase:** EXP1-C live CLI integration smoke.
- **Kind:** smoke
- **Run ID:** `019fb36f-b50f-73c3-a3b9-0d0f861cff9e`.
- **Exact command:** `.\.venv\Scripts\sandbox-benchmark.exe run
  --test-repository-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1
  --product-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox
  --product-bin-dir
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-8c79217e\bin
  --plan paper-env-smoke`, with `PYTHONDONTWRITEBYTECODE=1`.
- **Start/end/elapsed:** `2026-07-30T14:31:10.633046Z` to
  `2026-07-30T14:47:31.197137Z`; 980.564091 seconds by artifact timestamps.
  The outer command exited 0 after 1,059.3 seconds including CLI
  validation/startup and terminal projection outside the manifest interval.
- **Plan:** unchanged hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  `product_cli`, `paper-100m`, 19 cells, 19 measured trial batches, 55 planned
  requests, no warmups.
- **Product/environment:** clean local product `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c`; package/binary hashes match
  entry 034; pinned Linux AMD64 image digest
  `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`;
  Docker Engine 29.0.1, overlayfs, cgroup v2.
- **Acceptance result:** completed with correctness `pass`. All 19 cells and
  19 measured trials are successful and reportable; all 48 registered checks
  passed; all 55 planned request IDs are unique; report warnings, product
  failures, correctness failures, infrastructure failures, cleanup-invalid
  trials, missing primary latencies, retries, and exclusions are zero.
- **CLI evidence:** 400 unique native CLI invocations including setup,
  verification, observability, readiness, planned operations, and cleanup;
  all 400 exited 0, all response validations passed, total stderr bytes are
  zero, and no sanitized argv item contains an unredacted auth token.
- **Resource evidence:** 686 correlated resource observations cover all trial
  windows. Required daemon CPU/RSS, host free-space, workspace logical size
  and file-count readings are present; sandbox/cgroup and upperdir fields are
  present where the product boundary exposes them. Unavailable readings are
  explicitly typed `unavailable`, never zero. The report contains the single
  standing limitation that fixed-boundary unavailable resources remain
  explicit, but contains no warning.
- **Raw corpus:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\.benchmark-state\results\019fb36f-b50f-73c3-a3b9-0d0f861cff9e`;
  827 observations, 1,170 events, 19 bounded operation-evidence envelopes,
  and 1,200 CLI stdout/stderr/metadata files.
- **Cleanup proof:** run workspace and runtime directory are absent; no
  run-labelled or campaign-gateway-labelled container or volume remains; no
  run-labelled product process remains; product checkout remains clean.
- **Immutable archive:** generated once with
  `experiments/scripts/archive_exp1_run.py` and independently verified again:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb36f-b50f-73c3-a3b9-0d0f861cff9e`.
  The archive contains 1,254 inventoried files and 18,597,095 inventoried
  bytes; deterministic content-tree SHA-256 is
  `5f1db2f535e74b434ab63196abbe947186089e4fb1f50587094e52dc711255af`.
  It includes the complete raw corpus, exact manifest/plan/report, fixture
  manifest, CLI help and hashes, resource-only projection, event log, cleanup
  proof, environment preflight, failure/unavailability disclosure, and a
  per-file hash manifest.
- **Eligibility:** smoke values are qualification evidence only and are
  ineligible for manuscript tables.
- **Disposition:** passed. Gate 2/EXP1-C is accepted; run the single
  exploratory `paper-pilot` next without builds, installs, pulls, source
  mutation, or environment reconfiguration during its clock.

### 2026-07-30T14:58:48Z - Smoke archive provenance finalization

- **Entry ID:** `archive-exp1-smoke-provenance-037`
- **Phase:** EXP1-C evidence handoff before pilot.
- **Kind:** amendment
- **Reason:** post-archive contract review found that the raw benchmark run
  manifest records product source/binaries, plan, fixture profile, definition
  snapshot, schemas, image, and environment, but does not explicitly identify
  the complete paper-local benchmark source tree. The task packet requires a
  benchmark identity/hash for every archived attempt.
- **Boundary:** no raw file, metric, result, timing, report, plan, fixture,
  CLI record, cleanup proof, or source file used by the smoke was changed.
  The preliminary archive content-tree hash from entry 036 is preserved in
  the final archive manifest as the superseded candidate hash.
- **Finalization:** the reusable archive script now creates
  `benchmark-source-manifest.json` and `campaign-manifest.json`. The benchmark
  inventory excludes only generated/cache directories and records all 187
  paper-local benchmark source files, 2,763,849 bytes, per-file hashes, and
  content-tree SHA-256
  `22023daa06e6d5f03423eae310e1f7ab136fbbd4fce6759f7320129ead54017f`.
  The campaign manifest also records the authoritative protocol files,
  analysis/archiving code, paper Git context, exact plan/definition/fixture/
  product/image identities, cleanup proof, and the raw-corpus content-tree
  SHA-256
  `d1d134bd80ccbe54c4f29d80c31e921fe0fa4dabac4343bef12cfdf44158ba78`.
- **Final archive:** 1,256 inventoried files, 18,639,493 inventoried bytes,
  content-tree SHA-256
  `c73094f43144f32160095b8a2bedf95571d78c39ded2b2bee671745dfc8c33c3`.
  A separate verify-only invocation recomputed the same file inventory,
  byte count, and content-tree hash.
- **Superseded candidate hash:**
  `5f1db2f535e74b434ab63196abbe947186089e4fb1f50587094e52dc711255af`.
- **Disposition:** archive contract passed. The finalized run directory is
  immutable from this point; Gate 2 remains passed.

### 2026-07-30T15:30:44Z - Exploratory pilot passed but runtime gate failed

- **Entry ID:** `pilot-exp1-cli-runtime-gate-038`
- **Phase:** EXP1-D exploratory pilot before freeze.
- **Kind:** pilot
- **Run ID:** `019fb38a-1b44-77e6-b78a-e52f70fc49a3`.
- **Exact command:** `.\.venv\Scripts\sandbox-benchmark.exe run
  --test-repository-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1
  --product-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox
  --product-bin-dir
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-8c79217e\bin
  --plan paper-pilot`, with `PYTHONDONTWRITEBYTECODE=1`.
- **Preflight:** product `main`
  `8c79217ee42de327f789696e61ce2b7164a4bf3c` clean; package and pinned image
  unchanged; `paper-pilot` runnable at hash
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  19 cells, 133 batches, 385 requests, `product_cli`, only `paper-100m`;
  584,023,482,368 bytes free; no campaign runtime/container/volume; finalized
  smoke archive independently reverified. No build, installation, pull,
  source mutation, or environment reconfiguration occurred during the clock.
- **Start/end/elapsed:** `2026-07-30T15:00:00.744923Z` to
  `2026-07-30T15:24:01.547559Z`; 1,440.802636 seconds (24.013377 minutes) by
  artifact timestamps. The outer command exited 0 after 1,525.9 seconds.
- **Acceptance checks:** completed with correctness `pass`. All 38 warmup
  batches and 95 exploratory measured trials completed; all 95 measured
  trials are reportable; all 240 measured checks passed; 385 unique planned
  requests completed. Product, correctness, infrastructure, cleanup-invalid,
  missing-primary-latency, warning, retry, and exclusion counts are zero.
- **CLI/resource evidence:** 2,413 unique native CLI invocations all exited 0
  and validated, with zero stderr bytes and no unredacted token. The corpus
  contains 5,831 observations (385 request, 4,844 resource, 336 check, 133
  operation, 133 trial) and 7,746 events. Resource unavailability remains
  explicit and the report has no warning.
- **Raw corpus:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\.benchmark-state\results\019fb38a-1b44-77e6-b78a-e52f70fc49a3`.
- **Cleanup:** run workspace and runtime directory absent; no matching product
  process or run/campaign-labelled Docker container/volume; product checkout
  remains clean.
- **Immutable exploratory archive:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb38a-1b44-77e6-b78a-e52f70fc49a3`;
  7,409 inventoried files, 98,249,024 inventoried bytes, content-tree SHA-256
  `28aaa47ae2bbec9c2e68b7d7cb8b4c340d83090440029c9fc12bed254b193bac`.
  Independent verify-only regeneration matched. Archive-manifest SHA-256 is
  `70dfe88e79d821f6f054c485929de855d3d1d006c49089accb3321ac995c7686`;
  campaign-manifest SHA-256 is
  `79a906a0b4084434f77478c8874c44a086c549d981c3b66a806c9c15b025e664`.
- **Runtime projection:** deterministic script
  `experiments/scripts/project_exp1_final_runtime.py` (SHA-256
  `88604b889bd480f52a886781bc1ece922a09fc267703dde00476f1a702ad52b6`)
  consumed only the immutable smoke/pilot archives and emitted
  `experiments/analysis/pilot-final-runtime-projection.json` (SHA-256
  `1609711e8e0306982cf69f12a39586e2525847fcf2e7d58b8c35c900e925a008`).
  The final fixed plan is 1,938 batches/5,610 requests. The pilot elapsed time
  itself is a monotonic superset lower bound of 1,440.802636 seconds; an
  optimistic affine model credits 903.857667 seconds as fixed setup and scales
  only the observed 4.037180 seconds per additional batch, projecting
  8,727.912932 seconds (145.465216 minutes). Direct batch-proportional scaling
  projects 20,994.552696 seconds.
- **Gate decision:** the protocol limit is 1,200 seconds. Gate 3 runtime
  acceptance fails under the lower bound and both projections. Per the task
  packet, freeze and `paper-good-pass` are blocked; no final run was issued.
- **Eligibility:** all pilot and projection values are exploratory capacity
  evidence only and are ineligible for manuscript tables.
- **Next action:** complete read-only timing, harness, and product-root-cause
  audits. Continue only if they demonstrate a semantics-preserving pre-freeze
  defect correction that can plausibly satisfy the fixed 20-minute gate;
  otherwise stop with the runtime gate as the exact blocker.

### 2026-07-30T16:15:19Z - Pilot defect correction and create-path optimization

- **Entry ID:** `pilot-exp1-cli-corrections-039`.
- **Phase:** EXP1-D pilot review and pre-freeze defect correction.
- **Kind:** amendment.
- **Trigger:** exploratory pilot
  `019fb38a-1b44-77e6-b78a-e52f70fc49a3` passed correctness and cleanup but
  took 1,440.802636 seconds and failed the 1,200-second final-runtime
  projection gate. No final-eligible run was issued.
- **Read-only timing audit:** 25 pilot `create_sandbox` CLI invocations consumed
  910.049 seconds (36.402-second mean; 32.592-second median). Eighteen untimed
  per-cell creates consumed 662.944 seconds. The seven sandbox-create trials
  consumed 247.106 seconds. Pilot cell intervals decomposed to 837.005 seconds
  preparation, 530.170 seconds running, and 73.628 seconds family
  gateway/finalization residual.
- **Demonstrated product defect:** shared-base lookup copied and hashed the
  complete 100 MiB/4,000-file workspace into a 13,619-entry temporary tree
  before discovering an existing content-addressed cache entry, then deleted
  that tree. The exact paper fixture cache hit took 16.281615 seconds.
- **Product correction:** clean `main` commit
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3`
  (`perf(layerstack): reuse validated shared bases`) hashes the source and
  candidate cached layer read-only, reuses only an intact exact-root match,
  and fails closed without mutation on missing or corrupt cached content. The
  same validation applies to ordinary and race-reuse paths. Changed content
  still builds a new immutable base.
- **Product microbenchmark:** exact integrity-checked hit 1.055585 seconds
  versus 16.281615 seconds before (15.424x; 93.517% reduction); cold build
  2.870520 seconds; root hash unchanged at
  `93233d2d9deb96b1dc1701079a1ec01b658e3e26bdf35ff2d17cc0114acc3769`.
  These are diagnostic pre-freeze values, not manuscript results.
- **Product validation:** LayerStack 46 passed/1 ignored; Docker provider 17
  passed/1 ignored; manager core 18 passed; manager library passed; affected
  crate clippy targets passed with warnings denied; `git diff --check` passed.
  Broad Windows manager all-target clippy remains unavailable because
  pre-existing `manager_export.rs` test code unconditionally imports
  `std::os::unix`.
- **Docker lifecycle audit:** direct exact Docker creates with the populated
  shared volume were 0.138--0.150 seconds; 30 create/start/remove cycles stayed
  at 0.128--0.209 seconds create and 0.840--0.953 seconds start; 25 isolated
  full product cycles stayed at 1.212--1.759 seconds create. In contrast, 21
  later pilot-topology Docker create calls were 8.112--16.295 seconds
  (12.625-second mean). No provider, Bollard, resource-setting, stats-sampler,
  or shared-volume defect reproduced, so no speculative lifecycle change was
  made.
- **Harness corrections:** fixed-deadline 100 ms sampling now permits one
  expensive collection in flight and emits explicit unavailable records for
  every saturated deadline; samples retain scheduled, collection-start, and
  collection-completion offsets and persist in order at the trial boundary.
  Batch journal writes use one append/fsync per record batch. Waiting and
  ready-at-barrier intent is durable before release; makespan is the real
  barrier-release-to-last-validated-response interval and excludes event/CLI
  evidence persistence. File-write content is created and fsynced before
  barrier admission and removed on every exit path.
- **Scheduling decision:** current seeded cell permutation within persisted
  sequential family execution blocks is preserved and documented. The packet
  does not unambiguously require repetition-level re-randomization, which
  would change simultaneous prepared-sandbox load; no post-result scheduling
  change was made.
- **Harness validation:** 58 focused tests passed; full backend 161 passed/4
  skipped in 36.22 seconds. Skips are only Windows WinError 1314 symlink
  privilege. All plan identities and counts are unchanged: smoke
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  (19/19/55), pilot
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  (19/133/385), final
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  (19/1,938/5,610).
- **Rebuilt package:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5751f196`
  and `.zip`; archive 5,607,118 bytes, SHA-256
  `5dbb8cc6f514686987ed63d29342801812201f99496c9015ab3a5384c93c9a9b`.
  Gateway SHA-256
  `1da424822b129d82c4a3425ae1840a70e2e2abbc727ebb3b7c9571cb2de75ff0`;
  manager
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`;
  runtime
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`;
  observability
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`;
  daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`.
- **Failures/anomalies/unavailability:** resource collectors slower than 100 ms
  cannot yield an available reading at every deadline without perturbing the
  primary workload; missed ticks are now explicit rather than silently late.
  Pilot-topology Docker create slowdown remains unexplained and unreproduced
  in isolated diagnostics. Permission bits remain outside the inherited
  shared-base root-hash schema; concurrent source mutation after validation is
  an inherited TOCTOU limitation.
- **Cleanup:** all owned diagnostic gateways, containers, volumes, processes,
  temporary sources, and directories were removed. The unrelated pre-existing
  debug gateway PID 62980 was not touched. Product `main` is clean at the new
  commit.
- **Eligibility:** audit, microbenchmark, and prior pilot values remain
  exploratory and ineligible for paper tables.
- **Disposition:** pre-freeze defects corrected and package rebuilt. A strict
  package preflight and new smoke are required before deciding whether one
  post-correction exploratory pilot is justified. Freeze and final remain
  blocked until Gate 3 demonstrates a <=20-minute final projection.

### 2026-07-30T16:32:50Z - Post-correction product-CLI smoke

- **Entry ID:** `smoke-exp1-cli-post-correction-040`.
- **Phase:** EXP1-C requalification after pre-freeze defect correction.
- **Kind:** smoke.
- **Run ID:** `019fb3d1-3735-7170-bf0d-3e83764096e9`.
- **Exact command:** `.\.venv\Scripts\sandbox-benchmark.exe run
  --test-repository-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1
  --product-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox
  --product-bin-dir
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5751f196\bin
  --plan paper-env-smoke`, with `PYTHONDONTWRITEBYTECODE=1`.
- **Preflight:** product `main`
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3` clean; rebuilt package and
  pinned image exact; smoke plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  19 cells, 19 batches, 55 requests, `product_cli`, only `paper-100m`; no
  campaign process, runtime, container, or volume before launch. No build,
  installation, pull, source mutation, or environment reconfiguration
  occurred during the clock.
- **Start/end/elapsed:** `2026-07-30T16:17:40.975089Z` to
  `2026-07-30T16:27:03.258882Z`; 562.283793 seconds (9.371397 minutes) by
  artifact timestamps.
- **Acceptance checks:** completed with correctness `pass`. All 19 measured
  trials are reportable, all 48 measured checks passed, all 55 planned
  requests completed, and product, correctness, infrastructure,
  cleanup-invalid, missing-primary-latency, warning, retry, and exclusion
  counts are zero.
- **CLI/resource evidence:** 316 unique native CLI invocations all exited 0
  and validated, with zero stderr bytes and passed token redaction. The corpus
  contains 1,317 observations: 55 request, 1,176 resource, 48 check, 19
  operation, and 19 trial records. Saturated or inapplicable resource
  readings remain correlated and explicitly unavailable rather than encoded
  as zero; the report has no warning.
- **Performance qualification:** the measured cold `create_sandbox` trial
  took 48.114 seconds. Three additional cold family setup creates took
  46.845--47.692 seconds; the 15 cache-hit setup creates took
  2.818--2.988 seconds. The shared-base correction therefore reproduced
  under the complete campaign topology. Smoke timings remain qualification
  evidence only.
- **Cleanup:** run workspace and runtime directory absent; no matching
  campaign product process or run/campaign-labelled Docker container/volume;
  product checkout remains clean at the recorded commit.
- **Immutable smoke archive:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb3d1-3735-7170-bf0d-3e83764096e9`;
  1,004 inventoried files, 20,930,702 inventoried bytes, content-tree SHA-256
  `238803fe0c33e4c397d2d6c8e52e651b08ea308472205de80402f26ecd456fd0`.
  Independent verify-only regeneration matched. Archive-manifest SHA-256 is
  `0bc9ae261b9a230316213eb59d7fe6c0996663ef20d7a2b85f6b70ef35b55d0b`;
  campaign-manifest SHA-256 is
  `9994eef3d47300d12253079b033bf1bde5acf8566659625cb5b607d500e00a90`.
  The archived benchmark-source tree contains 188 files, 16,012,064 bytes,
  with content-tree SHA-256
  `620e9b74941a46373f403d0fb2b134281132d4fc797947a2f88b0eccb6074039`.
- **Eligibility:** smoke values are qualification evidence only and are
  ineligible for manuscript tables.
- **Disposition:** passed. The pre-freeze correction is requalified and one
  post-correction exploratory `paper-pilot` is justified. Freeze and final
  remain blocked until that pilot demonstrates the fixed <=20-minute final
  projection gate.

### 2026-07-30T17:01:46Z - Post-correction pilot exposed Gate 3 blockers

- **Entry ID:** `pilot-exp1-cli-post-correction-041`.
- **Phase:** EXP1-D exploratory pilot before freeze.
- **Kind:** pilot.
- **Run ID:** `019fb3e0-62d5-7c5d-9846-1a3b2402c0b9`.
- **Exact command:** `.\.venv\Scripts\sandbox-benchmark.exe run
  --test-repository-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1
  --product-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox
  --product-bin-dir
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5751f196\bin
  --plan paper-pilot`, with `PYTHONDONTWRITEBYTECODE=1`.
- **Preflight:** recovery found no run; product `main`
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3` clean; rebuilt package SHA-256
  `5dbb8cc6f514686987ed63d29342801812201f99496c9015ab3a5384c93c9a9b`;
  pinned local image exact; `paper-pilot` runnable at
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  19 cells, 133 batches, 385 requests, `product_cli`, only `paper-100m`;
  578,394,980,352 bytes free; no campaign process, runtime, container, or
  volume. No build, installation, pull, source mutation, or environment
  reconfiguration occurred during the clock.
- **Start/end/elapsed:** `2026-07-30T16:34:15.168559Z` to
  `2026-07-30T16:45:44.195423Z`; 689.026864 seconds (11.483781 minutes) by
  artifact timestamps.
- **Correctness and cleanup:** completed with correctness `pass`. All 38
  warmup batches and 95 exploratory measured trials completed; all 95
  measured trials are reportable; all 336 observed checks, including all 240
  measured checks, passed; all 385 planned requests completed. Product,
  correctness, infrastructure, cleanup-invalid, missing-primary-latency,
  warning, retry, and exclusion counts are zero. Run workspace and runtime
  directory are absent; no matching product process or run/campaign-labelled
  Docker container/volume remains; product checkout is unchanged and clean.
- **CLI evidence:** 1,819 unique native CLI invocations all exited 0 and
  validated, with zero stderr bytes and passed token redaction. The corpus
  contains 9,149 observations: 385 request, 8,162 resource, 336 check, 133
  operation, and 133 trial records.
- **Immutable exploratory archive:**
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb3e0-62d5-7c5d-9846-1a3b2402c0b9`;
  5,627 inventoried files, 111,574,583 inventoried bytes, content-tree SHA-256
  `576be9a442ff52767b8923d1f79d4cb4dc06d6bd4616a0a311f831b8cbe19fae`.
  Independent verify-only regeneration matched. Archive-manifest SHA-256 is
  `e5db177f138052b3c4c9532255aecf01055abc266bf5d07028fd975f3d03cb46`;
  campaign-manifest SHA-256 is
  `4c0d4bc79e7ff831ac81be41946b07d7c1c09b9493ccd13469531beadf7a3987`.
- **Runtime projection:** deterministic script
  `experiments/scripts/project_exp1_final_runtime.py` (SHA-256
  `88604b889bd480f52a886781bc1ece922a09fc267703dde00476f1a702ad52b6`)
  consumed only the matching immutable post-correction smoke/pilot archives
  and emitted
  `experiments/analysis/pilot-final-runtime-projection-postfix.json`
  (SHA-256
  `84ced6c0e065f408f900be3401a9f5c480c88cb2a1bd44fdb1e1fdb5910a509e`).
  The optimistic affine model estimates 541.159948 fixed seconds and
  1.111781 seconds per additional batch, projecting 2,695.792155 seconds
  (44.929869 minutes). Direct batch-proportional scaling projects
  10,040.105733 seconds. Both exceed the fixed 1,200-second limit.
- **Resource blocker:** the 583 scheduled sample sets contain only 148 actual
  collections and 435 explicit concurrency-cap misses. Of 133 trials, 119
  have only one actual collection. Consequently all 95 measured trials lack
  derived daemon CPU, sandbox CPU, block-read, and block-write deltas;
  workspace allocated bytes are also unavailable for all 95, and every
  CPU/latency correlation has support zero. Explicit unavailability is
  honest, but the packet's missing-or-uncorrelated-resource stop condition is
  met.
- **Determinism blocker:** rebuilding the report twice from the immutable raw
  observations produced identical canonical SHA-256
  `ad45938141e4a9dc02d1c21fd1ee3cad413e962713d50d77d1187b7f3d909b84`
  and matched the archived report data exactly. However, no four-table
  generator or table output exists, so EXP1-D's deterministic table
  regeneration item is not yet satisfied.
- **Read-only bottleneck audit:** cell preparation is 383.886 seconds, trial
  spans 210.070 seconds, cell-running gaps 17.777 seconds, and other
  family/report work 77.294 seconds. Four block-first base-seeding creates
  consume 185.806 seconds; the other 21 creates consume 53.740 seconds.
  The old Docker API step-up did not recur: all 25 product container-create
  API calls are 0.074906--0.101575 seconds. Per measured 19-cell round,
  23.258 seconds elapse while only a small minority is primary operation
  time; resource collection and independent correctness/setup/cleanup dominate
  the scalable remainder.
- **Gate decision:** Gate 3 fails independently on runtime projection,
  resource correlation, and the absent table generator. Per the task packet,
  no protocol freeze, tag, or `paper-good-pass` was issued.
- **Eligibility:** every pilot, bottleneck, resource, and projection value is
  exploratory capacity/instrumentation evidence only and is ineligible for
  manuscript tables.
- **Next action:** correct the demonstrated resource-window defect without
  changing primary timing, add the deterministic table/provenance generator,
  optimize only independent untimed verification/setup/cleanup work, rerun
  deterministic validation and a qualification smoke, and issue another
  exploratory pilot only if those corrections plausibly satisfy all Gate 3
  requirements.

### 2026-07-30T17:15:11.872Z - Pre-freeze resource-window correction validation

- **Entry ID:** `exp1-pre-freeze-resource-window-correction-20260730`
- **Phase:** EXP1-D defect correction before protocol freeze.
- **Kind:** amendment and deterministic validation; no live benchmark run.
- **Reason:** the exploratory pilot demonstrated that repeated 4,000-file
  resource walks made most scheduled samples miss their deadlines, left most
  trials with only one actual collection, and allowed resource collection to
  extend into correctness verification.
- **Scoped correction:** immutable host-workspace tree metrics are cached per
  resolved campaign path; runner RSS and host free space remain dynamically
  sampled. Non-create trials now await a completed pre-barrier baseline and
  stop immediately after validated product responses, serializing any active
  periodic collector before exactly one completed boundary collection. The
  fixed one-expensive-collector cap and explicit scheduled saturation records
  remain unchanged. Because no sandbox-scoped pre-create baseline can exist,
  `create_sandbox` daemon/sandbox counter deltas are explicitly inapplicable;
  post-create gauges remain eligible.
- **Safe untimed parallelism:** independent-path correctness reads and
  attribution checks may run concurrently only after resource sampling stops;
  independent `create_workspace` session destroys run concurrently and all
  complete before sandbox destruction. Setup publication remains sequential.
- **Files changed:**
  `benchmark/backend/benchmark_lab/resource_sampling.py`,
  `benchmark/backend/benchmark_lab/runner.py`,
  `benchmark/backend/tests/unit/test_resource_sampling.py`, and
  `benchmark/backend/tests/integration/test_runner.py`.
- **Protocol effect:** no cell, trial, request, exclusion, primary-latency,
  barrier, makespan, throughput, retry, or reportability rule changed.
  Prior exploratory values remain ineligible and are not reinterpreted.
- **Exact focused command:** `$env:PYTHONDONTWRITEBYTECODE='1';
  & .\.venv\Scripts\python.exe -m pytest
  benchmark\backend\tests\unit\test_resource_sampling.py
  benchmark\backend\tests\integration\test_runner.py -q`
- **Focused result:** exit `0`; `25 passed`.
- **Exact full command:** `$env:PYTHONDONTWRITEBYTECODE='1';
  & .\.venv\Scripts\python.exe -m pytest .\benchmark\backend\tests`
- **Full result:** exit `0`; `176 passed`, `5 skipped` because Windows symbolic
  link privilege is unavailable.
- **Product state observed after validation:** clean `main` at
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3`; no product source was changed by
  this correction.
- **Cleanup/result artifacts:** no gateway, sandbox, image, build, smoke,
  pilot, or final preset was started; no run ID or measurement artifact was
  created.
- **Disposition:** code validation passed; Gate 3 remains failed until all
  independent blockers are corrected and a permitted exploratory rerun passes.
- **Unsafe interpretation:** unit/integration success does not establish live
  resource availability, a passing runtime projection, or final evidence.
- **Next action:** complete the other demonstrated pre-freeze corrections,
  review the combined diff, then run only the next protocol-permitted
  qualification smoke/pilot sequence.

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

### 2026-07-30T17:31:12Z - Pre-freeze fixture materialization acceleration

- **Entry ID:** `amendment-exp1-fixture-copy-042`.
- **Phase:** EXP1-D pilot review and pre-freeze defect correction.
- **Kind:** amendment and deterministic validation.
- **Trigger:** the retained post-correction pilot attributed 202.024 seconds
  across 19 cells to independent fixture materialization. The existing Python
  path sequentially traversed 9,618 directories and copied 4,001 files /
  104,858,177 bytes, including the versioned manifest, for every cell.
- **Read-only audit:** a disposable non-live NTFS benchmark measured the
  inherited sequential copy at 9.038698 seconds, a 32-worker Python copy at
  7.415077 seconds, and native Robocopy `/MT:32` at 3.763499 seconds. Every
  candidate had the same 4,001 files, byte count, and independently recomputed
  content digest
  `20ade0739acb398399ff944dc01ea390d346552a84a5b76465e8861634a78710`.
- **Safety decision:** hardlinks were rejected because a cell write would
  mutate the shared NTFS file record; symlinks and junctions were rejected
  because they retain shared-cache mutation authority; and reflink/block clone
  was rejected because the qualified NTFS host exposes no supported
  copy-on-write clone primitive. The implementation creates ordinary
  independent files only.
- **Harness correction:** the cached fixture now receives a full
  reparse/plain-entry, layout, manifest, and exact tree-hash validation before
  its first process-local reuse. The retained cache key includes the canonical
  path, fixture/tree hashes, raw manifest SHA-256 plus file identity, and every
  file's relative path, size, modification time, and file identity. Every
  materialization revalidates that metadata before and after copying and fails
  closed on drift.
- **Windows copy path:** the benchmark invokes the absolute System32
  `robocopy.exe` through an argument array with no shell and options
  `/E /COPY:D /DCOPY:D /R:0 /W:0 /MT:32 /XJ`; file/directory listings are
  suppressed while the bounded process summary remains required. Exit codes
  0--7 are accepted; missing process output, missing/changed destination
  files, source drift, timeout/execution failure, and exit codes 8 or greater
  fail closed. Non-Windows hosts retain validated `shutil.copyfile` copies.
- **End-to-end disposable benchmark:** in a fresh Python process against the
  exact cached `paper-100m` fixture, the first complete materialization took
  8.716363 seconds including the full source tree-hash gate; the second took
  5.355070 seconds including all per-copy validation. Fixture identity remained
  `sha256:9484b132c8a35afd18bc37383759d0fe6d45dd4700b42a99336aed535e651cc7`
  and tree hash remained
  `sha256:d4c2fefbf94a30352f39d701ececaeeb8fad35603e4fb721dd5cf21296258c9f`.
  Applied to 19 materializations, this diagnostic projects 105.107617 seconds
  versus the 171.735262-second sequential-copy baseline, a fixed saving of
  66.627645 seconds (38.797%). These values are pre-freeze diagnostics and are
  ineligible for manuscript tables.
- **Attempts/anomalies:** the first real test used extended-length `\\?\`
  roots as Robocopy arguments and failed closed with exit code 16; ordinary
  absolute roots were then used because Robocopy itself handles the deep
  descendants. An initial per-cell full destination rehash was correct but
  took 48.663222 seconds before parallelization and then 11.046363 seconds;
  it was replaced by the once-per-process source hash gate plus per-copy
  metadata/content-identity checks described above. One concise PowerShell
  projection command had a parser error and was immediately repeated with a
  stored result collection. No live gateway, sandbox, Docker object, or
  performance preset was involved in any attempt.
- **Focused verification:** fixture tests exited 0 with 15 passes and one
  Windows WinError 1314 symlink-privilege skip.
- **Complete backend verification:** with
  `PYTHONDONTWRITEBYTECODE=1`,
  `.\.venv\Scripts\python.exe -m pytest .\benchmark\backend\tests -q`
  exited 0 with 184 passes and five WinError 1314 symlink-privilege skips in
  40.36 seconds.
- **Plan stability:** all presets remain runnable with zero findings and
  unchanged identities/counts: smoke
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  (19/19/55), pilot
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  (19/133/385), and final
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  (19/1,938/5,610).
- **Files changed:** `benchmark/backend/benchmark_lab/fixtures.py`,
  `benchmark/backend/tests/unit/test_fixtures.py`,
  `benchmark/PAPER_ARTIFACT.md`, and this append-only log.
- **Cleanup:** every disposable copy root was verified beneath the system temp
  directory and removed; no temporary root remains. The shared fixture cache
  was read-only throughout.
- **Disposition:** implementation and deterministic validation passed. This
  removes only part of the demonstrated fixed setup cost; Gate 3 remains
  blocked by the separately recorded resource-correlation and deterministic
  table-generation defects and still requires a fresh qualification decision
  before any further exploratory pilot.

### 2026-07-30T17:52:41.474Z - Combined pre-freeze qualification validation

- **Entry ID:** `exp1-pre-freeze-combined-validation-043`.
- **Phase:** EXP1-D qualification before a fresh smoke/pilot decision.
- **Kind:** amendment review and deterministic validation; no live benchmark
  run.
- **Product state:** clean `main` at
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3`, three local commits ahead of
  `origin/main`; `paper-v1-freeze` does not yet exist.
- **Run-start provenance correction:** each paper preset now captures and
  validates the exact Windows host and released sandbox resource limit
  authority before starting a gateway or measurement. A real capture passed
  for Windows 11 version `10.0.26200`, build `26200`, host
  `DESKTOP-OLP1ADS`, AMD Ryzen Threadripper 7960X 24-Cores, 48 logical
  processors, 137,438,953,472 bytes of memory, and NTFS `C:\`. The selected
  released configuration is
  `target/windows-exp1-5751f196/config/windows-amd64.yml`, SHA-256
  `27bee7e26d1d345f08e3842536c2051328d70b89eec75b60ba4c97419d39ae8e`,
  with profile `standard`, 1,000,000,000 nano-CPUs / one vCPU,
  536,870,912 memory bytes, 256 PIDs, and no create-request override.
- **Treatment identity rechecked:** source commit
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3`, source clean; daemon
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`,
  gateway
  `1da424822b129d82c4a3425ae1840a70e2e2abbc727ebb3b7c9571cb2de75ff0`,
  manager CLI
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`,
  runtime CLI
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`,
  and observability CLI
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`.
  The Ubuntu 24.04 image resolved to the required digest
  `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`.
- **Resource semantic correction:** mutable workspace allocation is now the
  signed boundary delta of product-observed live-session
  `upperdir_bytes`, sourced from
  `product_observability.snapshot.workspaces.disk_allocated_bytes.sum`,
  scoped to the workspace. It is not inferred from the immutable host NTFS
  fixture. Immutable fixture allocation remains separately recorded and may
  be explicitly unavailable on Windows. Monotonic counter reset rejection is
  unchanged; only a gauge delta may be signed.
- **Archival/freeze correction:** the archiver now preserves and verifies the
  run-start host and limit evidence, inventories the table generator, excludes
  only enumerated generated Python cache artifacts when checking the frozen
  paper source scope, and requires an annotated product-repository
  `paper-v1-freeze` tag whose peeled commit equals the recorded product
  commit for a final archive. Existing cache artifacts were preserved.
- **Deterministic table generator:** the new archive-only generator emits all
  four packet schemas, `tables.json`, a strict
  `ai-research-writing/numeric-evidence-v2` registry,
  `numeric-provenance.csv`, a generation log, and an output manifest. It uses
  linear `(n-1)q` p50/p95/p99 quantiles and arithmetic-mean throughput. A
  retained exploratory pilot generated nine byte-identical outputs in two
  independent new directories; the strict registry loader recomputed all 120
  entries successfully. The output is explicitly
  `exploratory_ineligible`.
- **Legacy archive boundary:** the corrected verifier intentionally rejects
  retained pilot `019fb3e0-62d5-7c5d-9846-1a3b2402c0b9` with
  `recorded run environment lacks final-host or sandbox-limit evidence`.
  The immutable archive was not modified or reclassified.
- **Plan validation:** all three plans are runnable, use `product_cli`,
  select `paper-100m`, have zero warnings/findings, and retain exact identities
  and counts: smoke
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  (19 cells / 19 batches / 55 requests), pilot
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  (19 / 133 / 385), and final
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  (19 / 1,938 / 5,610).
- **Complete validation:** backend tests exited 0 with 190 passes and five
  expected Windows symlink-privilege skips; analysis tests exited 0 with 12
  passes; the combined analysis/archive focused run exited 0 with 19 passes;
  web unit tests exited 0 with 43 passes in ten files; the production web
  build exited 0. Ruff check and format-check passed for the new generator,
  its tests, and the archive script after mechanical formatting, import
  ordering, use of `capture_output`, and marking an intentionally unused
  unpacked report.
- **Attempts/anomalies:** an initial pytest path selected zero tests and was
  corrected to the project `backend/tests` path. The host `.venv` did not have
  Ruff installed, so the pinned `uv run --project benchmark --with ruff`
  invocation was used. A broad Ruff command exposed pre-existing style debt
  outside the newly created analysis/archive files; it was not used to rewrite
  unrelated campaign code. PowerShell blocked the `npm.ps1` shim under the
  host execution policy, after which identical package scripts passed via
  `npm.cmd`. An earlier `sandbox-benchmark plan --help` attempt used a
  nonexistent subcommand; supported `validate`, `run`, `recover`, and
  `cleanup` commands were used thereafter. A request to remove disposable
  generator directories was rejected by the command policy, so none was
  deleted; they remain outside the frozen source and archive scopes.
- **Cleanup/result artifacts:** no gateway, sandbox, image pull, package
  build, smoke, pilot, or final preset was started by this entry. Generator
  outputs are disposable validation artifacts outside the immutable run
  archives.
- **Disposition:** combined code and deterministic qualification validation
  passed. The prior implementation blockers are corrected, but Gate 3 remains
  empirically open until a fresh smoke and exploratory pilot demonstrate live
  correctness, resource-boundary availability/correlation, cleanup, and a
  projected final duration of at most 1,200 seconds.
- **Unsafe interpretation:** these code tests and retained-corpus regeneration
  do not establish final performance or repair missing provenance in an older
  archive.
- **Next action:** run strict preflight, then one fresh qualification smoke and
  one fresh exploratory pilot; freeze only if every Gate 3 item passes.

### 2026-07-30T18:15:23.025Z - Terminal workspace recovery amendment

- **Entry ID:** `exp1-terminal-workspace-recovery-044`.
- **Phase:** EXP1-D qualification blocker correction; no live benchmark run.
- **Observed failure:** run
  `019fb15d-b8b6-7126-9ecd-637fe75b8e27` had already persisted a terminal
  `failed` manifest with `artifact_finalization_failed` after report
  finalization, but its exact `runs` ownership marker remained after workspace
  removal was interrupted. `recover` ignored every terminal manifest and
  explicit `cleanup` recovered only `runtime`, so the owned disposable
  workspace remained.
- **Read-only state audit:** the stranded finalization-failure workspace was
  distinguished from eight existing terminal `campaign_failed` workspaces.
  Every inspected workspace carried an exact run identity; no workspace was
  removed during this amendment.
- **Correction:** automatic recovery now removes exact owned `runs`/`runtime`
  residue for `completed`, `cancelled`, or
  `failed:artifact_finalization_failed` manifests. It continues to retain
  ordinary `campaign_failed` workspaces for diagnosis. Explicit cleanup may
  remove the exact owned residue for any terminal run. All present roles are
  adopted and validated before mutation; marker mismatch, symlink escape,
  role-root escape, or device-boundary violation fails closed. Immutable
  result artifacts and unrelated owned workspaces are never deletion targets.
- **Files changed:**
  `benchmark/backend/benchmark_lab/recovery.py`,
  `benchmark/backend/benchmark_lab/service.py`,
  `benchmark/backend/tests/integration/test_recovery.py`,
  `benchmark/backend/tests/contract/test_api.py`, and this append-only log.
- **Validation:** the focused recovery/service suite passed 24 tests. The full
  backend suite passed 196 tests with five expected Windows
  symlink-privilege skips. Regression coverage proves automatic recovery,
  explicit cleanup, exact marker mismatch refusal, byte-identical preservation
  of terminal manifest/report artifacts, preservation of an unrelated exact
  owned workspace, and continued automatic retention of a normal failed
  diagnostic workspace. Targeted Ruff fatal/import checks and `git diff
  --check` passed; pre-existing broad style debt was not rewritten.
- **Disposition:** harness correction passed deterministic validation. The
  stranded real workspace remains available for the root campaign controller
  to remove through the now-corrected cleanup/recovery command before the next
  strict preflight.

### 2026-07-30T18:26:57.238Z - Fresh-smoke resource-boundary amendment

- **Entry ID:** `exp1-fresh-smoke-resource-boundary-045`.
- **Phase:** EXP1-C/EXP1-D qualification blocker diagnosis and pre-freeze
  instrumentation correction; no live benchmark run.
- **Retained evidence:** immutable smoke archive
  `experiments/runs/019fb429-b255-70ae-91d6-5bdf4151a4c8` passed operation
  correctness and cleanup but exposed incomplete resource boundaries. Across
  its retained observations, `sandbox_cpu_time_ns`,
  `sandbox_block_read_bytes`, and `sandbox_block_write_bytes` each had 16
  unavailable non-create observations with reason
  `resource ring is not available yet`, plus two deliberately inapplicable
  create-sandbox observations. `upperdir_bytes` had 32 unavailable
  observations with reason
  `workspace upperdir allocation was not completely reported`. The archive
  was not modified or reclassified.
- **Exact diagnosis:** affected cgroup CLI responses were valid partial views
  with an empty `series`; affected snapshot CLI responses already listed the
  live workspace but had `workspace.resources.latest=null`. Product-source
  review found two independent two-second periodic samplers: the manager
  Docker cgroup ring used a hard-coded
  `RESOURCE_SAMPLE_INTERVAL = Duration::from_secs(2)`, while daemon workspace
  resource sampling used the default
  `observability.resource_stats.sample_interval_ms: 2000`. Immediate
  pre/post queries therefore observed startup races rather than legitimate
  zero values.
- **Harness correction:** every reportable non-create trial now holds the
  pre-operation barrier until product observability returns a complete cgroup
  counter baseline and complete upperdir allocation for every live workspace.
  After all measured CLI responses exit and validate, but before journal
  persistence, verification, or teardown, the sampler waits for cgroup and
  workspace sample timestamps strictly newer than that baseline. Polling is
  bounded to five seconds at 50-millisecond intervals. Only the ready boundary
  enters the resource series; discarded transient queries retain their normal
  sanitized CLI subprocess metadata. Unexpected partial responses, missing
  counter fields, truncation, or timeout fail closed rather than being
  converted to zero.
- **Workspace-create correction:** the runner passes the planned
  `workspace_count` to the sampler. Its baseline must contain no live
  workspaces, and its post-response boundary is not accepted until exactly the
  planned number of created workspaces have complete, post-baseline resource
  samples. A newer cgroup sample alone is insufficient.
- **Timing/protocol boundary:** readiness polling is untimed setup or
  post-response instrumentation. It does not move the native CLI subprocess
  launch-to-validated-response primary clock, alter the operation barrier,
  retry an operation, change a cell, change a trial count, or change a metric
  definition. Periodic 100-millisecond benchmark sampling remains unchanged.
- **Product cadence correction observed:** product `main` is clean at
  `31b1031f2ddc9fc4c702bdc15b7c2743288832eb` and passes the configured
  250-millisecond resource cadence to the manager sampler. Package
  `target/windows-exp1-31b1031f` uses configuration SHA-256
  `914d68807d97124a8412963d6f17e7a3914514bb0f0d210ea101ae52ba0ef512`,
  gateway SHA-256
  `cb36cc7c1ffba5f97a8216e30d6fb8213d04581c100bd097739981fe4bc0b463`,
  unchanged manager/runtime/observability CLI SHA-256 values
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`,
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`,
  and
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`,
  unchanged daemon SHA-256
  `a55d4775b992c02d603ca294746fb314e99d59774732ab7b8e7bf24ef010fb22`,
  and archive SHA-256
  `6451e2b72e92a99d5f359ab3d3ff247a0a6aeed80011c99cfb9fd320dfd739ca`.
- **Validation:** focused resource/runner tests exited 0 with 31 passes. The
  complete backend suite exited 0 with 201 passes and five expected Windows
  symlink-privilege skips in 46.60 seconds. Targeted Ruff import sorting
  passed; a targeted fatal/style run passed while ignoring only the already
  documented broad-file debt `BLE001`, `F821`, `F401`, and `S110`.
  `git diff --check` reported no content errors and only the repository's
  existing line-ending warnings.
- **Plan stability:** validation against
  `target/windows-exp1-31b1031f/bin` exited 0 for all presets with zero
  findings. Identities and counts are unchanged: smoke
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  (19/19/55), pilot
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  (19/133/385), and final
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  (19/1,938/5,610).
- **Attempts/anomalies:** the first package hash query used two incorrect
  daemon paths under `bin` and emitted read-only `Resolve-Path` errors. A
  recursive filename inspection found the packaged daemon at
  `dist/sandbox-daemon-linux-amd64`; its hash matched the prior treatment.
  No file was changed by those failed queries.
- **Files changed:**
  `benchmark/backend/benchmark_lab/resource_sampling.py`,
  `benchmark/backend/benchmark_lab/runner.py`,
  `benchmark/backend/tests/unit/test_resource_sampling.py`,
  `benchmark/backend/tests/integration/test_runner.py`, and this append-only
  log.
- **Disposition:** deterministic correction and validation passed. The prior
  code-level resource-boundary blocker is cleared; Gate 3 remains empirically
  open until a fresh smoke demonstrates complete first/last cgroup and
  workspace boundaries with the 250-millisecond treatment, followed by a
  qualifying exploratory pilot.

### 2026-07-30T18:28:34.154Z - Qualification smoke invalidation and resource-cadence product amendment

- **Entry ID:** `exp1-smoke-invalidation-product-cadence-046`.
- **Phase:** EXP1-C requalification and pre-freeze product amendment.
- **Invalidated smoke:** run `019fb429-b255-70ae-91d6-5bdf4151a4c8`
  used clean product `main` at
  `5751f196556fe837a0cb56c1c4cdba398cd38fc3` and package
  `target/windows-exp1-5751f196`. It ran `paper-env-smoke` through
  `product_cli` at unchanged plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  with 19 cells, 19 measured trials, and 55 requests.
- **Start/end/elapsed:** `2026-07-30T17:54:22.157355Z` to
  `2026-07-30T18:02:16.748616Z`; 474.591261 seconds by artifact
  timestamps. Correctness passed, all 19 trials were reportable, and the
  report recorded zero warnings.
- **Resource blocker:** non-create cgroup CPU/I/O counters and workspace
  upperdir allocation were not fully available at the trial boundaries.
  These missing readings are preserved as unavailable, never as zero. The
  exact diagnosis and harness correction are recorded in Entry 045.
- **Observer and cleanup anomalies:** the initial shell invocation timed out
  while the benchmark CLI continued detached. During setup, a recursive
  read-only filesystem listing traversed the generated fixture tree. After
  `report_ready`, two exact wrapper processes were terminated before the
  ownership ledger had finished its deep workspace removal, interrupting
  normal cleanup. The exact marker-validated run workspace was subsequently
  removed through `OwnershipLedger.adopt/remove`; the cleanup archive then
  verified. These actions do not change primary per-operation clocks, but
  they make this qualification attempt unsuitable for pairing with a pilot.
- **Immutable archive:** the retained smoke archive at
  `experiments/runs/019fb429-b255-70ae-91d6-5bdf4151a4c8` contains 1,211
  inventoried files and 18,638,999 inventoried bytes with content-tree
  SHA-256
  `sha256:16ba946fa5bf17163e15dae535a9206348e78b7a3a6e5e65769e8370632c0060`.
  Its disposition remains `smoke`; it was not modified.
- **Analysis attempts:** the four-table generator correctly rejected
  `smoke` as an unsupported manuscript disposition. A runtime projection
  using this smoke and retained older pilot
  `019fb3e0-62d5-7c5d-9846-1a3b2402c0b9` correctly rejected the pair because
  their identities drifted. No result was promoted.
- **Disposition:** failed as a resource-qualification gate and explicitly
  invalidated for smoke/pilot projection because the product treatment was
  subsequently amended. It is diagnostic evidence only.
- **Product correction:** product commit
  `63cfe81c8` adds explicit Windows resource sampling configuration at 250 ms.
  Audit then found the manager Docker cgroup ring still hard-coded to two
  seconds. Commit
  `31b1031f2ddc9fc4c702bdc15b7c2743288832eb` loads the validated
  observability configuration in the gateway and passes its exact cadence to
  the manager sampler. No API, benchmark cell, primary clock, fixture, image,
  or trial count changed.
- **Product validation attempts:** `cargo test -p sandbox-config` passed 78
  tests. Relevant manager core tests passed 18 tests and manager-router tests
  passed 20 tests; one unrelated Unix export test was filtered on Windows.
  `cargo check -p sandbox-gateway --bin sandbox-gateway`, manager-library and
  gateway-binary Clippy with `-D warnings`, formatting, and diff checks all
  passed. An initial broad Windows test attempt exposed existing ungated
  Unix-only tests, a pre-existing debug gateway holding a debug executable,
  and parallel Cargo target-lock contention. The relevant checks were
  repeated successfully in isolated target
  `target/exp1-cadence-check`; no unrelated source was rewritten.
- **New staged treatment:** package
  `target/windows-exp1-31b1031f` and its ZIP are the only candidates for the
  next qualification. ZIP SHA-256 is
  `6451e2b72e92a99d5f359ab3d3ff247a0a6aeed80011c99cfb9fd320dfd739ca`;
  gateway SHA-256 is
  `cb36cc7c1ffba5f97a8216e30d6fb8213d04581c100bd097739981fe4bc0b463`;
  configuration SHA-256 is
  `914d68807d97124a8412963d6f17e7a3914514bb0f0d210ea101ae52ba0ef512`.
  Manager, runtime, observability, and daemon hashes are recorded in Entry
  045. Product `main` is clean at the exact new commit.
- **Next action:** strict preflight and one fresh smoke under the corrected
  harness and `31b1031f` package. No pilot is allowed unless every non-create
  resource endpoint supplies complete measured boundaries and cleanup is
  clean.

### 2026-07-30T18:31:52.793Z - Corrected-treatment fresh-smoke preflight

- **Entry ID:** `exp1-corrected-treatment-smoke-preflight-047`.
- **Phase/kind:** EXP1-C requalification; strict preflight only.
- **Harness validation:** an independent full backend run passed 201 tests
  with five expected Windows symlink-privilege skips in 51.07 seconds.
  Analysis tests passed 12 tests in 1.07 seconds. Both runs set
  `PYTHONDONTWRITEBYTECODE=1` and disabled pytest's cache provider.
- **Recovery:** `sandbox-benchmark recover` against the staged package exited
  0 with `execution_available=true`, no issues, and no recovered run IDs.
- **Plan validation:** all presets are runnable through `product_cli`, use
  only `paper-100m`, and have zero warnings/findings. Smoke is
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  at 19/19/55; pilot is
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  at 19/133/385; final is
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  at 19/1,938/5,610.
- **Product/package:** product `main` is clean at
  `31b1031f2ddc9fc4c702bdc15b7c2743288832eb`. Staged ZIP size is
  5,616,849 bytes and SHA-256 is
  `6451e2b72e92a99d5f359ab3d3ff247a0a6aeed80011c99cfb9fd320dfd739ca`.
  The gateway, manager, runtime, observability, daemon, and configuration
  hashes exactly match Entry 045.
- **Docker/image/disk:** Docker server 29.0.1 reports Linux/AMD64. Local image
  `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
  independently inspects to the same image ID and digest on AMD64 Linux.
  Drive C has 575,893,774,336 free bytes.
- **Unrelated retained state:** the previously disclosed debug gateway PID
  62980, ten-day-old exited `eos-76263ba1-...` container, its two volumes,
  and three shared-base cache volumes remain untouched. None carries a
  benchmark run/campaign label for this qualification, and no benchmark CLI
  process or corrected-package gateway was active.
- **Disposition:** passed. No build, install, pull, live preset, or final
  command occurred. One corrected-treatment `paper-env-smoke` is authorized
  next; the pilot and freeze remain blocked on its empirical result.

### 2026-07-30T18:58:34.866Z - Corrected-treatment smoke exposed missing workspace-disk producer

- **Entry ID:** `exp1-workspace-disk-producer-smoke-failure-048`.
- **Phase/kind:** EXP1-C requalification; failed smoke.
- **Run/command:** run `019fb44c-887b-79ad-9ae0-5a5c0852696a` issued
  `.\.venv\Scripts\sandbox-benchmark.exe run --test-repository-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1
  --product-root
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox
  --product-bin-dir
  C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-31b1031f\bin
  --plan paper-env-smoke` with `PYTHONDONTWRITEBYTECODE=1`.
- **At-run identity:** product was clean `main` at
  `31b1031f2ddc9fc4c702bdc15b7c2743288832eb`; package, binary,
  configuration, image, host, limits, fixture, and plan identities matched
  Entry 047. No build, install, pull, source mutation, or environment
  reconfiguration occurred during the run clock.
- **Start/end/elapsed:** `2026-07-30T18:32:25.762441Z` to
  `2026-07-30T18:34:52.947894Z`; 147.185453 seconds.
- **Outcome:** terminal state `failed`, correctness `fail`, one
  infrastructure failure, zero warnings. The `create_sandbox` cell completed
  one reportable measured trial with both checks passed and cleanup restored.
  The first `exec_command` trial failed during mandatory pre-operation
  resource setup before any operation request was issued; it has null primary
  latency, request count zero, and cleanup restored. The campaign stopped
  immediately. No pilot or final command was issued.
- **Exact empirical diagnosis:** all 50 cgroup boundary polls were available,
  included required CPU, memory, read, and write counters, and advanced at
  approximately 250 ms. All 50 snapshots were also available and contained
  the same live workspace, but
  `workspaces[0].resources.latest` remained null throughout the five-second
  readiness window. The reconstructed terminal cause is
  `product resource boundary readiness timed out: workspace
  00000118c72503411e4c9b resource sample is not available yet`.
- **Source diagnosis:** the runtime exposes each live workspace ID and
  upperdir, the bounded `sample_upperdir` collector exists, and the public
  snapshot consumer expects workspace-scoped samples. Production never calls
  that collector or emits workspace-scoped disk samples; additionally,
  snapshot lookup reads the event reader rather than the dedicated resource
  reader. The manager cgroup cadence correction is valid; this is a separate
  missing producer/handoff bug.
- **Cleanup:** the benchmark destroyed the exact workspace session and
  sandbox; product list calls returned no sandboxes. Explicit terminal
  cleanup then removed the marker-validated retained diagnostic workspace in
  21.7 seconds. Runtime and run-workspace paths are absent, and no matching
  process, container, or volume remains.
- **Immutable failed archive:** the first archive attempt correctly failed
  under the then-existing completed-only rule. After the preservation
  amendment in Entry 049, the run archived as explicitly
  `failed_ineligible` at
  `experiments/runs/019fb44c-887b-79ad-9ae0-5a5c0852696a`: 389 files,
  4,899,939 bytes, content-tree SHA-256
  `sha256:03467746779e381aee6bb58764caa0650a2df262940234d6d8269efcc0a9900e`.
  A separate verify-only invocation matched exactly.
- **Disposition:** failed diagnostic evidence only. Gate 3 remains closed.
  The strongest pre-freeze correction is to wire bounded workspace-disk
  sampling into the daemon's owned cadence and resource reader, rebuild the
  treatment, and run a new smoke. A harness fallback that silently accepts an
  all-unavailable storage column was rejected because the intended public
  producer and consumer already exist.

### 2026-07-30T18:58:34.866Z - Failed-corpus archival preservation amendment

- **Entry ID:** `exp1-failed-corpus-archive-amendment-049`.
- **Phase/kind:** EXP1-C evidence-preservation amendment; no live run.
- **Correction:** `archive_exp1_run.py` now accepts an explicit terminal
  `--run-status failed` for smoke, exploratory pilot, or final attempts and
  assigns immutable eligibility `failed_ineligible`. It preserves partial
  observations, negative CLI evidence, warnings, raw report/events, and
  terminal failure data without weakening completed-run validation.
- **Fail-closed boundary:** verifier cross-checks run status, correctness,
  report copies, manifest eligibility, cleanup proof, at-run treatment, and
  post-run checkout provenance. Manifest editing cannot promote a failed
  archive. A failed final attempt still requires the annotated freeze tag
  against its recorded treatment. Completed and final-candidate archives
  still require a clean checkout exactly matching the recorded treatment.
- **Post-run drift disclosure:** a failed archive may record a dirty or
  advanced product checkout caused by the next corrective amendment. The
  clean at-run treatment from the run manifest, plus exact staged package and
  binary hashes, remains authoritative. Process, container, volume, runtime,
  run-workspace, branch, package, and binary checks remain strict. Failed-run
  benchmark-source provenance explicitly says the archived preservation code
  was amended after the run and is not byte-identical run-time source.
- **Files changed:** `experiments/scripts/archive_exp1_run.py`,
  `benchmark/backend/tests/unit/test_exp1_archive.py`, and this log.
- **Validation/attempts:** the completed-only real archive attempt failed
  with `only completed EXP1 runs can use this archive path`, motivating the
  amendment. Focused archive tests passed 13 tests; independent root rerun
  passed the same 13. Initial direct `ruff.exe` and
  `uv run --frozen ruff` attempts found no installed Ruff; `uvx ruff format
  --check` and `uvx ruff check` then passed.
- **Disposition:** passed. The failed smoke corpus is preserved, verified, and
  permanently ineligible for manuscript numbers.

### 2026-07-30T19:23:41.459Z - Bounded create-sandbox second-pass optimization audit

- **Entry ID:** `exp1-create-sandbox-second-pass-audit-052`.
- **Phase/kind:** EXP1-C pre-freeze diagnostic and optimization audit; no
  smoke, pilot, or final preset was issued.
- **Scope:** inspect the complete `create_sandbox` path after the validated
  shared-base and native-Windows fixture-copy optimizations, profile only
  isolated diagnostic operations, and retain the exact 19-cell protocol,
  fixture bytes/tree/hash, native `product_cli` semantics, correctness,
  cleanup, timing, and evidence boundaries.
- **Historical evidence inspected:** failed smoke
  `019fb44c-887b-79ad-9ae0-5a5c0852696a` recorded one reportable
  `create_sandbox` request at 47,812,097,100 ns. Its trial-level `setup_ns`
  was 17,300 ns because the independent `paper-100m` materialization is
  cell-scoped and outside every primary operation clock. These retained
  values remain failed-smoke diagnostic evidence and are ineligible for
  manuscript tables.
- **Isolated phase diagnostic:** a unique owned gateway and workspace used
  clean product `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`, package
  `target/windows-exp1-bc1e6ee0`, the fixed Ubuntu digest, manager CLI
  argument arrays, explicit request IDs, and CLI progress timestamps. The
  ordinary `paper-100m` materialization took 8.4055315 seconds. The first
  create took 47.0135836 seconds: shared-base construction completed at
  3.813 seconds, the first Docker runtime sandbox completed at 45.768
  seconds, and daemon installation/start/readiness plus state publication
  completed at 46.999 seconds. After manager-CLI destruction, the same
  workspace and gateway produced a second create in 1.5523349 seconds:
  validated shared-base reuse completed at 0.353 seconds, runtime sandbox
  creation at 0.482 seconds, and readiness/state publication at 1.538
  seconds. The two destroys took 0.9366223 and 1.0019202 seconds.
- **Interpretation boundary:** approximately 41.955 seconds of the cold
  create was Docker Desktop's first runtime-container creation for this
  shared-base mount, not fixture copying, base hashing, CLI launch, or daemon
  readiness. The unchanged pilot and final protocols already execute two
  warmup trials before measured trials in every cell. Moving Docker
  prewarming into setup, trusting an unvalidated cache, changing the
  `create_sandbox` cell, or excluding a cold measured value would alter the
  benchmark treatment or evidence boundary and was rejected.
- **Copy-engine matrix:** two independent ordinary-copy samples at each
  Robocopy worker count included copy plus all source-drift, destination-file,
  and manifest validation. Median seconds were `/MT:32` 8.34082875,
  `/MT:16` 10.2005869, `/MT:64` 11.7643670, and `/MT:128` 12.72309195.
  `/MT:32` remains the selected bounded setting. Its two samples
  (4.5323453 and 12.1493122 seconds) also show that this host path is noisy;
  no diagnostic timing is eligible for a paper table.
- **Component profile:** the first process-local full cache validation took
  4.0275112 seconds and a stable-identity validation took 0.5660631 seconds.
  Two direct native copies took 3.5675212 and 12.2348150 seconds; their
  post-copy source walks took 0.5800985 and 0.5829757 seconds, destination
  verification took 0.4260228 and 0.4330685 seconds, and manifest-byte
  verification took 0.0089029 and 0.0014380 seconds. Owned diagnostic-tree
  cleanup took 8.6437489 and 9.5096523 seconds and was excluded from every
  copy timing.
- **Validation-overlap check:** four alternating read-only samples gave a
  1.06716655-second median for sequential post-copy source-drift and
  destination verification and a 1.10508360-second median when overlapped.
  Parallel overlap was rejected because it was slower and added executor
  contention without strengthening correctness.
- **Focused validation:** with `PYTHONDONTWRITEBYTECODE=1` and pytest cache
  disabled,
  `python -m pytest benchmark/backend/tests/unit/test_fixtures.py` exited 0:
  15 tests passed and one Windows symlink-privilege case skipped in 10.07
  seconds. Repeated full fixture validation retained fixture hash
  `sha256:9484b132c8a35afd18bc37383759d0fe6d45dd4700b42a99336aed535e651cc7`
  and tree hash
  `sha256:d4c2fefbf94a30352f39d701ececaeeb8fad35603e4fb721dd5cf21296258c9f`.
- **Cleanup:** both diagnostic sandboxes were destroyed through the manager
  CLI. The isolated gateway, runtime/shared-base cache, marker-owned run
  workspace, and every copy-profile destination were removed; the final
  marker-owned run-tree removal took 18.4590787 seconds. No unrelated
  process, container, volume, cache, or generated artifact was deleted.
  Read-only terminal checks found the exact diagnostic run/runtime paths
  absent, zero remaining probe directories, no matching Docker object, and a
  clean product worktree on `main` at the recorded commit.
- **Diff validation:** a scoped `git diff --check` exited 0 with only the
  repository's existing Windows line-ending warnings. One read-only timestamp
  query initially used the unsupported PowerShell `Get-Date -AsUTC` option;
  it changed no state, and the portable `ToUniversalTime()` query succeeded.
- **Files changed:** this append-only experiment log only.
- **Disposition:** no additional safe speedup was demonstrated, so no
  benchmark or product source was changed. The existing fixture-copy and
  shared-base optimizations remain the fastest validated, protocol-preserving
  treatment. Gate 3 remains dependent on the separate fresh resource-complete
  smoke and exploratory pilot, not on this diagnostic.

### 2026-07-31T00:28:06.880Z - Workspace-resource producer corrective treatment and package

- **Entry ID:** `exp1-workspace-resource-producer-treatment-053`.
- **Phase/kind:** EXP1-C pre-freeze product correction, build, and
  qualification; no smoke, pilot, or final preset was issued.
- **Demonstrated defect:** failed smoke
  `019fb44c-887b-79ad-9ae0-5a5c0852696a` proved that every live workspace
  snapshot exposed `resources.latest: null` because production never invoked
  the existing bounded upperdir sampler and the snapshot path did not use the
  dedicated resource reader. Entry 048 preserves the exact failure.
- **Corrective treatment:** clean product `main` advanced to
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`
  (`fix(observability): sample workspace disk usage`). The daemon resource
  sampler now owns one configured blocking cadence, samples each live
  workspace upperdir through the existing bounded collector, and emits only
  strict-parser-safe logical bytes, allocated bytes, file count, and
  truncation fields. Snapshot queries receive the dedicated resource reader;
  event and layer readers remain unchanged. Read or budget failure omits the
  allocated value and records truncation rather than fabricating zero.
- **Product validation:** isolated WSL target
  `/tmp/ephemeral-sandbox-resource-target` passed daemon/query `cargo check`,
  all 15 observability-query tests, four focused workspace-resource sampler
  tests, one daemon-to-snapshot resource-store test, Clippy with
  `--no-deps -D warnings`, `cargo fmt --all --check`, and `git diff --check`.
  The full daemon unit binary passed 105 of 106 tests; the sole failure was
  unrelated `runner_tests::result_fd_writer_writes_to_fd_peer`, which WSL
  rejected with `ENXIO` while opening the result FD. A native-Windows query
  test attempt could not compile its Unix-only `rustix::fs` test dependency;
  it did not change source.
- **Linux daemon and package build:** the release packaging command
  `target\debug\xtask.exe package --builder zigbuild --target
  x86_64-unknown-linux-musl` completed in 31 seconds and produced
  `dist\sandbox-daemon-linux-amd64` with SHA-256
  `a620d6016fb23c0da82f3f913ac411850d9125dea342886fcbe1edca1ee301b6`.
  The first direct PowerShell packaging attempt was blocked by the host
  execution policy and misleadingly returned the enclosing shell's exit 0;
  the required retry used `powershell.exe -NoProfile -ExecutionPolicy Bypass
  -File .\bin\package-windows-amd64-release.ps1 -PackageName
  windows-exp1-bc1e6ee0 -OutDir target -Profile release` and succeeded.
- **Candidate package:** `target\windows-exp1-bc1e6ee0` and
  `target\windows-exp1-bc1e6ee0.zip`; archive size 5,658,062 bytes and
  SHA-256
  `f1bede6d96bdf7907c898c11c6c39865824888086ea6ae9e72518c93fef51240`.
  Executable SHA-256 values are gateway
  `cb36cc7c1ffba5f97a8216e30d6fb8213d04581c100bd097739981fe4bc0b463`,
  manager
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`,
  runtime
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`,
  and observability
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`.
- **Current read-only recheck:** product is clean `main`, six commits ahead of
  `origin/main`, at the recorded commit. Docker client/server remain 29.0.1,
  Linux AMD64, overlayfs, and cgroup v2. The fixed package and archive hashes
  match. The pre-existing unrelated debug gateway PID 62980 remains untouched.
- **Disposition:** the corrected treatment is technically qualified but not
  yet Gate-3 qualified. A one-cell isolated CLI diagnostic must first prove
  available, fresh workspace-disk boundaries; then a completely fresh smoke
  and exploratory pilot are required.

### 2026-07-31T00:35:18.777Z - Resource-producer diagnostic exposed strict snapshot-parser gap

- **Entry ID:** `exp1-workspace-resource-probe-failure-054`.
- **Phase/kind:** EXP1-C pre-freeze diagnostic failure and cleanup; not a
  smoke, pilot, or final attempt.
- **Plan validation:** the first temporary diagnostic plan incorrectly wrapped
  a preset-shaped default plan and failed closed with Pydantic's
  `invalid benchmark default plan`; no run was issued. The corrected raw
  experiment plan validated with no warnings as one `product_cli`
  `exec_command` cell, one measured batch, one issued request, and plan hash
  `sha256:d8d9071f9c5888378c62969e075cd831810d18b6ca7de0df154b28eff05800bf`.
- **Run/command:** run `019fb592-a95f-7dd4-9ce3-8791b991fae2` issued
  `.\\.venv\\Scripts\\sandbox-benchmark.exe run --test-repository-root
  C:\\Users\\yifan\\code\\Ephemeral-AI-Lab\\research-papers\\ephemeral-sandbox-v1
  --product-root
  C:\\Users\\yifan\\code\\Ephemeral-AI-Lab\\ephemeral-sandbox
  --product-bin-dir
  C:\\Users\\yifan\\code\\Ephemeral-AI-Lab\\ephemeral-sandbox\\target\\windows-exp1-bc1e6ee0\\bin
  --plan .\\tmp\\exp1-workspace-resource-probe.yml` with
  `PYTHONDONTWRITEBYTECODE=1`.
- **At-run identity:** clean product `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`, corrected package and binary
  hashes from Entry 053, fixed image digest, and validated custom-plan hash.
  No build, install, pull, source mutation, or environment reconfiguration
  occurred during the clock.
- **Start/end/elapsed:** `2026-07-31T00:28:35.833090Z` to
  `2026-07-31T00:29:51.145840Z`; the supervised process completed in 81.1
  wall-clock seconds. The CLI process exited 0 because it returned the
  persisted terminal run status; the run manifest correctly records state
  `failed`, correctness `fail`, and infrastructure failure.
- **Outcome:** the single measured trial failed in mandatory resource setup
  before the operation barrier. It issued zero operation requests, recorded
  null primary latency, restored trial cleanup, and produced no reportable
  sample. No smoke, pilot, or final command was issued.
- **Positive producer evidence:** the first snapshot now exposed the exact
  active workspace and a non-null fresh resource record at Unix millisecond
  `1785457778639`, with `disk_bytes: 0`,
  `disk_allocated_bytes: 4096`, `files: 0`, and
  `disk_truncated: false`. The concurrent cgroup boundary was available with
  CPU, memory, read, and write counters. This directly proves the Entry-053
  workspace producer and dedicated resource-reader handoff are live.
- **Exact failure:** the paper's strict `SnapshotMetrics`/`SnapshotDeltas`
  model was written for the previously hidden workspace-oriented subset. The
  now-correct sandbox resource sample also contains the authoritative daemon
  fields `metrics_source`, `cgroup_path`, `io_rbytes`, `io_wbytes`,
  `pids_cur`, plus read/write deltas. Local replay of the archived response
  raised seven `extra_forbidden` Pydantic errors and then
  `product snapshot response schema is invalid`. The released Rust sampler
  and snapshot serializer explicitly emit these fields; this is a paper-side
  strict-schema coverage defect, not missing product data.
- **Evidence preservation:** the exact 35-file, 256,561-byte result corpus is
  copied to
  `experiments/diagnostics/exp1-workspace-resource-probe-019fb592-a95f-7dd4-9ce3-8791b991fae2`
  with content-tree SHA-256
  `sha256:4ef738fd244b1c8fb47ef08c878345cd8b1e1fb846f1d93b208e8fcc00759628`.
  It is diagnostic-only and permanently ineligible for paper tables.
- **Cleanup:** explicit benchmark cleanup exited 0 with `cleaned: true`.
  The exact run workspace and runtime entry are absent; the exact sandbox has
  no matching container or volume; the isolated gateway is gone; and the
  product remains clean. The pre-existing unrelated debug gateway PID 62980
  remains untouched.
- **Disposition:** failed diagnostic retained. Gate 3 stays closed. Add exact
  strict models for the authoritative sandbox resource sample and workspace
  disk sample, retain rejection of unknown keys, validate the archived shape,
  then rerun a new one-cell diagnostic before any smoke or pilot.

### 2026-07-31T00:39:39.934Z - Context-strict snapshot resource parser correction

- **Entry ID:** `exp1-snapshot-resource-schema-amendment-055`.
- **Phase/kind:** EXP1-C pre-freeze harness correction and validation; no live
  preset.
- **Correction:** `observability.py` now models snapshot sandbox resources and
  workspace resources as distinct strict types. Sandbox samples require
  `metrics_source: sandbox_cgroup`, cgroup identity/availability, and accept
  only the released CPU, memory, I/O, PID, truncation, and counter-delta
  fields. Workspace samples require the disk-truncation identity and accept
  only logical bytes, allocated bytes, file count, truncation, and empty
  deltas.
- **Fail-closed boundary:** a root disk metric cannot masquerade as a sandbox
  cgroup sample; cgroup metrics or deltas cannot appear in a workspace disk
  sample; unknown future keys, mixed-scope shapes, wrong metric sources, and
  missing scope identities remain schema errors.
- **Regression evidence:** the exact field values preserved from failed
  diagnostic `019fb592-a95f-7dd4-9ce3-8791b991fae2` parse as
  `sandbox_cgroup`, sandbox read bytes `98304`, and workspace allocated bytes
  `4096`. Negative tests cover unknown keys, scope mixing, wrong source,
  missing cgroup identity, and missing workspace disk identity.
- **Validation:** the delegated exact schema suite passed 16 tests; its
  resource-sampling plus runner suite passed 32; and its full backend suite
  passed 220 tests with five expected Windows symlink-privilege skips. An
  independent root focused run passed all 48 tests in 4.66 seconds, and an
  independent full backend run passed 220 with the same five expected skips
  in 35.23 seconds. Every command used `PYTHONDONTWRITEBYTECODE=1` and disabled
  the pytest cache provider.
- **Files changed:** `benchmark/backend/benchmark_lab/observability.py`,
  `benchmark/backend/tests/unit/test_observability.py`, and this append-only
  log.
- **Disposition:** passed. The false-negative parser defect is resolved
  without weakening scope validation. A new isolated one-cell diagnostic must
  still prove both mandatory boundaries and cleanup before fresh smoke.

### 2026-07-31T00:43:07.977Z - Workspace-resource two-boundary diagnostic passed

- **Entry ID:** `exp1-workspace-resource-probe-pass-056`.
- **Phase/kind:** EXP1-C pre-freeze positive diagnostic; not a smoke, pilot,
  or final attempt.
- **Run/identity:** run `019fb59d-2877-700e-8299-bf3042d2da65` used clean
  product `main` at `bc1e6ee04d4df5541290537994a4bf270fcd36b6`,
  package `target\windows-exp1-bc1e6ee0`, the exact Entry-053 binaries, fixed
  image digest, `product_cli`, and the validated one-cell plan hash
  `sha256:d8d9071f9c5888378c62969e075cd831810d18b6ca7de0df154b28eff05800bf`.
- **Start/end:** `2026-07-31T00:40:03.751900Z` to
  `2026-07-31T00:41:19.011354Z`; the supervised process completed in 82.7
  wall-clock seconds. No build, install, pull, source mutation, or environment
  reconfiguration occurred during the clock.
- **Terminal outcome:** state `completed`, correctness `pass`, one measured
  batch, one issued operation request, zero failures, zero warnings, and one
  reportable trial. The runtime CLI request exited 0 with empty stderr and
  passed response validation. All three command checks passed and trial
  cleanup restored the baseline.
- **Mandatory boundaries:** the raw corpus contains exactly two persisted
  readings for every resource metric. Both `upperdir_bytes` readings are
  available at 4,096 allocated bytes. Baseline/post sandbox CPU counters are
  56,616,000/116,673,000 ns; block-read counters are 98,304/3,842,048 bytes;
  block-write counters are 16,384/16,384 bytes. The accepted snapshot
  workspace timestamps advance from `1785458464483` to `1785458464984`;
  accepted cgroup timestamps advance from `1785458464445` to
  `1785458464956`. Two earlier post-response polls were correctly rejected as
  not yet fresh.
- **Expected explicit unavailability:** the immutable host fixture's allocated
  byte count is unavailable because native Windows metadata lacks allocated
  block counts; LayerStack total allocated storage is unavailable because the
  product did not report it. Neither substitutes for the now-complete live
  workspace upperdir metric, and neither was fabricated as zero.
- **Preservation:** the exact 63-file, 442,066-byte result corpus is copied
  byte-for-byte to `experiments/diagnostics/resource-probe-019fb59d`.
  Source and copy inventories match at content-tree SHA-256
  `sha256:146a883858b8f8f3245d451d765f063a16e24c57c4271fdb23a51cfe1f80f82a`.
  An initial ordinary copy missed one overlong bounded-evidence pathname;
  the same file was already present through the long-path API, the directory
  was moved to the shorter marker path above, and the complete inventories
  then matched exactly.
- **Cleanup:** explicit benchmark cleanup exited 0 with `cleaned: true`. The
  exact run workspace and runtime entry are absent, the exact sandbox has no
  matching container or volume, the isolated gateway is gone, and the product
  remains clean. The unrelated debug gateway PID 62980 remains untouched.
- **Disposition:** passed. The resource-producer/parser blocker is resolved.
  A fresh `paper-env-smoke` is now permitted; pilot and freeze remain blocked
  until that smoke passes its full 19-cell correctness, resource, and cleanup
  gate.

### 2026-07-31T00:44:06.158Z - Fresh smoke qualification and exact-plan recheck

- **Entry ID:** `exp1-bc1e6ee0-smoke-preflight-057`.
- **Phase/kind:** EXP1-C corrected-treatment qualification; no live preset in
  this entry.
- **Test qualification:** independent full backend validation passed 220 tests
  with five expected Windows symlink-privilege skips in 35.23 seconds.
  Deterministic analysis plus archive-guard validation passed all 25 tests in
  5.01 seconds. The context-strict resource-focused suite passed all 48 tests
  in 4.66 seconds. All runs used Python 3.13.14,
  `PYTHONDONTWRITEBYTECODE=1`, and no pytest cache provider.
- **Exact expansions:** `paper-env-smoke` is runnable with no warnings or
  validation issues at plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`,
  19 cells, 19 batches, and 55 operation requests. `paper-pilot` is runnable
  at
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`,
  19 cells, 133 batches, and 385 requests. `paper-good-pass` is runnable at
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`,
  19 cells, 1,938 batches, and 5,610 requests. Every preset selects only
  `product_cli` and `paper-100m`.
- **Treatment/environment:** product is clean `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`; all four staged executable
  hashes match Entry 053. The local image ID exactly matches the fixed Ubuntu
  digest. C: free space is 572,616,560,640 bytes. No benchmark campaign,
  candidate gateway, or candidate sandbox process is active. The unrelated
  debug gateway PID 62980 remains outside campaign ownership.
- **Diff checks:** product and scoped paper `git diff --check` exited 0; only
  existing Git line-ending conversion notices were printed.
- **Disposition:** passed. A single fresh corrected-treatment
  `paper-env-smoke` is authorized by the protocol. No pilot or final command
  may run unless its complete 19-cell evidence, mandatory resources, and
  cleanup audit pass.

### 2026-07-31T00:58:32.472Z - Corrected-treatment CLI integration smoke passed

- **Entry ID:** `exp1-bc1e6ee0-smoke-pass-058`.
- **Phase/kind:** EXP1-C live CLI integration smoke.
- **Run/command:** run `019fb5a1-313c-7db7-969d-a064b43afa67` issued the
  validated `paper-env-smoke` command against
  `target\windows-exp1-bc1e6ee0\bin` with
  `PYTHONDONTWRITEBYTECODE=1`.
- **At-run identity:** clean product `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`; package, daemon, all four
  native Windows CLIs, image, host, sandbox limits, fixture, analysis source,
  and plan identities matched Entry 057. No build, install, pull, source
  mutation, or environment reconfiguration occurred during the run clock.
- **Start/end/elapsed:** `2026-07-31T00:44:31.290325Z` to
  `2026-07-31T00:52:06.451390Z`; 455.161065 seconds of manifest run time.
  The supervised wrapper returned exit 0 after 705.1 seconds; after the
  terminal report was written it spent approximately 250 seconds draining
  off-clock Python worker activity. No candidate gateway or sandbox remained
  during that drain, and no benchmark result uses wrapper elapsed time.
- **Outcome:** terminal state `completed`, correctness `pass`, 19 of 19 cells,
  19 of 19 reportable measured trials, all 55 planned operation requests, all
  48 registered correctness checks, 19 operation-evidence records, zero
  failed trials, and zero warnings. Every primary request used the required
  manager or runtime CLI; verification and observability used the required
  runtime or observability CLI.
- **Mandatory resource audit:** all 72 required
  non-`create_sandbox` metric/trial combinations for `upperdir_bytes`,
  sandbox CPU time, block reads, and block writes contain exactly two
  non-periodic mandatory boundaries and both are available. Sandbox-create's
  eight counter readings are explicitly inapplicable because a pre-create
  sandbox baseline cannot exist; none is fabricated as zero. The corpus
  contains 616 total resource records.
- **Periodic-sampling disclosure:** slower write/edit/create-workspace trials
  also emitted 84 scheduled 100-ms readings. Thirteen fields were explicitly
  unavailable: the known NTFS host allocated-byte field, the product's
  unavailable LayerStack total, and one workspace-create upperdir observation
  captured during the transition before the next disk sample. The mandatory
  before/after boundaries for that trial are both complete (0 and 20,480
  allocated bytes). No missing periodic value was converted to zero or
  removed.
- **Correlation boundary:** each of the 18 post-create cells has one eligible
  CPU/latency point; `create_sandbox` has zero because its CPU delta is
  inapplicable. Every smoke coefficient and interval is omitted as
  `insufficient_n`, as required for one-sample support.
- **Immutable archive:** archive
  `experiments/runs/019fb5a1-313c-7db7-969d-a064b43afa67` contains 1,421
  files and 18,963,304 bytes with content-tree SHA-256
  `sha256:6ab9facdab1e7ad75ef5e8a26c30dc121835b10edcc0d3b0ca252098b435e1c0`.
  Creation verification and a separate verify-only invocation both matched
  exactly.
- **Cleanup:** the archive proof records no run- or gateway-labeled
  containers or volumes, no matching product processes, no runtime or run
  workspace, clean product `main`, and the exact treatment commit. Explicit
  benchmark cleanup also exited 0. Independent terminal checks found zero
  running Docker containers, zero candidate sandbox processes, no run/runtime
  path, and a clean product. The unrelated debug gateway PID 62980 was not
  touched.
- **Disposition:** EXP1-C passed for the corrected treatment. A single fresh
  five-sample exploratory `paper-pilot` is now permitted; freeze and final
  remain blocked until its full correctness, resources, deterministic
  analysis, runtime projection, and cleanup audit pass.

### 2026-07-31T00:59:13.812Z - Five-sample exploratory pilot preflight

- **Entry ID:** `exp1-bc1e6ee0-pilot-preflight-059`.
- **Phase/kind:** EXP1-D strict fast preflight; no live pilot in this entry.
- **Treatment:** product remains clean `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`. Gateway, manager, runtime, and
  observability hashes remain respectively `cb36cc7...b463`,
  `032187d0...eac6`, `3ada794f...349`, and `406ca3fa...dfc3`. The exact image
  digest is present locally; no pull was issued.
- **Plan:** `paper-pilot` is runnable with only `product_cli` and
  `paper-100m`, zero warnings and validation issues, plan hash
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`,
  19 cells, 133 batches, and 385 operation requests.
- **Environment/cleanup:** C: free space is 572,263,915,520 bytes. No
  benchmark process, candidate gateway, or candidate sandbox process is
  active. Corrected smoke archive
  `019fb5a1-313c-7db7-969d-a064b43afa67` still verifies at
  `sha256:6ab9facdab1e7ad75ef5e8a26c30dc121835b10edcc0d3b0ca252098b435e1c0`.
- **Clock boundary:** no build, install, image pull, source mutation,
  dependency change, or environment reconfiguration will occur from pilot
  start until its terminal manifest and report are written.
- **Disposition:** passed. One exploratory `paper-pilot` command is permitted.
  Its values are permanently ineligible for manuscript tables.

### 2026-07-31T01:19:37.788Z - Exploratory pilot failed and corpus preserved

- **Entry ID:** `exp1-bc1e6ee0-pilot-failed-060`.
- **Phase/kind:** EXP1-D live five-sample exploratory pilot; permanently
  ineligible for manuscript tables.
- **Run/command:** run `019fb5ae-fe8f-796a-ac8a-f7fc0b99e60b` issued the
  validated `paper-pilot` command against
  `target\windows-exp1-bc1e6ee0\bin` with
  `PYTHONDONTWRITEBYTECODE=1`.
- **At-run identity:** clean product `main` at
  `bc1e6ee04d4df5541290537994a4bf270fcd36b6`; package, native CLIs, daemon,
  image, host, limits, fixture, analysis source, and plan identity matched
  Entry 059. No build, install, pull, source mutation, or environment
  reconfiguration occurred during the run clock.
- **Start/end:** `2026-07-31T00:59:35.424427Z` to
  `2026-07-31T01:07:53.405171Z`.
- **Terminal outcome:** failed correctness after 106 of 133 batches. The
  report contains 105 successful trials, 278 issued operation requests, one
  failed trial, and zero warnings. Failure occurred in the first warmup of
  cell
  `sha256:07844b8b3087d14ef328ba48b05955f3d5f9df4e7c572b5bd2e2dd19f87c3e02`:
  `file_edit`, concurrency 5, 262,144-byte independent targets, one exact
  replacement at density 1.0, destination `session`, fresh session per
  trial, and `paper-100m`.
- **Failure evidence:** trial
  `trial-d2e2dd19f87c3e02-warmup-000000` is `cleanup_invalid` with zero
  reportable requests, `product_succeeded: false`,
  `infrastructure_failed: true`, and
  `cleanup_baseline_restored: false`. Request 1 passed in 0.108710 seconds.
  Requests 0 and 2 each returned `internal_error` after 30.016745 and
  30.016014 seconds with the exact bounded message
  `sandbox daemon forwarding failed: daemon request timed out after 30000
  ms`. Requests 3 and 4 were cancelled after 30.016121 and 30.012904
  seconds. The post-operation mandatory snapshot and session destroy then
  returned `server_busy`, so no result from this trial is eligible.
- **Resource disclosure:** scheduled periodic sampling saturated its fixed
  one-sample concurrency cap while the edit requests were stuck, and one
  cgroup sample itself timed out near 30 seconds. These unavailable readings
  remain explicit in the corpus; none was removed or converted to zero.
- **Immutable archive:** exploratory failed-run archive
  `experiments/runs/019fb5ae-fe8f-796a-ac8a-f7fc0b99e60b` contains 6,304
  files and 83,770,836 bytes with content-tree SHA-256
  `sha256:5640483803335d2139e0ca2467a8145e0601fc379672d0b0ce82812c5f2a4b9a`.
  A separate verify-only invocation returned `verified: true`.
- **Preservation-tool note:** the first seal attempt used an incorrect
  truncated image digest copied from an intermediate status summary and
  failed its Docker-image preflight. The run manifest supplied the correct
  pinned digest
  `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`.
  The successful retry used that exact value. The failed attempt's
  run-specific duplicate staging tree was removed only after the valid
  archive independently verified; the raw result corpus remains present.
- **Cleanup:** scoped benchmark cleanup removed the exact run and runtime
  scopes. Independent checks found zero candidate benchmark/product
  processes and no exact run/runtime path. Archive cleanup verification
  passed, and the product remains clean `main` at the exact treatment commit.
  Unrelated Docker and debug resources were not touched.
- **Disposition:** failed and preserved. Gate 3 is closed. No treatment
  freeze, annotated tag, or `paper-good-pass` command has been issued.
  Product and harness diagnosis must identify and qualify a correction before
  any replacement exploratory pilot is authorized.

### 2026-07-31T01:25:33.662Z - Pilot starvation diagnosis and correction boundary

- **Entry ID:** `exp1-pilot-starvation-diagnosis-061`.
- **Phase/kind:** pre-freeze failed-pilot diagnosis; no live preset in this
  entry.
- **Method:** the primary agent and a read-only independent subagent compared
  the failed pilot's exact subprocess metadata and event timing with the
  successful matching smoke cell, then traced the daemon, namespace-execution,
  resource-sampler, and gateway timeout implementations. The subagent changed
  no files or runtime state.
- **Matched-cell evidence:** the smoke's concurrency-5, 262,144-byte session
  edit completed all five requests in 0.093467--0.177086 seconds. In smoke,
  request 1 ended only 0.100 ms before the first scheduled sampler CLI began.
  In the failed pilot, the three sampler CLIs began while request 1 was still
  active. Payload, factors, fixture profile, operation path, and treatment
  were otherwise equivalent.
- **Root cause:** high-confidence Tokio blocking-pool starvation. The standard
  daemon has exactly eight blocking workers. Its enabled internal
  `ResourceSampler` permanently occupies one. Each ordinary or observability
  RPC dispatch occupies another. After request 1 completed, four edit
  dispatches plus three periodic observability dispatches occupied all seven
  remaining workers. The namespace completion supervisor then attempted to
  run `complete_jobs` through the same exhausted blocking pool, so it could
  not resolve the file-runner promise that would release an edit dispatch.
  This closed dependency cycle explains the two exact 30-second forwarding
  timeouts, two cancellations, three 30-second sampler timeouts, and the
  subsequent `max_blocking_requests: 8` capacity errors.
- **Correction boundary:** timeout inflation, observation disablement,
  concurrency reduction, or retry would only mask the defect and is rejected.
  The smallest structural correction is to make namespace completion progress
  independent of Tokio's shared blocking pool by using the supervisor's
  existing dedicated completion-thread path even when constructed inside a
  multi-thread Tokio runtime. The configured worker counts and request
  admission limits remain unchanged.
- **Qualification requirement:** add a deterministic saturation regression
  that constructs the supervisor inside a Tokio runtime, occupies every
  blocking-pool worker, and proves an immediately complete child still
  resolves. Then run focused namespace-execution, daemon, full product, package
  identity, and a bounded pre-pilot reproduction before any replacement
  pilot.
- **Disposition:** correction authorized as a pre-freeze product bug fix.
  Gate 3 remains closed, and no freeze or final command is permitted.

### 2026-07-31T01:44:20.322Z - Namespace-completion correction qualification and treatment rebuild

- **Entry ID:** `exp1-namespace-completion-correction-062`.
- **Phase/kind:** pre-freeze product correction, qualification, and immutable
  treatment-package rebuild; no live benchmark preset in this entry.
- **Product correction:** committed direct to the authorized product `main` as
  `06f52dfbadc923b80840dd6d156bb7f026519e19`
  (`fix(runtime): isolate namespace completion worker`). Namespace completion
  now always uses the existing dedicated `eos-command-reaper` thread instead
  of scheduling its completion callback through Tokio's shared blocking pool.
  The configured Tokio worker count, daemon blocking-request limit, admission
  behavior, resource sampling, benchmark factors, and benchmark harness were
  not weakened or changed by this correction.
- **Regression:** the new deterministic supervisor test creates a Tokio runtime
  with `max_blocking_threads = 1`, occupies that sole blocking worker, and
  proves a completed child resolves before the pool is released. The exact
  regression passed.
- **Relevant package qualification (WSL Ubuntu, Rust 1.97.1, isolated
  `CARGO_TARGET_DIR=/tmp/eos-exp1-target`):**
  `sandbox-runtime-namespace-execution` passed its full test package;
  `sandbox-daemon --features jemalloc` passed 112 tests; and
  `sandbox-runtime` passed its full test package. Clippy passed with
  `--all-targets` for all three affected packages. The only emitted clippy
  warning was an unrelated pre-existing Rust 1.97 style suggestion in
  `crates/sandbox-observability/telemetry/src/sink.rs:201`.
- **Qualification-only test repairs in the same commit:** an invalid
  process-global `active_pty_readers == 0` assertion was removed after both
  default and serial package orderings demonstrated dependence on preceding
  tests while the exact isolated engine test passed. The daemon result-FD unit
  fixture was changed from a Unix socket, which Linux cannot reopen through
  `/proc/self/fd` and failed alone with `ENXIO`, to the `rustix` pipe used by
  production. Neither repair changes product runtime behavior.
- **Known qualification boundaries:** native Windows compilation of the
  Linux-only affected package stops in existing telemetry code because
  `rustix::fs` is unavailable on Windows. A workspace-wide
  `cargo test --workspace --all-features --quiet` on Rust 1.97.1 reaches an
  unrelated pre-existing lifetime error (`E0521`) at
  `crates/sandbox-runtime/workspace/tests/holder_lifecycle.rs:361`. These
  failures are outside the corrected dependency path; the affected Linux
  packages pass in full.
- **Rebuild tool note:** the repository-prescribed
  `bin/start-sandbox-docker-gateway --rebuild-binary --help` wrapper exited
  before any build or runtime mutation because the Windows checkout exposes
  its shebang as `/bin/sh^M`. The documented direct fallback
  `target/debug/xtask.exe package --builder zigbuild
  --target x86_64-unknown-linux-musl` then succeeded, explicitly recompiling
  `sandbox-runtime-namespace-execution`, `sandbox-runtime`,
  `sandbox-runtime-workspace`, and `sandbox-daemon`.
- **Treatment package:** Windows release packaging produced
  `ephemeral-sandbox/target/windows-exp1-06f52dfb.zip`, SHA-256
  `34f2bf79d59d5c76afcaaf0a8bf8ef032aec9a0d2bc91a8e0019e5442f12d512`.
  The archive has exactly the expected nine files. Component identities are:
  gateway
  `cb36cc7c1ffba5f97a8216e30d6fb8213d04581c100bd097739981fe4bc0b463`;
  manager CLI
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`;
  runtime CLI
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`;
  observability CLI
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`;
  corrected Linux daemon
  `dfec6818fa5bbece5e26bd88c5be464b2a9027a078bbcfb1e05eaf7e4acca282`;
  and config
  `914d68807d97124a8412963d6f17e7a3914514bb0f0d210ea101ae52ba0ef512`.
- **State/disposition:** product HEAD and package source identity agree, and
  the product worktree is clean. The old failed pilot remains permanently
  ineligible and immutable. Gate 3 remains closed pending a bounded live
  starvation reproduction, a fresh full smoke, and a complete replacement
  five-sample pilot; no freeze or final command is authorized yet.

### 2026-07-31T01:49:59.712Z - Corrected-daemon bounded-reproduction preflight

- **Entry ID:** `exp1-namespace-completion-reproduction-preflight-063`.
- **Phase/kind:** pre-freeze diagnostic preflight; no live benchmark command
  in this entry.
- **Harness qualification:** the complete benchmark backend suite passed
  220 tests with five expected Windows symlink-privilege skips in 37.95
  seconds under Python 3.13.14, `PYTHONDONTWRITEBYTECODE=1`, and no pytest
  cache provider. This includes the native-Windows ordinary-copy fixture
  acceleration, strict resource parser, runner, cleanup, product-CLI,
  artifact, archive, and deterministic-analysis contracts.
- **Official-plan revalidation:** `paper-env-smoke`, `paper-pilot`, and
  `paper-good-pass` are runnable and customized with zero findings, use only
  `product_cli` and `paper-100m`, and retain hashes
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`,
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`,
  and
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
  Their exact expansions remain 19/19/55, 19/133/385, and 19/1,938/5,610
  cells/trial batches/issued operation requests. Two PowerShell reporting
  helpers were discarded before accepting these results: one had a parser
  error before invoking validation, and one used an unsupported
  `ConvertFrom-Json -Depth` option and therefore printed invalid summaries.
  The three CLI validations were then reissued and parsed successfully.
- **Diagnostic-plan audit:** the first one-cell custom plan validated at
  `sha256:04c0b6b84d18fdc92f2e6fcdbb58e3053c397952ad4b9dfb40aaf343c72dcf68`,
  but inspection rejected it before execution because the planner only
  injects the mandatory `paper-100m` profile for a canonical paper-preset
  name. Its cell therefore did not match the failed pilot. The corrected
  diagnostic deliberately uses canonical name `paper-pilot` while remaining
  customized and contains only the failed cell. It validates with zero
  findings at
  `sha256:fab773f32855fe90061b775781d21ee89fa1f9b7cc8ceb16221cc37b403a4f72`:
  one cell, two warmups, five measured trials, seven batches, 35 issued
  requests, a 100-ms resource cadence, and a 120-second trial timeout.
  Its exact cell ID
  `sha256:07844b8b3087d14ef328ba48b05955f3d5f9df4e7c572b5bd2e2dd19f87c3e02`
  matches the failed pilot: `file_edit`, concurrency 5, 262,144 bytes, one
  exact replacement at density 1.0, session destination, independent targets,
  fresh sessions per trial, and `paper-100m`.
- **Treatment/environment recheck:** product is clean `main` at
  `06f52dfbadc923b80840dd6d156bb7f026519e19`; package archive remains
  `34f2bf79...12d512`, corrected daemon remains `dfec6818...ca282`, the
  four native Windows executables and config retain the Entry-062 hashes,
  and the fixed local image resolves exactly to
  `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`.
  Docker client/server are 29.0.1 on Linux AMD64, overlayfs, and cgroup v2.
  C: has 571,799,793,664 free bytes.
- **Ownership baseline:** zero containers or volumes carry the benchmark
  gateway-instance label, zero processes execute from the candidate package,
  and the benchmark runtime directory is empty. Older terminal run records
  and temporary command logs are retained as pre-existing user evidence and
  will not be cleaned. The unrelated debug gateway remains outside this
  treatment and is not touched.
- **Disposition:** preflight passed. One bounded diagnostic command is
  authorized. Any product error, missing resource boundary, cleanup failure,
  identity drift, or daemon instability stops the campaign and remains
  ineligible; smoke, pilot, freeze, and final remain blocked until this
  diagnostic is preserved and audited.

### 2026-07-31T01:56:38.634Z - Corrected-daemon starvation reproduction passed

- **Entry ID:** `exp1-namespace-completion-reproduction-pass-064`.
- **Phase/kind:** pre-freeze bounded live diagnostic; permanently
  diagnostic-only and ineligible for manuscript tables.
- **Run/identity:** run `019fb5dd-ff1e-770e-9524-e28bdea4afb3` invoked the
  exact Entry-063 custom-plan path against
  `target\windows-exp1-06f52dfb\bin`. At-run treatment is clean product
  `main` at `06f52dfbadc923b80840dd6d156bb7f026519e19`, corrected daemon
  `dfec6818...ca282`, the exact four native Windows executable hashes,
  `product_cli`, fixed Ubuntu digest, `paper-100m`, and plan hash
  `sha256:fab773f32855fe90061b775781d21ee89fa1f9b7cc8ceb16221cc37b403a4f72`.
  No build, install, pull, source mutation, dependency change, or environment
  reconfiguration occurred during the run clock.
- **Start/end/elapsed:** `2026-07-31T01:50:56.250746Z` to
  `2026-07-31T01:52:21.998213Z`, or 85.747467 seconds of manifest time.
- **Terminal outcome:** state `completed`, correctness `pass`, exact failed
  cell ID
  `sha256:07844b8b3087d14ef328ba48b05955f3d5f9df4e7c572b5bd2e2dd19f87c3e02`,
  seven of seven successful trial batches, two warmups, five reportable
  measured trials, all 35 operation requests successful, zero product,
  correctness, infrastructure, cleanup, or missing-latency failures, and zero
  warnings. All 21 trial check records passed.
- **CLI evidence:** all 430 primary, setup, verification, observability, and
  cleanup CLI invocations returned code 0, passed response validation, emitted
  zero stderr bytes, had unique request IDs, and preserved authentication
  redaction.
- **Mandatory resources:** every trial contains exactly two available
  non-periodic boundaries for each required starvation-reproduction metric:
  14 `upperdir_bytes`, 14 sandbox CPU, 14 sandbox block-read, and 14 sandbox
  block-write boundary records in total. Across mandatory and scheduled
  samples, each of these metrics has 26 available observations. Host
  allocated-byte metadata and LayerStack allocated storage remain explicitly
  unavailable in 26 readings each for the already disclosed platform/product
  reasons; no unavailable value was encoded as zero.
- **Timing discriminator:** the diagnostic is conclusive rather than merely
  green. In three measured trials a scheduled resource collection began while
  all five edit requests were still in flight: at 97.977 ms before the first
  completion at 122.720 ms; at 98.458 ms before 111.481 ms; and at 97.860 ms
  before 112.317 ms. These are the exact overlap conditions that deadlocked
  the old shared blocking-pool completion path. All requests still completed
  normally.
- **Immutable preservation:** the exact raw result first copied and verified
  at 1,308 files, 21,887,310 bytes, content-tree SHA-256
  `sha256:4a568a61eb11681e2323d5e694a0e130e87c52acaa193a0db8ebcde4f1ae667e`.
  The self-contained diagnostic corpus at
  `experiments/diagnostics/starvation-019fb5dd-ff1e` additionally preserves
  the validated source plan, outer command result/stderr, exact cleanup proof,
  and machine-readable acceptance audit. Its final inventory is 1,313 files,
  21,891,244 bytes, content-tree SHA-256
  `sha256:df031fff42b8b4553c08ead617d029d98f25f73e42c3776dcd57c883047f5357`.
- **Cleanup:** the independent proof found no run- or gateway-labeled
  container or volume, no matching product process, no run workspace, no
  runtime scope, clean product `main`, and the exact recorded treatment.
  Explicit benchmark cleanup then exited 0 with `cleaned: true`. A terminal
  result copy remains in `.benchmark-state/results` by benchmark design and
  is not a live resource or leak. Rechecks found zero candidate processes and
  zero matching Docker resources.
- **Disposition:** passed. The Tokio blocking-pool starvation correction is
  qualified under the exact previously failing concurrency/sampling timing.
  A fresh full `paper-env-smoke` on treatment `06f52dfb` is now authorized.
  Pilot, freeze, and final remain blocked until that smoke is preserved and
  passes all 19-cell correctness, resource, and cleanup gates.

### 2026-07-31T01:57:21.540Z - Fresh 06f52dfb smoke preflight

- **Entry ID:** `exp1-06f52dfb-smoke-preflight-065`.
- **Phase/kind:** EXP1-C strict fast preflight; no live preset in this entry.
- **Plan:** `paper-env-smoke` revalidated runnable and customized with zero
  findings or warnings at
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`,
  exactly 19 cells, 19 trial batches, and 55 issued operation requests. It
  selects only `product_cli` and `paper-100m`.
- **Treatment:** product remains clean `main` at
  `06f52dfbadc923b80840dd6d156bb7f026519e19`. Package archive, daemon,
  gateway, manager, runtime, and observability hashes remain respectively
  `34f2bf79...12d512`, `dfec6818...ca282`, `cb36cc7c...b463`,
  `032187d0...eac6`, `3ada794f...349`, and `406ca3fa...dfc3`.
- **Environment/ownership:** the fixed local image digest matches exactly;
  C: has 571,759,853,568 free bytes; the benchmark runtime directory is
  empty; and no candidate-package process, gateway-labeled container, or
  gateway-labeled volume is active. The unrelated debug gateway remains out
  of scope and untouched.
- **Prior diagnostic integrity:** the accepted starvation-reproduction archive
  independently re-verifies at 1,313 files, 21,891,244 bytes, content-tree
  SHA-256
  `sha256:df031fff42b8b4553c08ead617d029d98f25f73e42c3776dcd57c883047f5357`.
- **Clock boundary/disposition:** no build, install, pull, source mutation,
  dependency change, environment reconfiguration, or unrelated cleanup may
  occur from smoke start through terminal artifact production. One fresh
  `paper-env-smoke` command is authorized. Pilot, freeze, and final remain
  blocked.

### 2026-07-31T02:11:14.819Z - Fresh 06f52dfb CLI integration smoke passed

- **Entry ID:** `exp1-06f52dfb-smoke-pass-066`.
- **Phase/kind:** EXP1-C live CLI integration smoke.
- **Run/identity:** run `019fb5e4-3f62-7760-bc3f-e7501502ec74` issued the
  validated `paper-env-smoke` preset against
  `target\windows-exp1-06f52dfb\bin` with
  `PYTHONDONTWRITEBYTECODE=1`. At-run product, package, daemon, all four
  native Windows executables, image, host, sandbox limits, fixture, analysis
  source, and plan identities match Entry 065. No build, install, pull,
  source mutation, dependency change, or environment reconfiguration occurred
  during the run clock.
- **Start/end/elapsed:** `2026-07-31T01:57:44.888263Z` to
  `2026-07-31T02:05:39.454170Z`, or 474.565907 seconds of manifest time.
  The outer command flushed its terminal JSON at
  `2026-07-31T02:09:47.734Z`, 248.281 seconds later, while off-clock Python
  workers drained at near-zero wrapper CPU. No benchmark result uses that
  wrapper-drain time.
- **Outcome:** state `completed`, correctness `pass`, all 19 cells, all 19
  measured trial batches, all 55 planned operation requests, all 48
  registered correctness checks, and all 19 operation-evidence records passed.
  There are zero product, correctness, infrastructure, cleanup,
  missing-primary-latency, or warning counts.
- **CLI evidence:** all 462 primary, setup, verification, observability, and
  cleanup CLI invocations returned code 0, passed response validation,
  emitted zero stderr bytes, had unique request IDs, and preserved
  authentication redaction.
- **Resource audit:** the corpus contains 602 resource records. All 72
  required non-`create_sandbox` metric/trial combinations for
  `upperdir_bytes`, sandbox CPU time, block reads, and block writes have
  exactly two available non-periodic boundaries. The five scheduled sampling
  collections are retained. For `create_sandbox`, both recorded boundaries
  for each sandbox counter are explicitly unavailable because a
  sandbox-scoped pre-create baseline cannot exist; none is fabricated as
  zero. Host allocated bytes and LayerStack allocated storage remain
  explicitly unavailable in 43 readings each for the disclosed
  platform/product reasons.
- **Correlation boundary:** each of the 18 post-create cells has one eligible
  CPU/latency point; `create_sandbox` has zero because its CPU delta is
  inapplicable. Every coefficient interval is omitted as `insufficient_n`.
  The first read-only audit helper incorrectly assumed the omission was an
  object rather than its schema-defined string, raised `TypeError`, and
  changed no artifact; the corrected helper then passed all boundary and
  correlation assertions.
- **Immutable archive:** archive
  `experiments/runs/019fb5e4-3f62-7760-bc3f-e7501502ec74` contains 1,442
  files and 18,936,678 bytes with content-tree SHA-256
  `sha256:35023c597b7218af971bac1e317712d24651d82a00510fc2e6d2907ecb12b9bc`.
  Archive creation plus two independent verify-only invocations matched
  exactly.
- **Cleanup:** the archive proof and independent terminal recheck found no
  run- or gateway-labeled container or volume, matching product process, run
  workspace, or runtime scope; product remains clean `main` at the recorded
  treatment. Explicit benchmark cleanup exited 0 with `cleaned: true`.
- **Disposition:** EXP1-C passes for the corrected `06f52dfb` treatment. One
  fresh exploratory five-sample `paper-pilot` is now authorized. Freeze and
  final remain blocked until that pilot is preserved and passes correctness,
  resource correlation, deterministic table regeneration, runtime projection,
  anomaly review, and cleanup.

### 2026-07-31T02:12:15.605Z - Replacement five-sample pilot preflight

- **Entry ID:** `exp1-06f52dfb-pilot-preflight-067`.
- **Phase/kind:** EXP1-D strict fast preflight; no live pilot in this entry.
- **Plan:** `paper-pilot` revalidated runnable and customized with zero
  findings or warnings at
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`,
  exactly 19 cells, 133 trial batches, and 385 issued operation requests. It
  selects only `product_cli` and `paper-100m`, with two warmups and five
  measured trials per cell.
- **Treatment:** product remains clean `main` at
  `06f52dfbadc923b80840dd6d156bb7f026519e19`; package, corrected daemon, and
  all four native Windows executable hashes match Entries 062 and 065.
  The fixed local image digest matches exactly.
- **Environment/ownership:** C: has 571,460,431,872 free bytes; the benchmark
  runtime directory is empty; and no candidate-package process,
  gateway-labeled container, or gateway-labeled volume is active. The
  unrelated debug gateway remains outside campaign ownership.
- **Prior-gate integrity:** the corrected-treatment smoke archive independently
  re-verifies at 1,442 files, 18,936,678 bytes, content-tree SHA-256
  `sha256:35023c597b7218af971bac1e317712d24651d82a00510fc2e6d2907ecb12b9bc`.
- **Clock boundary/disposition:** no build, install, pull, source mutation,
  dependency change, environment reconfiguration, or unrelated cleanup may
  occur from pilot start through terminal artifact production. Exactly one
  replacement exploratory `paper-pilot` command is authorized. Its values are
  permanently ineligible for manuscript tables; freeze and final remain
  blocked.

### 2026-07-31T02:33:19.464Z - Replacement five-sample pilot passed and archived

- **Entry ID:** `exp1-06f52dfb-pilot-pass-068`.
- **Phase/kind:** EXP1-D live five-sample exploratory pilot; permanently
  ineligible for manuscript tables.
- **Run/identity:** run `019fb5f1-d73a-7128-9bab-d75dd229c020` issued the
  validated `paper-pilot` preset against
  `target\windows-exp1-06f52dfb\bin` with
  `PYTHONDONTWRITEBYTECODE=1`. At-run treatment is clean product `main` at
  `06f52dfbadc923b80840dd6d156bb7f026519e19`; package, corrected daemon,
  native CLIs, image, host, sandbox limits, fixture, benchmark source, and
  plan identities match Entry 067. No build, install, pull, source mutation,
  dependency change, or environment reconfiguration occurred during the run
  clock.
- **Start/end/elapsed:** `2026-07-31T02:12:35.693691Z` to
  `2026-07-31T02:22:44.909649Z`, or 609.215958 seconds of manifest time.
  The outer command flushed its terminal JSON at
  `2026-07-31T02:27:22.644Z`, 277.734 seconds later, during the known
  off-clock worker drain. No benchmark result uses wrapper-drain time.
- **Terminal outcome:** state `completed`, correctness `pass`, all 19 cells,
  all 133 trial batches, 38 warmups, 95 of 95 reportable measured trials, all
  385 issued operation requests, all 336 trial check records, and all 133
  operation-evidence records passed. Every cell has exactly two warmups and
  five successful measured trials. There are zero product, correctness,
  infrastructure, cleanup, missing-primary-latency, or warning counts.
- **CLI evidence:** all 2,966 primary, setup, verification, observability, and
  cleanup CLI invocations returned code 0, passed response validation,
  emitted zero stderr bytes, had unique request IDs, and preserved
  authentication redaction.
- **Resource/correlation audit:** the archive has 4,298 resource records.
  All 504 required non-`create_sandbox` metric/trial pairs for upperdir
  allocation, sandbox CPU, block reads, and block writes have exactly two
  available non-periodic boundaries. All 21 create-sandbox counter/trial
  pairs have exactly two explicitly inapplicable boundaries because no
  sandbox-scoped pre-create baseline can exist. The 41 periodic sample
  collections are retained. Six transition-time periodic upperdir readings
  are explicitly unavailable as incompletely reported; every corresponding
  mandatory boundary is available. Six create-sandbox memory boundary
  readings explicitly report that the resource ring is not available yet;
  the measured report still has complete post-create memory values. Host
  allocated bytes and LayerStack allocation remain explicitly unavailable as
  already disclosed. Each post-create cell has five aligned CPU/latency
  points and zero correlation exclusions; `create_sandbox` has zero by the
  counter-inapplicability rule.
- **Immutable archive:** archive
  `experiments/runs/019fb5f1-d73a-7128-9bab-d75dd229c020` contains 9,068
  files and 102,646,127 bytes with content-tree SHA-256
  `sha256:80658973aec8449bca7a3b8880a1b25ad15ee38ee1a9229b450aaca0fa62536e`.
  The first supervised archive invocation exceeded its 60-second shell
  timeout after the archiver had atomically installed the complete target;
  it left no staging duplicate and no archiver process. No archive retry was
  issued. Two subsequent verify-only invocations matched the inventory and
  hash exactly.
- **Cleanup:** the archive proof and independent terminal recheck found no
  run- or gateway-labeled container or volume, matching product process, run
  workspace, or runtime scope; product remains clean at the exact treatment.
  Explicit benchmark cleanup exited 0 with `cleaned: true`.
- **Disposition:** functional, correctness, resource, correlation, evidence,
  and cleanup portions of EXP1-D passed. Pilot data remain exploratory and
  ineligible. Gate 3 still requires deterministic table regeneration,
  runtime projection at or below 20 minutes, and anomaly review before freeze.

### 2026-07-31T02:33:19.464Z - Pilot tables deterministic; runtime projection blocks Gate 3

- **Entry ID:** `exp1-06f52dfb-pilot-analysis-blocker-069`.
- **Phase/kind:** EXP1-D immutable exploratory analysis and Gate-3 capacity
  decision; no live preset.
- **Deterministic tables:** generator
  `sha256:37f2dddec2684b6eb2682c65ebdb4750b3a4f795596045ec05da827f06dff7e3`
  regenerated all four expected tables twice from only the immutable pilot
  archive. Outputs
  `experiments/analysis/pilot-06f52dfb-tables-a` and `-b` are byte-identical:
  nine files, 228,981 bytes, content-tree SHA-256
  `sha256:7e142a8ee03477f807b1c29e68b5adfb00c03835d73e5eff92e0237dcbe9db24`.
  Their numeric-evidence v2 registry and numeric provenance are explicitly
  `exploratory_ineligible`; no pilot value may be copied into the manuscript.
- **Table component hashes:** environment
  `28028724...f752`, startup `a677b019...0fd7`, CLI operations
  `ad280978...3c8b`, resources `895bf303...de8d`, tables JSON
  `085fdcc4...20ed`, numeric evidence `e994a991...b771`, and provenance CSV
  `39a8eb6a...33c9`.
- **Runtime projection:** the immutable
  `project_exp1_final_runtime.py` source is
  `sha256:88604b889bd480f52a886781bc1ece922a09fc267703dde00476f1a702ad52b6`.
  Projection output
  `experiments/analysis/pilot-final-runtime-projection-06f52dfb.json` is
  SHA-256
  `6a4c0e3f7133aee4c138ac5f99d0ce0cf1ee6d05fbddd2eebe5efe4f29e98552`.
  Smoke and pilot identities match exactly. The completed pilot is a
  609.215958-second monotonic lower bound; the affine model estimates
  452.124232 fixed seconds plus 1.181141 seconds per trial batch, yielding
  2,741.175099 seconds (45.686252 minutes) for the fixed 1,938-batch final.
  Direct proportional scaling yields 8,877.146817 seconds. Even the optimistic
  model exceeds the fixed 1,200-second limit.
- **Decision/blocker:** `gate_3_runtime_pass: false`,
  `block_freeze_and_final_runtime_projection_exceeds_20_minutes`. This is a
  mandatory protocol stop, not a manuscript result. Freeze, tag, and the
  exactly-once final command remain prohibited. Read-only subagents are
  decomposing phase/gateway/CLI costs and auditing the product
  `create_sandbox` plus harness setup paths for a protocol-preserving speed
  correction. Any source correction will require focused tests, a new
  treatment package, bounded qualification, fresh smoke, and a fresh
  exploratory pilot before Gate 3 can be reconsidered.

### 2026-07-31T02:58:13.077Z - Pre-freeze CLI evidence I/O acceleration

- **Entry ID:** `amendment-exp1-cli-evidence-io-070`.
- **Phase/kind:** EXP1-D pilot review and pre-freeze harness correction; no
  live preset.
- **Trigger:** every retained CLI invocation re-read and hashed the same
  checksum-pinned executable and independently flushed immutable stdout,
  stderr, and metadata files. The accepted pilot retained 2,966 such
  invocations, so this paper-local evidence path was a repeated fixed-cost
  component outside the primary operation timing.
- **Executable identity correction:** `ProductCliAccess` now computes each of
  the manager, runtime, and observability executable SHA-256 values exactly
  once at instance construction and reuses the immutable values in every
  invocation record. The fixed campaign forbids product-package mutation
  during a run, so this preserves the existing executable identity contract.
- **Durable evidence contract:** schema-v2 metadata losslessly embeds the
  already-redacted stdout and stderr byte streams as base64, with their exact
  lengths and SHA-256 values. The normal on-disk layout remains exactly three
  immutable files per invocation: `.stdout`, `.stderr`, and `.json`.
  Stdout/stderr are closed immutable projections written without individual
  flushes; the self-contained metadata file is written last and fsynced as
  the sole durable `metadata-packed-payload-fsync-v1` commit marker. POSIX
  additionally syncs the evidence directory; the Windows helper remains a
  deliberate no-op because this optimization targets the qualified NTFS
  host.
- **Crash/failure behavior:** a failed metadata write or flush removes the
  marker, retains any redacted immutable projection orphans as failure
  evidence, and an identical request cannot overwrite them because all three
  files use exclusive creation. If an NTFS crash loses or tears an unflushed
  projection after the marker commits, the marker still contains the exact
  redacted bytes needed for reconstruction. Archive verification decodes and
  authenticates the packed streams, rejects malformed markers, unsafe or
  missing projection paths, projection/packed mismatches, and any size or
  digest mismatch. It never silently accepts a partial record.
- **Bounded-evidence size control:** packed byte fields exist only in the
  durable `.json` marker. They are explicitly omitted from the compact
  `transport_evidence` returned to request observations, so the packed payload
  is not duplicated into journals or bounded trial evidence.
- **Artifact journal audit:** `ArtifactStore.append_records` already writes
  each caller-supplied record batch with one append and one fsync, while
  recovery quarantines a partial tail and durably truncates to the last
  complete newline. No additional proven trial-level barrier exists, so
  journal durability, `artifacts.py`, `runner.py`, and
  `resource_sampling.py` were not changed.
- **Focused verification:** product-CLI and archive evidence tests passed
  31/31 in 1.36 seconds with `PYTHONDONTWRITEBYTECODE=1`. Coverage includes
  once-per-instance executable hashing, one NTFS fsync for the three-file
  record, exact layout and redaction, packed-stream reconstruction, compact
  transport evidence, failed marker flush cleanup, immutable orphan retry
  refusal, and marker/projection/path/hash corruption rejection.
- **Complete backend verification:** all 233 tests passed with five expected
  Windows WinError 1314 symlink-privilege skips in 36.62 seconds under
  `PYTHONDONTWRITEBYTECODE=1`.
- **Disposable NTFS diagnostic:** five alternating rounds of 40 invocations
  per method compared the inherited three-fsync layout with the new packed
  metadata commit using the same three files. Median latency was 9.980020
  milliseconds per invocation versus 4.317100 milliseconds, a diagnostic
  saving of 5.662920 milliseconds and 2.312x speedup. The system temporary
  directory was removed automatically. These values are pre-freeze
  engineering diagnostics and are ineligible for manuscript tables.
- **Protocol stability:** no preset, definition, cell, repetition, warmup,
  concurrency, metric, success, retry, exclusion, timeout, or analysis rule
  changed. The existing official identities/counts therefore remain smoke
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  (19/19/55), pilot
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`
  (19/133/385), and final
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`
  (19/1,938/5,610).
- **Files changed:** `benchmark/backend/benchmark_lab/product_cli.py`,
  `benchmark/backend/tests/unit/test_product_cli.py`,
  `experiments/scripts/archive_exp1_run.py`,
  `benchmark/backend/tests/unit/test_exp1_archive.py`, and this append-only
  log.
- **Source identities:** `product_cli.py`
  `sha256:145c13646af0bcd35196da18c638707fbd5a9f1a087ff435a946367a5dcab19d`,
  its unit test
  `sha256:d6040ca0436fd7c1a77a560e00f4d55f53f2a35e5d6c8ed140c8ef108672e295`,
  archive verifier
  `sha256:25cca63e4acc035a60384dce11221d6571a10ccd1bdf5b3a39e0e7a0d027426e`,
  and its unit test
  `sha256:a2a0fb0e0d91bea42c25d3f946ead02eeb854bac514191f6521a09313339e250`.
- **Cleanup/scope:** no live gateway, sandbox, Docker object, fixture, product
  checkout, preset, or measurement corpus was touched. No live performance
  command ran.
- **Disposition:** implementation and offline validation passed. This removes
  a demonstrated fixed CLI-evidence cost but does not by itself clear Gate 3;
  the combined corrected harness still requires bounded qualification, a
  fresh smoke, and a fresh exploratory pilot before freeze or final can be
  reconsidered.

### 2026-07-31T03:06:50.782Z - Pre-freeze sampling and independent-work acceleration

- **Entry ID:** `amendment-exp1-sampling-independent-work-071`.
- **Phase/kind:** EXP1-D pilot review and pre-freeze harness correction; no
  live preset.
- **Trigger:** the accepted exploratory pilot showed mandatory resource
  boundaries, independent fixture setup, and paged correctness reads as
  repeated untimed costs. Mandatory resource collection alone increased by
  47.450 seconds over the 114 smoke-to-pilot incremental batches.
- **Sampling correction:** the mandatory product boundary, host/workspace
  metrics, and daemon observation now start concurrently. Boundary failure
  remains fatal, while the established unavailable-field behavior is
  preserved for dynamic and daemon collectors. The boundary poll interval is
  100 milliseconds, matching the newly qualified Windows product ring and
  avoiding repeated CLI polls against one generation.
- **Independent work correction:** fixture writes for independent read,
  write, and edit targets execute concurrently. Verification reads and
  attribution checks for independent targets also execute concurrently.
  Exact reads still establish the bounded page contract from the first page,
  then fetch all remaining deterministic pages concurrently and validate
  every offset, line count, byte count, total, and payload before assembly.
- **Timing/protocol stability:** setup, verification, resource collection, and
  teardown remain outside the primary operation interval. No operation,
  preset, cell, repetition, warmup, concurrency, payload, metric, success,
  retry, exclusion, or analysis rule changed.
- **Focused verification:** 37 runner/resource tests passed in 5.26 seconds
  under `PYTHONDONTWRITEBYTECODE=1`.
- **Complete verification:** the subsequent combined backend suite, including
  the run-scoped cache tests below, passed 238 tests with five expected
  Windows symlink-privilege skips in 40.48 seconds.
- **Files/source identities:** `resource_sampling.py`
  `sha256:a9a9c420d0726907b51eb2a28371f5967f210eaefd35ccb130fd7968594befdd`;
  `runner.py`
  `sha256:768d0eb2b8c9f7f3c51034788cecc88181cf3962d8ab6553cdea718d4aacaeed`;
  resource tests
  `sha256:76c98df12c0a33eae58ffc22f618e1532ddd53bf79780cb2509a592e12676d46`;
  runner tests
  `sha256:eab9c477e803927aec777cacab9cda95a5417dd03d3ecfbf86f54d689d7a6f41`.
- **Cleanup/scope:** no live gateway, sandbox, Docker object, fixture,
  package, or preset was run or mutated.
- **Disposition:** offline correction passed. Gate 3 remains blocked pending a
  rebuilt exact product package, bounded qualification, fresh smoke, and a
  fresh exploratory pilot.

### 2026-07-31T03:06:50.782Z - Run-scoped shared-base cache for create_sandbox

- **Entry ID:** `amendment-exp1-run-scoped-shared-base-cache-072`.
- **Phase/kind:** EXP1-D pilot review and pre-freeze `create_sandbox`
  correction; no live preset.
- **Trigger:** the first sandbox created under each isolated gateway family
  spent about 42 seconds reseeding the same content-addressed Docker shared
  base after intermediate cleanup removed both the host cache and volume.
  Warm measured sandbox creation was approximately 1.8--2.0 seconds.
- **Correction:** every isolated gateway in one campaign receives the same
  owned run-scoped `EOS_SHARED_BASE_CACHE`. Intermediate cleanup may retain
  only a volume whose content-addressed name and complete gateway/root/target/
  readonly label proof validate. Ordinary volumes and all containers are
  still removed.
- **Final cleanup proof:** the runner records every unique gateway identity and
  performs a mandatory final Docker sweep across all of them on success,
  operation failure, cleanup failure, and cancellation. A retained volume is
  removed through its original owner identity even after later gateways reuse
  it. Ambiguous ownership fails closed. Stale-gateway recovery and failed
  startup always request full cleanup and never retain volumes.
- **Cross-gateway verification:** two distinct gateway identities for the same
  run receive the identical cache directory; the first close retains the
  validated shared volume, a later non-owner sweep cannot claim it, and final
  cleanup removes it through the original owner. Runner success, failure, and
  cancellation paths all assert finalization.
- **Focused verification:** 38 tests passed with one expected Windows symlink
  skip. Scoped Ruff formatting/import checks and `git diff --check` passed.
- **Complete verification:** 238 backend tests passed with five expected
  Windows symlink-privilege skips in 40.48 seconds under
  `PYTHONDONTWRITEBYTECODE=1`.
- **Files/source identities:** `gateway.py`
  `sha256:f8e1e55699e351f76f64ffb7079a7852596ee52e02f209452543edde5025f85d`;
  `runner.py`
  `sha256:768d0eb2b8c9f7f3c51034788cecc88181cf3962d8ab6553cdea718d4aacaeed`;
  gateway lifecycle tests
  `sha256:cd5dbf28570111c282733809a33bd607485d531338945c0c1c722393264c791d`;
  runner tests
  `sha256:eab9c477e803927aec777cacab9cda95a5417dd03d3ecfbf86f54d689d7a6f41`.
- **Cleanup/scope:** no live sandbox, gateway, Docker command, preset, fixture,
  or measurement corpus was run or mutated.
- **Disposition:** offline correction passed. It removes repeated fixed
  create-sandbox cold work but cannot clear Gate 3 without fresh measurements.

### 2026-07-31T03:06:50.782Z - Product cadence and termination-aware teardown

- **Entry ID:** `amendment-exp1-product-cadence-holder-073`.
- **Phase/kind:** EXP1-D pilot-discovered product performance corrections
  before freeze; no live preset.
- **Resource-ring evidence:** corrected pilot cgroup samples had a 256
  millisecond median generation delta and workspace snapshots had a 251
  millisecond median, while the fixed campaign requires 100 millisecond
  resource sampling. Mandatory boundaries therefore waited and repolled a
  250-millisecond product ring.
- **Cadence correction:** the committed Windows release configuration now uses
  a 100-millisecond resource sampling interval. The observability
  configuration's documented/validated minimum is 100 milliseconds, its edge
  test rejects 99 milliseconds, and the committed Windows configuration guard
  asserts the exact 100-millisecond value.
- **Recorded failed validation:** after changing only the Windows release
  value, `cargo test -p sandbox-config --all-features` failed 1 of 79 tests
  because the then-current validator still rejected values below 250
  milliseconds. This exposed the incomplete correction; no result was hidden.
- **Corrected validation:** after aligning the validator and edge tests,
  `cargo test -p sandbox-config --all-features` passed 79/79,
  `cargo fmt --all --check` passed, and
  `cargo clippy -p sandbox-config --all-targets --all-features -- -D warnings`
  passed. Commit `4a05a9563c1d2920caec79da85b6d88a74cec2c0`
  (`perf(observability): align Windows resource cadence`) contains this
  correction.
- **Holder-teardown evidence:** exploratory phase decomposition showed 84
  incremental session destroys consuming 11.53 subprocess-seconds. The
  holder supervisor's 50-millisecond idle cadence could delay observation
  after termination had already started.
- **Holder correction:** idle polling remains 50 milliseconds. While any
  owned holder has an active termination attempt, the supervisor caps its
  poll interval at 5 milliseconds. Sole-child ownership, wait/reap, grace
  deadline, escalation, and finalization proof semantics are unchanged.
- **Holder validation:** all 30 holder tests passed under WSL; the new focused
  regression, library build/test, scoped Clippy with `-D warnings --no-deps`,
  `cargo fmt --check`, and `git diff --check` passed. Native Windows telemetry
  still has the previously known unrelated Unix-only `rustix::fs` build
  failure; the broader WSL package test still has the existing
  `tests/holder_lifecycle.rs:361` E0521 failure; unscoped Clippy still has the
  existing telemetry `byte_char_slices` lint. Commit
  `57b437ba60a2304e896e7345f13e6bc43f431f55`
  (`perf(runtime): accelerate pending holder teardown`) contains this
  correction.
- **Product source identities:** Windows config
  `sha256:987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`;
  observability validator
  `sha256:b709d3054d6ab06a803778f48749f4fd31cf869e2ff05e290655964ce3a1641e`;
  validator tests
  `sha256:7505b5455c72d9476318a3dcd02a385e7a89084b13e3848461b69e2bcf40f729`;
  holder supervisor
  `sha256:424d13b90d282a78dcfd7928e38088ff90c2c3f9de26111e01255be0073af301`;
  holder tests
  `sha256:f5a741b463fc1e6740fc4ba775e49522cd1a7e5e3e8efbe1e2db65cc98500a17`.
- **Repository state:** product remains direct clean `main`; no branch,
  worktree, tag, or push was created. The new treatment commit is
  `57b437ba60a2304e896e7345f13e6bc43f431f55`.
- **Cleanup/scope:** no live sandbox, gateway, Docker command, preset, fixture,
  or measurement corpus ran during either product correction.
- **Disposition:** product corrections passed their proportional offline
  validation. Release binaries must be rebuilt from the exact new commit
  before bounded qualification, smoke, or pilot. Freeze and final remain
  blocked.

### 2026-07-31T03:10:49.371Z - Exact 57b437ba treatment package rebuild

- **Entry ID:** `validation-exp1-package-57b437ba-074`.
- **Phase/kind:** EXP1-D pre-freeze off-clock treatment build; no live preset.
- **Precondition:** product was clean direct `main` at
  `57b437ba60a2304e896e7345f13e6bc43f431f55`.
- **Recorded failed attempt:** the first direct
  `target\debug\xtask.exe package --builder zigbuild --target
  x86_64-unknown-linux-musl` invocation was issued with an insufficient
  command-runner timeout and exited 124 after approximately five seconds. A
  filtered process check found no surviving `xtask`, `cargo`, or `rustc`
  process. This was a build-orchestration failure, not a live benchmark
  attempt.
- **Linux daemon build:** the same exact xtask command was reissued off-clock
  under a hidden process with bounded log capture and exited 0. It produced
  `dist\sandbox-daemon-linux-amd64`, 7,171,600 bytes,
  `sha256:f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`.
- **Windows package build:** `bin\package-windows-amd64-release.ps1
  -PackageName windows-exp1-57b437ba -OutDir target -Profile release`
  exited 0. The release gateway build took 1 minute 1 second; the three CLI
  target checks completed from cache.
- **Candidate package:** absolute directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-57b437ba`;
  ZIP
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-57b437ba.zip`,
  5,651,981 bytes,
  `sha256:0d6a784a5447ef012d03d4b8742beac0693f30766e14c2bd9dc4c53e9c4cb359`.
- **Packaged identities:** gateway 3,320,832 bytes,
  `sha256:526ba4e1b90b38d8605475b4ad1e53ded12eeef396cb533acfe0d1c90854dfaa`;
  manager CLI 819,712 bytes,
  `sha256:032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`;
  runtime CLI 825,344 bytes,
  `sha256:3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`;
  observability CLI 819,200 bytes,
  `sha256:406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`;
  packaged daemon identity as above; packaged Windows config 1,997 bytes,
  `sha256:987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Config guard:** the packaged Windows config contains
  `sample_interval_ms: 100`.
- **Postcondition:** product remained clean direct `main` at the same commit.
  No tag or push was created.
- **Cleanup/scope:** no live gateway, sandbox, Docker command, preset, fixture,
  or measurement corpus was run. Build logs remain under `target` as
  off-clock diagnostics.
- **Disposition:** exact treatment package build passed. The package is not
  frozen and cannot be used for final measurement until the remaining
  paper-source corrections pass, bounded qualification and fresh smoke/pilot
  pass, and Gate 3 clears.

### 2026-07-31T03:19:47.510Z - Trial hot-path consolidation and shared daemon observation

- **Entry ID:** `amendment-exp1-trial-hot-path-consolidation-075`.
- **Phase/kind:** EXP1-D pilot review and pre-freeze paper-harness correction;
  no live preset.
- **Session mutation baseline:** session-destination `file_write` and
  `file_edit` cells now publish their deterministic baseline paths once during
  cell setup. Every trial still creates and destroys a fresh shared-network
  no-op session and begins from the unchanged published snapshot. Independent
  and same-target semantics, measured operation timing, verification,
  attribution, and cleanup are unchanged. Publish-destination cells retain
  per-trial preparation because they do not have a reusable cell context.
- **Daemon observation consolidation:** product `cgroup` responses already
  contain the same daemon process metrics under
  `topology.daemon`. A shared strict `DaemonProcessMetrics` model now validates
  both the standalone shape and extraction from the exact cgroup response.
  Mandatory and periodic samplers make no redundant standalone daemon CLI
  subprocess. Missing or malformed embedded metrics preserve the prior
  unavailable-field behavior with an explicit observability error. Metric
  sources now disclose
  `product_observability.cgroup.topology.daemon`.
- **Trial journal group commit:** trial phase, resource, request observation,
  correctness, operation, and trial records are buffered and committed with
  at most one append/fsync per journal at each trial durability boundary.
  Setup records flush before request admission. Waiting and ready barrier
  states remain independently durable before release, and deferred request
  terminal records retain their existing durable post-batch append. Trial
  preparation is durable before the transaction; success, failure, and
  cancellation flush the grouped records before the terminal trial state.
  Public run-state/cancellation transitions force a preceding flush and remain
  immediately durable. Sequence numbers and event-sink delivery preserve
  commit order.
- **Crash/recovery behavior:** a crash during setup leaves the durable
  preparing state; a crash after request admission leaves the durable
  waiting/ready barrier. A partial grouped append is still handled by the
  existing journal tail quarantine/truncation path. Missing terminal trial
  evidence fails archive completeness and is never silently accepted.
- **Focused validation:** session baseline tests passed 8/8 and the then-current
  runner integration file passed 29/29. Observability/resource tests passed
  39/39, metric derivation passed 6/6, and the mock runner path passed. After
  journal grouping, the complete runner integration file passed 32/32.
  The combined runner/observability/resource/derivation selection passed
  77/77.
- **Complete backend validation:** 254 tests passed with five expected Windows
  symlink-privilege skips in 38.93 seconds under
  `PYTHONDONTWRITEBYTECODE=1`.
- **Recorded validation failures/corrections:** the first formatting command
  attempted `.venv\Scripts\python.exe -m ruff`, which failed because Ruff is
  not installed in that virtual environment. Cached
  `uvx --offline ruff 0.16.1` was used thereafter. The first 32-test runner
  attempt had one failed test because the new synthetic failure-path test
  wrote an intentionally underspecified schema-v5 trial observation and then
  invoked the strict decoder. The invalid synthetic observation was removed;
  the production implementation was unchanged, and all 32 tests passed.
  An unscoped Ruff invocation without the repository's intended rule
  selection reported 39 existing/scoped diagnostics, including broad
  `BaseException` policy, Python-target inference for `BaseExceptionGroup`,
  and one unused import; it was not used as a qualification result. The
  intended scoped import check then exposed one unsorted import block in the
  new observability test, fixed it mechanically, and passed. Final scoped
  import checks and `git diff --check` passed.
- **Files/source identities:** runner
  `sha256:a3c2b26bbc1a095eb8c6a8abc8b64ed8abb86d3c2403c2b2c589ba2cf9c4fd79`;
  observability models
  `sha256:dfc25aa2efce2405ed12d3d73d240fd143aa0506535cbf6ddae56de11c1e1500`;
  resource sampler
  `sha256:434ea0b49f96871ec83fcc474ed5a033b1697fd866ca37c2a7cf6d9d38168e89`;
  runner tests
  `sha256:214ffb815e0580c265fd83fa0e26f3f507e088ae352ec1d5830aa1ce9a81955b`;
  observability tests
  `sha256:a23d8094dd34bda65408189ff0b39d282688542e32c0032a0ab75e8fea91363c`;
  resource tests
  `sha256:5f9633aad13175d1ef26371cc8ec9b2cabd4ad0edb8734b4c251a35247b81ea3`.
- **Timing/protocol stability:** no primary timing boundary, preset, cell,
  repetition, warmup, concurrency, payload, success, retry, exclusion, metric,
  or final analysis rule changed. The daemon metric source disclosure changed
  to its actual containing response before freeze.
- **Cleanup/scope:** no live gateway, sandbox, Docker command, fixture,
  package mutation, preset, or measurement corpus was run.
- **Disposition:** combined offline validation passed. The corrected source
  still requires the preregistered structural runtime projection, bounded
  qualification, fresh smoke, and fresh exploratory pilot before Gate 3 can
  clear.

### 2026-07-31T03:19:47.510Z - 57b437ba packaged CLI help-contract check

- **Entry ID:** `validation-exp1-package-help-076`.
- **Phase/kind:** EXP1-D off-clock static package validation; no gateway.
- **Package:** `target\windows-exp1-57b437ba`, ZIP identity
  `sha256:0d6a784a5447ef012d03d4b8742beac0693f30766e14c2bd9dc4c53e9c4cb359`.
- **Results:** packaged gateway `--help` exited 0, wrote 93 stdout bytes with
  `sha256:1a01a7c60c1ee1507b47b39c47ffab5d843184e9f94b5d49ecc89ab424f57934`,
  and wrote zero stderr bytes. Manager `help` exited 0, wrote 802 stdout bytes
  with
  `sha256:b8c3a96951784a67b8dfd021cc754ec1e58ddd5e3ba83512424721709c576fe5`,
  and zero stderr. Runtime `help` exited 0, wrote 1,137 stdout bytes with
  `sha256:2b2bb48142678f0418d6b01a528e0c79b8de6ab89fafc843d4d660ccd0d7dc5e`,
  and zero stderr. Observability `help` exited 0, wrote 1,026 stdout bytes with
  `sha256:090d943792ace5873bf7099e3f185030474efd73a59fa876a56fa46878f56243`,
  and zero stderr.
- **Security/scope:** the checks required no gateway socket or authentication
  token; only exit status, byte counts, and digests were printed. No live
  sandbox, Docker command, preset, or measurement corpus was touched.
- **Disposition:** static packaged help contracts passed. Live CLI behavior
  remains subject to bounded qualification and fresh smoke.

### 2026-07-31T03:33:17.889Z - Structural Gate 3 runtime projection preregistration

- **Entry ID:** `amendment-exp1-structural-runtime-projection-077`.
- **Phase/kind:** EXP1-D pre-freeze analysis correction and preregistration;
  no live preset.
- **Trigger/defect:** the prior script estimated one slope from two whole-run
  elapsed totals and scaled the smoke-to-pilot delta by final batch count.
  That delta confounded run-, family-, and cell-level fixed setup/cleanup
  variance with trial work, assigned the smoke's one cold trial to steady
  state, verified only four provenance fields, and selected the minimum of two
  candidate projections as its gate. The 20-minute limit was fixed, but this
  projection formula was not preregistered.
- **Structural inputs:** the replacement verifies the complete archive
  inventory/tree hash; terminal disposition, eligibility, correctness, and
  cleanup; raw event/observation/plan hashes; benchmark, fixture, product,
  binaries, config, image, Docker, host, sandbox limits, artifact schema,
  lifecycle, gateway, protocol, and analysis identities; a separately
  supplied reviewed final expanded plan; contiguous schema-v1 event and
  schema-v5 observation journals; and exact product-CLI cell/request/trial
  counts.
- **Semantic matching:** smoke, pilot, and final cells are matched by their
  canonical comparison semantics rather than `cell_id`, because the fixed
  repetition policy changes cell identities. Family/block order and stable
  canonical/effective environment values must agree.
- **Decomposition:** integer monotonic event times partition each run into a
  run residual, family residuals, per-cell leading/trailing fixed work, trial
  active spans, and between-trial gaps. Every interval must be nested,
  ordered, non-overlapping, and nonnegative. Trial phase sums may not exceed
  their event span, and every trial must be successful, reportable when
  measured, checked, cleanup-restored, and matched to its exact request and
  operation observations.
- **Central model:** retain the componentwise maximum smoke/pilot run, family,
  cell-leading, and cell-trailing fixed work once; retain the pilot's two
  observed warmups and their transitions; scale the exact mean of five
  measured trial spans to 100; and scale the exact mean of the four
  measured-to-measured gaps to 99. `Fraction` arithmetic is exact and gating
  uses the ceiling in integer nanoseconds.
- **Observed envelope:** retain the same fixed maxima; use the larger of pilot
  warmups and the smoke cold trial for both final warmups; use the largest
  pilot measured span for all 100 measured trials; and use the largest pilot
  transition gap for all 101 final transitions.
- **Frozen pass rule:** the runtime component passes only if strict
  provenance/structure validation succeeds and all three are at most exactly
  1,200,000,000,000 nanoseconds: completed pilot elapsed, central structural
  projection, and observed-envelope projection. There is no candidate-model
  `min()` selection. Other Gate 3 correctness, resource, determinism,
  anomaly, and cleanup conditions remain independent.
- **Required CLI:** the script now requires `--smoke-archive`,
  `--pilot-archive`, `--final-plan`, and a new nonexisting `--output`. It
  records the final-plan file SHA-256, internal plan hash, script SHA-256,
  exact source archive identities, all decomposition components, rational
  numerators/denominators, integer ceilings, and deterministic display
  seconds. Output is deterministic sorted JSON.
- **Synthetic verification:** the fixed/family/cell decomposition test
  produced exact central `226773/4` nanoseconds (ceiling 56,694),
  envelope 82,861 nanoseconds, and proved each fixed component is retained
  once.
- **Immutable negative control:** strict parsing of accepted corrected smoke
  `019fb5e4-3f62-7760-bc3f-e7501502ec74` and corrected exploratory pilot
  `019fb5f1-d73a-7128-9bab-d75dd229c020` produced pilot elapsed
  609.215958000 seconds, central 2460.664462900 seconds, and envelope
  2745.098529500 seconds. Conditions were true/false/false and Gate 3
  remained FAIL. These are engineering/gate diagnostics and remain
  ineligible for manuscript tables.
- **Scientific decision:** this is a logged post-pilot instrumentation
  amendment with explicit gate-gaming risk. It is accepted before the next
  corrected pilot because it fixes structural confounding, is more
  conservative than the former optimistic selector, and does not reverse the
  observed FAIL decision. The formula and pass rule may not be changed after
  viewing the next pilot without a new logged protocol amendment and another
  pilot.
- **Focused tests:** two projection tests passed first in 4.28 seconds and
  again after independent review/formatting in 3.94 seconds under
  `PYTHONDONTWRITEBYTECODE=1`.
- **Recorded validation failures/corrections:** the first ad hoc importlib
  inspection omitted registering the temporary module in `sys.modules`, so
  Python dataclass processing raised `AttributeError`; the corrected
  inspection registered it and strictly loaded both archives. A broad
  recursive search for an existing final plan timed out after 14 seconds;
  it made no changes. The first Ruff format-check correctly reported the two
  new files would be reformatted; formatting was applied. The next scoped
  import check reported both new import blocks; mechanical import sorting
  fixed them, after which format, import, tests, and `git diff --check`
  passed.
- **Files/source identities:** structural projection
  `sha256:d6126902dac9bddd868be57425fb1f29d0e1ec95cf4a9c8aa14cdfbaeb694afc`;
  tests
  `sha256:f31ecb3a89d5066fad342c952d95bb8b8186acf7b3dce1cdb6684a8263428c69`.
- **Cleanup/scope:** no live gateway, sandbox, Docker command, fixture,
  package mutation, preset, or measurement corpus was run or changed.
- **Disposition:** the structural projection is now the fixed Gate 3 runtime
  rule for the next corrected smoke/pilot pair. The old 06f52dfb projection
  remains immutable historical failure evidence and cannot qualify the new
  treatment.

### 2026-07-31T03:33:17.889Z - Final combined offline backend validation before live qualification

- **Entry ID:** `validation-exp1-pre-live-backend-078`.
- **Phase/kind:** EXP1-D pre-live complete backend validation; no live preset.
- **Recorded failed attempt:** the first complete-suite invocation used a
  five-second shell timeout and exited 124 before completion. It was an
  orchestration timeout, not a test failure and not a live benchmark attempt.
- **Corrected command/result:** with
  `PYTHONDONTWRITEBYTECODE=1`,
  `.venv\Scripts\python.exe -m pytest benchmark\backend\tests -q` exited 0:
  256 tests passed and five expected Windows symlink-privilege tests skipped
  in 41.83 seconds.
- **Formatting/static result:** the two projection files pass cached
  `uvx --offline ruff 0.16.1` format and scoped import checks. The complete
  modified runner/gateway/observability/resource file set passed scoped import
  checks after the recorded mechanical correction, and `git diff --check`
  passed with only expected line-ending warnings.
- **Product postcondition:** product remains clean direct `main` at
  `57b437ba60a2304e896e7345f13e6bc43f431f55`; exact package
  `windows-exp1-57b437ba` remains unchanged.
- **Cleanup/scope:** no live gateway, sandbox, Docker command, fixture,
  package mutation, preset, or measurement corpus was run.
- **Disposition:** all current paper-harness and analysis corrections pass
  offline validation. The next authorized step is bounded live qualification
  of the exact package/source, followed by a new smoke and exploratory pilot;
  freeze/final remain prohibited until the new structural Gate 3 rule passes.

### 2026-07-31T03:35:05.829Z - Exact plan validation and structural negative-control CLI

- **Entry ID:** `validation-exp1-plans-structural-cli-079`.
- **Phase/kind:** EXP1-D pre-live static plan and analysis validation; no live
  preset.
- **Recorded failed attempt:** the first three validation commands invoked
  `python -m benchmark_lab.cli`. That module defines `main` but is not the
  executable module, so each process exited 0 with zero stdout/stderr and did
  not validate a plan. The six zero-byte files with the unsuffixed
  `*-57b437ba-expanded` names are retained as failed orchestration evidence
  and are ineligible inputs.
- **Corrected command:** the executable module is
  `.venv\Scripts\python.exe -m benchmark_lab validate`, with the absolute
  paper root, clean product root, and exact
  `target\windows-exp1-57b437ba\bin` package. All three corrected `-v2`
  commands exited 0 and wrote zero stderr bytes.
- **Smoke expansion:** 19 cells, 19 batches, 55 requests, zero warmups, one
  measured trial per cell, `product_cli`, runnable with zero validation
  findings. Plan hash
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  generated file
  `experiments\analysis\paper-env-smoke-57b437ba-expanded-v2.json`,
  `sha256:c3812cc033c067617a985282615e9672e8d9e9ec606046c68f1b4160bc3031fc`.
- **Pilot expansion:** 19 cells, 133 batches, 385 requests, two warmups and
  five measured trials per cell, `product_cli`, runnable with zero validation
  findings. Plan hash
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  generated file
  `experiments\analysis\paper-pilot-57b437ba-expanded-v2.json`,
  `sha256:3cacb95b7a8e0adaf52067db63c9741a727264b18dde3e966595a6770a129f6e`.
- **Final expansion:** 19 cells, 1,938 batches, 5,610 requests, two warmups and
  100 measured trials per cell, `product_cli`, runnable with zero validation
  findings. Plan hash
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`;
  generated reviewed-plan file
  `experiments\analysis\paper-good-pass-57b437ba-expanded-v2.json`,
  `sha256:6307cc2f485bdbef356d3b370f0eec4f9aa1534636493cb1216843cf7c5347f5`.
- **Plan stability:** the three canonical plan hashes and counts are unchanged
  by the protocol-preserving speed corrections. No plan admits or falls back
  to `direct_client` or `cli_e2e`.
- **End-to-end structural negative control:** the production projection CLI
  consumed the immutable corrected smoke/pilot archives plus the reviewed
  final expansion, exited 0, and emitted the already reviewed FAIL decision:
  pilot 609.215958000 seconds, central 2460.664462900 seconds, observed
  envelope 2745.098529500 seconds; true/false/false. Output
  `experiments\analysis\pilot-final-runtime-structural-06f52dfb-negative.json`,
  44,498 bytes,
  `sha256:5ac734611e301d964bc2de74ec768bca49ea2166f13aa0839fc5bf261f6ee20b`.
- **Eligibility:** these old smoke/pilot values and the projection are
  engineering negative-control evidence only and remain ineligible for
  manuscript tables. They do not qualify commit 57b437ba or its package.
- **Cleanup/scope:** plan validation refreshed only paper-local catalog/state
  metadata and wrote the listed analysis artifacts. No live gateway, sandbox,
  Docker command, fixture, package mutation, smoke, pilot, or final run
  occurred.
- **Disposition:** static plan/product-boundary and structural CLI validation
  passed. Proceed to bounded live qualification of the exact new package and
  source; freeze/final remain prohibited.

### 2026-07-31T03:38:29.404Z - Optimized-package live preflight

- **Entry ID:** `preflight-exp1-optimized-package-080`.
- **Phase/kind:** EXP1-C pre-live qualification; no live preset or measurement
  clock started.
- **Command-surface checks:** `python -m benchmark_lab --help`,
  `python -m benchmark_lab run --help`, and
  `experiments\scripts\archive_exp1_run.py --help` all exited 0 with
  `PYTHONDONTWRITEBYTECODE=1`. The exact runner requires the paper root,
  product root, package `bin` directory, and preset ID.
- **Qualified host:** native Windows AMD64 host `DESKTOP-OLP1ADS`, build
  26200, 48 logical CPUs, 137,438,953,472 bytes physical memory, and
  571,251,810,304 bytes free on `C:` at the check.
- **Qualified Docker/image:** client/server 29.0.1; Linux AMD64 server,
  `overlayfs`, cgroup v2. Exact image
  `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
  is present locally with the same image ID; no pull occurred.
- **Product/package:** clean direct `main` at
  `57b437ba60a2304e896e7345f13e6bc43f431f55`. Exact package archive remains
  5,651,981 bytes with
  `sha256:0d6a784a5447ef012d03d4b8742beac0693f30766e14c2bd9dc4c53e9c4cb359`.
  Gateway, manager, runtime, and observability binary SHA-256 values remain,
  respectively,
  `526ba4e1b90b38d8605475b4ad1e53ded12eeef396cb533acfe0d1c90854dfaa`,
  `032187d0d4b3827ddfc37594ddf3571e6d3510ad52a2d37d222cbbe7db63eac6`,
  `3ada794fea0c6c1c1ed1705bf308d7f60f5fe45242e7ac93d12091c6c011d349`,
  and
  `406ca3fa7c74f9cccb5228fc20cb4c54374dc5472b15685bfc891728e0c5dfc3`.
- **Preserved baseline:** host gateway PID 62980 and the pre-existing stopped
  `eos-gateway` container
  `5ce30657bf836cc332141baf2697192d48ec4553cf41ecf103ef4f1b05175f85`
  remain untouched. Five pre-existing `eos-gateway` volumes remain untouched:
  two sandbox volumes for
  `eos-76263ba1-97f9-475c-9b85-229ab45f87d4` and three validated
  content-addressed shared-base volumes.
- **Recorded diagnostic failures:** two read-only Docker inspection attempts
  used unsupported or incorrectly quoted Go-template expressions and emitted
  template parse errors. They changed no state. A first timestamp command used
  the unavailable Windows PowerShell `Get-Date -AsUTC` parameter and exited 1;
  the corrected UTC conversion exited 0.
- **Corrected ownership inspection:** Docker JSON was parsed in memory and
  projected to non-secret ID/name/status/ownership fields only. It confirmed
  the single labeled container is exited and the five labeled volumes are the
  preserved baseline above. Authentication labels were neither printed nor
  logged.
- **Disposition:** the exact optimized source/package and qualified
  environment pass the no-build/no-install/no-pull preflight. Freeze and final
  remain prohibited until a fresh smoke and exploratory pilot pass Gate 3.

### 2026-07-31T03:46:35.303Z - Optimized-package smoke failed at retained shared-base cleanup

- **Entry ID:** `smoke-exp1-optimized-shared-base-cleanup-failure-081`.
- **Phase/kind:** EXP1-C live `paper-env-smoke`; failed/partial and permanently
  ineligible.
- **Run identity:** `019fb640-f59a-71cb-a3dd-a6a0bd23d86e`; exact plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  exact clean product `main` commit
  `57b437ba60a2304e896e7345f13e6bc43f431f55`; exact
  `windows-exp1-57b437ba` package and qualified image from entry 080.
- **Clock/result:** started `2026-07-31T03:39:01.368982Z`, ended
  `2026-07-31T03:40:02.983296Z`, elapsed 61.614314 seconds. The terminal
  manifest state is `failed`, correctness is `fail`, and only one of 19 trial
  batches and one product request completed. This attempt is not a passed
  smoke and no value is eligible for a paper table or Gate 3 projection.
- **Successful product work:** the measured `create_sandbox` request exited 0
  with empty stderr; both observability boundaries, sandbox inspection, and
  manager-CLI destroy exited 0. The single trial is internally recorded as
  reportable/success with product success, two passed correctness checks,
  correlated resources, and restored per-trial cleanup baseline. No automatic
  retry occurred.
- **Failure boundary/root evidence:** `sandbox_lifecycle` and its first cell
  reached `completed`, then campaign block cleanup failed before the next
  family. A single new content-addressed shared-base volume,
  `eos-shared-base-0be2ebdcdc1e0d39996e614a76461bd21a28e90b688ad3dd502dea995ca2b63d`,
  remained. Its exact gateway label is
  `benchmark-gateway-6ab02f5eb81af0965b7085aa0a964a28`, matching this
  run's PID-46800 gateway ownership record; no container referenced it. This
  is an infrastructure cleanup failure introduced by the pre-freeze
  cross-gateway cache optimization, not a product request or correctness
  failure.
- **Clock discipline:** no build, install, pull, test, source edit,
  experiment-log edit, or environment reconfiguration occurred during the
  live clock. A read-only recursive progress probe enumerated fixture paths
  noisily and returned exit 1 after its bounded output; it changed no state
  and was not repeated.
- **Cleanup:** the run-owned gateway exited. After strict name, gateway-label,
  root-hash, readonly-label, and zero-container-reference checks, only the
  exact leaked shared-base volume above was removed. The benchmark's exact
  `cleanup --run-id` command then exited 0, removed the owned run workspace and
  runtime directory, and preserved the immutable result store. The post-run
  baseline is again only gateway PID 62980, one pre-existing exited
  `eos-gateway` container, and five pre-existing `eos-gateway` volumes.
  Product remains clean direct `main`.
- **Archive attempts:** archive attempts 1 and 2 each exited 1 with
  `post-run cleanup proof failed`: the first captured the retained volume and
  owned directories, and the second still captured the owned directories
  before the benchmark cleanup command. After cleanup, attempt 3 exited 0 with
  zero stderr and verified the failed corpus.
- **Retained failed archive:** absolute directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb640-f59a-71cb-a3dd-a6a0bd23d86e`,
  65 files, 4,385,878 bytes, content-tree
  `sha256:8d9049af62474e93da6d525abac22fe6e790a5936c761c32ee3ecec8cb840eda`.
  The initial live stdout/stderr and all three archive-attempt captures remain
  under `tmp`; live stderr was empty.
- **Recorded diagnostic mistakes:** two safe event/observation shape probes
  selected an incorrect nesting level before corrected reads, a gateway-log
  probe tried to JSON-decode the product's `cli_log(...)` text and failed, and
  one post-archive inspection mistakenly passed the archive directory to
  `Get-FileHash` and then called a method on the null result. None changed
  evidence or external state.
- **Disposition:** stop condition enforced. The failed smoke is preserved and
  the final remains untouched. A paper-harness fix and tests are required
  before a wholly new smoke; the pre-registered cells, trials, metrics,
  stopping rules, and projection model remain unchanged.

### 2026-07-31T03:49:53.652Z - Shared-base Docker label cleanup amendment

- **Entry ID:** `amendment-exp1-shared-base-dotted-labels-082`.
- **Phase/kind:** EXP1-C pre-freeze paper-harness correction after failed smoke
  019fb640-f59a-71cb-a3dd-a6a0bd23d86e; no live preset.
- **Demonstrated cause:** the product's Docker provider and the retained live
  volume use `eos.shared_base.root_hash`, `eos.shared_base.target`, and
  `eos.shared_base.readonly`. The newly added paper-harness cleanup validator
  instead looked for underscore spellings
  `eos.shared_base_root_hash`, `eos.shared_base_target`, and
  `eos.shared_base_readonly`. It therefore failed closed on the valid
  content-addressed volume during intermediate retention and again during the
  final sweep.
- **Correction:** changed only those three paper-harness label literals in
  `benchmark/backend/benchmark_lab/gateway.py`. Updated the existing
  cross-gateway final-cleanup and ambiguous-volume fixtures in
  `benchmark/backend/tests/integration/test_gateway_lifecycle.py` to use the
  released product's exact dotted label contract. The regression now would
  fail with the old harness constants and proves that intermediate cleanup
  retains the validated shared base while the final sweep removes it through
  its original gateway owner.
- **Protocol impact:** none. Product source/package, plan cells/counts/order,
  trials, timing boundaries, metrics, exclusions, resource sampling, fixture,
  image, stopping rules, and the pre-registered structural projection model
  are unchanged. This is a justified pre-freeze cleanup-contract defect fix.
- **Focused validation:** gateway-lifecycle plus runner integration tests
  exited 0: 45 passed and one expected Windows symlink-privilege skip in
  5.92 seconds.
- **Full validation:** complete backend suite exited 0: 256 passed and five
  expected Windows symlink-privilege skips in 42.67 seconds.
- **Formatting/static validation:** the first scoped Ruff format check exited
  1 because the three patched lines needed mechanical newline normalization;
  import checks and `git diff --check` passed. Cached offline Ruff 0.16.1 then
  formatted the file, and both format and import checks exited 0. The
  post-format gateway-lifecycle suite exited 0: 13 passed and one expected
  Windows skip in 4.38 seconds.
- **Independent blocker audit:** a read-only subagent independently traced the
  product constants in `sandbox-provider-docker/src/labels.rs` and their
  runtime emission, confirmed the old harness literals made both retain-mode
  cleanup and final cleanup reject the same valid volume before `volume rm`,
  and found no second cleanup defect. It recommended no retry or backoff
  change; the strict ownership/name/root/target/readonly checks remain
  fail-closed.
- **Disposition:** offline correction is green. A wholly new unique smoke,
  followed by a wholly new exploratory pilot if smoke passes, is required.
  The failed smoke remains archived and ineligible; freeze/final remain
  prohibited.

### 2026-07-31T03:51:32.784Z - Corrected-smoke fast preflight

- **Entry ID:** `preflight-exp1-corrected-smoke-083`.
- **Phase/kind:** EXP1-C fast preflight after the dotted-label amendment; no
  live clock started.
- **Plan validation:** `benchmark_lab validate` exited 0 with zero stderr and
  zero findings. `paper-env-smoke` remains runnable `product_cli`, 19 cells,
  19 trial batches, 55 issued requests, and plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
  A first read of the successful JSON selected nonexistent nested properties
  and therefore displayed null/one placeholders; corrected direct top-level
  selectors confirmed the values above. The retained validation output is
  `tmp\paper-env-smoke-after-label-fix.validate.json`.
- **Environment drift check:** native host `DESKTOP-OLP1ADS` build 26200;
  Docker client/server 29.0.1, Linux AMD64, `overlayfs`, cgroup v2; exact
  qualified image ID; 570,993,184,768 bytes free on `C:`.
- **Treatment drift check:** product remains clean direct `main` at
  `57b437ba60a2304e896e7345f13e6bc43f431f55`; package archive remains
  `sha256:0d6a784a5447ef012d03d4b8742beac0693f30766e14c2bd9dc4c53e9c4cb359`;
  staged config remains
  `sha256:987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Cleanup baseline:** only the protected host gateway PID 62980, one
  pre-existing exited labeled container, and five pre-existing labeled
  volumes exist. No resource from failed run
  019fb640-f59a-71cb-a3dd-a6a0bd23d86e remains.
- **Disposition:** all corrected-smoke prerequisites pass. Start exactly one
  new unique smoke; freeze, pilot, and final remain prohibited until its
  terminal cleanup and archive pass.

### 2026-07-31T04:01:59.138Z - Corrected optimized-package smoke passed

- **Entry ID:** `smoke-exp1-corrected-optimized-pass-084`.
- **Phase/kind:** EXP1-C live `paper-env-smoke`; accepted smoke evidence but
  ineligible for manuscript tables.
- **Run identity:** `019fb64d-4841-742e-9e70-115c7f8d378c`; exact clean
  product commit `57b437ba60a2304e896e7345f13e6bc43f431f55`; exact package,
  image, fixture protocol, and unchanged plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Terminal result:** manifest `completed`, correctness `pass`, report ready;
  19/19 trial batches, 55 issued product operation requests, zero failures,
  zero warnings. Every product subprocess record has return code 0 and empty
  required stderr; all operation-specific checks, correlations, and
  per-trial cleanup proofs passed.
- **Campaign timing:** manifest start
  `2026-07-31T03:52:28.413517Z`, end
  `2026-07-31T03:56:29.401572Z`, exact manifest elapsed 240.988055 seconds.
  The redirected stdout file existed from
  `2026-07-31T03:52:25.3093494Z` until its terminal write at
  `2026-07-31T04:00:25.5517553Z`, a 480.2424059-second file-lifetime bracket.
  The post-manifest portion was the required recursive deletion of 19 deep
  NTFS `paper-100m` cell copies. This outer cleanup overhead is engineering
  evidence only and is not inserted into an operation-latency distribution.
- **Outer CLI observation:** the process watcher acquired the already-running
  Windows process and confirmed termination, but Windows `Get-Process`
  returned a null `ExitCode` for that externally reopened handle. Terminal
  stdout is valid JSON, stderr is zero bytes, and the CLI's persisted terminal
  state is completed. This outer-wrapper capture limitation does not affect
  the recorded return code of any product CLI subprocess; an explicit
  exit-status sidecar wrapper will be used for the pilot and final.
- **Cleanup:** after the report was ready, the runner removed the complete
  owned run workspace and runtime directory. Post-run state is exactly the
  protected baseline: gateway PID 62980, one pre-existing exited labeled
  container, and five pre-existing labeled volumes. Product remains clean
  direct `main`; no run-owned process, container, volume, registry state, or
  workspace remains.
- **Archive:** `archive_exp1_run.py` exited 0 with zero stderr and verified
  the corpus at
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb64d-4841-742e-9e70-115c7f8d378c`.
  The archive has 1,175 files, 30,036,537 bytes, and content-tree
  `sha256:746b71ded2733c2ad7ce1572ee8731c590e432bf199e9684b9f2aab3384c3471`.
- **Clock discipline:** no build, install, pull, source edit, test, log edit,
  or environment reconfiguration occurred during the live clock. Read-only
  progress checks inspected only committed event records and process state.
- **Disposition:** EXP1-C smoke passes for the corrected pre-freeze source.
  Proceed to one wholly new five-sample exploratory pilot after a strict fast
  preflight. Freeze/final remain prohibited pending Gate 3 projection and
  anomaly review.

### 2026-07-31T04:03:13.782Z - Five-sample pilot fast preflight

- **Entry ID:** `preflight-exp1-five-sample-pilot-085`.
- **Phase/kind:** EXP1-D strict fast preflight; no pilot clock started.
- **Outer exit capture:** added the paper-local temporary orchestration helper
  `tmp\run-benchmark-with-exit-capture.ps1`. It starts the exact Python CLI
  with argument arrays, waits on its own process handle, emits the benchmark
  exit code in a sidecar, and exits with that code. PowerShell syntax parsing
  passed; helper
  `sha256:7091ecdcee6b69ef471e0322aae4f28e1a5e61e776b80c0f04f84fabb9b6aa4f`.
  It changes no benchmark behavior, timing boundary, plan, or raw evidence and
  writes only outer orchestration stdout/stderr after the campaign command.
- **Pilot plan:** `benchmark_lab validate` exited 0 with zero stderr and zero
  findings. `paper-pilot` remains runnable `product_cli`, 19 cells, 133 trial
  batches, 385 requests, two warmups plus five measured trials per cell, no
  warnings, and exact plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Smoke prerequisite:** independent archive verification exited 0 with zero
  stderr and reconfirmed corrected-smoke content-tree
  `sha256:746b71ded2733c2ad7ce1572ee8731c590e432bf199e9684b9f2aab3384c3471`.
- **Environment/treatment:** native host `DESKTOP-OLP1ADS` build 26200;
  Docker 29.0.1 Linux AMD64, `overlayfs`, cgroup v2; exact qualified image;
  570,920,165,376 bytes free on `C:`. Product is clean direct `main` at
  `57b437ba60a2304e896e7345f13e6bc43f431f55`; package archive remains
  `sha256:0d6a784a5447ef012d03d4b8742beac0693f30766e14c2bd9dc4c53e9c4cb359`.
- **Cleanup baseline:** only the protected gateway PID 62980, one pre-existing
  exited labeled container, and five pre-existing labeled volumes exist.
- **Disposition:** every EXP1-D start condition passes. Run one new complete
  exploratory pilot. It is ineligible for manuscript tables regardless of
  outcome; freeze/final remain prohibited until its cleanup, archive,
  deterministic regeneration, structural projection, and anomaly review pass.

### 2026-07-31T04:17:54.579Z - Fresh pilot passed; structural projection still blocks Gate 3

- **Entry ID:** `exp1-57b437ba-pilot-analysis-blocker-086`.
- **Phase/kind:** EXP1-D live exploratory pilot, immutable archival,
  deterministic regeneration, and preregistered structural Gate-3 decision.
  Pilot evidence is permanently ineligible for manuscript tables.
- **Run identity:** `019fb657-802d-78d4-9245-518de0de50d7`; clean product
  `main` commit `57b437ba60a2304e896e7345f13e6bc43f431f55`; exact optimized
  package/image; plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Terminal result:** outer benchmark exit code 0 captured by the exact
  sidecar wrapper; terminal manifest `completed`, correctness `pass`, report
  ready; 19/19 cells, 133/133 trial batches, 385 product requests, 95 measured
  trials, zero failures, and zero warnings. All request, correctness,
  observability, correlation, and per-trial cleanup requirements passed.
- **Timing:** manifest start `2026-07-31T04:03:38.098552Z`, end
  `2026-07-31T04:08:56.546172Z`, exact elapsed 318.447620 seconds. The
  redirected command-output file lifetime, including the complete recursive
  NTFS workspace deletion, was 580.2188861 seconds. Both observed bounds are
  under 1,200 seconds, but pilot duration alone is not the final projection.
- **Cleanup:** the runner removed the entire run workspace and runtime
  directory. Product remains clean direct `main`; only protected gateway PID
  62980, the one pre-existing exited labeled container, and five pre-existing
  labeled volumes remain. No pilot-owned process, container, volume, registry
  state, or workspace remains.
- **Immutable archive:** archiver exited 0 with zero stderr and verified
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb657-802d-78d4-9245-518de0de50d7`.
  It contains 6,605 files and 181,314,655 bytes with content-tree
  `sha256:4a2fc3c3c2a79f33661ddc1ec6085d1589b7af99f582ae188e35e58f9ebd9362`.
- **Deterministic tables:** generator
  `sha256:37f2dddec2684b6eb2682c65ebdb4750b3a4f795596045ec05da827f06dff7e3`
  exited 0 twice with zero stderr using only the immutable pilot archive.
  Outputs
  `experiments\analysis\pilot-57b437ba-019fb657-tables-a` and `-b` are
  byte-identical: nine files, 228,902 bytes, content-tree
  `sha256:1ea56e99abc227a8a0319091f5df4548f70dd4a56d96d5ce936010c9cd1cee72`.
  Both explicitly record `exploratory_ineligible` and
  `ai-research-writing/numeric-evidence-v2`.
- **Table component hashes:** environment
  `9741d1de397004ad249dbd0e0b6270dd91663999e81aaa127ce0a6c79e5a07a0`;
  startup
  `ee336c13149c0ec064921eac48a91859763ac2f455a1b5f02e068b7d9a4644f1`;
  CLI operations
  `b3fca8615ec9359c872f6a58bae620e81e5bdd2f0e7518b9fa29c747712c2bd2`;
  resources
  `e41cb7a37a4953c87db6e34f6140493bd6547a5ca2b0023b59b6c653ddcef5e7`;
  tables JSON
  `c97fa723fb24fed3b8f25143faa6e47b9ef8bbbf71f2153b8b02cafae78d62cf`;
  numeric evidence
  `8ddd30b60810648db1741ec19180e0079010fcd3c01cf0394938256e7cca8cad`;
  numeric provenance
  `491040b0a4f3d74b2a964dcf69d16a7c3989e7165ea93f8da8a7a6cf8835043c`.
- **Recorded analysis mistake:** the first canonical tree-comparison attempt
  passed quoted Python source through native PowerShell argument parsing;
  quotes were stripped and it exited 1 with `NameError`. No output directory
  or evidence changed. The corrected temporary helper invoked the existing
  `archive_inventory` function and proved the two complete output inventories
  identical.
- **Structural projection:** preregistered script
  `sha256:d6126902dac9bddd868be57425fb1f29d0e1ec95cf4a9c8aa14cdfbaeb694afc`
  consumed only the fresh verified smoke/pilot archives and the reviewed exact
  final plan, exited 0 with zero stderr, and emitted
  `experiments\analysis\pilot-final-runtime-structural-57b437ba-019fb657.json`,
  44,406 bytes,
  `sha256:4450cda5eabbc534163cd38909d30b42b3d865adde04fccde478a6190329259c`.
- **Gate-3 result:** pilot elapsed 318.447620000 seconds is within the limit,
  but the exact central structural projection is 1455.634228525 seconds and
  the observed envelope is 1604.045005800 seconds. Pass conditions are
  true/false/false; `gate_3_runtime_pass: false`; decision
  `block_freeze_and_final_runtime_projection_exceeds_20_minutes`.
- **Clock discipline:** no build, install, pull, test, source edit, log edit,
  or environment reconfiguration occurred during the pilot clock. All
  analysis and log mutation began only after command exit and cleanup.
- **Disposition/blocker:** Gate 3 remains FAIL. Freeze, local commit/tag, and
  the exactly-one eligible final pass remain untouched and prohibited.
  Three parallel read-only audits are decomposing exact contributors and
  protocol-preserving harness/product speed options. Any adopted correction
  requires offline tests and another entirely fresh smoke/pilot before Gate 3
  can be reconsidered.

### 2026-07-31T04:31:11.025Z - Gate-3 decomposition and one-shot CLI runtime correction

- **Entry ID:** `exp1-gate3-cli-current-thread-correction-087`.
- **Phase/kind:** post-pilot read-only decomposition, offline microbenchmark,
  and pre-freeze product-source correction. No smoke, pilot, freeze, tag, or
  final clock was active.
- **Exact blocker decomposition:** the immutable pilot remains functionally
  healthy, but the frozen structural model remains 1455.634228525 seconds
  central and 1604.045005800 seconds envelope, requiring reductions of
  255.634228525 and 404.045005800 seconds. Exact central components are
  173.6189496 seconds cell-fixed, 84.0605484 seconds warmup active,
  1189.184050 seconds measured active, 4.480688825 seconds gaps, and
  4.2899917 seconds run/family fixed. The final remains untouched.
- **Resource-boundary evidence:** the archived pilot contains 457 cgroup and
  457 snapshot CLI calls. Across the 126 non-create trials, 92 baselines
  completed in one attempt and 34 required two; only four post boundaries
  completed in one attempt and 122 required two. Each paired attempt is about
  37--43 milliseconds median, while the product ring advances about 106
  milliseconds. Mandatory baseline plus post-boundary wall therefore offers
  539.521980 seconds of final-scaled central opportunity, but a true fresh
  synchronous product boundary is required for a robust 50--75 millisecond
  target; merely changing the fixed 100-millisecond retry sleep is not enough.
- **Other exact opportunities:** mutation verification has 41--48 seconds of
  final-scaled independent-read overlap; repeated fresh-copy cell preparation
  consumed 83.848695 seconds of pilot leading wall while still requiring 19
  distinct fresh copies; per-invocation paper CLI evidence durability has a
  diagnostic upper opportunity of about 121 final seconds but needs a focused
  microbenchmark. No protocol decision was changed.
- **Parallel product audit:** all three released one-shot CLIs used default
  multi-thread `tokio::main` on this 48-logical-processor host even though each
  process parses and sends one request. Final-mode evidence projects about
  30,170 such launches. The narrow product correction changes only
  `sandbox-manager-cli`, `sandbox-runtime-cli`, and
  `sandbox-observability-cli` to Tokio's `current_thread` flavor. Request
  schemas, CLI timing, transport, concurrency across subprocesses, resource
  cadence, and lifecycle behavior are unchanged.
- **Offline before/after diagnostic:** 60 release `--help` launches per binary
  against the immutable `57b437ba` package had medians
  9.869/9.882/9.581 milliseconds and p95
  10.927/11.046/10.724 milliseconds for manager/runtime/observability.
  Locally rebuilt corrected binaries had medians
  6.277/6.534/6.388 milliseconds and p95
  6.954/7.482/7.429 milliseconds. Means had unrelated host outliers and are
  not used as a performance claim. This diagnostic is exploratory and
  ineligible for paper tables.
- **Validation:** `cargo fmt --check`, `cargo test -p sandbox-cli`, and
  `cargo clippy -p sandbox-cli --all-targets -- -D warnings` all exited 0.
  Feature-specific locked release builds for all three corrected executables
  exited 0.
- **Recorded analysis/validation mistakes:** initial post-pilot factor joins
  addressed `plan.cells` instead of the envelope's `plan.data.cells` and were
  rerun against the correct schema. A first PowerShell resource aggregation
  had a trailing comma in `Sort-Object` and did not parse; the corrected
  aggregation produced the counts above. The first offline launch benchmark
  used a direct `foreach` pipeline that PowerShell rejected as an empty pipe
  element; the array-wrapped rerun passed. A one-second combined Cargo command
  timed out before validation and was rerun with an adequate bound. A generic
  `cargo build --release -p sandbox-cli --bins` was a no-op because every
  binary is feature-gated; the three exact feature-specific builds succeeded.
  `Get-Date -AsUTC` was unsupported in this PowerShell version; the timestamp
  was captured with `DateTime.UtcNow`. None of these failed attempts changed
  evidence, product state beyond the three intended source lines, or the live
  environment.
- **Disposition:** retain the three-line product optimization, complete
  proportional product validation, commit it directly on authorized local
  `main`, and produce a new immutable Windows package. Because product source
  changed, the prior smoke and pilot remain archived exploratory evidence only;
  an entirely fresh smoke and pilot are required before Gate 3 can be
  reconsidered. Freeze, tag, and final remain prohibited.

### 2026-07-31T04:38:35.158Z - Current-thread CLI commit and immutable Windows package

- **Entry ID:** `exp1-product-cli-current-thread-package-088`.
- **Phase/kind:** offline product validation, authorized direct-`main` local
  commit, and immutable Windows package construction. No live benchmark clock,
  freeze, tag, or final attempt was active.
- **Product commit:** the three-line one-shot CLI runtime correction was
  committed directly on clean local `main` as
  `37fdbcfeab2400e2b3741fd9993392d3ecfe7537`
  (`Reduce one-shot CLI runtime startup cost`). No branch, worktree, push, or
  unrelated product file was created or changed. Product status is clean.
- **Focused validation:** all-feature `sandbox-cli` tests passed 58 tests
  across compatibility, help, manager, observability, projection, request
  building, and runtime suites. All-feature `sandbox-cli` Clippy with warnings
  denied passed. The earlier no-feature format/test/Clippy checks and all three
  feature-specific locked release builds also passed.
- **Platform-scoped workspace check:** `cargo test --workspace` was attempted
  proportionally and failed during compilation because
  `sandbox-observability-telemetry` imports `rustix::fs`, which is deliberately
  gated out by `rustix` on Windows. This pre-existing cross-platform workspace
  incompatibility is unrelated to the three changed binary attributes; no
  test executed or product file changed. The exact applicable Windows CLI
  feature suites above pass.
- **Package:** exact directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-37fdbcfe`
  and archive `windows-exp1-37fdbcfe.zip`; 5,623,169 archive bytes;
  archive
  `sha256:3d2d876ea881fc529acf1c7cc80d549f03bcb7803e52143d81b413b549a56d66`.
  The package script rebuilt the Windows gateway and the three exact
  feature-gated release CLIs from the committed tree.
- **Packaged component hashes:** gateway
  `526ba4e1b90b38d8605475b4ad1e53ded12eeef396cb533acfe0d1c90854dfaa`;
  manager CLI
  `564876d4c11040a254d149622d28d3c01259c997ae6472f247dab05e9e1e72ed`;
  runtime CLI
  `c73a5b3bf4b04df5326391bc77b233904074bde72eabc20f393a0f7031d5c1c8`;
  observability CLI
  `25906c1910119a52d98580c748cdad5886aa118d59eccef1f7aa87265c754f26`;
  Linux daemon
  `f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`;
  configuration
  `987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Recorded packaging mistakes:** direct invocation of the repository
  PowerShell package script was rejected by the host execution policy before
  it ran; the exact rerun used `powershell.exe -NoProfile -ExecutionPolicy
  Bypass` and passed. A first component-hash display used a direct `foreach`
  pipeline that PowerShell rejected before evaluation; the array-wrapped
  read-only rerun passed. No partial package existed before the successful
  script, and both exact targets were confirmed absent before its scoped
  cleanup/create step.
- **Disposition:** this package is qualified for the next smoke only if no
  additional product source correction is adopted. Paper-harness source is
  still being optimized before that smoke, so no live run has begun. Freeze,
  tag, and final remain prohibited.

### 2026-07-31T04:48:19.638Z - Protocol-preserving harness runtime amendments validated

- **Entry ID:** `exp1-gate3-harness-runtime-amendments-089`.
- **Phase/kind:** offline pre-freeze paper-harness optimization and validation.
  No benchmark, freeze, tag, or final clock was active.
- **Resource-boundary correction:** mandatory post-response product-boundary
  sampling now waits one qualified 100-millisecond product-ring cadence before
  its first CLI poll. Periodic sampling remains exactly 100 milliseconds and
  the existing fail-closed retry/readiness contract remains intact. This
  removes the pilot's almost-certain stale first post-boundary observation
  without weakening freshness.
- **Mutation verification overlap:** independent content reads and product
  attribution checks now execute concurrently behind the existing complete
  failure-gathering boundary. Tests prove the independent reads overlap and
  that simultaneous branch failures are both retained.
- **Fixture materialization:** all contextual cell workspaces are still fresh,
  distinct, fully verified copies, but they are materialized once in a bounded
  four-worker batch before the first execution block. The source inventory is
  validated once before the batch and again after it; exact destination
  inventory, manifest, inode independence, and the eight-worker hard cap are
  tested. The existing single-workspace API is unchanged.
- **CLI evidence durability:** paper `product_cli` now exposes an explicit
  per-trial evidence transaction. Redacted stdout/stderr projections are
  staged without per-command durable metadata writes; exact schema-2 marker
  bytes are sorted and durably committed with bounded concurrency before the
  trial journal commits. Immediate durable behavior remains unchanged outside
  a trial, flush failures stay pending and fail closed, cleanup after the
  boundary is immediate, and archive compatibility is unchanged.
- **Diagnostic microbenchmark:** 12 repetitions over a 256-KiB evidence case
  measured 61.652 milliseconds median for immediate durability versus 26.895
  milliseconds stage plus 9.999 milliseconds boundary commit, or 36.894
  milliseconds total and 1.67x exploratory speedup. The resulting evidence
  trees were byte-identical. This diagnostic is ineligible for paper tables.
- **Exact amended implementation hashes:** fixtures
  `sha256:5edd3f2ed1c23fd0305d519a6066a48de77720156d4a64937595d03d75cf8903`;
  product CLI
  `sha256:44dc001cdd51b137d084412431f6f9f3d7981e196788acd2418a7dd737ceda05`;
  resource sampling
  `sha256:b45c7f5063a60aa052056adcf7d403f1677847348cc01c1b59470614a80cdbf7`;
  runner
  `sha256:453e7dcdd11e9a35d097e8369341f5edd8231c87dcbe08e458afdae315994396`.
- **Validation:** focused product-CLI and runner tests passed 54 tests; fixture
  tests passed 24 with one expected Windows symlink-privilege skip; resource
  tests passed 16; archive compatibility passed six. After integrating all
  four amendments, the complete backend suite passed 275 tests with five
  expected Windows symlink-privilege skips in 48.28 seconds. Ruff 0.16.1
  formatting and import checks pass on all eight touched implementation/test
  files.
- **Recorded validation mistakes:** a first direct `uv run --offline ruff`
  attempt failed before linting because Ruff is not installed in the project
  virtual environment. The cached exact Ruff 0.16.1 executable was located.
  A first inspection command used paths relative to the paper backend while
  spelling them from the benchmark root and therefore found no files; the
  corrected read-only inspection passed. A whole-backend Ruff invocation then
  exposed the repository's broad pre-existing unformatted/lint baseline; it
  changed nothing. The exact touched-file invocation identified four files
  needing format normalization and three import blocks; the mechanical
  correction followed by repeated exact checks passed. No live evidence or
  environment state changed.
- **Disposition:** retain these amendments. Product `create_sandbox` transport
  optimization is completing separate validation; after its exact commit and
  immutable package, run an entirely fresh smoke and pilot. Gate 3 remains
  blocked until that new pilot's preregistered structural projection passes.
  Freeze, tag, and final remain prohibited.

### 2026-07-31T04:50:55.035Z - Gateway daemon-forwarding optimization committed and packaged

- **Entry ID:** `exp1-product-daemon-forwarding-package-090`.
- **Phase/kind:** offline product correction, validation, authorized
  direct-`main` commit, and immutable Windows package construction. No live
  benchmark, freeze, tag, or final clock was active.
- **Product correction:** `TcpSandboxDaemonClient` no longer creates and joins
  one operating-system thread and constructs/tears down one current-thread
  Tokio runtime for every forwarded daemon request. It performs the same
  authenticated newline-framed exchange synchronously with `std::net` inside
  the manager router's existing `spawn_blocking` boundary.
- **Preserved protocol/safety:** the 16-MiB response bound, authentication,
  newline termination, response decoding, error surface, and request timeout
  remain fail closed. One monotonic total deadline now spans numeric endpoint
  resolution, connect attempts, partial writes, shutdown, and partial reads;
  remaining read/write timeout is reset before every syscall. Synchronous DNS
  itself cannot be interrupted, but elapsed time is checked immediately after
  it and the qualified endpoint is the numeric `127.0.0.1`.
- **Tests/review:** six focused tests cover successful authenticated framing,
  a stalled response, a drip-fed response that must not reset the total
  deadline, missing newline, oversized response, and eight independent
  concurrent calls. Root independently reran `cargo fmt --all -- --check`,
  those six tests, focused library/test Clippy with warnings denied, and
  `git diff --check`; all exited 0. The exact forwarding call site was
  independently confirmed to run under `tokio::task::spawn_blocking`.
- **Broader pre-existing checks:** `cargo test -p sandbox-gateway` reaches the
  existing `gateway_streams_create_sandbox_progress_before_final_response`
  assertion failure, which uses `RecordingDaemonClient`, not this TCP client.
  All-target gateway Clippy reaches unchanged unused items in
  `tests/local_daemon_installer.rs`. A running protected gateway locks the
  default debug executable, so the focused checks used separate scoped Cargo
  target directories and did not stop or alter it.
- **Product commit:** two scoped files were committed directly on authorized
  local `main` as
  `214cea7a9926abfc5c5e3d681946949eda040ab6`
  (`Reduce gateway daemon forwarding overhead`). Product is clean and
  `main` is eleven commits ahead of `origin/main`; there was no branch,
  worktree, push, or unrelated product change.
- **Immutable package:** exact directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-214cea7a`
  and 5,615,826-byte archive `windows-exp1-214cea7a.zip`; archive
  `sha256:0d8dc9802048d2db99f5d47c2e4d136a55130f749042d7d4f71fac6e6b828852`.
  The repository package script rebuilt the exact locked release gateway and
  three feature-gated one-shot CLIs from the committed tree.
- **Packaged component hashes:** gateway
  `6f40fefd527cac17212470373678a69def55b4f89f4741388454c69b069494a7`;
  manager CLI
  `564876d4c11040a254d149622d28d3c01259c997ae6472f247dab05e9e1e72ed`;
  runtime CLI
  `c73a5b3bf4b04df5326391bc77b233904074bde72eabc20f393a0f7031d5c1c8`;
  observability CLI
  `25906c1910119a52d98580c748cdad5886aa118d59eccef1f7aa87265c754f26`;
  Linux daemon
  `f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`;
  configuration
  `987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Recorded packaging mistake:** the first read-only package-script lookup
  guessed a nonexistent `scripts` directory and produced an `rg`/file-not-found
  diagnostic. The correct tracked script was then located under `bin`; exact
  stage/archive absence was confirmed before its scoped create step, and the
  package and checksum verification passed.
- **Disposition:** use this exact clean product commit and immutable package
  for a fresh post-correction smoke. If smoke and archive checks pass, run one
  new exploratory five-sample pilot and the preregistered structural
  projection. Gate 3 remains blocked until that projection passes; freeze,
  tag, and final remain prohibited.

### 2026-07-31T04:53:21.433Z - Post-optimization smoke fast preflight passed

- **Entry ID:** `preflight-exp1-214cea7a-smoke-091`.
- **Phase/kind:** EXP1-C strict fast preflight; no live benchmark clock
  started.
- **Offline qualification:** the combined paper backend passed 275 tests with
  five expected Windows symlink-privilege skips in Entry 089. Exact touched
  files pass Ruff 0.16.1 formatting/import checks and paper `git diff --check`
  passes with only the repository's expected line-ending notices.
- **Plans:** fresh `benchmark_lab validate` subprocesses exited 0 with empty
  stderr. `paper-env-smoke` is runnable/customized with zero findings and
  warnings, only `product_cli` and `paper-100m`, exactly 19 cells, 19 trial
  batches, 55 issued requests, and plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
  `paper-pilot` remains runnable/customized with zero findings and warnings,
  the same 19 cells/cohort/profile, 133 batches, 385 requests, and plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Command surface:** Python is 3.13.14. The exact packaged gateway, manager,
  runtime, and observability `--help` invocations all exited 0 with empty
  stderr. Outer exit-capture helper remains
  `sha256:7091ecdcee6b69ef471e0322aae4f28e1a5e61e776b80c0f04f84fabb9b6aa4f`;
  archive script
  `sha256:25cca63e4acc035a60384dce11221d6571a10ccd1bdf5b3a39e0e7a0d027426e`.
- **Treatment:** product is clean direct local `main` at
  `214cea7a9926abfc5c5e3d681946949eda040ab6`. The exact package remains
  5,615,826 bytes and
  `sha256:0d8dc9802048d2db99f5d47c2e4d136a55130f749042d7d4f71fac6e6b828852`;
  gateway/manager/runtime/observability hashes remain
  `6f40fefd527cac17212470373678a69def55b4f89f4741388454c69b069494a7`,
  `564876d4c11040a254d149622d28d3c01259c997ae6472f247dab05e9e1e72ed`,
  `c73a5b3bf4b04df5326391bc77b233904074bde72eabc20f393a0f7031d5c1c8`,
  and
  `25906c1910119a52d98580c748cdad5886aa118d59eccef1f7aa87265c754f26`.
- **Qualified host:** `DESKTOP-OLP1ADS`, Windows build 26200, 64-bit, 48
  logical processors, 137,438,953,472 physical-memory bytes, and
  565,626,413,056 free bytes on `C:`.
- **Qualified Docker/image:** client/server 29.0.1, Linux AMD64,
  `overlayfs`, cgroup v2. Exact pinned Ubuntu image ID/digest
  `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
  is present locally; no pull was issued.
- **Preserved baseline:** protected debug gateway PID 62980 remains the only
  sandbox-named process. The one pre-existing labeled container remains
  exited with exact ID
  `5ce30657bf836cc332141baf2697192d48ec4553cf41ecf103ef4f1b05175f85`;
  the two preserved sandbox volumes and three content-addressed read-only
  shared-base volumes remain the only five labeled volumes. Benchmark runtime
  is empty. Eight older terminal run records are retained unchanged as
  pre-existing evidence.
- **Recorded inspection mistakes:** the first successful plan-summary display
  selected nonexistent nested fields and PowerShell's null-array conversion
  misleadingly printed one finding/warning. Direct schema inspection proved
  `validation` is an empty top-level array and warnings are the empty
  `estimates.warnings` array. A first corrected two-plan display used a bare
  `foreach` pipeline that this PowerShell rejects as an empty pipe element;
  the array-wrapped read-only rerun printed the exact zero/count values above.
  Neither attempt changed plans, evidence, or environment state.
- **Clock discipline/disposition:** from the next smoke command start through
  its terminal artifact/cleanup production, no build, test, install, pull,
  source/log edit, dependency mutation, or environment reconfiguration is
  permitted. Exactly one fresh `paper-env-smoke` is authorized. Pilot, freeze,
  tag, and final remain prohibited until smoke is archived and audited.

### 2026-07-31T05:04:27.313Z - Post-optimization CLI integration smoke passed

- **Entry ID:** `smoke-exp1-214cea7a-pass-092`.
- **Phase/kind:** EXP1-C live `paper-env-smoke`; accepted qualification
  evidence and permanently ineligible for manuscript tables.
- **Run/identity:** run `019fb685-9524-7555-ba91-7dac3008ae7e`; clean product
  commit `214cea7a9926abfc5c5e3d681946949eda040ab6`; exact package/binaries,
  pinned image, fixture protocol, and plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`
  from Entry 091.
- **Captured process result:** the exact sidecar wrapper recorded benchmark
  exit code 0 and completed at `2026-07-31T05:02:09.3739052Z`. Benchmark and
  wrapper stderr are both zero bytes. The outer wrapper lifetime from launch
  timestamp was 494.5649052 seconds and includes complete recursive deletion
  of all 19 fresh 100-MiB workspace trees.
- **Terminal corpus:** manifest start
  `2026-07-31T04:53:58.660663Z`, end
  `2026-07-31T04:57:56.944424Z`, exact elapsed 238.283761 seconds. State is
  `completed`, correctness `pass`, report ready/non-provisional; 19/19 cells
  and trial batches, 55/55 issued product requests, zero failures, and zero
  warnings.
- **CLI evidence:** 339 exact schema-2 subprocess records have 339 unique
  request IDs, return code 0, passed response validation, zero stderr bytes,
  and `metadata-packed-payload-fsync-v1`. The independent archive CLI summary
  agrees, and authentication redaction passed.
- **Correctness/resources:** every requested correctness check passed. All
  unavailable resource fields remain explicitly unavailable rather than zero;
  the expected Windows allocated-block-count and unreported LayerStack
  limitations are retained. Mandatory correlated resource windows completed.
- **Cleanup:** the exact run workspace and runtime scope are absent; archive
  cleanup proof reports no run/gateway-labeled container or volume and no
  matching process, with clean exact product `main`. Independent terminal
  checks found only the one pre-existing exited labeled container, five
  pre-existing labeled volumes, and protected debug gateway PID 62980.
  Explicit benchmark cleanup exited 0 with `cleaned: true`.
- **Immutable archive:** archive creation and an independent verify-only
  invocation both exited 0 with empty stderr and exact agreement at
  `experiments\runs\019fb685-9524-7555-ba91-7dac3008ae7e`: 1,073 files,
  29,744,883 bytes, content-tree
  `sha256:35336d8e6112d294e4c888c645f837ecc2d6a7ff16fee9782c77a6a59a20b023`.
  Disposition is `smoke` and eligibility `qualification_only`.
- **Clock discipline:** no build, test, install, pull, source/log edit,
  dependency mutation, or environment reconfiguration occurred during the
  live command. Progress inspection read only event/manifest/process state.
  One early progress probe recursively counted the still-materializing run
  tree and therefore added avoidable disk reads; it was immediately
  discontinued. Because this is non-quantitative smoke evidence, it does not
  affect a paper estimate, but no such probe is permitted during pilot/final.
- **Recorded inspection mistakes:** a transient process exited while a
  read-only process list sorted by `StartTime`, producing one harmless
  property-read diagnostic. After archival, an inspection accidentally
  serialized the complete archive manifest and produced oversized console
  output; no file changed. A first independent CLI metadata aggregation
  selected nonexistent `.data.return_code` fields and thus misclassified null
  values; direct schema inspection and the corrected top-level selectors
  proved zero nonzero exits or validation failures.
- **Disposition:** EXP1-C passes for the exact `214cea7a` treatment. One fresh
  exploratory five-sample `paper-pilot` is authorized after a strict fast
  preflight. Freeze, tag, and final remain prohibited until pilot archival,
  deterministic regeneration, preregistered structural runtime projection,
  anomaly review, and cleanup pass Gate 3.

### 2026-07-31T05:05:15.538Z - Post-optimization five-sample pilot preflight passed

- **Entry ID:** `preflight-exp1-214cea7a-pilot-093`.
- **Phase/kind:** EXP1-D strict fast preflight; no live pilot clock started.
- **Smoke prerequisite:** independent verify-only invocation exited 0 with
  empty stderr and reconfirmed accepted smoke
  `019fb685-9524-7555-ba91-7dac3008ae7e`: 1,073 files, 29,744,883 bytes,
  content-tree
  `sha256:35336d8e6112d294e4c888c645f837ecc2d6a7ff16fee9782c77a6a59a20b023`.
- **Plan:** fresh `paper-pilot` validation exited 0 with empty stderr. It is
  runnable/customized with zero findings/warnings, only `product_cli` and
  `paper-100m`, 19 cells, two warmups plus five measured trials per cell,
  133 batches, 385 issued product requests, and plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Treatment:** product remains clean direct local `main` at
  `214cea7a9926abfc5c5e3d681946949eda040ab6`; package remains
  `sha256:0d8dc9802048d2db99f5d47c2e4d136a55130f749042d7d4f71fac6e6b828852`.
  No source, package, dependency, fixture, image, or protocol identity drifted
  after the smoke.
- **Environment/cleanup baseline:** exact pinned image remains local. There is
  one pre-existing exited labeled container, five pre-existing labeled
  volumes, zero benchmark-runtime entries, and protected gateway PID 62980.
  No candidate package process or smoke-owned resource remains. `C:` has
  565,559,267,328 free bytes.
- **Clock discipline/disposition:** no recursive workspace inventory or other
  avoidable disk probe will run during the pilot. From pilot command start
  through terminal artifact and recursive cleanup production, only small
  event/manifest/process reads are allowed; no build, test, install, pull,
  source/log edit, dependency mutation, or environment reconfiguration may
  occur. Exactly one fresh exploratory `paper-pilot` is authorized. It remains
  ineligible for manuscript tables; freeze, tag, and final remain prohibited.

### 2026-07-31T05:20:04.169Z - Fresh pilot passed; Gate 3 projection remains above limit

- **Entry ID:** `exp1-214cea7a-pilot-analysis-blocker-094`.
- **Phase/kind:** EXP1-D live exploratory pilot, immutable archival,
  deterministic regeneration, exact-final-plan revalidation, and fixed
  structural Gate-3 decision. All pilot/projected values remain ineligible for
  manuscript tables.
- **Run/identity:** run `019fb690-7dac-72c0-88fc-7f81898b0f8c`; clean product
  commit `214cea7a9926abfc5c5e3d681946949eda040ab6`; exact package/image;
  pilot plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Terminal result:** captured benchmark exit code 0, empty benchmark/wrapper
  stderr, terminal `completed`, correctness `pass`, report-ready and
  non-provisional. All 19 cells, 133 trial batches, 385 product requests, and
  95 measured trials completed with zero failures and warnings.
- **Timing:** manifest start `2026-07-31T05:05:53.021835Z`, end
  `2026-07-31T05:10:44.994593Z`, exact elapsed 291.972758 seconds. The outer
  launch-to-wrapper-completion bracket was 566.0244449 seconds including
  complete recursive workspace deletion. The prior healthy pilot elapsed was
  318.447620 seconds, so this treatment reduced manifest elapsed by
  26.474862 seconds.
- **CLI/correctness audit:** 1,897 schema-2 subprocess records have unique
  request IDs, return code 0, passed response validation, zero stderr bytes,
  packed evidence identity, and passed authentication redaction. Every
  correctness and cleanup check passed; unavailable resource fields remain
  explicit.
- **Cleanup:** exact run workspace/runtime are absent, archive proof records
  no run/gateway-labeled resource or matching process, and explicit benchmark
  cleanup exited 0. Independent checks found only the protected PID 62980,
  one pre-existing exited labeled container, and five pre-existing volumes;
  product remains clean direct `main`.
- **Immutable archive:** creation and independent verify-only invocation
  exited 0 with empty stderr and exact agreement at
  `experiments\runs\019fb690-7dac-72c0-88fc-7f81898b0f8c`: 5,861 files,
  177,596,758 bytes, content-tree
  `sha256:cebbe121541420f9c940aeb9b891055b722c50e16c68d47dc22ee3aa1eaff0a8`.
- **Deterministic tables:** generator
  `sha256:37f2dddec2684b6eb2682c65ebdb4750b3a4f795596045ec05da827f06dff7e3`
  exited 0 twice with empty stderr using only the immutable archive. Outputs
  `pilot-214cea7a-019fb690-tables-a` and `-b` are byte-identical: nine
  files, 228,904 bytes, content-tree
  `sha256:b7e1d21a0c31665c23eaba2c8e559dc38eac0d02940df7883329e753ab7ef245`;
  both are explicitly `exploratory_ineligible`.
- **Table component hashes:** environment
  `e1e000cc50cc6fb281676cc5424045c2dd5d53fb576891f7fb0ff9364efadea5`;
  startup
  `5606b9cf54b0c27aee87503cca6540e66fad96567824e51fb967a52c24da90f6`;
  CLI operations
  `19353b4283556df9e48bd85ab790ac859f61d9a9006dc1355fec39a5a7b5171c`;
  resources
  `bf7932d47bafe05121f1fd1ac6958eb961d03e9d5054c3482190d4e7eb7ecdc7`;
  tables JSON
  `fd2e9b6f60796ee6aadfc7008829f722fd5b681e13ea3841eeac551dfaf18528`;
  numeric evidence
  `57cc819c65a4376cfe0830b845f76d7037ffaa0060fb010d6c29b96a53d14fd0`;
  provenance
  `0e722d7ae842973ac90dcc455e17908d4586162ef2ebe6ee94355306e2bc20b6`.
- **Exact final-plan revalidation:** `paper-good-pass` is runnable/customized
  with zero findings/warnings, only `product_cli`/`paper-100m`, exactly 19
  cells, 1,938 batches, 5,610 issued requests, and plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
  Reviewed expansion
  `paper-good-pass-214cea7a-expanded-v2.json`, 42,157 bytes,
  `sha256:625bd7c4924607fecdf4f8069082719f6d4d19da05bff8211ce103111f6ae0a1`.
- **Structural projection:** fixed script
  `sha256:d6126902dac9bddd868be57425fb1f29d0e1ec95cf4a9c8aa14cdfbaeb694afc`
  exited 0 with empty stderr. Output
  `pilot-final-runtime-structural-214cea7a-019fb690.json`, 44,385 bytes,
  `sha256:201a2c85b34f707053107614e4c46346cc88dd5caa7f840cd3e406cbb1578b5c`.
- **Gate-3 result:** pilot elapsed condition passes, but central structural
  projection is 1,246.701123050 seconds and observed envelope is
  1,388.753949600 seconds. They exceed the 1,200-second limit by
  46.701123050 and 188.753949600 seconds; decision remains
  `block_freeze_and_final_runtime_projection_exceeds_20_minutes`.
  Versus the prior projection, central/envelope fell by 208.933105475 and
  215.291056200 seconds.
- **Decomposition:** new run-fixed cost is 89.974739 seconds (primarily the
  batched 19-copy fixture boundary), family-fixed 1.1799336 seconds, cell
  projected central 1,155.54645045 seconds, cell-fixed 74.6359862 seconds,
  and cell envelope 1,297.599277 seconds. Family central/envelope totals are:
  command 116.60083145/121.3424404; files
  613.486186575/674.8308374; workspace lifecycle
  82.9191334/85.4662777; sandbox lifecycle
  342.540299025/415.9597215 seconds.
- **Clock discipline:** no builds, tests, pulls, installs, source/log edits,
  recursive workspace scans, or environment mutations occurred during the
  pilot clock; progress reads touched only small event/manifest/process state.
- **Recorded analysis mistake:** a first post-projection PowerShell component
  aggregation passed script blocks to `Measure-Object -Property`, which this
  host treated as nonexistent literal property names and emitted diagnostics.
  The corrected explicit decimal loops produced the decomposition above.
- **Disposition/blocker:** Gate 3 remains FAIL. Freeze, commits/tag, and the
  exactly-one eligible final remain untouched and prohibited. Launch focused
  parallel audits of the new immutable pilot for protocol-preserving fixture,
  sandbox-lifecycle, and CLI/file-family savings; any adopted correction
  requires offline validation and an entirely fresh smoke/pilot pair.

### 2026-07-31T05:33:50.721Z - Gate-3 bottleneck audit remains pre-amendment

- **Entry ID:** `exp1-214cea7a-gate3-bottleneck-audit-095`.
- **Phase/kind:** EXP1-D read-only analysis of immutable pilot
  `019fb690-7dac-72c0-88fc-7f81898b0f8c` plus parallel implementation
  research. No live benchmark clock, protocol amendment, source edit, product
  build, package, freeze, tag, or final run occurred in this entry.
- **Authoritative blocker:** the accepted Entry-094 structural projection
  remains 1,246.701123050 seconds central and 1,388.753949600 seconds observed
  envelope, respectively 46.701123050 and 188.753949600 seconds above the
  fixed 1,200-second Gate-3 limit.
- **Sandbox lifecycle audit:** the projected family is 342.540299025 seconds
  central and 415.959721500 seconds envelope. Archived trial/CLI evidence
  attributes approximately 95% of steady create-sandbox trial span to the
  product manager create and destroy calls: five measured active spans are
  2.612771300--3.025206400 seconds, measured create CLI calls are
  1.577--1.999 seconds, verification is 16--23 milliseconds, and teardown
  destroy is 0.907--0.926 seconds. The first cold create is 54.493 seconds;
  the second warmup create is 1.574 seconds. Product source inspection
  confirmed the create path builds/reuses the shared base, creates a Docker
  container and runtime volumes, uploads seed and daemon archives, starts and
  authenticates the daemon, while destroy gracefully stops, force-removes the
  container, and removes runtime volumes. No product change is yet accepted.
- **CLI evidence audit:** all 1,897 archived CLI records were parsed by the
  delegated audit: 1,807 are trial-scoped and 90 are outside trials, with
  82.8 MiB metadata and 59.6 MiB stdout. File trials contain 5--35 CLI calls
  and at most 45 buffered calls, 2.62 MiB stdout, and 3.56 MiB marker bytes.
  Although file active-minus-recorded-phase overhead is approximately
  193--358 milliseconds per trial, the exact post-teardown grouped
  marker/journal gap is only approximately 10--29 milliseconds. Marker fsync
  alone therefore cannot close Gate 3. Deferring successful-output projection
  and base64/JSON materialization to the existing bounded flush is being
  replay-benchmarked; it is not accepted or source-modified yet.
- **Fixture audit:** current batch materialization uses four outer Robocopy
  workers, each with `/MT:32`. A same-sweep, four-destination raw-copy
  comparison measured `/MT:4` at 23.81 seconds, `/MT:8` at 49.59 seconds,
  `/MT:16` at 47.39 seconds, and `/MT:32` at 54.79 seconds. `/MT:4` was
  56.6% below `/MT:32` in that exploratory sweep. Applying that ratio to the
  measured 82.7-second materialization component would optimistically save
  approximately 46.8 seconds, but this is not yet an end-to-end result and is
  explicitly not accepted as a projection input. Direct Win32 copy and
  end-to-end API comparisons remain in progress. Ordinary PowerShell
  traversal of the depth-100 research copies encountered `MAX_PATH`; validated
  extended-length cleanup succeeded and the research temp roots were removed.
- **Resource-boundary audit:** a fresh read-only aggregation of every archived
  resource observation formed collection groups by trial and monotonic
  collection offsets. There are 133 trials: 98 have two groups and 35 have
  three because one periodic 100-millisecond collection was admitted. The
  final boundary span across all trials has minimum 31.1981 ms, median
  133.5581 ms, mean 128.278330827 ms, p95 135.9063 ms, and maximum
  142.2804 ms. Exactly seven create-sandbox trials are below 80 ms
  (31.1981--33.8030 ms); all 126 non-create trials exceed 100 ms. This matches
  the intentional 100-millisecond post-response wait plus approximately
  30--42 ms of concurrent product-observability/local collection. Removing or
  overlapping that wait is not accepted: the final cgroup/workspace boundary
  must be newer than the validated product response and verification,
  journaling, or teardown must not contaminate the resource window.
- **Current source identities:** resource sampler
  `sha256:b45c7f5063a60aa052056adcf7d403f1677847348cc01c1b59470614a80cdbf7`;
  fixture module
  `sha256:4cc1d1e29e1574014890b9eb57c41844c18ee1cfe29bc6346f0506ac10f57c9c`;
  CLI adapter
  `sha256:44dc001cdd51b137d084412431f6f9f3d7981e196788acd2418a7dd737ceda05`.
- **Recorded read-only diagnostics:** one `rg --files | Select-Object`
  inventory stopped with exit 1 after the requested first 80 paths because
  the downstream pipeline closed; it returned the intended archive layout.
  A broad two-root resource-cadence search used directories that exist only
  in one of the two repositories and emitted missing-directory diagnostics
  plus truncated output; the narrower rerun established the packaged Windows
  product cadence as 100 milliseconds. Several `rg | Select-Object` source
  inspections likewise returned exit 1 after the downstream result cap while
  returning the requested matches. A timestamp command first used unsupported
  `Get-Date -AsUTC`; the compatible `ToUniversalTime()` rerun produced this
  entry timestamp. The earlier broad raw-observation `rg` attempt also ended
  at its output cap. None of these read-only attempts changed the archive,
  source, package, Docker state, or protected gateway PID 62980.
- **Disposition:** continue the three bounded audits. Adopt only changes whose
  semantics preserve the fixed measurement and evidence boundaries and whose
  end-to-end validation supports enough central and envelope savings. Any
  accepted amendment invalidates Entry-092/094 treatment evidence and requires
  a complete offline validation followed by an entirely fresh smoke and
  five-sample pilot. Freeze and final remain prohibited.

### 2026-07-31T05:40:42.936Z - Bound Windows fixture-copy oversubscription

- **Entry ID:** `exp1-fixture-robocopy-mt4-amendment-096`.
- **Phase/kind:** pre-freeze EXP1-D harness implementation amendment and
  offline exploratory microbenchmark. No live smoke, pilot, final, Docker, or
  protected-gateway operation occurred.
- **Amendment:** changed only the native Windows Robocopy option from
  `/MT:32` to `/MT:4` in
  `benchmark/backend/benchmark_lab/fixtures.py` and the exact command-vector
  assertion in `benchmark/backend/tests/unit/test_fixtures.py`. The four
  outer destination workers, native Robocopy boundary, source/destination
  validation, exact manifest/inventory checks, independent-file identity,
  no-link policy, fixture bytes, fixture hash, 19 fresh per-cell copies, and
  failure semantics are unchanged. This caps the intended copy batch at 16
  Robocopy threads instead of 128 for the metadata-heavy depth-100 fixture.
- **Representative fixture/protocol:** NTFS; exact `paper-100m` fixture with
  4,000 payload files, 104,857,600 logical bytes, maximum depth 100, 9,619
  directories plus the fixture manifest; four distinct destinations and four
  outer workers.
- **Exploratory comparisons:** a same-sweep raw Robocopy comparison measured
  `/MT:4` 23.805 seconds, `/MT:8` 49.59 seconds, `/MT:16` 47.39 seconds, and
  `/MT:32` 54.79 seconds. A direct Win32
  `CopyFile2(FAIL_IF_EXISTS)` implementation was rejected after 67.892
  seconds for four destinations because Python-driven creation of the 9,619
  directories dominated. Full validated API `/MT:4` measured 20.229 seconds;
  an initial clean validated `/MT:32` baseline measured 20.991 seconds, while
  an adjacent load/noise-sensitive `/MT:32` repeat measured 54.922 seconds.
- **Interpretation:** Defender/cache/order noise makes the large paired
  improvement unsuitable as a claim. The defensible observed floor is 0.762
  seconds per four-copy batch, or approximately 3.62 seconds when linearly
  scaled to 19 destinations; an optimistic application to the prior
  82.7-second materialization component is approximately 52.25 seconds. Both
  are exploratory capacity estimates only. A fresh smoke/pilot is required to
  establish the actual run-fixed central and envelope effect.
- **Validation:** with `PYTHONDONTWRITEBYTECODE=1`, Ruff 0.16.1 format and
  selected import checks passed. The exact focused fixture suite passed 24
  tests with one expected Windows symlink-privilege skip. Scoped
  `git diff --check` passed with only the repository's expected CRLF notice.
  Fixture module hash is
  `sha256:4cc1d1e29e1574014890b9eb57c41844c18ee1cfe29bc6346f0506ac10f57c9c`;
  focused test hash is
  `sha256:bda49e6e1942fee6eea2674788bc0600d644cdcce5d032f7c413f5d8f6dde1da`.
- **Cleanup:** all `fixture-copy-bench-*` research roots were removed through
  the validated extended-length path cleanup. Ordinary PowerShell enumeration
  had encountered `MAX_PATH` during research, but no temp root remains.
- **Disposition:** retain the minimal `/MT:4` amendment for combined offline
  validation. Entries 092--094 no longer qualify the current harness
  treatment. Freeze and final remain prohibited; a new complete smoke/pilot
  pair and fixed structural projection are mandatory after all accepted
  amendments settle.

### 2026-07-31T05:42:32.476Z - Further CLI-evidence deferral rejected

- **Entry ID:** `exp1-cli-evidence-deferral-nochange-097`.
- **Phase/kind:** EXP1-D read-only immutable-pilot replay and design audit.
  No source, evidence protocol, archive, product, Docker, preset, freeze, tag,
  or live-run state changed.
- **Corpus:** parsed all 1,897 CLI invocations from immutable pilot
  `019fb690-7dac-72c0-88fc-7f81898b0f8c`: 1,807 trial-scoped and 90 outside
  trials, approximately 82.8 MiB of schema-2 metadata and 59.6 MiB stdout.
  File trials contain 5--45 calls and the largest trial buffer remains bounded
  at approximately 2.62 MiB stdout and 3.56 MiB packed metadata.
- **Candidate:** defer successful-call projection writes and base64/JSON
  materialization to the existing bounded trial flush, reuse the already
  computed stdout digest, and skip redundant successful-output redaction work
  while retaining outside-trial and failure durability.
- **Valid replay result:** a disk-free archived-payload replay sampled one
  measured trial from each of the 12 file cells, repeated seven times. Its
  CPU-only difference linearly projects to only approximately 1.13 seconds
  across the final run.
- **Ceiling:** the complete archived post-teardown gap, which contains all CLI
  marker commits plus observation and event journal commits, scales to only
  approximately 21.6 seconds across the 12 final file cells. CLI evidence is
  only a subset of this interval, so even its defensible absolute ceiling is
  below 20 seconds.
- **Excluded attempt:** a full disk replay ran concurrently with the fixture
  copy audit and encountered multi-second, sign-inconsistent NTFS/Defender
  interference. That replay is invalid, is explicitly discarded, and is not
  used in any estimate or decision.
- **Decision:** reject the candidate without editing. Its approximately
  1.13-second CPU benefit is disproportionate to delayed failure evidence,
  raw-output memory lifetime, partial-write recovery complexity, and risk of
  moving stdout I/O into the primary timing boundary. Preserve the already
  validated `metadata-packed-payload-fsync-v1` grouped-marker implementation.
  Gate 3 remains open on fixture, resource-boundary, and product-lifecycle
  work; freeze and final remain prohibited.

### 2026-07-31T05:46:10.000Z - Batch pre-release evidence uses one durability transaction

- **Entry ID:** `exp1-request-barrier-grouped-commit-amendment-098`.
- **Phase/kind:** pre-freeze EXP1-D harness implementation amendment and
  immutable-pilot replay analysis. No live smoke, pilot, final, Docker,
  protected-gateway, product-package, freeze, tag, or manuscript-eligible
  operation occurred.
- **Amendment:** `_run_request_batch` now combines already-buffered
  setup/phase records, `waiting_at_barrier` records, and the complete
  `ready_at_barrier` set into one ordered durable transaction immediately
  before the operation gate is released. A failed transaction leaves the
  operation coroutines behind the barrier. In-flight and terminal records
  remain post-release records and retain their prior order and failure
  semantics. `benchmark/PAPER_ARTIFACT.md` now states this exact durability
  boundary.
- **Archived evidence:** in immutable pilot
  `019fb690-7dac-72c0-88fc-7f81898b0f8c`, the two removed historical
  pre-release commit intervals have minimum 4.5383 ms, median 4.9895 ms, mean
  6.8522 ms, p95 18.4573 ms, and maximum 23.8374 ms across 1,938 projected
  final batches. Replaying the complete operation-running-to-ready interval
  gives an observed structural upper saving of 13.0379455 seconds central and
  13.3770556 seconds envelope; because that interval also contains small
  non-fsync setup/scheduling work, it is explicitly an upper, not a guaranteed
  saving. Multiplying the strict historical minimum by 1,938 gives an
  8.7952254-second floor for the removed intervals only.
- **Validation:** three existing focused barrier tests first passed. The new
  injected-commit-failure regression then failed twice only because its
  assertions inspected the outer `ExceptionGroup` string rather than its
  direct leaf exception; after correcting the test inspection, all four
  focused tests passed. The complete runner integration file passed 36 tests.
  A subsequent full shared backend run, after this amendment and the resource
  amendment below, passed 276 tests with five expected skips. The regression
  proves a failed pre-release journal commit cannot launch an operation.
- **Recorded implementation/analysis attempts:** the first combined patch
  failed atomically because the documentation context differed from the
  expected text; exact source inspection and a narrower patch succeeded. A
  first inline projection import omitted the dynamically loaded module from
  `sys.modules` and raised a dataclass import error; the corrected import then
  addressed a nonexistent `identity` key before exact semantic inspection
  established `semantics["operation"]["cell"]`. A PowerShell attempt to find
  the first create stdout double-prefixed an already-relative
  `cli-subprocesses` path and returned no result; the corrected path lookup
  succeeded, while a later request-ID search legitimately found no match.
  These failed read-only/atomic attempts changed no evidence or runtime state.
- **Source identities:** runner
  `sha256:464e2caeac12fe00d5d0c160dd26cdefaa37e80c7ada9b95965a50edade72357`;
  runner integration test
  `sha256:8305f3fa3033f3595bee0fec2ea337f5eed38f74310fc661467b92013872c7c5`;
  artifact contract
  `sha256:90385fda5fc65e7cbe47bd3cea1ad2f97307b248f510ea021aa9b20c2bed9ecb`.
- **Disposition:** retain the protocol-preserving amendment. Prior smoke/pilot
  treatment evidence no longer qualifies the current harness; a fresh
  complete smoke/pilot pair remains mandatory before freeze.

### 2026-07-31T05:49:05.000Z - Post-response freshness overlaps admitted sampler drain

- **Entry ID:** `exp1-resource-boundary-overlap-amendment-099`.
- **Phase/kind:** pre-freeze EXP1-D resource-instrumentation amendment and
  immutable-pilot replay. No live benchmark, Docker, product, package, freeze,
  tag, or final operation occurred.
- **Amendment:** `TrialResourceSampler.stop()` now fixes both its wall-clock
  post-response freshness threshold and monotonic 100-ms not-before deadline
  immediately at stop entry. It stops the cadence loop, drains any periodic
  collector admitted during the primary window, and waits only the remainder
  of that same fixed interval before launching the mandatory final product
  boundary query. Product queries remain serialized, the final query cannot
  start before 100 ms, strict product-ring timestamp validation and retry
  remain active, samples retain scheduled order, and verification/journaling/
  teardown remain outside the resource window.
- **Regression:** a deterministic test holds an admitted periodic collector
  beyond 100 ms, then proves the mandatory final boundary starts at least
  100 ms after stop entry and less than 75 ms after the collector is released.
  This distinguishes overlap from weakening or removing the freshness wait.
- **Archived capacity bound:** only 20 archived periodic collections completed
  after the last validated response. Their affected overlap is approximately
  11.7072--25.8808 ms. The maximum immutable-pilot replay benefit is
  4.9117802 seconds central and 5.1694866 seconds envelope; actual benefit may
  be zero when no collector overlaps. Early polling, product-ring phase
  prediction, and reuse of a pre-stop snapshot were rejected because they
  would weaken the post-response evidence boundary.
- **Validation:** the focused resource suite passed 17 tests; resource plus
  runner suites passed 52; the full shared backend passed 276 with five
  expected skips. Ruff format/import checks and scoped `git diff --check`
  passed.
- **Source identities:** sampler
  `sha256:c051089fa2730e00962aebcf26d2be0777e6c5e00df25867fb95a933222a07b3`;
  unit test
  `sha256:200b11197edcd784c4c8509d828c6369dc78f1d0806f06aa19caf2229e1c55ec`.
- **Disposition:** retain the amendment. As with every current pre-freeze
  change, it requires fresh smoke/pilot treatment evidence.

### 2026-07-31T05:52:16.998Z - User-authorized Gate-3 limit is 1,400 seconds

- **Entry ID:** `exp1-gate3-limit-1400-amendment-100`.
- **Phase/kind:** explicit user-authorized pre-freeze protocol amendment and
  offline validation. The user stated that 1,400 seconds is allowed. No live
  run, Docker operation, evidence deletion, final, freeze, commit, or tag
  occurred.
- **Fixed amended rule:** the pilot elapsed time, central structural
  projection, and observed-envelope projection must each be no more than
  1,400,000,000,000 ns (1,400 seconds; 23 minutes 20 seconds). All other Gate
  3 correctness, cleanup, resource, determinism, anomaly, and protocol
  requirements remain unchanged. The full 19-cell matrix, two warmups, 100
  measured trials, 1,938 batches, and 5,610 issued requests are unchanged.
- **Implementation:** updated the current experiment inventory, EXP0 protocol
  note, EXP1 campaign packet, deterministic projection constant and stable
  failure decision, plus its exact unit expectation. Historical log entries
  and historical analysis JSON remain immutable records of the former
  1,200-second rule.
- **Immediate interpretation:** immutable pilot
  `019fb690-7dac-72c0-88fc-7f81898b0f8c` had elapsed 291.972758 seconds,
  central 1,246.701123050 seconds, and observed envelope 1,388.753949600
  seconds, so those three values would satisfy the amended limit. They do not
  qualify the current harness because Entries 096, 098, and 099 changed the
  treatment after that pilot. A fresh smoke, five-sample pilot, deterministic
  table regeneration, and projection are still mandatory before freeze.
- **Validation:** the first unit-test command incorrectly selected a
  nonexistent backend-local virtual environment, fell back to an unrelated
  Python, and failed with `No module named pytest`; it changed no file. The
  corrected repository virtual environment passed both projection tests in
  4.23 seconds.
- **Current identities:** experiment inventory
  `sha256:2c7eaa10d395c6460da07f6ef4cab2b5f40f6b431f50c2df82685b109d7467ea`;
  EXP0 packet
  `sha256:401223fdb65c43423121c2f640b77a80f101383e1833cd680ed4ace001c4de33`;
  EXP1 packet
  `sha256:c021ecdd47cc80b1601171c7c175ed4f42d12dfe51229aa4c36b603b8d0a18ce`;
  projection script
  `sha256:444eafef866c9d8be5a00f63a80eeb3727b6dfddd0faa0128d2f54deb161319f`;
  unit test
  `sha256:25d111a6c9c77852e247b6d79116fea3b3d8647ca13941e38c9223f0ebdf18be`.
- **Disposition:** the former runtime blocker is removed in principle, but
  freeze remains prohibited until the current complete harness and whichever
  product optimization is retained pass offline validation and a fresh
  qualification pair.

### 2026-07-31T05:55:42.000Z - Combined paper amendments pass offline validation

- **Entry ID:** `exp1-paper-amendments-offline-validation-101`.
- **Phase/kind:** pre-freeze EXP1-D offline validation and formatting only. No
  live preset, Docker operation, product package, evidence deletion, freeze,
  tag, or final operation occurred.
- **Full suite:** with `PYTHONDONTWRITEBYTECODE=1`, the complete backend suite
  passed 277 tests with five expected Windows symlink-privilege skips in
  45.71 seconds. After line-ending/import normalization, the combined resource,
  runner, and projection suites passed 55 tests in 8.78 seconds.
- **Formatting/import/diff:** offline Ruff 0.16.1 reports the seven changed
  backend Python files and the projection script formatted; selected import
  checks pass. Ruff mechanically normalized the newly inserted runner and
  runner-test lines to their files' existing CRLF convention and fixed one
  resource-test import separator. Scoped `git diff --check` passes with only
  expected checkout line-ending notices.
- **Recorded validation attempts:** the first full-suite command was
  accidentally given a one-second command-runner timeout. The exact
  workspace-scoped pytest process was verified, terminated by PID, and the
  full suite was rerun to a captured terminal result. A first Ruff command
  addressed a nonexistent venv-local `ruff.exe`. The corrected offline Ruff
  command initially checked the complete historically unformatted backend and
  reported 43 baseline files that would be reformatted; it changed nothing.
  The scoped format check then exposed only mixed line endings introduced in
  the two changed runner files, which were mechanically normalized. A broad
  all-rule scoped lint also surfaced pre-existing project-wide policy findings
  such as intentional `BaseException` handling and an old unused import; the
  contract-relevant format and import checks were rerun narrowly and passed.
- **Current amendment identities:** fixture
  `sha256:4cc1d1e29e1574014890b9eb57c41844c18ee1cfe29bc6346f0506ac10f57c9c`;
  resource sampler
  `sha256:c051089fa2730e00962aebcf26d2be0777e6c5e00df25867fb95a933222a07b3`;
  runner
  `sha256:b08270d8d4e00f412dc29ea16acc3c9669a36eb9a7b2916856a8b455472a149f`;
  resource test
  `sha256:39c6425652aacc6cad93c30caa0a368d2986c2e485d7e3b78267c080ea15bb73`;
  runner test
  `sha256:76c7e91317b1df3ddbd7f413649065d5725a84c7bc7db3b59df9efcb8487d22e`.
- **Disposition:** all current paper-side treatment amendments pass offline
  validation. They remain pre-freeze and require a fresh smoke/pilot pair.

### 2026-07-31T06:01:31.188Z - Create-sandbox product optimization committed and packaged

- **Entry ID:** `product-exp1-create-sandbox-optimization-102`.
- **Phase/kind:** user-requested, user-authorized pre-freeze product
  optimization, offline validation, local direct-`main` commit, and release
  packaging. No push, tag, live benchmark, Docker command, protected-gateway
  action, or baseline-resource mutation occurred.
- **Retained product changes:** ordinary Docker bridge calls now share one
  lazily initialized one-worker Tokio runtime and Bollard client while each
  synchronous caller waits for its own typed result. The daemon installation
  tar is encoded with fast gzip and cached by byte-exact daemon/config
  contents; every install still rereads and compares both source files, so a
  byte change rebuilds the archive. Docker volume mutation ordering, graceful
  stop behavior, readiness cadence, daemon semantics, and external CLI
  contracts are unchanged.
- **Rejected/pruned candidates:** speculative readiness polling/configuration
  changes were reverted byte-for-byte before commit because archived evidence
  did not quantify failed-poll frequency. Concurrent volume mutations were
  rejected because they would change failure ordering. Bollard still opened
  one test TCP connection per request, so executor savings are not claimed
  before live qualification.
- **Offline payload evidence:** the exact daemon install archive decreased
  from 7,176,192 to 2,918,377 bytes, a reduction of 4,257,815 bytes or 59.333%
  per create. Five-run construction averages were 23.343 ms plain and
  228.119 ms gzip. Because the cache pays compression once per content
  identity, 102 lifecycle creates would transfer approximately 434.3 MB fewer
  archive bytes; realized seconds remain unclaimed until the fresh pilot.
- **Validation:** all 17 non-live provider tests passed and the one
  Docker-required test remained explicitly ignored. The new archive test
  verifies gzip magic and exact extracted paths, 0755/0644 modes, and bytes;
  the runtime regression exercises repeated executor calls from inside a
  separate Tokio runtime. `cargo fmt --all -- --check`, provider all-target
  Clippy with warnings denied, `cargo check -p sandbox-gateway`, and
  `git diff --check` passed. Root independently repeated the offline provider
  suite and all four checks successfully.
- **Commit:** exact local product commit
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`
  (`perf(docker): reuse executor and compress daemon archive`) on direct
  `main`, parent `214cea7a9926abfc5c5e3d681946949eda040ab6`.
  Product is clean and 12 commits ahead of `origin/main`; no branch, worktree,
  push, or tag was created.
- **Source identities:** archive
  `sha256:98a0aad398c52fccb42a856d4f2a66e28832be71a33f0aa8f5a6dd56cbd3d751`;
  engine
  `sha256:14c737fc9276f4bc788a498216f65b102b397a296a24a5776e48f286de7bd5bf`;
  installer
  `sha256:07df5ef2963ea47b76441fd0b0e0b2add7c775887c1b05628e7ac1b0246e3571`;
  archive test
  `sha256:650c0b8bb10752e3adcb7a602ab841edfa8df858099f75526b82addd0ee7f923`;
  runtime test
  `sha256:8129e7a4efe119aa7f354c8ea554d2c38a10e66ab38ddd9868e0d4300646cf5d`.
- **Package build attempts:** a fresh Linux daemon xtask rebuild failed before
  output because the newly cleared cross-target build needed `sh` for
  jemalloc's configure script and no Windows `sh.exe` is installed. The
  daemon crate/source was untouched by this commit, so the exact prior verified
  7,171,600-byte daemon binary was retained with unchanged
  `sha256:f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`.
  The first Windows package-script launch was blocked before execution by the
  host PowerShell execution policy; the explicit repository-local
  `-ExecutionPolicy Bypass -File` rerun exited 0.
- **Immutable candidate package:** exact directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-0392b299`;
  5,685,130-byte ZIP
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-0392b299.zip`;
  ZIP
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`.
  Component hashes are gateway
  `9f2102d13e9643e57e0988644f9ea61534c469e26f4c705b5b8913e892ff7285`,
  manager
  `564876d4c11040a254d149622d28d3c01259c997ae6472f247dab05e9e1e72ed`,
  runtime
  `c73a5b3bf4b04df5326391bc77b233904074bde72eabc20f393a0f7031d5c1c8`,
  observability
  `25906c1910119a52d98580c748cdad5886aa118d59eccef1f7aa87265c754f26`,
  daemon as above, and config
  `987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Cleanup:** the subagent's exact 50-MiB offline archive-benchmark directory
  was resolved beneath `C:\Users\yifan\AppData\Local\Temp`. A first native
  `Remove-Item` command was blocked before execution by shell policy; the same
  exact validated path was deleted through the PowerShell-hosted .NET
  directory API and confirmed absent. No other path was removed.
- **Disposition:** this exact clean commit/package is the candidate treatment.
  It requires fast preflight, complete smoke, archive verification, and a
  fresh five-sample pilot before any freeze decision.

### 2026-07-31T06:03:35.829Z - Candidate 0392b299 smoke preflight passed

- **Entry ID:** `preflight-exp1-0392b299-smoke-103`.
- **Phase/kind:** EXP1-C strict fast preflight after all current paper/product
  amendments. No live benchmark clock, source edit during measurement, Docker
  mutation, pull, install, freeze, tag, or final operation occurred.
- **Plans:** fresh validation subprocesses exited 0 with empty stderr,
  `runnable: true`, `is_customized: true`, and zero findings/warnings.
  `paper-env-smoke` has 19 cells, 19 batches, 55 issued requests, and plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  `paper-pilot` has 19/133/385 and
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  `paper-good-pass` has 19/1,938/5,610 and
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
  All plans select only `product_cli`, the pinned image, and `paper-100m`.
- **Exact treatment:** clean product direct `main` at
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; exact package ZIP
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`.
  Gateway/manager/runtime/observability `--help` each exited 0 with empty
  stderr and hashes
  `9f2102d13e9643e57e0988644f9ea61534c469e26f4c705b5b8913e892ff7285`,
  `564876d4c11040a254d149622d28d3c01259c997ae6472f247dab05e9e1e72ed`,
  `c73a5b3bf4b04df5326391bc77b233904074bde72eabc20f393a0f7031d5c1c8`,
  and
  `25906c1910119a52d98580c748cdad5886aa118d59eccef1f7aa87265c754f26`.
- **Host/environment:** `DESKTOP-OLP1ADS`, Windows build 26200, NTFS, 48
  logical processors, 137,438,953,472 physical-memory bytes, and
  563,732,828,160 free bytes on `C:`. Docker client/server remains 29.0.1,
  Linux AMD64, `overlayfs`, cgroup v2. Exact image
  `sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf`
  is local; no pull was issued.
- **Preserved baseline:** protected debug gateway PID 62980 is the only
  sandbox-named process. There is one pre-existing exited labeled container,
  two sandbox volumes, three shared-base volumes, an empty benchmark runtime,
  and the same eight older terminal run records. Nothing was started, stopped,
  removed, or relabeled.
- **Recorded diagnostic mistake:** one read-only Docker preflight used the
  complete JSON formatter and locally printed the stopped protected baseline
  container's full label set, which included its authentication label. The
  value is intentionally not reproduced here. It was not written to campaign
  artifacts or user-facing reporting, and no resource changed. All future
  baseline probes are restricted to ID/name/state fields.
- **Clock discipline/disposition:** outer exit-capture helper remains
  `sha256:7091ecdcee6b69ef471e0322aae4f28e1a5e61e776b80c0f04f84fabb9b6aa4f`.
  From the next smoke command start through its terminal artifact and recursive
  workspace cleanup, no build, test, install, pull, source/log edit,
  dependency mutation, recursive workspace probe, or environment
  reconfiguration is permitted. Exactly one fresh smoke is authorized; pilot,
  freeze, tag, and final remain prohibited pending archival and audit.

### 2026-07-31T06:13:21.440Z - Candidate 0392b299 CLI integration smoke passed

- **Entry ID:** `smoke-exp1-0392b299-pass-104`.
- **Phase/kind:** EXP1-C live `paper-env-smoke`, immutable archival,
  independent archive verification, and explicit cleanup. This is accepted
  qualification evidence and permanently ineligible for manuscript tables.
- **Run/identity:** run `019fb6c5-dab0-7958-b7ba-94f2a9eda944`; clean product
  commit `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; candidate package ZIP
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`;
  pinned image; smoke plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`.
- **Captured result:** supervised wrapper and benchmark both exited 0.
  Benchmark stderr and wrapper stderr are empty. Manifest start
  `2026-07-31T06:04:10.415013Z`, end
  `2026-07-31T06:07:51.671728Z`, exact elapsed 221.256715 seconds. The outer
  launch-to-wrapper-completion bracket is 448.5456188 seconds and includes
  complete recursive deletion of all 19 deep fixture copies.
- **Terminal corpus:** state `completed`, correctness `pass`, report ready and
  non-provisional; all 19 cells, 19 trial batches, 55 issued requests, 48
  correctness checks, and 19 operation-evidence records passed with zero
  failures and report warnings. The cold create-sandbox request was
  52.0341268 seconds, proving Docker accepted and extracted the compressed
  daemon archive. The total manifest elapsed is 17.027046 seconds below the
  prior accepted smoke, but smoke values remain qualification-only and the
  combined treatment prevents attribution to a single amendment.
- **CLI/resource evidence:** all 339 schema-2 CLI invocations have unique
  request IDs, return code 0, passed response validation, zero stderr bytes,
  and passed authentication redaction. There are 602 resource records with
  complete mandatory windows. Expected Windows allocated-byte and LayerStack
  limitations remain explicit unavailable values; nothing is coerced to zero.
- **Cleanup:** the owned run workspace/runtime are absent. Archive cleanup proof
  reports no run/gateway-labeled candidate container or volume, no matching
  process, and a clean exact product checkout. Independent restricted probes
  found only protected gateway PID 62980, the one pre-existing exited
  container, and the five pre-existing volumes. Explicit benchmark cleanup
  exited 0 with `cleaned: true`.
- **Immutable archive:** creation and independent verify-only invocations exited
  0 with empty stderr and exact agreement at
  `experiments\runs\019fb6c5-dab0-7958-b7ba-94f2a9eda944`: 1,073 files,
  29,730,028 bytes, content-tree
  `sha256:3ad6e3aba681cfdf257939df79a0561a5b73b710a73d46686146bc5780fe8a6b`.
  Archive-manifest SHA-256 is
  `6fc6924f5bf775b4572093d6f5d619c249e2362273b69dc5d1626ec2bb8e21d1`;
  campaign-manifest SHA-256 is
  `bf301771c5c2fff3ee82687d8ee8982a6c6d8451635664b411a2140afd99a325`.
  Disposition is `smoke`, eligibility `qualification_only`, and protocol state
  `pre_freeze`.
- **Clock discipline:** no build, test, install, pull, source/log edit,
  dependency mutation, Docker inspection, or recursive filesystem probe
  occurred from command start through wrapper cleanup. Progress reads were
  restricted to the exact wrapper process and small run-manifest fields.
- **Disposition:** EXP1-C passes for the exact `0392b299` treatment. One fresh
  exploratory five-sample pilot is authorized after a strict fast preflight.
  Freeze, tag, and final remain prohibited until pilot archival, deterministic
  table regeneration, the amended 1,400-second structural projection, anomaly
  review, and cleanup pass Gate 3.

### 2026-07-31T06:14:06.087Z - Candidate 0392b299 pilot preflight passed

- **Entry ID:** `preflight-exp1-0392b299-pilot-105`.
- **Phase/kind:** EXP1-D strict fast preflight; no live pilot clock started.
- **Smoke prerequisite:** an additional independent verify-only invocation
  exited 0 with empty stderr and reconfirmed smoke
  `019fb6c5-dab0-7958-b7ba-94f2a9eda944`: 1,073 files, 29,730,028 bytes,
  content-tree
  `sha256:3ad6e3aba681cfdf257939df79a0561a5b73b710a73d46686146bc5780fe8a6b`.
- **Plan:** fresh `paper-pilot` validation exited 0 with empty stderr. It is
  runnable/customized with zero findings/warnings, only `product_cli` and
  `paper-100m`, exactly 19 cells, two warmups plus five measured trials per
  cell, 133 batches, 385 issued requests, and plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Treatment/environment:** product remains clean direct local `main` at
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; package remains
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`.
  `C:` has 563,676,590,080 free bytes. Benchmark runtime is empty and the
  smoke workspace is absent. Restricted probes found only protected gateway
  PID 62980, the one pre-existing exited container, and the same five
  pre-existing volumes.
- **Clock discipline/disposition:** from the next pilot command start through
  terminal artifact and recursive cleanup production, no build, test, install,
  pull, source/log edit, dependency mutation, Docker inspection, recursive
  workspace scan, or environment reconfiguration is permitted. Exactly one
  fresh exploratory pilot is authorized. It is permanently ineligible for
  manuscript tables; freeze, tag, and final remain prohibited pending its
  complete Gate-3 audit.

### 2026-07-31T06:28:19.016Z - Fresh pilot passes amended Gate 3

- **Entry ID:** `exp1-0392b299-pilot-gate3-pass-106`.
- **Phase/kind:** EXP1-D live exploratory pilot, immutable archival,
  independent archive verification, deterministic regeneration, exact
  final-plan validation, preregistered structural runtime projection, anomaly
  review, and cleanup. Every pilot/projected value remains ineligible for
  manuscript tables.
- **Run/identity:** run `019fb6cf-6021-76d5-ab4f-c6ed53e1d293`; clean product
  commit `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; candidate package/image;
  pilot plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Terminal result:** supervised benchmark exit 0, empty benchmark/wrapper
  stderr, terminal `completed`, correctness `pass`, report-ready and
  non-provisional. All 19 cells, 133 trial batches, 385 product requests, 336
  checks, 133 operation-evidence records, and 95 measured trials completed with
  zero failures, exclusions, or report warnings.
- **Timing:** manifest start `2026-07-31T06:14:34.194294Z`, end
  `2026-07-31T06:19:10.698722Z`, exact elapsed 276.504428 seconds. The outer
  launch-to-wrapper-completion bracket is 563.5771511 seconds including
  complete recursive deletion of all deep fixture copies. Relative to the
  prior healthy current-protocol pilot, manifest elapsed decreased
  15.468330 seconds.
- **CLI/correctness/resources:** all 1,901 schema-2 CLI invocations have unique
  request IDs, return code 0, passed response validation, zero stderr bytes,
  and passed authentication redaction. There are 4,256 resource records and
  385 correlated request IDs. One optional periodic collector in a warmup
  explicitly recorded its fixed-concurrency-cap saturation; its records are
  marked `sampled: true`, the mandatory baseline/final boundaries completed,
  and no measured request/correctness result is missing. Expected Windows
  allocated-byte and unreported LayerStack fields remain explicit unavailable
  values.
- **Cleanup/archive:** exact run workspace/runtime are absent; cleanup proof
  records no run/gateway-labeled candidate resource or matching process and a
  clean exact product checkout. Explicit benchmark cleanup exited 0. Creation
  and independent verify-only invocations agree at
  `experiments\runs\019fb6cf-6021-76d5-ab4f-c6ed53e1d293`: 5,873 files,
  177,619,234 bytes, content-tree
  `sha256:f81cf711bbb734f04201c7fdc09652e0d59c7cbdecd50fe3676370b1df77b93c`.
  Archive-manifest SHA-256 is
  `c2810ac9014f835c676dce294ba4a164c7cc979c4e9cd49be4c3239bdf9bdbc6`;
  campaign-manifest SHA-256 is
  `de60036c6fa2bb5d715315e61c36909a50701462a030d9f2af649a079b1033cb`.
- **Deterministic tables:** generator
  `sha256:37f2dddec2684b6eb2682c65ebdb4750b3a4f795596045ec05da827f06dff7e3`
  exited 0 twice with empty stderr using only the immutable archive. The two
  nine-file outputs are byte-identical: 228,922 bytes, content-tree
  `sha256:4196b53dac63db96053375ca779bf60321849bd14e66366f4390854e85877cd8`,
  and both say `exploratory_ineligible`. Component hashes are environment
  `325a9c8ac9326f0b4b5bc4009df89453bed4033802a4269f1cb5fb593c9fe11d`;
  startup
  `3b413b5a12e2f4d5ec35cc3017cdfc7577638456acc47a27fd4043b4814a9556`;
  CLI operations
  `7eb9709e4d9870190f2ab6d7d66b6a2f895bd188b4c674a9e16216803d624fa0`;
  resources
  `7c9ed30898589abf5d726d3582c2e157d94f6460cddafa156edd6dfb87c56d75`;
  tables JSON
  `2697a52ecd376dc573784c8ab5525b002f8a60a376da1f81c1be384b78909794`;
  numeric evidence
  `92478bd426e10ba1b58ecbd50f10b904be3922dd75fed0a17aecd287bcc524e6`;
  provenance
  `aaab8dc3584bba274c3d8d2651a62bfa386c0a0d490bf8ef7bbbcbcdb8052072`.
- **Exact final plan:** `paper-good-pass` remains runnable/customized with zero
  findings/warnings, only `product_cli`/`paper-100m`, 19 cells, 1,938 batches,
  5,610 requests, plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`;
  reviewed expansion SHA-256
  `4d2389e1782a5075bf4130b3a158b55cc39cc697a1f53593f8c93ff2388e7c92`.
- **Structural projection:** amended fixed script
  `sha256:444eafef866c9d8be5a00f63a80eeb3727b6dfddd0faa0128d2f54deb161319f`
  exited 0 twice with empty stderr and byte-identical output
  `experiments\analysis\pilot-final-runtime-structural-0392b299-019fb6cf-limit1400.json`,
  `sha256:8b02470b98a8ff2374d140398e6a7bb00abb469fa96810db4a680ab00079a4a8`.
  Pilot elapsed is 276.504428 seconds, central structural projection is
  1,170.818322650 seconds, and observed envelope is 1,307.100411100 seconds.
  All are below 1,400 seconds; central margin is 229.181677350 seconds and
  envelope margin is 92.899588900 seconds. Decision is
  `pass_runtime_projection`.
- **Projection decomposition:** run-fixed 80.922308300 seconds; family-fixed
  1.154963500; cell central 1,088.741050850; cell envelope 1,225.023139300.
  Family central/envelope totals are command
  112.089687425/116.950502100; files
  583.998037100/634.833464900; workspace lifecycle
  79.595985150/82.700570800; sandbox lifecycle
  313.057341175/390.538601500 seconds. Versus the prior current-protocol
  projection, central/envelope decreased 75.882800400/81.653538500 seconds.
- **Clock discipline:** no build, test, pull, install, source/log edit,
  dependency mutation, Docker inspection, recursive workspace read, or
  environment reconfiguration occurred during the pilot or its wrapper
  cleanup. Progress reads touched only exact process and small manifest fields.
- **Gate-3 decision:** PASS. Correctness, cleanup, timing separation, resource
  correlation, deterministic regeneration, anomaly review, and all three
  amended runtime conditions pass. Freeze is now authorized under the user's
  prior explicit local commit/tag permission; no final run has occurred.

### 2026-07-31T06:34:57.974Z - EXP1 protocol v1.0 and treatment frozen

- **Entry ID:** `exp1-protocol-v1-freeze-107`.
- **Phase/kind:** EXP1-E scoped local source commit, annotated product tag,
  machine-readable freeze record, and independent clean-scope verification.
  No final measurement clock has started.
- **Paper source:** exact staged review covered 62 campaign source, test,
  preset, protocol, analysis, and experiment-log files; `git diff --cached
  --check` exited 0. Local commit
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`
  (`feat(benchmark): freeze EXP1 CLI protocol v1.0`) was created on the
  existing paper branch. The archive script's final-mode provenance check
  independently reports `dirty: false`, empty scoped status, and
  `clean_frozen_commit`. Excluded caches and non-frozen evidence remain
  preserved.
- **Benchmark identity:** 207 non-excluded files, 16,290,860 bytes,
  content-tree
  `sha256:1efeff548dd664580dcb452829d86e1ae114477828a1af65589b7e34cc311b67`.
  The frozen protocol and expected-table specifications hash to
  `sha256:c021ecdd47cc80b1601171c7c175ed4f42d12dfe51229aa4c36b603b8d0a18ce`
  and
  `sha256:7c1ae3d78a9ca7a5b6cbb4a9cc80bac555d676c5833a40d2846597884f8f50da`.
- **Product treatment:** direct clean product `main` remains
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`. Annotated local tag
  `paper-v1-freeze` was created; tag object
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d` has object type `tag` and
  peels exactly to the measured commit. Nothing was pushed.
- **Package/image/fixture:** candidate ZIP is 5,685,130 bytes,
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`;
  the Ubuntu 24.04 digest is unchanged. Fixture hash is
  `sha256:9484b132c8a35afd18bc37383759d0fe6d45dd4700b42a99336aed535e651cc7`
  with tree
  `sha256:d4c2fefbf94a30352f39d701ececaeeb8fad35603e4fb721dd5cf21296258c9f`.
- **Final plan/analysis:** the reviewed final plan remains
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`,
  seed 20260712, 19 cells, two warmups plus 100 measured trials, 1,938
  batches, and 5,610 requests, exclusively `product_cli` and `paper-100m`.
  Archive, table-generation, and projection scripts hash to
  `sha256:25cca63e4acc035a60384dce11221d6571a10ccd1bdf5b3a39e0e7a0d027426e`,
  `sha256:37f2dddec2684b6eb2682c65ebdb4750b3a4f795596045ec05da827f06dff7e3`,
  and
  `sha256:444eafef866c9d8be5a00f63a80eeb3727b6dfddd0faa0128d2f54deb161319f`.
- **Freeze artifact:** the complete machine-readable record is
  `experiments\analysis\exp1-freeze-record-eb10c26-0392b299.json`. It freezes
  protocol version, Git identities, binary/package/image/fixture identities,
  seed, trials, plan, table schema, metrics, exclusions, stopping rules, and
  analysis identities.
- **Gate-4 decision:** PASS. Every scientific and executable identity is now
  fixed. The sole eligible `paper-good-pass` is authorized after one final
  read-only preflight; any source/protocol/treatment mutation from this point
  would invalidate the freeze and block final execution.

### 2026-07-31T06:38:09.609Z - Frozen final preflight passed

- **Entry ID:** `preflight-exp1-0392b299-final-108`.
- **Phase/kind:** EXP1-F last read-only preflight for the sole eligible final
  attempt. No final benchmark clock had started while this record was written.
- **Freeze/source:** the machine-readable freeze JSON parses successfully and
  hashes to
  `sha256:38608c306476ce19cd63f1e42808aaa45cd030e3e160a88dd6defd1189aa3429`.
  Frozen paper scope remains clean at
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`. Product remains clean direct
  `main` at `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; annotated tag object
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d` still peels exactly to that
  commit. Candidate package SHA-256 remains
  `2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`.
- **Fresh final-plan validation:** `benchmark_lab validate` exited 0 with empty
  stderr. The UTF-16 PowerShell capture hashes to
  `sha256:fc12b1e75fb9716369a0c63743b074277252121f08b7de28d143d6418d1fd534`.
  Corrected structural parsing confirms `runnable: true`, no findings or
  warnings, 19 cells, 1,938 batches, 5,610 requests, `product_cli`, and exact
  plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
- **Uniqueness/state:** there are zero prior `paper-good-pass` result manifests
  and zero final archives. Benchmark runtime and campaign workspace are
  absent; `C:` has 563,278,090,240 free bytes.
- **Protected baseline:** restricted probes that exposed no labels found only
  protected gateway PID 62980, one pre-existing exited container
  `5ce30657bf83`, and the same five pre-existing volumes. No protected resource
  was changed.
- **Inspection corrections retained:** one wrapper-sidecar read used a
  nonexistent timestamped filename before the exact existing filename was
  read; one combined no-match `rg` probe propagated exit 1 before a corrected
  no-match-aware probe proved both final counts are zero; one malformed
  exploratory `rg` regular expression was replaced by fixed-string searches.
  The first PowerShell view misleadingly counted absent JSON properties as one,
  and a first Python parse assumed UTF-8 for a UTF-16 PowerShell redirect.
  Corrected UTF-16 structural parsing produced the accepted values above.
  These were read-only orchestration/inspection failures and did not mutate
  the frozen treatment or consume a final attempt.
- **Authorization/clock discipline:** exactly one `paper-good-pass` launch is
  now authorized. From its command start through terminal wrapper cleanup, no
  build, test, install, pull, source/log edit, dependency change, Docker
  inspection, recursive workspace scan, archive, or environment
  reconfiguration may occur. Progress reads are limited to the exact wrapper
  process and small run-manifest fields.

### 2026-07-31T07:19:03.383Z - Sole frozen final fails and is preserved ineligible

- **Entry ID:** `exp1-0392b299-final-failed-handoff-109`.
- **Phase/kind:** EXP1-F sole frozen final attempt, terminal failure
  preservation, exact cleanup, independent archive verification, post-run
  diagnosis, claim-boundary handoff, and final Gate 0--7 report. No second
  final was launched; no frozen source, treatment, environment, plan, metric,
  exclusion, or trial count was changed.
- **Run/identity:** `paper-good-pass` run
  `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`; frozen paper commit
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`; clean product commit
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`; annotated product tag object
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`; package
  `sha256:2d487a7d42bfb85058ce0f9a2336229e1bda112b940a6854ee25fbd2e604920e`;
  final plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
- **Terminal result:** benchmark/wrapper process exit 0 and empty stderr do not
  override the run manifest: terminal state is `failed`, correctness `fail`,
  eligibility `failed_ineligible`, and infrastructure failure is true. The
  manifest started `2026-07-31T06:39:01.112787Z`, ended
  `2026-07-31T06:50:13.449078Z`, and records 672.336291 seconds. The run
  completed 853/1,938 trial batches and issued 2,077/5,610 product requests
  before its single failure; these are completion/provenance counts, not
  performance results.
- **Failed trial:** family `files`, operation `file_read`, cell
  `sha256:22e51aa86c53171ed08483202c70fd8275700d0232908737242749a59d59cc16`,
  measured trial
  `trial-242749a59d59cc16-measured-000034`. The product request succeeded, but
  the mandatory post-response snapshot boundary failed before verification.
  Only one of two 14-metric resource boundary batches was durably recorded.
  The trial is `infrastructure_failed`, `reportable: false`, and records
  `cleanup_baseline_restored: true`.
- **Direct connection evidence:** observability request
  `trial-242749a59d59cc16-measured-000034.observe.snapshot.1.boundary.0`,
  invocation record
  `raw/cli-subprocesses/de511434eb741316c53eba28b2e8586c402560f3d346b593c3f37c36e4547311.json`,
  returned 1 with
  `transport_error:gateway transport failed (connection_error)` and Windows
  WSAEADDRINUSE 10048. Record SHA-256 is
  `3e188c6e284c0f65e2a909df854ac18a5f550ea1daffb86f2eb3d02ebc26ab0f`;
  its 187-byte stderr hashes to
  `b61e0c2f370d165f3aee73407c216ca82db0bed41112c5462f1257f9888bab5c`.
  The concurrent post-boundary cgroup sibling returned valid data, so the
  gateway was still live and the product file-read was not the proximate
  failure.
- **System evidence/root cause:** a read-only post-run query retrieved exact
  Windows System/Tcpip event 4227, record 88385, timestamp
  `2026-07-31T06:50:09.9652511Z`. Its message says the selected local endpoint
  had recently been used for the same remote endpoint and identifies high-rate
  connection open/close churn as the typical cause. The primary event capture
  is
  `experiments/analysis/exp1-final-system-event-4227.json`,
  `sha256:b6eac476b6ecf8c20de529be5c5ca8de297874ae9273c65a4baaf6ffc34ac89d`;
  message SHA-256 is
  `535f882dfc5e90d98a9ffb429ef7a2c3d5eeb45d71892b54eb0af2bb1bc548dc`;
  XML SHA-256 is
  `864d02daffa7ea1c6030f520ccbe7983279229ea8f6ff0e2a5d468bc0a134c34`.
  High-confidence scoped diagnosis is Windows local TCP endpoint-reuse
  pressure at the snapshot connection. The evidence does not establish that
  all 16,384 dynamic ports were simultaneously occupied, an exact TIME_WAIT
  count, or a universal Windows ceiling.
- **Connection-pressure context:** before stop, the archive retained 7,992
  committed CLI invocation records: 7,991 return-code-zero and exactly one
  return-code-one snapshot. Of these, 6,760 were produced in the preceding
  240 seconds; roles are manager 328, runtime 3,829, and observability 3,835.
  The host reported IPv4 and IPv6 dynamic TCP ranges beginning at 49,152 with
  16,384 ports each. These contextual counts do not prove instantaneous port
  occupancy.
- **Evidence-group disclosure:** the raw CLI projection directory has 7,993
  basenames, one more than the 7,992 committed invocation metadata records.
  Basename
  `766ed434998f2dc7c002bac6dd08c3d642cf1ec416eb2d2cc7df65a6906471a0`
  has a 20,165-byte valid cgroup JSON stdout
  (`sha256:0c53f4064938e550a540f0b7004f3ee0f131e097bfabb39a3874e34ff03e4c5b`)
  and empty stderr, but no metadata commit marker. It is consistent with the
  concurrent cgroup sibling completing while the snapshot exception unwound
  the boundary gather; the exact persistence race is not logged and is not
  claimed as proven.
- **Archival attempts and cleanup:** the first archive invocation failed
  closed because the exact owned
  `.benchmark-state/runs/019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`
  workspace still existed. Explicit exact-run benchmark cleanup then exited 0
  with `cleaned: true`; the owned workspace and benchmark runtime are absent.
  The second archive creation and an independent verify-only invocation both
  exited 0 and agree at
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`:
  24,867 files, 620,311,242 bytes, content-tree
  `sha256:7efa643b12aba09f0ba5ecfbed5b5692a166a5c12931490402d3992d92f3ae6a`.
  Archive-manifest SHA-256 is
  `5e0a3c4f7c864df8070a668d2f373b75bece3c2a57cc4340cd89ece292cc7927`;
  campaign-manifest SHA-256 is
  `8eefbec9772406943bb1baa2476b181c7436a6fafd7a6d7984874e8889f96982`;
  raw-tree SHA-256 is
  `1cc85e7883136ede15e342aa6f2ac50d72bdf6d4eace340dc0e6dba9e992f5b5`;
  verify output SHA-256 is
  `13b4b44f9a6f2e8835fd85b81d73de0bba7a65ac0eb7c110a57ad21168f43630`.
- **Independent final cleanup proof:** no benchmark runtime or exact run
  workspace exists; no matching process remains. Protected gateway PID 62980
  remains live. The one pre-existing exited container and five pre-existing
  volumes remain. Product is clean direct `main` at `0392b299`, and
  `paper-v1-freeze^{}` still resolves exactly to that commit. No protected
  resource was changed and nothing was pushed.
- **Inspection/orchestration attempts:** the initial background wrapper launch
  returned blank output and the exact process/run ID was recovered without a
  relaunch. Early progress reads addressed absent or nested manifest
  properties and were corrected against the actual envelope. An initial final
  archive failed cleanup proof as described above. A combined tracker patch
  failed before any partial edit because of a quote-encoding mismatch; smaller
  patches then succeeded. The first post-run `git diff --check` found four
  Markdown trailing-space defects, which were removed. One PowerShell tag-peel
  expression was parsed as a script block; quoting `paper-v1-freeze^{}` fixed
  it. One orphan-group inspection searched for `.stdout.txt` instead of the
  actual `.stdout` suffix and was corrected. The host PowerShell/.NET version
  lacks static `SHA256.HashData`; a disposable instance `ComputeHash`
  calculation then reproduced the accepted message/XML hashes. These
  attempts did not mutate the frozen treatment or consume another final.
- **Validation and independent audit:** `paper_state.json`, the freeze record,
  the failure diagnostic, and the System-event capture parse as JSON.
  The first final-report marker check required literal `Gate 0` through
  `Gate 7`, while the table initially used bare numbers for Gates 1--7; the
  labels were made explicit and the complete JSON/diff/encoding/marker check
  then exited 0. Post-format scoped `git diff --check` passes. A
  user-requested independent read-only subagent audit reproduced the failed
  trial classification, WSAEADDRINUSE connection error, still-live gateway
  evidence, frozen-code control flow, archive count discrepancy, and rerun
  prohibition. It made no edit or Docker call.
- **Post-run documents:** failure diagnostic
  `experiments/analysis/exp1-final-failure-diagnostic.json`, claim handoff
  `experiments/analysis/exp1-final-handoff.md`, primary Event 4227 capture
  `experiments/analysis/exp1-final-system-event-4227.json`, and required final
  report `experiments/analysis/exp1-gate0-7-final-report.md` were created.
  `claim_evidence_map.md`, `experiment_inventory.md`, `progress.md`,
  `plan/progress.md`, `paper_state.json`, and `benchmark/PAPER_ARTIFACT.md`
  were updated. These post-run records do not alter the immutable freeze or
  make partial values eligible.
- **Gate/protocol decision:** Gates 0--4 PASS. Gate 5 FAILS. Gates 6 and 7
  FAIL because partial-final aggregation and numeric paper handoff are
  prohibited. No final tables or numeric-evidence v2 record are generated.
  Smoke/pilot values remain qualification/exploratory only; all partial-final
  performance values are excluded. Frozen v1.0 cannot be relaunched. Any
  future attempt requires a scientifically documented protocol amendment, a
  new source/environment freeze, and explicit author authorization; it cannot
  replace this immutable failed archive.

### 2026-07-31T07:39:16.055Z - Read-only v1.1 endpoint-pressure remedy audit

- **Entry ID:** `exp1-v1.1-endpoint-remediation-proposal-110`.
- **Phase/kind:** post-failure archive forensics, frozen source-path audit,
  primary Microsoft documentation review, host TCP configuration read, and
  protocol-remediation decision package. This is diagnostic planning only:
  no source, product, network setting, registry value, Git object, Docker
  resource, protected process, frozen archive, or live benchmark was changed.
- **Independent audits:** three user-authorized read-only subagents separately
  reviewed Windows primary sources, the immutable final archive, and
  product/paper remedy options. Two recommended connection reuse as the
  long-term engineering fix. One recommended per-cell gateway blocks as the
  smallest paper-only amendment; root extended that audit with the accepted
  pilot's cells that the failed final never reached and found a 4,532-call
  projected worst cell, slightly above the failed endpoint's 4,398 committed
  calls. Per-cell rotation is therefore retained as a fallback requiring a
  stronger qualifier, not accepted as sufficient by itself.
- **Exact connection inventory:** the archive identifies 7,993
  client-to-gateway TCP attempts: 7,992 committed schema-2 metadata records
  plus the exact valid cgroup orphan projection. Manager accounts for 328;
  runtime 3,829; observability 3,836. Exact operations are create/destroy/
  inspect/list sandbox 110/110/102/6; create/destroy session 208/208;
  exec 1,224; file read 1,567; file write 622; cgroup 1,918; snapshot 1,918.
  The committed trace spans 589.946 seconds; the diagnostic average is 13.549
  attempts/second.
- **Failure-centered rates:** exact 10/30/60/120/240-second windows contain
  186/657/1,349/3,145/6,760 attempts, or
  18.600/21.900/22.483/26.208/28.167 attempts/second. Maximum rolling rates
  were 43.700/42.767/41.667/33.100/28.404 attempts/second. The failure
  occurred near the maximum sustained 240-second count, not the short-window
  rate peak. These are failure-diagnostic counts, not performance results or
  a universal threshold.
- **Resource split:** 3,626 connections were mandatory and 210 periodic;
  mandatory traffic is 94.53% of observability and periodic traffic only
  2.63% of all attempts. There are 1,705 mandatory and 105 periodic retained
  14-metric batches. The absent 1,706th mandatory batch is the failed final
  snapshot. All 1,917 complete cgroup/snapshot pairs overlapped; the 1,918th is
  the failed snapshot plus its valid cgroup sibling. Removing periodic cadence
  cannot solve the mandatory failure and would weaken the frozen resource
  construct.
- **Endpoint and projected demand:** committed endpoints carried 2,878
  command, 4,398 files, and 716 sandbox-lifecycle calls. Proportional
  trial-scoped extrapolation from the accepted seven-trial pilot to 102 trials
  gives a diagnostic 26,392 total calls: files 20,578; command 2,856;
  workspace lifecycle 2,244; sandbox lifecycle 714. The largest single
  projected cell is the concurrency-5 256-KiB file-edit cell at 4,532 calls.
  Periodic/freshness polls make these structural estimates rather than exact
  final counts.
- **Frozen mechanism:** product
  `crates/sandbox-operations/client/src/client.rs`,
  `sha256:61ed900ae92a6911649390966b7dc47aec9eff98898f1942305c77ef4740edcc`,
  creates a fresh `TcpStream::connect` and shuts down its write side per
  request. Gateway
  `crates/sandbox-gateway/src/gateway/connection.rs`,
  `sha256:0cd590e9e3bc3db0c3c4eb0cd878bda44b7085487f3a91c5a514604b49be8a8b`,
  reads one request and shuts down after its response. Retaining a client
  object cannot pool this protocol; actual persistence requires product and
  CLI redesign and is a separate treatment.
- **Read-only host state:** all reported TCP profiles use dynamic range
  49,152 plus 16,384 and auto-reuse range 0 plus 0. IPv4 and IPv6 `netsh`
  ranges agree. `TcpTimedWaitDelay`, `MaxUserPort`, and
  `StrictTimeWaitSeqCheck` are not explicitly configured in the inspected
  registry key; no default duration is asserted. A transport-filter query
  returned Windows access denied, and the read-only Windows principal check
  reports `IsAdministrator: false`.
- **Candidate decisions:** removing all periodic sampling saves only 210
  connections and is rejected. Removing observed baseline repolls plus all
  periodic sampling saves 424, 5.30%, and is not evidence of safety. Combining
  cgroup/snapshot into one product operation would save 1,918 observed calls,
  24.00%, and removes the incomplete-pair shape but requires a new product
  schema and has no validated safe threshold. Serializing the pair saves zero
  calls. Persistent multiplexing is the preferred product fix but changes the
  frozen timing construct if used for measured calls. TIME_WAIT reduction,
  `SO_REUSEADDR`, pacing, sleeps, retries, and reboot-only recovery are
  rejected for the first amendment.
- **Recommended campaign path:** pending explicit author authorization, use an
  elevated active-store-only IPv4 range of 1,025 plus 64,511 through the
  current boot. This preserves every measured one-shot subprocess/transport
  boundary and changes no product operation, metric, cell, payload, trial,
  exclusion, or analysis schema. It is a disclosed experiment workaround,
  not the long-term product fix. The exact proposed command, not run, is
  `netsh interface ipv4 set dynamicportrange protocol=tcp startport=1025
  numberofports=64511 store=active`; exact rollback, also not run, is
  `startport=49152 numberofports=16384 store=active`. IPv6, TIME_WAIT,
  auto-reuse, routing, firewall, Docker, and protected resources would remain
  unchanged.
- **Required qualification before freeze:** capture elevated pre-state and
  event cursor; apply/verify only the active IPv4 range; wait for prior state
  to quiesce; run an ineligible strict same-endpoint native-CLI qualifier for
  at least 700 seconds and 20,000 successful connections at no less than the
  failed run's sustained 240-second rate; capture BOUND/TIME_WAIT and Event
  4227/4231 evidence; fail on any transport error/event; clean up and quiesce;
  then repeat complete smoke/pilot, deterministic exploratory regeneration,
  cleanup, and the no-more-than-1,400-second projection. Only then may v1.1
  source/environment identities be frozen and exactly one new final
  separately authorized. The active range must be restored after archival,
  including on failure.
- **Primary documentation:** Microsoft port-exhaustion/Event-4227 guidance,
  dynamic-range support, `netsh` active/persistent store, SQL connection-pool
  guidance, Winsock error definitions, TCP-setting WMI documentation, and
  `SO_REUSEADDR` safety guidance are linked in the decision package. Microsoft
  characterizes range expansion as mitigation and recommends addressing
  connection churn/pooling for the long term.
- **Recorded read-only attempts:** one source inspection requested a
  nonexistent `sandbox-operations/client/src/transport.rs` beside the actual
  `client.rs`; the missing read changed nothing. `Get-NetTransportFilter`
  failed with access denied and establishes the external elevation boundary.
  A `netsh ... set dynamicport tcp ?` help probe returned a missing-parameter
  diagnostic plus authoritative syntax; no setting argument was supplied and
  no mutation occurred. One broad request-ID categorization initially counted
  create-sandbox mandatory samples and freshness repolls as periodic; the
  independent resource-observation audit corrected the accepted split to
  3,626 mandatory and 210 periodic.
- **Artifacts/blocker:**
  `experiments/analysis/exp1-v1.1-remediation-decision.json` and `.md` retain
  the complete machine/human decision. Both JSON state files parse; scoped
  diff and encoding checks pass; operation, resource-split, range-arithmetic,
  and required-marker consistency checks exit 0. The exact remaining blocker
  is one author decision approving or rejecting the host-wide active-store
  IPv4 mutation and the complete qualifier/refreeze/one-final sequence. No
  step of that sequence is implied by earlier v1.0 authorization.

### 2026-07-31T07:59:50.209Z - Author authorized permanent CLI transport fix and EXP1 v1.1 resumption

- **Author direction:** after reviewing the local TCP endpoint-reuse failure
  and the temporary dynamic-range workaround, the author directed: “fix the
  issue then resume the goal.” This authorizes the demonstrated released-CLI
  transport defect to be corrected in product `main` and authorizes the EXP1
  campaign to resume as a new protocol/treatment version after qualification.
- **Protocol decision:** EXP1 v1.1 will replace one-shot CLI-to-gateway
  loopback TCP with direct OS-local IPC to the existing gateway: Windows named
  pipes on the fixed host, with Unix-domain sockets implemented for
  cross-platform product parity and TCP retained only as an explicit
  compatibility/remote endpoint. Each measured request remains one fresh
  native CLI subprocess and one request/response exchange. No persistent CLI,
  broker, retry, pacing, cell, payload, trial, sampling, exclusion, metric, or
  table change is authorized.
- **Why this supersedes the prior proposal:** independent native CLI processes
  cannot share an in-process TCP pool. Direct local IPC removes Windows
  ephemeral TCP allocation from the measured CLI-to-gateway path without an
  additional broker process, while preserving the native subprocess timing
  boundary. The existing gateway request handler is already transport-neutral;
  only endpoint discovery/connect/listen plumbing needs to change.
- **Evidence boundary:** the sole v1.0 final and its archive remain immutable,
  failed, and ineligible. Its partial values will not be rerun, replaced,
  pooled, or compared numerically with v1.1. Local IPC is a scientifically
  material transport treatment and therefore requires a new product identity,
  package hashes, protocol/source/environment freeze, smoke, five-sample
  pilot, projection no greater than 1,400 seconds, and exactly one new final
  only if all preceding gates pass.
- **Host state:** the proposed IPv4 active-store range expansion was never
  applied and is no longer the selected v1.1 path. IPv4, IPv6, TIME_WAIT,
  auto-reuse, routing, firewall, Docker, and protected resources remain
  unchanged.
- **Implementation/qualification gate:** before live benchmark smoke, require
  product transport parity and failure tests, bounded gateway lifecycle and
  cleanup, an ineligible high-churn native-CLI named-pipe qualification of at
  least 25,000 successful invocations including concurrency-5 bursts, zero
  transport failures, no new TCP/IP 4227/4231 event attributable to the
  qualifier, no silent TCP fallback, and bounded process handle/RSS growth.
  Any failure remains a pre-freeze blocker.
- **Git boundary:** work remains directly on product `main`; no branch,
  worktree, push, or movement of the existing `paper-v1-freeze` tag is
  authorized. Any successful v1.1 freeze will use new immutable commit/tag
  identities and preserve all v1.0 identities.

### 2026-07-31T08:42:08.878Z - Permanent local-IPC product fix committed and packaged

- **Product identity:** direct product `main` commit
  `56c676d588fbb704bf3da8f67d22be910453644d` (`Use local IPC for gateway
  CLI transport`). No push occurred and the existing `paper-v1-freeze` tag was
  not moved.
- **Implemented treatment:** typed `tcp://`, `npipe://`, and `unix://`
  endpoints; Windows named-pipe and Unix-domain listeners; Windows named-pipe
  client; Windows local-IPC defaults; explicit `--gateway-endpoint` with the
  released `--gateway-socket` compatibility alias; and updated Windows
  launcher/package documentation. The client performs one connection attempt,
  one request, and one response with no retry or transport fallback.
- **Product verification:** formatting and diff checks passed. The complete
  changed-crate suite for config, gateway, operation client, all three CLIs,
  and MCP passed, including real named-pipe request/response and concurrency-5
  tests. Warnings-denied all-target Clippy passed for the changed crates.
  A fresh release-binary integration launched five native manager CLI
  processes concurrently against one named-pipe gateway; all five exited 0,
  wrote one valid `{"sandboxes":[]}` JSON line, and had empty stderr.
- **Portability repairs discovered by validation:** the existing gateway
  progress test compared an unescaped Windows path inside a JSON-framed log;
  it now compares the serialized message. The POSIX local-daemon installer
  test is now explicitly Unix-only. Both previously failing gateway tests
  pass.
- **Whole-workspace boundary:** `cargo test` was attempted on native Windows.
  It first exposed the pre-existing Unix-only telemetry `rustix::fs` import.
  A temporary diagnostic portability experiment was fully reverted and was
  not committed; the next attempt reached the pre-existing Linux namespace
  process crate, which cannot compile `std::os::fd`, `std::os::unix`, or
  `libc::pause` on Windows. This is not on the changed Windows
  gateway/client/CLI path; changed-crate tests and strict Clippy are the
  applicable native-Windows gates.
- **Package build:** the first direct `.ps1` invocation was rejected by the
  host execution policy before the script ran. The repository-documented
  `powershell.exe -NoProfile -ExecutionPolicy Bypass -File` invocation then
  completed successfully as
  `target/windows-exp1-56c676d5`. The package ZIP is 5,706,464 bytes,
  `sha256:bba3376de85a80c1664cbc12114666cf00a2d9f45cc4f8cf09477cc5c6df9b1d`.
- **Packaged identities:** gateway
  `sha256:80948557a439e4072a7acbd29fa7bd52824ac7e7ebdcade53656cacc1ca11c68`;
  manager CLI
  `sha256:9ee4ad89c1be3f9461991d4ee468b0ac5be1b8f97bd393d90b1d844c0977fa16`;
  runtime CLI
  `sha256:3b66c73bfe3661ec9a1c71e4d7b74925f6b0ab1957ccb6a33891c710f762082a`;
  observability CLI
  `sha256:3197990555825ee17a2224cad62933ff3eb720f411661015b5604360cc7c1a5b`;
  Linux daemon
  `sha256:f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`;
  Windows config
  `sha256:987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Package smoke:** the packaged gateway and manager CLI repeated the
  concurrency-5 native-process named-pipe check with five exit-0, empty-stderr,
  single-JSON responses. Earlier ad hoc PowerShell result-check wrappers
  mis-handled empty files and process exit-code properties; those wrapper
  errors did not indicate product failures and the final
  `System.Diagnostics.Process` verifier passed.
- **Host/protected state:** no host network setting changed. Protected gateway
  PID 62980 remained alive and untouched. The high-churn qualifier, live
  smoke, pilot, freeze, and final have not started.

### 2026-07-31T08:52:59.986Z - Final local-IPC candidate and qualifier policy preregistered

- **Entry ID:** `exp1-v1.1-ipc-preregistration-113`.
- **Phase:** prequalification protocol/provenance freeze; no live benchmark or
  qualifier result.
- **Candidate correction:** product follow-up commit
  `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8` (`Preserve TCP endpoint
  compatibility`) supersedes `56c676d588fbb704bf3da8f67d22be910453644d`
  as the prequalification candidate. It preserves legacy DNS TCP endpoints,
  retains the strict Windows named-pipe default, and rejects ambiguous Unix
  endpoint syntax. Product `main` is clean; neither commit nor tag was pushed.
- **Final candidate package:** staged directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5c48dae1`;
  ZIP size 5,739,735 bytes and
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`.
  Gateway SHA-256 is
  `42e7642dd025487811abbcd78dcc5513760f2aaa1e6057cfdfa3e74c03748358`;
  manager CLI
  `e1faa2fe0e9f4909fa2d694166784ac65dde40ba82795b7e0c503eb5fea86513`;
  runtime CLI
  `e18827cf765945c958e169748575b89645c730b310ee5ffc1b42c382b44a0e26`;
  observability CLI
  `2b1c13bba36c9486f768824178d1e2ea8d2b1da019bd21cd1f9ea250d5da34c5`;
  Linux daemon
  `f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a`;
  Windows config
  `987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a`.
- **Package validation:** packaged gateway plus five simultaneous native
  manager CLI processes completed on one unique named pipe. Each process
  exited 0, had empty stderr, and emitted exactly one valid
  `{"sandboxes":[]}` JSON line. No retry or TCP fallback was present.
- **Preregistration:** created
  `experiments/exp1-v1.1-protocol-amendment.md` before any live qualifier
  result. The stable
  `EXP1 v1.1 IPC qualification policy preregistration` section fixes exactly
  25,000 `list_sandboxes` invocations as 5,000 concurrency-5 batches; one
  unique named pipe; unique request IDs; strict exit/stdout/stderr validation;
  no TCP, retry, fallback, or pacing; event 4227/4231 coverage through
  post-cleanup; gateway-owned TCP checks at readiness, every 100 batches,
  pre-stop, and post-cleanup; gateway process sampling at readiness, every
  100 batches, and pre-stop; peak and final growth caps of 32 handles, 16 MiB
  private bytes, and 16 MiB RSS; exact-cap pass and cap-plus-one failure;
  complete source/package/command/host provenance; and fail-closed cleanup.
  The qualifier is explicitly `qualification_only` and cannot supply
  performance evidence.
- **Rationale fixed before evidence:** 32 handles is no greater than the
  gateway listener pending-instance maximum. The two 16 MiB allowances are
  conservative fixed engineering-qualification bounds, not measured
  performance results.
- **Supersession:** the historical active-store IPv4 range proposal is marked
  superseded without execution. No IPv4, IPv6, TIME_WAIT, auto-reuse,
  firewall, routing, Docker, or other host network setting changed.
- **Next gate:** finish harness/archive/table hardening and the complete
  backend test suite, create a clean paper prequalification commit, then run
  the preregistered live qualifier. Smoke, pilot, freeze, and final remain
  prohibited until that gate passes.

### 2026-07-31T12:33:58.622Z - Provenance-only Table 1 schema clarification preregistered

- **Phase:** prequalification protocol/documentation hardening; no live
  qualifier, smoke, pilot, or performance evidence was collected.
- **Clarification:** the earlier prohibition on a table change continues to
  lock Tables 2--4 and every numeric/measured definition. Because gateway
  transport is the scientifically material v1.1 treatment, Table 1 now adds
  exactly one non-numeric text row named `Gateway transport`.
- **Schema boundary:** the deterministic table and output-manifest schema is
  version 2 solely to bind the protocol version and typed transport provenance.
  The value is derived from archived run-manifest evidence, never entered
  manually or copied from qualifier results. Legacy v1.0 regeneration may
  disclose its loopback transport without changing the frozen raw corpus.
- **Unchanged design:** the 19 cells, trials, seed, timing boundary, metrics,
  aggregations, eligibility, resource cadence, correctness gates, exclusions,
  and every numeric table field remain unchanged. This is the only authorized
  v1.1 table-schema change.
- **Freeze-scope correction:** authoritative root `progress.md` is now included
  in the archived protocol identity and scoped clean-freeze check alongside
  `plan/progress.md`; tracker drift can no longer escape final provenance.

### 2026-07-31T12:41:43.385Z - V1.1 prequalification source gate passed

- **Entry ID:** `exp1-v1.1-prequalification-source-gate-115`.
- **Phase:** independent integrated review before the clean paper commit and
  live IPC qualifier; no qualifier invocation or performance measurement.
- **Integrated tests:** with `PYTHONDONTWRITEBYTECODE=1`, the complete
  `benchmark\backend\tests` plus `experiments\analysis\tests` run passed:
  354 passed, five expected Windows-symlink-privilege skips, exit 0 in
  48.88 seconds. The final qualifier-only rerun passed 46/46 in 5.28 seconds.
- **Qualifier lint/format:** offline Ruff format-check and lint over
  `ipc_qualification.py` and `test_ipc_qualification.py` both exited 0.
  `git diff --check` exited 0 apart from informational LF-to-CRLF checkout
  warnings.
- **Recorded non-mutating tool failures:** a broader Ruff format-check over
  the imported benchmark subtree exited 1 because 49 legacy files do not
  match the currently cached Ruff formatter; check mode changed no file. A
  broader Ruff lint invocation also exited 1 on pre-existing exception-policy,
  Python-target, import-order, and style findings across legacy runner/gateway
  sources. The scoped qualifier files pass both checks, and the full runtime
  suite passes. No dependency was installed and no bulk reformat was applied.
- **Independent parity correction:** direct comparison found that the
  qualifier's scoped paper path tuple redundantly named files already covered
  by `benchmark`, while the archive tuple did not. The redundant entries were
  removed; qualifier and archive `PAPER_FROZEN_SCOPE` and generated-file
  exclusions now compare exactly equal. The 46 qualifier tests pass after the
  correction.
- **Exact plan validation:** all three plans are runnable, select only
  `product_cli`, and use only `paper-100m`. Smoke remains 19 cells, 19
  batches, 55 requests,
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  pilot remains 19/133/385,
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  final remains 19/1,938/5,610,
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
- **Gate decision:** source, protocol, qualifier, plan, archive, projection,
  and table hardening are ready for a scoped clean paper commit. The live
  qualifier remains prohibited until that commit exists and the qualifier's
  own product-global and paper-scoped clean checks pass.

### 2026-07-31T12:48:54.009Z - EXP1 v1.1 local-IPC qualifier passed

- **Entry ID:** `exp1-v1.1-ipc-qualification-pass-116`.
- **Disposition:** `qualification_only`; `performance_evidence: false`. No
  value from this attempt is eligible for a manuscript table, projection, or
  performance claim.
- **Bound identities:** paper prequalification commit
  `50d068d3ed55a7dfd8a9be9f8a3d52f064610866`; product clean direct `main`
  `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`; package ZIP
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`;
  fixed host `DESKTOP-OLP1ADS`, Windows build 26200, x64, 48 logical
  processors, 137,438,953,472 bytes physical memory.
- **Qualification identity:** `718cf58dace44dba83bed54601854bc9`;
  endpoint
  `npipe://./pipe/ephemeral-sandbox-exp1-ipc-718cf58dace44dba83bed54601854bc9`;
  isolated gateway PID 12132. The protected v1.0 gateway PID 62980 remained
  alive and untouched.
- **Strict workload result:** exactly 25,000 attempted and successful native
  manager-CLI `list_sandboxes` processes in exactly 5,000 concurrency-5
  batches; zero failed invocations. Independent NDJSON verification found
  25,000 lines, 25,000 unique request IDs, 25,000 unique batch/slot pairs, and
  zero records that deviated from exit 0, empty stderr, the expected 17-byte
  stdout hash, or the qualification-only flags.
- **No-TCP/event gates:** all 53 readiness/cadence/pre-stop/post-cleanup TCP
  samples found zero gateway-owned endpoints. The conservative System/Tcpip
  query from record 88541 through 88548 found zero new 4227/4231 events.
  `tcp_used: false`; no fallback, retry, or pacing was permitted.
- **Resource gates:** all 52 required process samples were present. Peak and
  final handle growth above readiness were both 0 against the fixed cap 32.
  Peak and final private-byte growth were both 389,120 bytes, and peak/final
  RSS growth were both 475,136 bytes, against fixed 16,777,216-byte caps.
- **Cleanup:** isolated gateway process exit and PID-file removal both
  validated; termination mode `terminate`; gateway return code 1 is the
  recorded Windows termination status and is accepted by the preregistered
  stop schema. The isolated PID is no longer alive; protected PID 62980
  remains alive. CLI stderr capture is empty.
- **Primary evidence:** active directory
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\.benchmark-state\results\qualification-only\exp1-ipc-718cf58dace44dba83bed54601854bc9`.
  `summary.json` SHA-256
  `5219f09cfe58627a44dd46443c148758483b02b56125fc4a5126a30387e1d286`;
  manifest
  `599c8054ea1ca8517acb778648c86deca70ae20228f94fb5cc73b79fc6b7e880`;
  host evidence
  `83ce2faee1126340798747ce54b14d5c2ea2f541a1f7dba509e72e88fd7842ce`;
  invocations NDJSON
  `1605d176d6bb791ffa726ef5474e70537571719b26798356fc81bfb4de5fb9f8`.
- **Retained copy:** four files, 18,405,217 total bytes, copied with zero
  SHA-256 mismatch to
  `experiments\diagnostics\exp1-v11-ipc-qualification-718cf58dace44dba83bed54601854bc9`;
  compressed archive size 951,312 bytes, SHA-256
  `2c4f87dc5bb123157f76e6be58b769bafef8943aba36ee8e9202601b50e62a02`.
- **Wrapper evidence limitation:** the detached `Start-Process` object was not
  retained after process termination, so its OS-level wrapper exit code is
  unavailable. The exact CLI stdout object byte-for-byte parses equal to
  `summary.json`, reports `status: passed` with no gate failure, and its
  stderr file is zero bytes. All 25,000 scientifically relevant child process
  exit codes are directly present and equal to zero.
- **Next gate:** commit this append-only result/tracker update, then run one
  fresh complete 19-cell v1.1 smoke. Pilot, projection, freeze, and final
  remain prohibited until smoke passes.

### 2026-07-31T13:02:42.753Z - EXP1 v1.1 CLI integration smoke passed

- **Entry ID:** `smoke-exp1-v1.1-5c48dae1-pass-117`.
- **Phase/kind:** EXP1-C live `paper-env-smoke`, immutable archival, and
  verify-only replay. This is qualification-only evidence and is permanently
  ineligible for manuscript tables, runtime projection, or performance claims.
- **Bound identities:** run `019fb83a-54bc-79db-b6ac-6189fb28f5f2`; clean
  paper commit `09795c39a2e4ab92ef57470064a6313985568037`; clean product direct
  `main` commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`; package ZIP
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`;
  smoke plan
  `sha256:1a8364a4612ac16834747d7619be1f63da3857d0223ec181c8a93c6851793937`;
  protocol `ephemeral-sandbox-v1-practical-performance-v1.1`; pinned image
  unchanged.
- **Captured result:** the supervised wrapper and benchmark both exited 0;
  wrapper and benchmark stderr are empty. Manifest start
  `2026-07-31T12:51:02.121558Z`, end
  `2026-07-31T12:54:41.773028Z`, exact corpus elapsed 219.651470 seconds.
  The launch-to-wrapper-completion bracket was 455.068 seconds and includes
  complete recursive deletion of all 19 deep fixture copies.
- **Terminal corpus:** state `completed`, correctness `pass`, report ready and
  non-provisional; all 19 cells, 19 trial batches, 55 issued requests, 48
  correctness checks, and 19 operation-evidence records passed with zero
  failures or report warnings. The cold create-sandbox request was
  47.4741525 seconds.
- **Transport/CLI evidence:** the manifest records exactly four execution
  blocks, all `windows_named_pipe`, `local_only`, and
  `per_execution_block`, with `npipe` endpoint URIs. All 339 schema-2 CLI
  invocations have unique request IDs, return code 0, passed response
  validation and authentication redaction, and produced zero stderr bytes.
  All 602 resource records and mandatory observation windows are retained.
- **Cleanup:** wrapper cleanup removed the owned run workspace and runtime.
  Archive cleanup proof records no matching product process, run- or
  gateway-labeled container or volume, and a clean exact product checkout.
  Independent PID/name/state checks found only protected gateway PID 62980,
  which remained alive and untouched.
- **Immutable archive:** creation and verify-only replay both exited 0 and
  agreed at
  `experiments\runs\019fb83a-54bc-79db-b6ac-6189fb28f5f2`: 1,073 files,
  29,778,180 bytes, content-tree
  `sha256:c8e0e872d42c0df2ce2c19c4b030a29b615a7d250c95097dac9bff66fa4405e4`.
  Archive-manifest SHA-256 is
  `66736f3c23ebe372bb350071f531491a01c038d2137eb9170921ba805286d8aa`;
  campaign-manifest SHA-256 is
  `e2df50964644bc22abfbafffe034c71ee32569c64bb1b5789a3a01feafef6e72`.
  Disposition is `smoke`, eligibility `qualification_only`, and protocol
  freeze state `pre_freeze`.
- **Runtime-budget interpretation:** the inventory's three-minute acceptance
  budget belongs to the already accepted Phase-2 two-lifecycle/20-call
  environment qualifier, not this packet's 19-cell EXP1-C integration smoke.
  EXP1-C acceptance is correctness, warnings, and leak based and specifies no
  runtime cap. The 219.651470-second duration is retained as an anomaly and is
  1.605245 seconds below the previously accepted v1.0 treatment smoke
  `019fb6c5-dab0-7958-b7ba-94f2a9eda944`; it does not block the pilot.
- **Diagnostic evidence-handling correction:** one read-only progress
  diagnostic inspected live process command-line metadata and caused a
  transient gateway credential to appear in diagnostic tool output. The
  literal is intentionally not reproduced, was not copied into campaign
  artifacts, and became unusable when the isolated gateway exited. All
  subsequent live checks are restricted to PID/name/state and exact artifact
  fields.
- **Disposition:** EXP1-C passes for the exact v1.1 treatment. One fresh
  exploratory five-sample pilot is authorized after a strict fast preflight.
  Freeze, tag, and final remain prohibited until pilot archival,
  deterministic table regeneration, the conservative no-more-than-1,400
  second projection, anomaly review, and cleanup pass Gate 3.

### 2026-07-31T13:11:50.680Z - EXP1 v1.1 pilot preflight passed

- **Entry ID:** `preflight-exp1-v1.1-5c48dae1-pilot-118`.
- **Phase/kind:** EXP1-D strict read-only fast preflight; no pilot clock,
  gateway, sandbox, source mutation, Docker mutation, pull, build,
  installation, cleanup, freeze, tag, or final operation occurred.
- **Independent smoke review:** a read-only independent audit confirmed that
  the three-minute inventory budget names the earlier two-lifecycle/20-call
  environment qualifier, not the 19-cell EXP1-C smoke. It decomposed current
  smoke elapsed into 81.281300 seconds fixture materialization, 52.190791
  seconds cell setup, 81.999392 seconds cell-active time, and 2.711728 seconds
  terminal cleanup. The 47.474461-second cold create dominates primary
  operation time, is protocol-required, and must not be prewarmed or reordered.
  No amendment or rerun is warranted.
- **Smoke prerequisite:** two additional verify-only invocations, one by the
  primary workflow and one independent, exited 0 and reconfirmed run
  `019fb83a-54bc-79db-b6ac-6189fb28f5f2`: 1,073 files, 29,778,180 bytes,
  content-tree
  `sha256:c8e0e872d42c0df2ce2c19c4b030a29b615a7d250c95097dac9bff66fa4405e4`.
- **Plan:** fresh `paper-pilot` validation exited 0. It is runnable and
  customized with zero findings/warnings, only `product_cli` and
  `paper-100m`, exactly 19 cells, 133 trial batches, 385 issued product
  requests, four execution blocks, two warmups, and five measured trials per
  cell. Plan SHA-256 is
  `e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`.
- **Treatment/source:** paper frozen scope was clean at commit
  `d427df75e62751c99b99f42d5eebfc20bff35ff7`; product was clean direct
  `main` at `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`. Package ZIP remained
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`.
  Gateway, manager, runtime, observability, daemon, and configuration hashes
  matched the preregistered v1.1 values.
- **CLI contract preflight:** gateway, manager, runtime, and observability help
  exited 0 with empty stderr. Their stdout SHA-256 values were
  `1a01a7c60c1ee1507b47b39c47ffab5d843184e9f94b5d49ecc89ab424f57934`,
  `b8c3a96951784a67b8dfd021cc754ec1e58ddd5e3ba83512424721709c576fe5`,
  `2b2bb48142678f0418d6b01a528e0c79b8de6ab89fafc843d4d660ccd0d7dc5e`,
  and
  `090d943792ace5873bf7099e3f185030474efd73a59fa876a56fa46878f56243`.
- **Host/environment:** `DESKTOP-OLP1ADS`, Windows build 26200, NTFS, 48
  logical processors, 137,438,953,472 physical-memory bytes, and
  544,201,162,752 free bytes on `C:`. Docker client/server remained 29.0.1,
  Linux x86_64, `overlayfs`, cgroup v2. The exact pinned image remained local;
  no pull was issued.
- **Preserved baseline:** the same eight old terminal benchmark-runtime
  records, one pre-existing exited gateway-labeled container, and five
  pre-existing gateway-labeled volumes remained. The only sandbox-named
  process was protected gateway PID 62980. Nothing was started, stopped,
  removed, or relabeled.
- **Preflight wrapper corrections:** three fail-closed helper defects were
  retained. A help attempt from the backend subdirectory used a nonexistent
  relative `.venv` path; a subsequent inventory command requested a
  nonexistent backend-local `pyproject.toml`; neither started a product or
  benchmark process. The first aggregate preflight looked for the Linux daemon
  under nonexistent `libexec` instead of package `dist`; the second
  incorrectly required the historical runtime-record directory to be empty
  rather than equal to its known eight-entry baseline. A third aggregate
  attempt disposed its help process object before retaining the exit code and
  therefore falsely reported gateway-help failure. Each wrapper stopped
  before the pilot. Corrected read-only checks then passed; no artifact,
  source, process, Docker object, or environment state was changed by these
  helper failures.
- **Clock discipline/disposition:** after committing this preflight log, one
  final minimal identity/cleanliness check may run. From pilot command start
  through terminal artifact and recursive workspace cleanup, no build, test,
  install, pull, source/log edit, dependency mutation, Docker inspection,
  recursive workspace scan, or environment reconfiguration is permitted.
  Exactly one fresh exploratory v1.1 `paper-pilot` is authorized. It remains
  ineligible for manuscript tables; freeze, tag, and final remain prohibited
  pending complete Gate-3 audit.

### 2026-07-31T13:37:01.222Z - EXP1 v1.1 pilot and Gate 3 passed

- **Entry ID:** `pilot-exp1-v1.1-5c48dae1-gate3-pass-119`.
- **Phase/kind:** EXP1-D live five-sample exploratory pilot, immutable
  archival, deterministic exploratory analysis, anomaly review, runtime
  projection, and pre-freeze checker correction. Pilot and projected values
  remain permanently ineligible for manuscript tables or performance claims.
- **Bound identities:** run `019fb84e-aef1-7fdc-9a56-1adbe712f30d`; clean
  paper commit `4b962228813c43e57bfcad6d2dae7bde0e71d9d5`; clean product direct
  `main` commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`; package ZIP
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`;
  pilot plan
  `sha256:e142322153e5beec84c72994ce0da20fb78b2e418174324b96d954b6e8b6631f`;
  reviewed final plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`;
  protocol `ephemeral-sandbox-v1-practical-performance-v1.1`; pinned image
  unchanged.
- **Live result:** the supervised wrapper and benchmark exited 0 with empty
  stderr. Manifest start `2026-07-31T13:13:14.786824Z`, end
  `2026-07-31T13:17:50.880871Z`, exact corpus elapsed 276.094047 seconds,
  within the five-minute pilot budget. The wrapper completed recursive owned
  cleanup at `2026-07-31T13:22:21.9399141Z` and retained benchmark exit 0.
- **Terminal corpus:** state `completed`, correctness `pass`, report ready and
  non-provisional; exactly 19 cells, 133 trial batches, 38 warmups, 95
  successful measured trials, and 385 issued product requests. Raw evidence
  contains 133 trial, 133 operation, 385 request, 336 passed correctness-check,
  and 4,214 resource observations. All measured cells have exactly five
  reportable trials; product, correctness, infrastructure, cleanup, and
  missing-primary-latency failure counts are zero. Report warnings are empty.
- **CLI/transport evidence:** four execution blocks are exclusively
  `windows_named_pipe`, `local_only`, and `per_execution_block`; no TCP
  endpoint or fallback appears. All 1,903 captured native CLI invocations have
  unique request IDs, return code 0, passed response validation and
  authentication redaction, and emitted zero stderr bytes.
- **Resource correlation and unavailable fields:** all 4,214 resource records
  carry a trial ID and cover all 133 trial IDs; all 385 request records have
  unique request IDs. Eighteen cells have five aligned measured CPU/latency
  pairs. The create-sandbox cell has zero CPU pairs because a sandbox-scoped
  pre-create counter baseline is inapplicable, recorded explicitly rather
  than zero-filled. Of 4,214 resource observations, 678 are explicitly
  unavailable: 301 `layerstack_bytes` readings because the product does not
  report LayerStack allocation, 301 `workspace_allocated_bytes` readings
  because host metadata lacks allocated block counts, 14 each for daemon CPU,
  sandbox CPU, block-read, and block-write deltas where the pre-create
  baseline is inapplicable, and 10 each for current/peak sandbox memory before
  the resource ring exists. These are preregistered boundary limitations, not
  missing or uncorrelated samples.
- **Cleanup:** the owned run worktree and runtime were removed. Archive proof
  records no matching product process, run- or gateway-labeled container or
  volume, and an exact clean product checkout. Protected gateway PID 62980
  remained alive and untouched.
- **Immutable pilot archive:** creation and verify-only replay exited 0 and
  agreed at
  `experiments\runs\019fb84e-aef1-7fdc-9a56-1adbe712f30d`: 5,879 files,
  177,813,974 bytes, content-tree
  `sha256:e951342a73d94b2f21aec76d1926bd2b1fc196303fabde5ced01d6c3ab5a4da9`.
  Archive-manifest SHA-256 is
  `eb7f674dabd09491de4d6ad44aa8476d4e9f9e7393033aa416cd2415e2222dd9`;
  campaign-manifest SHA-256 is
  `f102bd2f0f5e6a5802f8460836780900f3d3cdcb523abdb254573dfab40109eb`.
  Disposition is `pilot`, eligibility `exploratory_ineligible`, and freeze
  state `pre_freeze`.
- **Deterministic exploratory tables:** generation into
  `experiments\analysis\pilot-v11-019fb84e-tables-a` and
  `experiments\analysis\pilot-v11-019fb84e-tables-b` succeeded. Each output
  contains nine files and 229,557 bytes; outputs are byte-identical with
  content-tree
  `sha256:f3e2e0c4d6f39622f23251c2661eb270689cd980cd00730c53ae8a600067858e`.
  They are validation artifacts only and cannot enter the manuscript.
- **Projection attempts retained:** the first attempt incorrectly supplied
  preset YAML to a command requiring expanded-plan JSON and failed with a
  JSON parse error before producing output. Fresh final validation then
  produced
  `tmp\validate-paper-good-pass-v11-20260731T1327Z.json` (42,157 bytes,
  `sha256:7c4d2fc4f086e06971146dcdf38028ecd4dff9865745b16b238305594e51138c`).
  The second attempt failed closed because four mandatory evidence/status
  files evolved between smoke and pilot. No projection output was produced by
  either failed attempt.
- **Projection defect and correction:** an independent read-only recursive
  provenance audit proved that every scientific identity matched and only
  `progress.md`, `experiments/experiment_log.md`, `paper_state.json`, and
  `plan/progress.md` changed. The six immutable scientific/protocol files and
  every benchmark, analysis/archive, schema, definition, Docker, fixture,
  gateway/transport, host, image, lifecycle, product/package/binary, limit,
  and treatment identity were byte-identical. The checker now normalizes only
  byte count and SHA-256 for those exact four pre-freeze status paths, retains
  their original identities in output, requires `pre_freeze` and
  `pre_freeze_worktree`, requires the exact ten-file v1.1 protocol set, and
  rejects missing, extra, duplicate, malformed, frozen, or scientific drift.
  This does not claim general append-prefix verification; Git history proves
  the exact observed status evolution.
- **Projection validation:** the initial narrowly corrected output
  `experiments\analysis\pilot-v11-019fb84e-final-runtime.json` is retained but
  superseded by the tightened-checker outputs
  `pilot-v11-019fb84e-final-runtime-prefreeze.json` and
  `pilot-v11-019fb84e-final-runtime-prefreeze-repeat.json`. The final pair are
  byte-identical at 48,311 bytes and
  `sha256:a7b4eda8cd1f15e59bca2e6495cb8b8c36914619e4c812143ac361bdb1803822`;
  analysis-script SHA-256 is
  `d6d73f75f3a2186eef3f92ae8ef8f176f60133e366d89f6ae69a78ad5aa47781`.
  Exact exploratory scheduling values are pilot 276.094047000 seconds,
  central structural projection 1179.784426150 seconds, observed envelope
  1303.732241600 seconds, and limit 1400.000000000 seconds. Every condition is
  true and the decision is `pass_runtime_projection`.
- **Pre-freeze identity correction:** the first draft of this entry copied a
  non-authoritative candidate final-plan hash from orchestration notes. The
  fresh validated expansion, frozen preset inventory, prior protocol records,
  and both tightened projection outputs agree on final plan hash
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
  The incorrect transcription was corrected before freeze preflight or final
  launch; no plan, preset, benchmark, archive, projection value, or treatment
  changed.
- **Tests/checks:** the first real-archive regression run failed one assertion
  because the test expected an invented decision prefix instead of the
  implementation's exact `pass_runtime_projection`; the assertion was
  corrected without changing behavior. Targeted projection tests then passed
  26/26. Full benchmark plus analysis tests passed 377 with five expected
  Windows-symlink-privilege skips in 52.24 seconds. Offline Ruff 0.16.1
  formatting, format check, and scoped `E,F,I` lint passed; `git diff
  --check` passed with only line-ending notices. Earlier attempts to invoke a
  nonexistent venv Ruff executable/module failed without mutation; a broad
  Ruff policy run exposed three pre-existing UP035/RUF007 findings, so no
  unrelated policy rewrite was made.
- **Read-only helper failures retained:** monitoring once queried
  `StartTime.ToUniversalTime()` across processes lacking accessible start
  times and emitted null-value errors; a directory-listing `foreach` pipeline
  had a PowerShell syntax error; neither changed state. During this audit,
  Windows PowerShell rejected unsupported `ConvertFrom-Json -Depth`, and a
  follow-up initially indexed `cells` above the report envelope's `data`
  object; corrected read-only queries produced the counts above. No live
  gateway, sandbox, Docker object, archive, source identity, or protected PID
  was altered by these helper errors.
- **Disposition:** Gate 3 passes for the exact v1.1 treatment. No unresolved
  scientific or instrumentation decision remains. Gate 4 may proceed by
  committing the scoped checker/evidence update and creating the authorized
  annotated local `paper-v1.1-freeze` identity. The sole eligible final run
  remains prohibited until that freeze and strict final preflight pass.

### 2026-07-31T13:40:38.895Z - EXP1 v1.1 measurement freeze and final preflight passed

- **Entry ID:** `freeze-preflight-exp1-v1.1-1680b59-5c48dae1-120`.
- **Phase/kind:** EXP1-E Gate-4 measurement freeze and strict read-only
  final preflight. No final benchmark clock began during this entry.
- **Paper freeze:** measurement source is clean frozen commit
  `1680b599129532f72e706b6acb12ef62c63759e2` on
  `agent/complete-pw3-and-final-host-prep`. Its benchmark source inventory is
  213 files, 16,451,598 bytes, content-tree
  `sha256:c060e397ce3511a7839c71e13506dd4db99c9ad774464d0a0555f6949319dabd`.
- **Product freeze:** clean direct `main` commit
  `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`; annotated local
  `paper-v1.1-freeze` tag object
  `834c84534359f37653fb25ac45304091e82c37a6`, peeled to the same commit.
  Historical `paper-v1-freeze` tag object
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d` remained unchanged. Nothing was
  pushed.
- **Package/treatment:** package ZIP remained 5,739,735 bytes at
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`.
  Gateway, manager, runtime, observability, daemon, Windows configuration,
  named-pipe transport, image, fixture, sandbox limits, and host identities
  all matched the accepted pilot and preregistration.
- **Freeze record:** created
  `experiments\analysis\exp1-v11-freeze-record-1680b59-5c48dae1.json`, 6,888
  bytes,
  `sha256:5b8ca3962f479f1776be0298acbbe7620b683a334c1964889b031122a0ffdc32`.
  It verifies the exact ten protocol files, product/package/binaries/tag,
  paper source, image, fixture, final plan, archive/projection scripts, and
  frozen table generator
  `sha256:7fd9c21d99ceb4b9fc3b962977ee9c0d270411ec2c6b76cc88960387a2fcbeb7`.
- **Strict final plan:** fresh expanded output
  `tmp\validate-paper-good-pass-v11-frozen-20260731T1342Z.json` is 42,157
  bytes,
  `sha256:b5dd979532151f0964b031072a54c6e73f00e74f94a3948b2fc2eda0633a1880`.
  Validation exited 0 with empty stderr, zero findings/warnings, exactly 19
  cells, 1,938 batches, 5,610 requests, two warmups plus 100 measured trials,
  only `product_cli` and `paper-100m`, and plan
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`.
- **Host/baseline:** host identity, Docker Desktop 29.0.1 Linux AMD64 engine,
  `overlayfs`, cgroup v2, pinned local image, 543,051,427,840 free bytes, one
  pre-existing exited container, five pre-existing volumes, and protected
  gateway PID 62980 matched the frozen baseline. No earlier v1.1 final
  existed.
- **Read-only helper failures retained:** two `rg` free-space searches
  returned exit 1 despite producing the needed read-only context; one
  PowerShell `rg` command had an unterminated quote; and one Docker Go-template
  `join` expression failed to parse before corrected JSON inspection. None
  started or changed a process, Docker object, source file, archive, package,
  host setting, or protected resource.
- **Disposition:** Gate 4 passes. Exactly one `paper-good-pass` v1.1 final is
  authorized under the frozen identities and no other final attempt is
  permitted.

### 2026-07-31T14:12:41.290Z - Sole EXP1 v1.1 final and immutable archive passed

- **Entry ID:** `final-exp1-v1.1-019fb86c-gate5-pass-121`.
- **Phase/kind:** EXP1-F sole frozen final, fail-closed terminal cleanup,
  immutable archive creation, and independent verify-only replay. The final
  was launched once and was not rerun.
- **Run/timing:** run `019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`; manifest start
  `2026-07-31T13:45:18.307991Z`; end
  `2026-07-31T14:05:29.554460Z`; exact corpus elapsed 1,211.246469 seconds,
  below the fixed 1,400-second envelope. The supervisor completed at
  `2026-07-31T14:12:41.2897460Z` after owned deep-workspace cleanup. Benchmark
  and supervisor exited 0; both stderr captures are empty.
- **Terminal corpus:** state `completed`, correctness `pass`, report ready and
  non-provisional, warnings empty. Exactly 19 cells, 1,938 attempted batches,
  38 warmups, 1,900 measured attempts, 1,900 successful/reportable measured
  trials, and 5,610 issued requests. Product, correctness, infrastructure,
  cleanup, and missing-primary-latency failure counts are all zero. All
  4,800 correctness checks passed.
- **CLI/transport:** four execution blocks are exclusively
  `windows_named_pipe`, `local_only`, and `per_execution_block`. All 26,692
  native CLI invocation records have unique request IDs, return code 0,
  passed response validation and authentication redaction, and zero stderr
  bytes. No TCP fallback, retry, or pacing appears.
- **Observations:** 76,276 retained observations: 1,938 trial, 1,938
  operation, 5,610 request, 4,896 check, and 61,894 resource observations.
  Raw events are 45,659,053 bytes and raw observations are 67,045,771 bytes.
- **Unavailable fields:** the final report preserves LayerStack allocated
  storage and host workspace allocated-block counts as unavailable for all
  1,900 reportable trials. Create-sandbox counter deltas are unavailable for
  100 trials because a sandbox-scoped pre-create baseline cannot exist;
  sandbox current/peak memory is unavailable for 50 trials before its ring
  exists. No unavailable value is encoded as zero. The complete raw
  observation availability counts remain in `failures.md` and
  `resources/resource-summary.json`.
- **Cleanup:** the owned workspace and benchmark runtime were removed. No
  matching product process, run- or gateway-labeled container or volume
  remains. Product is clean direct `main` at the frozen commit. Protected
  gateway PID 62980 remained alive and untouched; the pre-existing container
  and volume baseline remained unchanged.
- **Archive:** creation completed successfully after 872 seconds at
  `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`.
  The archive contains 82,051 files and 3,139,214,747 bytes, content-tree
  `sha256:606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`.
  Its raw subtree contains 82,025 files and 2,964,792,876 bytes, tree
  `sha256:561dd3bd8ac1a7106fcf970acdcd6972a76da24fa07da147e4f19d49c83f3981`.
  Archive-manifest SHA-256 is
  `239dbedb781f2e427fb61b316629ea57393d1a92a3be56a45bd107e998d9131c`;
  campaign-manifest SHA-256 is
  `93dd241e38c48b2a3f337d66065492f101d8945f7189c2f6402a32fa0fd7e7cf`.
- **Independent verification:** immediate verify-only replay exited 0 in 36
  seconds with the identical file count, byte count, run ID, and content tree.
  A later post-analysis replay again returned the same identity. The archive
  remained immutable.
- **Monitoring/read-only attempts:** one progress helper queried the
  observations file before it existed and emitted a `Get-Item` error; it did
  not change state. The first post-final report aggregate exceeded a 10-second
  helper timeout; an identical read-only aggregation with a 60-second limit
  succeeded. Neither condition affected the benchmark, corpus, archive, or
  final-attempt count.
- **Disposition:** Gate 5 passes with one complete provenance-rich corpus.
  The final cannot be relaunched; Gate 6 may analyze only the immutable
  archive.

### 2026-07-31T14:44:57.843Z - Post-freeze analysis erratum, deterministic tables, and Gates 6--7 passed

- **Entry ID:** `analysis-handoff-exp1-v1.1-019fb86c-pass-122`.
- **Initial fail-closed result:** the frozen generator's first final invocation
  exited 1 before creating its requested output directory:
  `ERROR: final archive lacks required environment fields: host OS edition,
  host OS build`. The archive already contained canonical verified
  `os_caption` and `os_build_number` in both campaign and preflight evidence;
  the reader accepted only synthetic legacy aliases `os_edition` and
  `os_build` for final eligibility. The pilot did not expose this because
  exploratory output tolerates missing qualification fields.
- **Protocol decision:** an independent read-only blocker audit concluded
  that the only defensible path was a narrow post-final analysis-only schema
  compatibility correction. Rerunning would violate the exactly-one-final
  rule, and editing the archive would violate immutability. The correction
  does not change a metric, selector, aggregate, exclusion, eligibility rule,
  raw value, or Tables 2--4. It is explicitly an erratum and is not described
  as the frozen generator passing unchanged.
- **Correction identity:** local paper commit
  `538f6c98233863957082620329203348ddaa781c` accepts canonical caption/build,
  retains legacy aliases, avoids duplicated OS-family presentation, and
  fails closed if caption/edition or build evidence is absent. Corrected
  generator SHA-256 is
  `ff93953a6b8b94f10bc35138356a3039f6709a28ff0860d05c0da25e2064727b`;
  frozen identity remains
  `7fd9c21d99ceb4b9fc3b962977ee9c0d270411ec2c6b76cc88960387a2fcbeb7`.
- **Tests:** targeted analysis tests passed 22/22. The final complete
  `experiments\analysis\tests` plus `benchmark\backend\tests` run passed 380
  with five expected Windows-symlink-privilege skips in 59.86 seconds.
  Python compilation and scoped `git diff --check` passed.
- **Numeric-neutrality proof:** corrected-generator replay on immutable pilot
  `019fb84e-aef1-7fdc-9a56-1adbe712f30d` produced byte-identical
  `numeric-evidence.json`, `numeric-provenance.csv`, Table 2, Table 3, and
  Table 4 relative to the frozen-generator pilot output. Parsed Tables 2--4
  structures are identical; only intended non-numeric Table 1 host display
  changed.
- **Final generation:** fresh outputs
  `experiments\analysis\final-v11-019fb86c-tables-a` and `...-tables-b`
  each contain nine files and 231,047 bytes. All paths, byte counts, and
  SHA-256 values are identical; output content-tree is
  `sha256:27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`.
  Output-manifest SHA-256 is
  `a77b30469c3d46c26ed045f748f09313a646ef13b571f40c45a7a31f7a72505e`;
  tables JSON is
  `c8aaa13c58d0dad900f3d08d6a926d7736c281bacdb665e3976da269cbdab3dd`.
- **Numeric provenance:** schema
  `ai-research-writing/numeric-evidence-v2` contains 153 entries and the CSV
  contains 153 rows, with 153 unique IDs, no duplicate, missing ID, or numeric
  mismatch. All four archive source hashes, all report selectors'
  `reportable_measured` scope, and all output-manifest hashes independently
  verified.
- **Archive immutability after analysis:** verify-only replay exited 0 and
  reproduced 82,051 files, 3,139,214,747 bytes, and original tree
  `sha256:606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`.
- **Post-final helper failures retained:** the venv has no Ruff module, so a
  requested format/lint invocation failed without changing files; Python
  compile, tests, and diff checks supplied the applicable validation. A
  PowerShell output-tree helper used unavailable `Convert.FromHexString` and
  `Convert.ToHexString`; a compatible byte converter then produced the output
  tree above. Two preliminary PowerShell numeric audits falsely reported 153
  and then five mismatches because of single-object `.Count` behavior and
  PowerShell JSON floating-point coercion; an exact Python CSV/JSON audit
  verified 153/153 values. Other read-only inspections included an `rg`
  no-match exit, a nonexistent `backend` directory query, a path-separator
  pattern miss, and an initially unquoted PowerShell tag-peel expression;
  corrected checks succeeded. None mutated the archive, source treatment,
  Docker, host settings, or protected PID, and no final was rerun.
- **Host-caption disclosure:** the canonical archived caption is literally
  `Microsoft Windows 11 ???`; the localized edition suffix was not preserved
  legibly by the frozen capture. Build 26200, version, architecture, computer
  name, and the remaining host identity are present. A post-run read-only
  registry query reported `EditionID=Core`, `CompositionEditionID=Core`, and
  build 26200. That external context was not inserted into the immutable
  archive or substituted into Table 1, which preserves the exact archived
  caption.
- **Handoff:** `claim_evidence_map.md`, `experiment_inventory.md`,
  `progress.md`, `plan/progress.md`, `paper_state.json`,
  `benchmark/PAPER_ARTIFACT.md`, `exp1-final-handoff.md`, and the required
  Gate report now bind the final run, outputs, supported wording, unsafe
  wording, exclusions, unavailable fields, cleanup, and erratum. No numeric
  result was manually inserted into LaTeX.
- **Generated-byte preservation:** repository `core.autocrlf=true`, so the
  freeze record and deterministic final table trees are explicitly marked
  `-text` in the root `.gitattributes`. They are versioned at their reported
  paths with their generated bytes unchanged, preserving the recorded
  SHA-256 identities. Large run archives, temporary diagnostics, exploratory
  projections, and Python caches remain local and are excluded by the root
  `.gitignore`.
- **Disposition:** Gates 6 and 7 pass. EXP1 v1.1 and the complete focused
  CLI-only performance campaign are finished. There is no remaining EXP1
  execution or analysis blocker. The next external action is author review of
  generated tables and bounded wording before LaTeX import; broader paper
  work remains outside this campaign.
