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
