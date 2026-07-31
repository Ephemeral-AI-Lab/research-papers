# EXP1 v1.1 final evidence handoff

Status date: 2026-07-31.

## Outcome

EXP1 v1.1 completed Gates 0--7. The sole eligible final run
`019fb86c-096e-7589-a0a4-a6d6ef5d7f8b` contains exactly 19 cells, 1,938
batches, 38 warmups, 1,900 successful/reportable measured trials, and 5,610
issued product requests. Correctness passed, report warnings are empty, and
all product, correctness, infrastructure, cleanup, and missing-latency failure
counts are zero.

The immutable archive is:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\runs\019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`

It contains 82,051 files and 3,139,214,747 bytes with content tree
`sha256:606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`.
Its raw subtree is bound by
`sha256:561dd3bd8ac1a7106fcf970acdcd6972a76da24fa07da147e4f19d49c83f3981`.

The earlier v1.0 final remains `failed_ineligible`; no v1.0, qualifier, smoke,
pilot, projection, or partial-final value is included in this handoff.

## Analysis identity and erratum

The measurement freeze records table generator
`sha256:7fd9c21d99ceb4b9fc3b962977ee9c0d270411ec2c6b76cc88960387a2fcbeb7`.
Its first post-final invocation failed before output because it did not accept
the archive's canonical `os_caption` and `os_build_number` keys.

Post-freeze analysis-only correction commit
`538f6c98233863957082620329203348ddaa781c` has generator hash
`sha256:ff93953a6b8b94f10bc35138356a3039f6709a28ff0860d05c0da25e2064727b`.
The correction changes only Table 1 host-field compatibility. Against the
frozen pilot archive, numeric evidence, numeric provenance, and Tables 2--4
remain byte-identical. The final archive was not changed and the final was not
rerun.

## Deterministic outputs

Primary output:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\analysis\final-v11-019fb86c-tables-a`

Independent repeat:

`C:\Users\yifan\code\Ephemeral-AI-Lab\research-papers\ephemeral-sandbox-v1\experiments\analysis\final-v11-019fb86c-tables-b`

Both directories contain the same nine files and 231,047 bytes. Every path,
byte count, and SHA-256 matches. Output tree:
`sha256:27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`.

Use these artifacts:

- `table-1-environment.md` for the tested environment and workload;
- `table-2-startup.md` for sandbox/workspace startup and first no-op;
- `table-3-cli-operations.md` for the 16 public CLI rows;
- `table-4-resources.md` for the seven preregistered resource rows;
- `numeric-provenance.csv` for the 153 raw source/hash/selector/aggregate
  bindings;
- `numeric-evidence.json` as the
  `ai-research-writing/numeric-evidence-v2` import registry;
- `output-manifest.json` for generator, archive, protocol, and output hashes.

## RQ3 claim mapping

| Result family | Supported wording | Direct evidence | Boundary |
|---|---|---|---|
| Environment and treatment | "The result uses native Windows build 26200, Docker Desktop 29.0.1, a pinned Ubuntu 24.04 image, `paper-100m`, and local Windows named pipes rotated per execution block." | Table 1, campaign/run/environment manifests. | One disclosed host and treatment only. |
| Startup | "In the tested environment, sandbox create plus base mount had p50/p95/p99 1,659.811/1,749.739/1,794.902 ms." | Table 2 and `table2.create_sandbox.none.c1.*` numeric selectors. | Not a cold-machine, remote, or cross-platform result. |
| Workspace/first command | "Session create and first no-op values are those in Table 2 for concurrency 1 or 5." | Table 2 and matching numeric selectors. | Session create is distinct from sandbox create. |
| CLI latency | "For each fixed operation/payload/concurrency row, end-to-end native CLI p50/p95/p99 is the value in Table 3." | Table 3; `batch_makespan_ns` selectors over 100 reportable trials. | Includes native process launch, CLI/gateway transport, validation, and process exit. |
| CLI throughput | "Mean completed-operation throughput changed between concurrency 1 and 5 as shown in Table 3." | Table 3; `throughput_ops_s` selectors. | Describe change; do not claim linear scaling or improved per-request latency. |
| Resources | "Peak/mean resource observations for the seven preregistered rows are those in Table 4." | Table 4 and matching daemon/cgroup/upperdir selectors. | Sampled/available metrics only; unavailable values are not zero. |
| Completeness | "The sole v1.1 final completed all 1,900 measured trials with zero classified failures." | Report counts, campaign manifest, archive verifier. | Does not establish broader reliability. |

Every displayed table value has a unique numeric-provenance row. No table
contains a verification/pass column, and no number was manually copied into
LaTeX during this campaign.

## Supported representative sentences

- "Sandbox create plus base mount had p50/p95/p99 latency of
  1,659.811/1,749.739/1,794.902 ms in the tested environment."
- "No-op native CLI throughput changed from 37.28 operations/s at concurrency
  1 to 107.61 operations/s at concurrency 5; p50 batch makespan changed from
  26.719 to 45.998 ms."
- "At concurrency 5, the 256-KiB file-edit row had p50/p95/p99
  187.357/208.008/294.392 ms and mean throughput 26.36 operations/s."
- "For the preregistered 256-KiB/concurrency-5 resource rows, peak measured
  sandbox memory was 14.977 MiB for read, 54.270 MiB for write, and 66.715 MiB
  for edit."

## Unsafe wording

- "Ephemeral Sandbox is fast/scalable/cheap" without the tested-environment
  qualifier and exact workload.
- Any superiority or competitive-baseline claim.
- Any claim beyond concurrency 1 and 5, the fixed payloads, `paper-100m`, the
  pinned image, this host, or this source identity.
- Any causal interpretation that concurrency improves individual latency.
- Any performance use of v1.0, qualifier, smoke, pilot, projection, setup,
  verification, teardown, partial, or unavailable evidence.
- Any security, isolation, publication correctness, fault tolerance,
  multi-agent quality, or productivity conclusion from EXP1.

## Unavailable and excluded evidence

Final failures, report warnings, and excluded final trials: none.

Explicitly unavailable at the reportable-trial level:

- the frozen OS caption's localized edition suffix is represented literally
  as `???`; Table 1 preserves that archived string. A later read-only registry
  query found `EditionID=Core`, but it is external context and is not inserted
  into the archive-derived table;
- LayerStack allocated storage: 1,900/1,900;
- host workspace allocated blocks: 1,900/1,900;
- create-sandbox daemon/sandbox CPU and block-I/O deltas: 100/1,900 each,
  because no sandbox-scoped pre-create baseline can exist;
- sandbox current and peak memory before the resource ring exists: 50/1,900
  each.

These values remain unavailable. Table 4's workspace column is the separately
defined, available `upperdir_bytes` delta.

## Cleanup and next action

The final workspace/runtime are absent, no owned process/container/volume
remains, product `main` is clean at `5c48dae1`, and protected gateway PID 62980
is alive and untouched. Nothing was pushed.

There is no remaining EXP1 blocker. The next external action is author review
of the generated tables and bounded sentences before evidence-backed values
are imported into `main.tex`.
