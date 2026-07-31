# EXP1 CLI-only focused performance campaign

**Status:** v1.0 preserved failed/ineligible; authorized v1.1 campaign resumed

**Date prepared:** 2026-07-30

**Scope:** Complete Gates 0 and 3--7 of the focused RQ3 practical-performance
protocol

**Authoritative protocol:** [`../../experiment_inventory.md`](../../experiment_inventory.md)

**Run log:** [`../../experiments/experiment_log.md`](../../experiments/experiment_log.md)

**Active amendment:**
[`../../experiments/exp1-v1.1-protocol-amendment.md`](../../experiments/exp1-v1.1-protocol-amendment.md)

The packet below remains authoritative except for the explicit v1.1 amendment.
The amendment changes the Windows CLI-to-gateway treatment from loopback TCP
to isolated named-pipe IPC, replaces the active product/package/freeze
identities, adds a preregistered 25,000-invocation qualification gate, and
names the new tag `paper-v1.1-freeze`. It does not change the matrix, trials,
seed, timing boundary, metrics, resource cadence, correctness gates,
exclusions, 1,400-second projection limit, or exactly-one-final rule. All v1.0
freeze and failed-final text below is retained as historical evidence.

## Objective

Complete the paper's bounded RQ3 practical-performance campaign on the already
qualified native Windows/Docker Desktop environment:

1. implement and review the benchmark's released-product-CLI subprocess cohort;
2. validate the planner, runner, correctness, cleanup, provenance, and analysis
   paths without collecting paper results;
3. run a five-sample exploratory pilot over every final cell;
4. resolve pilot-discovered protocol or instrumentation defects before freeze;
5. freeze the approved protocol and exact product, benchmark, image, binary,
   fixture, and analysis identities;
6. run one complete `paper-good-pass`;
7. deterministically generate the four expected tables and a claim-mapped
   evidence handoff.

This packet must be executed as an evidence campaign, not as a request to obtain
favorable numbers. A negative, partial, slow, or failed result is retained and
reported.

## Required read-first sequence

Read every file below completely before editing or running anything:

1. `C:\Users\yifan\.codex\skills\ai-research-writing\SKILL.md`
2. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\progress.md`
3. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiment_inventory.md`
4. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\environment_setup.md`
5. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\expected_tables.md`
6. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\experiment_log.md`
7. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\benchmark\PAPER_ARTIFACT.md`
8. `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\benchmark\docs\phase-3-product-boundary.md`
9. `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\AGENTS.md`
10. `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\CLAUDE.md`
11. `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\README.md`
12. `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\docs\linux-setup.md`

Also inspect the complete current Git status of both repositories. The paper
working tree is intentionally dirty and contains unrelated user work. Preserve
every pre-existing change.

## Starting state that must remain true

### Qualified environment

| Item | Required value |
|---|---|
| Host | Native Windows x64, `DESKTOP-OLP1ADS`, build 26200 |
| Host capacity | 48 logical CPUs; 137,438,953,472 bytes physical memory |
| Host filesystem | NTFS |
| Docker | Docker Desktop client/server 29.0.1 |
| Docker engine | Linux AMD64, `overlayfs`, cgroup v2 |
| Sandbox image | `ubuntu:24.04@sha256:52df9b1ee71626e0088f7d400d5c6b5f7bb916f8f0c82b474289a4ece6cf3faf` |
| Product | clean `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`, annotated `v0.1.4` |
| Product checkout | `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox` |
| Paper checkout | `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1` |
| Released package | `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4` |
| Performance workspace | deterministic `paper-100m`; never the product or paper checkout |

The accepted environment evidence is:

- directory:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6`;
- summary: `windows-docker-cli-env-summary.json`;
- archive:
  `C:\Users\yifan\code\Ephemeral-AI-Lab\final-host-staging\diagnostics\qualification-windows-docker-20260730-final-6.zip`;
- archive SHA-256:
  `eea981665b031846677046d4c211e71ad144f8a32507c09058923241d4d0f7f9`.

Do not reinterpret Ubuntu as the host. Do not add an SSH, ext4-host,
native-Ubuntu-host, WSL-host, or host-CPython qualification requirement.
Python 3.13 or newer is a benchmark-orchestration dependency, not part of the
already passed product environment gate.

### Exact released executables

Use only these native Windows executables from the staged official package:

```text
C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4\bin\sandbox-gateway.exe
C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4\bin\sandbox-manager-cli.exe
C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4\bin\sandbox-runtime-cli.exe
C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-v0.1.4\bin\sandbox-observability-cli.exe
```

Expected SHA-256 values:

```text
sandbox-gateway.exe            3a96bedcfa9857bd3881155d758ec2d969f6265456ec3b2878eb6dbb26dc9368
sandbox-manager-cli.exe        b43ec520edc2f436adc8aa7e8b2b50680bb9021883fe23d79a85b17afd2e10fe
sandbox-runtime-cli.exe        df99f2993a7a9e305d33b656fa239b9e11b61a9e2da6e8dfc2f29ae8953067d4
sandbox-observability-cli.exe  0e0471e52750805570876a6244868764c44e166ec653627b9ebd490176e2fcbe
```

Never resolve these executables from an ambient `PATH`, another build
directory, WSL, or the separately staged Linux raw binaries.

## Scientific scope

This packet completes only the focused RQ3 characterization of startup,
workspace/session readiness, command, file read, file write, file edit, and
their resource envelope in the disclosed environment.

It does not complete the broader RQ1--RQ5 lane. The following are out of scope:

- competitive superiority or matched-baseline rankings;
- shared-directory, Git-worktree, team, or swarm comparisons;
- general isolation/security claims;
- publication/fault/restart correctness campaigns;
- a universal concurrency ceiling;
- Windows reflink or LayerStack 2.0 performance;
- changes to the manuscript Results section before final evidence handoff.

Do not place pilot values, qualification elapsed time, simulated preview
values, or partial final-run values in paper tables.

## Fixed protocol decisions

These decisions are made before viewing performance measurements:

1. `product_cli` is the canonical client-cohort identifier. Do not use
   `direct_client` or `cli_e2e` for a paper run.
2. Every sandbox lifecycle operation uses `sandbox-manager-cli.exe`.
3. Every workspace/session, command, and file operation uses
   `sandbox-runtime-cli.exe`.
4. Every product-level sandbox observation and resource snapshot uses
   `sandbox-observability-cli.exe`.
5. Docker commands may verify the engine and perform an independent leak
   cross-check; they may not substitute for product CLI operations.
6. Primary latency is end-to-end native CLI subprocess latency. It starts
   immediately before process creation and ends after exit, stdout/stderr
   capture, JSON parsing, and response validation.
7. Primary latency includes process launch and CLI-to-gateway transport.
   Product-reported internal durations are separate secondary observations.
8. Concurrent requests are released from one benchmark barrier. Batch
   makespan ends after the last CLI response validates.
9. Setup, verification, resource sampling, and teardown are excluded from the
   primary operation interval but must still use the product CLIs for sandbox
   operations.
10. Every measured cell uses a fresh benchmark-owned copy of the deterministic
    `paper-100m` base: 4,000 files, 104,857,600 logical bytes, maximum depth
    100, seed `20260712`.
11. File-operation targets are prepared inside that base during untimed setup.
12. Sandbox create + base mount is a distinct manager-CLI operation. Session
    create is a distinct runtime-CLI `create_workspace_session` operation.
13. The final matrix has 19 cells: one sandbox-create cell, two
    workspace/session-create cells, four command cells, and four each for read,
    write, and edit.
14. The pilot uses the final two warmups plus five measured trials per cell.
15. The final pass uses two warmups plus 100 measured trials per cell.
16. Concurrency is 1 and 5 where specified. Payloads are 4 KiB and 256 KiB.
17. Scheduling is seeded randomized blocks. Resource sampling is 100 ms.
18. There are no automatic retries and no silent outlier removal.

Any change to these decisions before protocol lock must be appended to the
experiment log with a reason. Any change after lock requires a protocol version
bump and rerunning every affected final cell.

## Worktree and mutation rules

- Preserve the dirty paper working tree and all unrelated files.
- Do not delete or clean existing `__pycache__`, test caches, generated
  artifacts, or user changes merely to make status look clean.
- Set `PYTHONDONTWRITEBYTECODE=1` for Python validation to avoid adding more
  bytecode noise.
- Keep the product repository on `main`, clean, and at the required commit.
- Do not create a product branch or product worktree.
- Do not modify product source unless a demonstrated CLI-contract defect makes
  the campaign impossible. If that occurs, stop, log the evidence, and request
  authorization before changing product behavior.
- Paper-local benchmark implementation, tests, presets, analysis, protocols,
  and run artifacts are in scope.
- Do not commit, tag, or push unless the active user request explicitly
  authorizes that Git mutation. A missing authorization is a Gate 4 blocker,
  not permission to weaken the freeze requirement.
- Use `apply_patch` for manual file edits.
- Append every validation, smoke, pilot, final-run, failure, amendment,
  analysis, and cleanup attempt to `experiments/experiment_log.md`.

## Implementation contract

### 1. Cohort model and planning

Update the paper-local benchmark so that:

- `product_cli` is accepted in backend plan types, validation, canonicalization,
  manifests, environment metadata, reports, and web types if the web build is
  part of validation;
- operation definitions advertise `product_cli` only when the operation has a
  complete reviewed CLI implementation;
- `paper-env-smoke`, a new `paper-pilot`, and `paper-good-pass` select
  `product_cli`;
- paper presets fail closed if expanded to `direct_client`;
- the expanded final plan contains exactly 19 cells, 1,938 trial batches, and
  5,610 product operation requests before failure or cancellation;
- the pilot contains the same 19 cells with two warmups and five measured
  trials per cell.

Do not rename the paper cohort to the web prototype's existing `cli_e2e`
spelling. Normalize the code and fixtures to `product_cli`.

### 2. CLI product-access adapter

Refactor the current direct `GatewayClient`-bound access layer behind an
explicit cohort interface and add a CLI implementation. The runner must choose
the implementation from the expanded plan; it must not construct direct
product access unconditionally.

The CLI adapter must:

- use absolute executable paths beneath the checksum-verified package;
- use argument arrays rather than a shell command string;
- launch subprocesses asynchronously so the concurrency barrier is real;
- pass the exact gateway socket and authentication token without logging the
  token;
- preserve the benchmark request ID when the CLI contract supports it and
  record the resulting response identity;
- capture stdout and stderr separately;
- require exit code zero, empty stderr where the released contract requires
  it, exactly one valid JSON response, and the expected operation schema;
- convert the response into the benchmark's timed response/evidence model
  without fabricating fields;
- retain raw redacted command metadata, start/end monotonic timestamps, elapsed
  nanoseconds, return code, stdout artifact path, stderr artifact path, and
  response validation status;
- cancel and reap subprocesses safely on timeout or campaign cancellation;
- never silently fall back to the direct gateway client.

### 3. CLI operation ownership

At minimum, implement these mappings:

| Benchmark action | Required executable |
|---|---|
| list/inspect/create/destroy sandbox | manager CLI |
| create/publish/destroy workspace session | runtime CLI |
| execute command | runtime CLI |
| file read/write/edit and verification reads | runtime CLI |
| product snapshot/resources/topology used by the campaign | observability CLI |

Use the source-derived CLI contract and the released executable `--help`
outputs as authority. Archive the relevant `--help` output and exact CLI
versions in the implementation-validation evidence.

### 4. Timing and concurrency

Use a monotonic high-resolution clock. For each request, start timing
immediately before asynchronous process creation and stop only after the
process has exited and its captured output has passed response validation.

For concurrent batches:

1. prepare every immutable argument vector;
2. register every request as waiting;
3. release all subprocess launches from one barrier;
4. retain per-request elapsed time;
5. calculate batch makespan from barrier release through the final validated
   response;
6. compute throughput as completed requests divided by batch makespan.

Do not subtract a separately estimated process-launch cost. Do not mix the
`wall_time_seconds` or `command_total_time_seconds` fields returned by some
commands into the primary latency distribution.

### 5. Workspace and startup operation

Extend file read, write, and edit cells so their per-cell workspace is copied
from the cached `paper-100m` seed. Record and verify the fixture manifest and
hash before each campaign.

Add an explicit `create_sandbox` benchmark operation with:

- one concurrency-1 cell;
- `paper-100m`;
- the shared network profile;
- manager-CLI process-launch-to-ready timing;
- sandbox identity/readiness validation;
- product-CLI destruction during teardown;
- independent Docker owner-label leak cross-check after cleanup.

Do not derive this row from generic cell setup time. Do not count session
creation as sandbox creation.

### 6. Correctness and cleanup

Every trial is reportable only if:

- the measured CLI exits successfully and validates;
- operation-specific correctness checks pass;
- verification reads use the runtime CLI;
- observability evidence correlates to the same sandbox/trial;
- session and sandbox teardown use the product CLIs;
- the benchmark-owned workspace is restored or removed according to policy;
- no gateway-owned container, volume, process, or runtime state leaks;
- the product checkout remains clean at the required commit;
- infrastructure did not fail.

Preserve failed and partial trials. Never convert a failed sample to a retry.

### 7. Resource and analysis output

Confirm or implement deterministic emission of:

- per-request end-to-end latency;
- concurrent batch makespan and throughput;
- p50, p95, and p99 over reportable measured trials;
- daemon CPU-time delta and peak RSS;
- sandbox CPU, peak memory, and block-I/O deltas;
- workspace logical and allocated-byte deltas;
- host free-space minimum;
- unavailable fields represented explicitly as `unavailable`, never zero.

The analysis must regenerate all four tables in
`experiments/expected_tables.md` from immutable raw artifacts. No table number
may be manually typed or edited.

## Required tests before any live pilot

Add or update unit, contract, and integration tests for:

- plan parsing and canonical `product_cli` serialization;
- rejection of `direct_client` by every paper preset;
- exact executable selection by operation;
- argument-vector construction and token redaction;
- valid JSON, malformed JSON, nonzero exit, unexpected stderr, timeout, and
  cancellation;
- request IDs and response schema validation;
- end-to-end timing boundaries and concurrent barrier behavior;
- `paper-100m` use by all operation families;
- sandbox-create separation from session-create;
- correctness verification through CLI calls;
- cleanup and leak detection;
- raw observation, manifest, report, and table regeneration;
- 19-cell/1,938-batch/5,610-request final-plan counts.

Run the narrow tests first, followed by the complete benchmark backend suite.
Use the prepared Python environment and disable bytecode writes:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
Set-Location -LiteralPath 'C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1'
& .\.venv\Scripts\python.exe -m pytest .\benchmark\backend\tests
```

If the virtual environment does not exist, create/install it off-clock and log
the tool versions and commands. Installation is forbidden once a pilot or
final campaign clock begins.

## Execution phases

### EXP1-A: audit and protocol review

1. Read the required inputs and applicable repository instructions.
2. Record both Git states and hashes of every file that will be edited.
3. Audit all current direct-client construction, operation definitions,
   manifests, resource sampling, and analysis paths.
4. Verify the fixed decisions in this packet are reflected consistently in the
   protocol and table schemas.
5. Add an experiment-log entry. Do not run a live performance preset.

Acceptance: Gate 0 cross-links/configuration pass, and no unresolved
measurement-boundary ambiguity remains.

### EXP1-B: implement and validate `product_cli`

1. Implement the cohort, operation mappings, timing, workspace policy,
   sandbox-create cell, raw evidence, and tests.
2. Update `PAPER_ARTIFACT.md` with the complete paper-local modification list.
3. Run targeted and full benchmark tests.
4. Expand and inspect `paper-env-smoke`, `paper-pilot`, and
   `paper-good-pass`.
5. Confirm paper presets cannot select or fall back to `direct_client`.
6. Append all attempts and failures to the log.

Acceptance: deterministic tests pass; final expansion is exactly 19 cells,
1,938 batches, and 5,610 requests; no live performance result has been
collected.

### EXP1-C: live CLI integration smoke

1. Recheck the qualified environment and exact hashes.
2. Start a unique released gateway instance.
3. Run only `paper-env-smoke` through `product_cli`.
4. Require all operations and correctness checks to pass.
5. Require no warnings, failures, leaked containers, volumes, processes, or
   runtime state.
6. Archive the complete smoke evidence and append the log.

Acceptance: the benchmark's own CLI cohort, not the standalone qualifier,
passes its minimal live gate.

### EXP1-D: exploratory pilot

1. Re-run fast preflight without builds, installs, pulls, or source mutation.
2. Run `paper-pilot` once over all 19 cells with two warmups and five measured
   trials per cell.
3. Mark every artifact and report `exploratory`; pilot numbers are ineligible
   for manuscript tables.
4. Verify correctness, cleanup, timing separation, resource correlation, and
   deterministic table regeneration.
5. Project the full good-pass duration and require no more than 1,400 seconds
   (23 minutes 20 seconds).
6. Review anomalies and resolve instrumentation/protocol defects before freeze.
7. Append every attempt and amendment to the log.

Acceptance: Gate 3 passes. A slow, failed, leaking, or ambiguous pilot blocks
freeze and final measurement.

### EXP1-E: protocol and source freeze

1. Resolve every Gate 0--3 item.
2. Record the clean product `main` commit, annotated release tag, tag object,
   and binary hashes.
3. Obtain explicit user authorization before creating any new Git commit,
   annotated `paper-v1-freeze` tag, or push.
4. Freeze the paper-local benchmark revision and complete plan hash.
5. Freeze the image digest, fixture manifest/hash, table schema, metrics,
   exclusions, seed, trials, analysis code, and protocol version `v1.0`.
6. Append the freeze record to the experiment log.

Acceptance: Gate 4 passes and no scientific decision remains conditional.
Without the required Git authorization, stop at this gate and report that
single exact blocker.

### EXP1-F: final good pass

1. Create a new immutable run directory under `experiments\runs`.
2. Re-run the strict fast preflight.
3. Confirm no build, image pull, installation, source mutation, environment
   reconfiguration, or unrelated process load is introduced.
4. Run the frozen `paper-good-pass` exactly once.
5. Preserve the run manifest, expanded plan, raw observations, resource
   samples, traces, stdout/stderr, failures, and cleanup proof.
6. Require all 19 cells to contain exactly 100 reportable measured trials.
7. Preserve and report the corpus even if partial or failed. Do not rerun
   without a logged cause and protocol decision.

Acceptance: Gate 5 passes with one complete provenance-rich corpus.

### EXP1-G: deterministic analysis and paper handoff

1. Validate the immutable raw corpus.
2. Generate all four expected tables exclusively from archived data.
3. Regenerate the tables a second time and require byte-identical output.
4. Record the analysis command, code identity, input selectors, output hashes,
   exclusions, anomalies, and unavailable fields.
5. Create or update numeric-evidence v2 records before any number enters
   LaTeX.
6. Map every result to its RQ3 claim and record supported and unsafe wording.
7. Update `claim_evidence_map.md`, `experiment_inventory.md`, `progress.md`,
   `plan/progress.md`, `paper_state.json`, and the experiment log.
8. Do not draft broader performance, superiority, security, or multi-agent
   claims.

Acceptance: Gates 6 and 7 pass; every displayed number has a raw selector and
recomputable aggregate.

## Run and artifact contract

Each smoke, pilot, or final attempt uses a unique run ID and immutable directory:

```text
experiments/
|-- runs/
|   `-- RUN_ID/
|       |-- environment-preflight.txt
|       |-- run-manifest.json
|       |-- intent-plan.yml
|       |-- expanded-plan.json
|       |-- fixture-manifest.json
|       |-- cli-help/
|       |-- raw/
|       |-- resources/
|       |-- logs/
|       |-- cleanup/
|       `-- failures.md
`-- analysis/
    |-- scripts/
    |-- tables/
    |-- numeric-evidence.json
    `-- generation-log.txt
```

Generated `.benchmark-state` data may be used while the campaign is active,
but the complete retained evidence must be copied or linked into the immutable
run directory before the run is accepted.

Every run manifest must include:

- run ID and exploratory/final disposition;
- host, Docker, image, product, release, package, CLI, daemon, benchmark,
  protocol, plan, fixture, and analysis identities/hashes;
- exact sanitized command vectors and environment;
- seed, warmups, trials, scheduling, timeout, and resource interval;
- start/end/elapsed timestamps;
- cell and request counts;
- failures, exclusions, cleanup result, and artifact paths.

Authentication tokens and other secrets must be redacted from manifests,
events, console output, and logs.

## Stop conditions

Stop immediately, retain evidence, clean up safely, append the log, and report
the blocker if any of these occurs:

- host, Docker, image, product, package, CLI, daemon, fixture, plan, or analysis
  drift;
- a paper plan expands to `direct_client` or `cli_e2e`;
- any sandbox operation bypasses the product CLIs;
- malformed JSON, nonzero exit, unexpected stderr, request mismatch, or
  correctness failure;
- setup/verification/teardown contaminates primary timing;
- missing or uncorrelated resource samples;
- disk pressure below the protocol threshold;
- repeated cleanup leakage or daemon instability;
- product working tree or branch drift;
- a measured cell has fewer than the required reportable trials;
- a requested commit, tag, or push lacks explicit user authorization.

Do not weaken a gate, remove a slow cell, reduce final trials, retry silently,
or change exclusions after seeing results.

## Required final report

The executing agent must finish with:

1. a Gate 0--7 PASS/FAIL table;
2. exact code and documentation files changed;
3. tests and commands run with exit status;
4. run IDs and absolute artifact paths;
5. hashes for the final run archive and generated tables;
6. failures, partial evidence, exclusions, unavailable metrics, and cleanup
   outcome;
7. claim wording supported by the evidence;
8. wording still unsafe;
9. exact remaining blockers and the single next external action, if any.

Never fabricate or estimate benchmark metrics in the final report.
