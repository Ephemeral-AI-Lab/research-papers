# EXP1 v1.1 local-IPC protocol amendment

**Protocol ID:** `ephemeral-sandbox-v1-practical-performance-v1.1`

**Status:** authorized pre-measurement treatment; qualification pending

**Date:** 2026-07-31

**Supersedes for new work:** the unexecuted IPv4 dynamic-port-range proposal in
`experiments/analysis/exp1-v1.1-remediation-decision.{md,json}`

**Does not supersede:** the immutable v1.0 protocol, freeze, sole failed final,
or failed archive

## Decision and evidence boundary

The author directed the permanent CLI issue to be fixed and the EXP1 goal to
resume. For v1.1, native Windows product CLIs communicate with the native
gateway through Windows named pipes. TCP remains available only when an
explicit TCP endpoint is requested for compatibility or remote use; it is not
permitted in the v1.1 paper treatment. No host network setting is changed.

The sole v1.0 final remains permanently `failed_ineligible`. Its archive,
paper freeze, product tag, and partial values are immutable. Those values may
be used only as failure evidence; they must not be pooled with, substituted
for, or numerically compared with v1.1 measurements.

The transport change is scientifically material. V1.1 therefore requires a
new product identity, package, qualification, smoke, pilot, projection,
paper/source freeze, annotated `paper-v1.1-freeze` tag, and exactly one final
attempt after all preceding gates pass.

## Locked treatment delta

Only these treatment facts change from v1.0:

| Item | Locked v1.1 value |
|---|---|
| CLI-to-gateway transport | `windows_named_pipe` |
| Endpoint scope | `local_only` |
| Endpoint identity | `isolated_windows_named_pipe_per_execution_block` |
| Endpoint rotation | once per gateway execution block |
| Endpoint syntax | `npipe://./pipe/<unique-name>` |
| Canonical CLI option | `--gateway-endpoint` |
| Client behavior | one native CLI process, one named-pipe connection attempt, one request, one validated response, no retry and no fallback |
| Gateway behavior | one isolated released gateway per execution block; bounded pending pipe instances |
| Host network mutation | none |

Every other scientific choice is retained unchanged: the 19 cells, fixed
image and `paper-100m` fixture, operation definitions, seed, two warmups,
pilot five-sample count, final 100-sample count, concurrency levels, scheduling,
timeouts, resource cadence, correctness rules, exclusions, metrics, and all
numeric/measured table definitions. The sole provenance-table clarification
below does not add or alter a measurement.

### Provenance-only Table 1 clarification

Because transport is the scientifically material v1.1 treatment, Table 1 adds
exactly one non-numeric text row named `Gateway transport`. Its value is
derived deterministically from the archived run manifest's transport object;
it is never copied from qualification output or entered manually. The machine
table/output-manifest schema advances to version 2 solely to carry this typed
provenance field and the protocol version.

Tables 2--4, every numeric column, cell, metric, aggregation, eligibility rule,
and sample count remain unchanged. For legacy v1.0 archive regeneration, the
same provenance field may disclose the historical loopback transport without
changing the frozen v1.0 raw corpus. This is the only table-schema change
authorized by v1.1.

The primary timing boundary remains immediately before native CLI process
creation through validated JSON response and process exit. Named-pipe
connection establishment remains inside that boundary. Gateway setup,
readiness, endpoint selection, verification, sampling, and teardown remain
outside primary timing.

## Frozen product candidate

The prequalification product candidate is clean direct `main` commit
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`, consisting of:

- `56c676d588fbb704bf3da8f67d22be910453644d`:
  `Use local IPC for gateway CLI transport`;
- `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`:
  `Preserve TCP endpoint compatibility`.

The staged package is
`C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox\target\windows-exp1-5c48dae1`;
its ZIP is `windows-exp1-5c48dae1.zip`.

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| Package ZIP | 5,739,735 | `11e83246b2f509da9708a0237bb6ab600d042e1cb390c81fc41dc834d897c506` |
| `bin\sandbox-gateway.exe` | 3,480,064 | `42e7642dd025487811abbcd78dcc5513760f2aaa1e6057cfdfa3e74c03748358` |
| `bin\sandbox-manager-cli.exe` | 827,904 | `e1faa2fe0e9f4909fa2d694166784ac65dde40ba82795b7e0c503eb5fea86513` |
| `bin\sandbox-runtime-cli.exe` | 833,536 | `e18827cf765945c958e169748575b89645c730b310ee5ffc1b42c382b44a0e26` |
| `bin\sandbox-observability-cli.exe` | 826,880 | `2b1c13bba36c9486f768824178d1e2ea8d2b1da019bd21cd1f9ea250d5da34c5` |
| `dist\sandbox-daemon-linux-amd64` | — | `f5a71c3c3fe05345958b1d4d4561c64dec298022d80d3595bb0397c9b15f3c2a` |
| `config\windows-amd64.yml` | — | `987776d700108c8a9a9c1a3ed42b9155a4db46e7dde20765a79ef6df6e13677a` |

The candidate remains provisional until the qualification, smoke, pilot,
projection, and freeze gates pass. Any source, binary, package, or protocol
drift invalidates the corresponding downstream evidence.

## EXP1 v1.1 IPC qualification policy preregistration

This policy is fixed before the first live v1.1 qualifier. Qualification is a
strict engineering and environment gate, not performance evidence.

### Workload and success criteria

- Run exactly 25,000 native
  `sandbox-manager-cli.exe list_sandboxes` invocations.
- Schedule exactly 5,000 batches at concurrency 5 against one unique named
  pipe and one isolated packaged gateway.
- Use the canonical `--gateway-endpoint` option with the exact named-pipe URI.
- Do not use TCP, pacing, sleeps, retries, connection fallback, or an
  alternate direct client.
- Give every invocation a unique request ID.
- Require every process to exit 0, write empty stderr, and write exactly one
  valid JSON line with the expected list-sandboxes response shape.
- Mark all qualifier artifacts `qualification_only: true` and
  `performance_evidence: false`. They are never eligible for manuscript
  tables, runtime projection, or numeric claims.
- Preserve per-invocation timestamps, request IDs, exit status, output hashes,
  command provenance, and all partial failure evidence.

Any invocation, response-shape, stderr, process, gateway, cleanup, or evidence
failure fails the qualifier. There is no retry.

### TCP and Windows event evidence

- Capture the System event-log cursor immediately before gateway start.
- After gateway cleanup, query the closed interval from that cursor through a
  newly captured final cursor for provider `Tcpip` event IDs 4227 and 4231.
- Any newly observed matching event fails qualification conservatively,
  regardless of attribution uncertainty.
- At readiness, every 100 batches, immediately before gateway stop, and after
  cleanup, capture `Get-NetTCPConnection` evidence.
- The gateway PID must own no TCP listener or TCP connection in every sample.
  Any owned TCP endpoint fails qualification and proves treatment drift or
  fallback.

### Gateway resource gates

Capture gateway process samples at readiness, every 100 batches, and
immediately before stop. Record handles, private bytes, and resident-set bytes
for every sample and evaluate both the peak above readiness and the final
above readiness.

| Resource | Peak-over-readiness limit | Final-over-readiness limit |
|---|---:|---:|
| Handles | 32 | 32 |
| Private bytes | 16 MiB | 16 MiB |
| Resident-set bytes | 16 MiB | 16 MiB |

The exact cap passes; one unit or byte above it fails. The 32-handle allowance
is no greater than the gateway listener's maximum pending-instance bound. The
16 MiB memory allowances are conservative fixed qualification limits selected
before evidence is collected; they are not performance results.

### Provenance and fail-closed cleanup

The qualification summary and manifest must bind:

- clean product branch, commit, status, source identities, package directory,
  package ZIP, and SHA-256 for every packaged binary/configuration artifact;
- clean prequalification paper commit and status over the archive's frozen
  source/protocol/analysis scope and documented generated-file exclusions,
  qualifier source and test hashes, protocol-amendment hash, and exact
  sanitized commands (pre-existing excluded caches and generated evidence are
  preserved, not deleted to manufacture a globally empty worktree);
- host/build identity, package build command, endpoint URI, gateway PID,
  gateway executable path, token redaction, timestamps, counters, thresholds,
  event cursors/query, TCP samples, and resource samples;
- gateway stop command/result, original PID/path, confirmed process exit,
  PID-file removal, output hashes, and cleanup return state.

The harness must attempt cleanup in `finally`-equivalent control flow. Missing,
ambiguous, or failed stop/cleanup evidence fails the qualifier, while retaining
all evidence already written.

## Postqualification gate sequence

If and only if the qualifier passes:

1. run a fresh complete 19-cell CLI integration smoke and archive/verify it;
2. run one fresh complete 19-cell, five-sample exploratory pilot and
   archive/verify it;
3. regenerate exploratory tables twice, require byte identity, and require a
   conservative final projection no greater than 1,400 seconds;
4. resolve only pre-freeze instrumentation defects allowed by the original
   packet, rerunning affected exploratory gates when necessary;
5. commit the clean paper/source/environment freeze and create the local
   annotated `paper-v1.1-freeze` tag without moving `paper-v1-freeze`;
6. run exactly one v1.1 `paper-good-pass` after a read-only preflight;
7. archive and independently verify the attempt whether it succeeds or fails;
8. generate final tables and numeric evidence only from a complete eligible
   final archive.

No v1.1 result is known or implied by this preregistration.
