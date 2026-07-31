# EXP1 CLI-only performance campaign: v1.1 final Gate 0--7 report

Report date: 2026-07-31.

Protocol: `ephemeral-sandbox-v1-practical-performance-v1.1`.

Outcome: **EXP1 is complete. Gates 0--7 pass.** The sole eligible v1.1 final
completed, its immutable archive was independently verified, and all four
tables plus numeric-evidence v2 provenance regenerate byte-identically. This
closes the focused RQ3 experiment; it does not by itself make the full paper
submission-ready.

The earlier v1.0 final remains permanently failed and ineligible. Its corpus
was neither replaced, pooled, nor numerically compared with v1.1.

## Gate decisions

| Gate | Phase | Decision | Evidence |
|---|---|---:|---|
| Gate 0 | Audit and protocol review | PASS | The fixed environment, CLI-only ownership, timing boundaries, workload, correctness, resource policy, table schemas, exclusions, and stop conditions were cross-checked before live work. |
| Gate 1 | Native-Windows `product_cli` and permanent local IPC | PASS | Product `main` at `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8` implements no-fallback local named-pipe transport for the paper treatment. The preregistered qualifier completed 25,000/25,000 native CLI calls with no owned TCP endpoint, new TCP/IP 4227/4231 event, transport failure, or resource-bound violation. |
| Gate 2 | Fresh v1.1 CLI integration smoke | PASS | Run `019fb83a-54bc-79db-b6ac-6189fb28f5f2` completed all 19 cells and 55 requests through four local named-pipe execution blocks, with correctness, stderr, warning, cleanup, archive, and protected-process gates passing. |
| Gate 3 | Five-sample pilot and runtime projection | PASS | Run `019fb84e-aef1-7fdc-9a56-1adbe712f30d` completed 19 cells, 133 batches, 95 measured trials, and 385 requests with zero failures. Repeated projection outputs were byte-identical; the 1,303.732241600-second envelope was below the fixed 1,400-second limit. Pilot values remain exploratory/ineligible. |
| Gate 4 | Measurement protocol/source/treatment freeze | PASS | Paper measurement commit `1680b599129532f72e706b6acb12ef62c63759e2`, product commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`, annotated tag object `834c84534359f37653fb25ac45304091e82c37a6`, plan, package, image, fixture, metrics, exclusions, seed, trials, and analysis identities were frozen before the final. The later Table-1 reader compatibility erratum is separately identified and does not claim that the frozen generator passed unchanged. |
| Gate 5 | Sole eligible v1.1 final | PASS | Run `019fb86c-096e-7589-a0a4-a6d6ef5d7f8b` completed exactly once: 19 cells, 1,938 batches, 38 warmups, 1,900 successful/reportable measured trials, 5,610 product requests, 4,800 correctness checks, zero failures, zero warnings, and clean teardown. |
| Gate 6 | Deterministic final aggregation | PASS | The immutable 3,139,214,747-byte archive reverified at its original tree hash. Two corrected-generator builds produced nine files/231,047 bytes each and matched byte-for-byte at output tree `sha256:27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`. Numeric-evidence v2 contains 153 unique selector-bound values. |
| Gate 7 | Numeric evidence and RQ3 handoff | PASS | All four archive-derived tables, 153-row numeric provenance, supported wording, unsafe wording, unavailable metrics, exclusions, and claim boundaries are recorded. No result number was manually entered into LaTeX. |

## Frozen measurement identities

- Paper measurement commit:
  `1680b599129532f72e706b6acb12ef62c63759e2`.
- Benchmark-source inventory: 213 files, 16,451,598 bytes,
  `sha256:c060e397ce3511a7839c71e13506dd4db99c9ad774464d0a0555f6949319dabd`.
- Product commit: `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`,
  clean direct local `main`.
- Annotated product tag: `paper-v1.1-freeze`; tag object
  `834c84534359f37653fb25ac45304091e82c37a6`; peeled commit
  `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`.
- Preserved v1.0 tag object: `paper-v1-freeze`,
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`.
- Windows package: 5,739,735 bytes,
  `sha256:11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506`.
- Final plan:
  `sha256:391b521b406f0f221a7a342b822cfa8d459e339fee6c53b4a60a913a2cb0089b`;
  19 cells, two warmups and 100 measured trials per cell, 1,938 batches,
  5,610 product requests, `product_cli`, `paper-100m`, seed 20260712.
- Freeze record:
  `experiments/analysis/exp1-v11-freeze-record-1680b59-5c48dae1.json`;
  6,888 bytes;
  `sha256:5b8ca3962f479f1776be0298acbbe7620b683a334c1964889b031122a0ffdc32`.
- Frozen table generator:
  `sha256:7fd9c21d99ceb4b9fc3b962977ee9c0d270411ec2c6b76cc88960387a2fcbeb7`.
- No commit or tag was pushed.

## Sole final result and archive

Run `019fb86c-096e-7589-a0a4-a6d6ef5d7f8b` started at
`2026-07-31T13:45:18.307991Z` and ended at
`2026-07-31T14:05:29.554460Z`; exact corpus elapsed time was 1,211.246469
seconds. The benchmark and supervisor exited 0, and both stderr captures are
empty.

The terminal report is non-provisional, correctness `pass`, and warning-free:

- 19/19 cells;
- 1,938/1,938 attempted batches;
- 38 warmups and 1,900/1,900 successful reportable measured trials;
- 5,610 issued product requests;
- 4,800/4,800 correctness checks passed;
- zero product, correctness, infrastructure, cleanup, or primary-latency
  failures;
- 26,692/26,692 native CLI invocations returned 0, passed response validation
  and authentication redaction, used unique request IDs, and emitted zero
  stderr bytes;
- four execution blocks, exclusively `windows_named_pipe`, `local_only`, and
  `per_execution_block`;
- 76,276 retained observations: 1,938 trials, 1,938 operations, 5,610
  requests, 4,896 checks, and 61,894 resource observations.

Absolute archive path:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`

Archive identities:

- 82,051 files; 3,139,214,747 bytes;
- content tree
  `sha256:606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`;
- raw subtree: 82,025 files; 2,964,792,876 bytes; tree
  `sha256:561dd3bd8ac1a7106fcf970acdcd6972a76da24fa07da147e4f19d49c83f3981`;
- archive manifest
  `sha256:239dbedb781f2e427fb61b316629ea57393d1a92a3be56a45bd107e998d9131c`;
- campaign manifest
  `sha256:93dd241e38c48b2a3f337d66065492f101d8945f7189c2f6402a32fa0fd7e7cf`;
- final report input
  `sha256:ebea3dc4119919969370897b64ea004cbc9555e3403463bc44cba534461d2982`.

Archive creation and two verify-only replays exited 0. The post-analysis replay
reproduced the same file count, byte count, and content tree.

## Post-freeze analysis compatibility erratum

The first final table-generation attempt failed closed before creating an
output directory:

`ERROR: final archive lacks required environment fields: host OS edition, host OS build`

The archive and archiver use the canonical verified keys `os_caption` and
`os_build_number`; the frozen reader accepted only synthetic legacy aliases
`os_edition` and `os_build`. Both canonical values were already present in the
immutable archive. No raw file, selector, exclusion, metric, aggregate,
eligibility decision, or measured result was missing or changed.

Local post-freeze correction commit
`538f6c98233863957082620329203348ddaa781c` accepts the canonical keys, retains
legacy aliases, avoids duplicating the generic OS family before a full caption,
and still fails closed when caption/edition or build evidence is absent. The
corrected generator is
`sha256:ff93953a6b8b94f10bc35138356a3039f6709a28ff0860d05c0da25e2064727b`.

This correction is disclosed as an analysis erratum, not as an unchanged
frozen generator. Its numeric neutrality was tested three ways:

1. Targeted generator tests, including explicit v1.1 canonical-only host
   metadata and missing-field negatives, pass 22/22.
2. The complete backend plus analysis suite passes 380 tests with five
   expected Windows symlink-privilege skips.
3. Replaying the corrected generator on the frozen pilot archive produces
   byte-identical `numeric-evidence.json`, `numeric-provenance.csv`, and Tables
   2--4 relative to the frozen generator. Only the intended non-numeric Table
   1 host presentation changes.

A rerun would have violated the exactly-one-final rule, and archive mutation
would have violated corpus immutability; neither occurred.

## Final tables and numeric provenance

The two fresh output directories are:

- `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\analysis\final-v11-019fb86c-tables-a`
- `C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\analysis\final-v11-019fb86c-tables-b`

Each contains nine files and 231,047 bytes. Path, byte-count, and SHA-256
inventories are identical. The output content tree is
`sha256:27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`.

| Artifact | SHA-256 |
|---|---|
| `generation-log.txt` | `481f89a1900a051649102b986ac3ad6a7083b53959cfa4a9bcf419e383d3d0b3` |
| `numeric-evidence.json` | `8a247f492b5bbf5bb35f1a89e0ed7dc3effcaaab0f935b746e1dcd89d62a367c` |
| `numeric-provenance.csv` | `e967539c2b62af1ab6c5c369c5825604ea545a2090b481544e74d9f174bff3d1` |
| `output-manifest.json` | `a77b30469c3d46c26ed045f748f09313a646ef13b571f40c45a7a31f7a72505e` |
| `table-1-environment.md` | `ebce68ac85292844cd1f397494211e3fe44250d9b5bf7dae019b62d10993b575` |
| `table-2-startup.md` | `9887ffedc5dd1bd98c5385bd2470cc2aa5e11bb07843a3bc4c8058a9601bdea6` |
| `table-3-cli-operations.md` | `6c194fb477a8279c31cf45f498954fdb80d7751328d1b4bef0f222f643410b80` |
| `table-4-resources.md` | `ed3fd61377ab075fc870194769919b138432053e0906b05a4d1c96cd5c6c1d78` |
| `tables.json` | `c8aaa13c58d0dad900f3d08d6a926d7736c281bacdb665e3976da269cbdab3dd` |

Numeric provenance is schema `ai-research-writing/numeric-evidence-v2`: 153
entries, 153 unique evidence IDs, no duplicates or value mismatches. Every
archive source hash, output-manifest entry, and `reportable_measured` selector
was independently rechecked.

## Result summary and evidence boundary

The complete reportable values are the generated tables, not this prose
summary. Representative bounded results are:

- sandbox create plus base mount: p50/p95/p99
  1,659.811/1,749.739/1,794.902 ms, mean throughput 0.62 ready/s;
- no-op CLI command at concurrency 1 versus 5: p50 26.719 versus 45.998 ms,
  and mean throughput 37.28 versus 107.61 operations/s;
- 256-KiB file edit at concurrency 5: p50/p95/p99
  187.357/208.008/294.392 ms, mean throughput 26.36 operations/s;
- for that same preregistered resource row, peak daemon RSS was 62.602 MiB,
  peak sandbox memory 66.715 MiB, mean sandbox CPU 148.732 ms/trial, and mean
  workspace allocated delta 1.258 MiB.

These are descriptive values for one disclosed native-Windows/Docker Desktop
host, one pinned image, one fixed 100-MiB fixture, one product/benchmark
revision, and concurrency 1 or 5. They are not competitive, universal, or
multi-agent productivity claims.

## Failures, exclusions, warnings, and unavailable metrics

The v1.1 final has no product, correctness, infrastructure, cleanup, or
primary-latency failure; no report warning; no excluded final trial; no retry;
and no silent outlier removal. Smoke, pilot, projection values, the failed
v1.0 partial final, setup/verification/teardown timings, and unavailable
observations remain excluded from manuscript result rows.

Explicit final-report unavailability is retained rather than encoded as zero:

- the archived canonical OS caption is the literal
  `Microsoft Windows 11 ???`; its localized edition suffix is not legible in
  the frozen capture. Build 26200, version, architecture, computer name, and
  all other host fields remain present. A post-run read-only registry query
  reported `EditionID=Core`, but that external check is not substituted into
  the archive-derived Table 1;
- `layerstack_bytes`: 1,900/1,900 reportable trials unavailable because the
  product does not report LayerStack allocated storage;
- `workspace_allocated_bytes`: 1,900/1,900 unavailable because host metadata
  does not expose allocated block counts;
- `daemon_cpu_time_ns`, `sandbox_cpu_time_ns`, and sandbox block read/write:
  100/1,900 unavailable for create-sandbox trials where a sandbox-scoped
  pre-create counter baseline cannot exist;
- sandbox current/peak memory: 50/1,900 unavailable before the resource ring
  exists.

Table 4 uses the available, preregistered `upperdir_bytes` workspace delta for
the rows it reports; it does not silently substitute unavailable
`workspace_allocated_bytes`.

## Code and documentation changed

The v1.1 product delta from the frozen v1.0 treatment
`0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3` through `5c48dae1` changed exactly:

```text
README.md
bin/package-windows-amd64-release.ps1
bin/start-sandbox-windows-docker-gateway.ps1
crates/sandbox-cli/src/manager.rs
crates/sandbox-cli/src/observability.rs
crates/sandbox-cli/src/runtime.rs
crates/sandbox-cli/tests/manager.rs
crates/sandbox-config/src/configs/gateway.rs
crates/sandbox-config/tests/unit/configs/gateway.rs
crates/sandbox-gateway/src/gateway/config.rs
crates/sandbox-gateway/src/gateway/lifecycle.rs
crates/sandbox-gateway/src/gateway/listener.rs
crates/sandbox-gateway/src/gateway/main.rs
crates/sandbox-gateway/src/gateway/mod.rs
crates/sandbox-gateway/src/lib.rs
crates/sandbox-gateway/tests/gateway_server.rs
crates/sandbox-gateway/tests/local_daemon_installer.rs
crates/sandbox-mcp/src/config.rs
crates/sandbox-mcp/src/lib.rs
crates/sandbox-operations/client/src/client.rs
crates/sandbox-operations/client/src/config.rs
crates/sandbox-operations/client/src/endpoint.rs
crates/sandbox-operations/client/src/lib.rs
crates/sandbox-operations/client/tests/config.rs
crates/sandbox-operations/client/tests/endpoint.rs
crates/sandbox-operations/client/tests/transport.rs
docs/windows-setup.md
```

The v1.1 paper/benchmark measurement delta through frozen commit `1680b59`
changed these exact experiment-scoped paths:

```text
benchmark/PAPER_ARTIFACT.md
benchmark/backend/benchmark_lab/cli.py
benchmark/backend/benchmark_lab/gateway.py
benchmark/backend/benchmark_lab/ipc_qualification.py
benchmark/backend/benchmark_lab/metadata.py
benchmark/backend/benchmark_lab/product_cli.py
benchmark/backend/benchmark_lab/runner.py
benchmark/backend/benchmark_lab/transport.py
benchmark/backend/tests/integration/test_gateway_lifecycle.py
benchmark/backend/tests/integration/test_gateway_transport.py
benchmark/backend/tests/integration/test_runner.py
benchmark/backend/tests/unit/test_exp1_archive.py
benchmark/backend/tests/unit/test_exp1_runtime_projection.py
benchmark/backend/tests/unit/test_ipc_qualification.py
benchmark/backend/tests/unit/test_metadata.py
benchmark/backend/tests/unit/test_product_cli.py
claim_evidence_map.md
experiment_inventory.md
experiments/analysis/exp1-final-failure-diagnostic.json
experiments/analysis/exp1-final-handoff.md
experiments/analysis/exp1-final-system-event-4227.json
experiments/analysis/exp1-freeze-record-eb10c26-0392b299.json
experiments/analysis/exp1-gate0-7-final-report.md
experiments/analysis/exp1-v1.1-remediation-decision.json
experiments/analysis/exp1-v1.1-remediation-decision.md
experiments/analysis/pilot-final-runtime-structural-0392b299-019fb6cf-limit1400.json
experiments/analysis/scripts/generate_exp1_tables.py
experiments/analysis/tests/test_generate_exp1_tables.py
experiments/environment_setup.md
experiments/exp1-v1.1-protocol-amendment.md
experiments/expected_tables.md
experiments/experiment_log.md
experiments/scripts/archive_exp1_run.py
experiments/scripts/project_exp1_final_runtime.py
paper_state.json
plan/progress.md
plan/task-packets/exp1-cli-performance-campaign.md
progress.md
```

The post-freeze analysis erratum changes only
`experiments/analysis/scripts/generate_exp1_tables.py` and its test file at
commit `538f6c9`. Post-final evidence updates modify this report,
`exp1-final-handoff.md`, the claim map, experiment inventory, two progress
trackers, paper state, benchmark artifact note, and the append-only experiment
log. Generated archives/tables and temporary diagnostics remain outside source
commits unless explicitly named.

## Tests and material commands

| Command or command class | Exit/status |
|---|---|
| Changed product-crate tests, real named-pipe request/response and concurrency-5 tests | Exit 0. |
| Changed product-crate all-target Clippy with warnings denied; formatting/diff checks | Exit 0. |
| Native release packaging and packaged concurrency-5 manager-CLI round trip | Exit 0 after the first policy-blocked `.ps1` launch was corrected to the documented bypass invocation. |
| Preregistered v1.1 IPC qualifier | PASS: 25,000/25,000 calls, 5,000 batches, zero transport/TCP/event/resource/cleanup gate failures. |
| Full prequalification benchmark/analysis suite | Exit 0: 354 passed, five expected skips. |
| Fresh v1.1 smoke, archive creation, and independent verification | Exit 0; terminal `completed`. |
| Fresh v1.1 pilot, archive creation, two table builds, projection, and independent verification | Exit 0; terminal `completed`; repeated outputs byte-identical. |
| Final freeze record, strict final preflight, package/tag/plan verification | Exit 0; final validation 19 cells/1,938 batches/5,610 requests and zero findings/warnings. |
| Sole v1.1 final benchmark and supervisor | Exit 0; terminal `completed`; stderr empty. |
| Final archive creation and two verify-only replays | Exit 0; all reproduce 82,051 files, 3,139,214,747 bytes, and the same content tree. |
| Initial frozen table-generator attempt | Exit 1 before output: canonical host schema was not recognized. No archive/output mutation. |
| Corrected generator targeted tests | Exit 0: 22 passed. |
| Corrected complete backend plus analysis suite | Exit 0: 380 passed, five expected Windows symlink skips. |
| Corrected final table generation into A and B | Exit 0 twice; 9/9 paths byte-identical. |
| Numeric-provenance/hash verification and frozen-pilot neutrality replay | Exit 0: 153/153 selectors verified; numeric artifacts and Tables 2--4 byte-identical to frozen-generator pilot output. |

The experiment log also retains non-result helper failures: read-only `rg`
exit propagation, one malformed PowerShell quote, one Docker template parse,
one pre-file-existence monitor read, a 10-second aggregate timeout followed by
a successful 60-second retry, unavailable venv Ruff, unsupported PowerShell
hex helpers, and two PowerShell numeric-audit false alarms corrected by exact
Python verification. None mutated a corpus, treatment, archive, Docker object,
host setting, or protected process, and none consumed another final attempt.

## Cleanup outcome

The final run workspace and runtime are absent. No matching benchmark process,
run- or gateway-labeled container, or volume remains. The product checkout is
clean direct `main` at `5c48dae1`. Protected pre-existing gateway PID 62980 is
alive and was never touched. The pre-existing exited container and five
pre-existing volumes remain unchanged.

## Supported wording

- "Under the disclosed native-Windows/Docker Desktop EXP1 v1.1 environment,
  the archive-derived latency, throughput, and resource values are those in
  Tables 2--4 for the fixed `paper-100m` workload and concurrency 1 or 5."
- "Sandbox create plus base mount had p50/p95/p99 latency of
  1,659.811/1,749.739/1,794.902 ms in this environment."
- "For the no-op native CLI command, mean throughput changed from 37.28
  operations/s at concurrency 1 to 107.61 operations/s at concurrency 5,
  while p50 batch makespan changed from 26.719 to 45.998 ms."
- "For the preregistered 256-KiB/concurrency-5 resource rows, peak measured
  sandbox memory ranged from 14.977 MiB for read to 66.715 MiB for edit."
- "The sole v1.1 final completed all 1,900 measured trials without a product,
  correctness, infrastructure, cleanup, or primary-latency failure."
- "The v1.0 failed corpus remains ineligible and was not pooled or compared
  numerically with v1.1."

## Wording that remains unsafe

- Any claim that Ephemeral Sandbox is universally fast, cheap, scalable,
  superior, or production-ready.
- Any competitive claim: no independent sandbox/worktree/container baseline
  was measured by this focused campaign.
- Any extrapolation beyond this host, image, product revision, fixture,
  workload, concurrency 1/5, or end-to-end native CLI boundary.
- Any causal claim that concurrency improves individual latency; the measured
  batch makespan and throughput must be reported separately.
- Any use of qualifier, smoke, pilot, projection, failed-v1.0 partial, setup,
  verification, teardown, unavailable, or silently rounded values as final
  manuscript results.
- Any security, isolation-correctness, multi-agent task-quality, publication,
  fault-tolerance, or useful-work claim from EXP1.

## Remaining blockers and next external action

There is **no remaining EXP1 execution or analysis blocker** and no rerun is
authorized or needed. The single next external action is author review of the
generated tables and bounded wording before selected numeric-evidence-backed
values are imported into `main.tex`.

Broader paper blockers—other RQs, competitive baselines, author metadata,
figure normalization, novelty review, and submission checks—remain outside
this focused experiment.
