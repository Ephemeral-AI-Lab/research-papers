# Expected experiment tables

**Status:** Schema draft; no measured values exist  
**Protocol:** [`../experiment_inventory.md`](../experiment_inventory.md)  
**Rule:** every numeric cell must be generated from archived run data

The focused study produces four tables: one provenance table and three measured
result tables. It does not include a baseline-ranking table because the study
is intended to characterize practical performance, not claim superiority.

Verification remains mandatory inside the benchmark, but it is not shown as a
column. A row is displayed only when all contributing samples pass the
operation, correctness, infrastructure, and cleanup gates.

## Table 1 - Environment and workload

**Purpose:** make the performance cell reproducible and bound every claim to
one host, image, product revision, benchmark revision, and workspace.

| Field | Expected value | Evidence source |
|---|---|---|
| Host OS | Ubuntu Server 24.04 LTS | preflight record |
| Kernel | `TBD` | `uname -r` |
| Architecture | x86-64 / `amd64` | `uname -m`, image inspect |
| CPU | `TBD model`, 8 vCPU or more | `/proc/cpuinfo`, `nproc` |
| Memory | 16 GiB or more | `/proc/meminfo` |
| Storage | local NVMe-backed ext4 | `findmnt`, `lsblk` |
| Docker Engine | `TBD` | `docker version` |
| Cgroup | v2 | `/sys/fs/cgroup/cgroup.controllers` |
| Product commit/tag | `TBD final clean main` | Git record |
| Benchmark commit | `TBD paper-local commit` | Git record |
| Sandbox image | pinned Ubuntu 24.04 digest | plan and image inspect |
| Sandbox limits | 1 vCPU, 512 MiB, 256 PIDs | effective configuration |
| Workspace | 4,000 files, 100 MiB, depth 100 | fixture manifest |
| Client | `direct_client` | expanded plan |
| Seed | `20260712` | expanded plan |
| Trials | 2 warmups + 100 measured per cell | expanded plan |

No value may be copied manually from this design document. The final table is
generated from the preflight record, expanded plan, fixture manifest, and run
manifest.

## Table 2 - Startup and workspace readiness

**Purpose:** show the cost of obtaining a usable private workspace on the
100 MiB/depth-100 base.

| Stage | Concurrent creates | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ready/s) |
|---|---:|---:|---:|---:|---:|---:|
| Sandbox create + base mount | 1 | 100 | -- | -- | -- | -- |
| Session create to ready | 1 | 100 | -- | -- | -- | -- |
| Session create to ready | 5 | 100 | -- | -- | -- | -- |
| First no-op command | 1 | 100 | -- | -- | -- | -- |

The first row is blocked until the runner preserves an explicit
`create_sandbox` request-to-ready timing. It must be omitted rather than filled
from generic setup time if that instrumentation is not added. "Session create"
uses the existing prepared-sandbox `create_workspace` boundary and must not be
renamed to sandbox creation.

## Table 3 - Public CLI-operation performance

**Purpose:** provide per-operation numbers for the public operations corresponding
to the CLI's `exec_command`, read, write, and edit actions.

| Operation | Case | Payload/file size | Concurrency | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ops/s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `exec_command` | no-op | -- | 1 | 100 | -- | -- | -- | -- |
| `exec_command` | no-op | -- | 5 | 100 | -- | -- | -- | -- |
| `exec_command` | fixture read | 4 KiB | 1 | 100 | -- | -- | -- | -- |
| `exec_command` | fixture read | 4 KiB | 5 | 100 | -- | -- | -- | -- |
| Read | snapshot | 4 KiB | 1 | 100 | -- | -- | -- | -- |
| Read | snapshot | 4 KiB | 5 | 100 | -- | -- | -- | -- |
| Read | snapshot | 256 KiB | 1 | 100 | -- | -- | -- | -- |
| Read | snapshot | 256 KiB | 5 | 100 | -- | -- | -- | -- |
| Write | session-local | 4 KiB | 1 | 100 | -- | -- | -- | -- |
| Write | session-local | 4 KiB | 5 | 100 | -- | -- | -- | -- |
| Write | session-local | 256 KiB | 1 | 100 | -- | -- | -- | -- |
| Write | session-local | 256 KiB | 5 | 100 | -- | -- | -- | -- |
| Edit | one replacement | 4 KiB | 1 | 100 | -- | -- | -- | -- |
| Edit | one replacement | 4 KiB | 5 | 100 | -- | -- | -- | -- |
| Edit | one replacement | 256 KiB | 1 | 100 | -- | -- | -- | -- |
| Edit | one replacement | 256 KiB | 5 | 100 | -- | -- | -- | -- |

This table deliberately has no "verification", "pass", or "failure" column.
Failed, non-reportable, and partial samples remain visible in the run manifest
and [`experiment_log.md`](experiment_log.md). A row with fewer than 100
reportable samples is not published.

These are public gateway-operation timings, not shell-process startup timings
for launching the `sandbox` CLI executable itself.

## Table 4 - Resource envelope

**Purpose:** show the resource cost accompanying Table 3 rather than presenting
low latency without its CPU, memory, I/O, or storage context.

| Operation/case | Concurrency | Peak daemon RSS (MiB) | Peak sandbox memory (MiB) | Sandbox CPU (ms/trial) | Block read (MiB/trial) | Block write (MiB/trial) | Workspace allocated delta (MiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Workspace create, 100 MiB/depth 100 | 1 | -- | -- | -- | -- | -- | -- |
| Workspace create, 100 MiB/depth 100 | 5 | -- | -- | -- | -- | -- | -- |
| `exec_command`, no-op | 1 | -- | -- | -- | -- | -- | -- |
| `exec_command`, no-op | 5 | -- | -- | -- | -- | -- | -- |
| Read, 256 KiB | 5 | -- | -- | -- | -- | -- | -- |
| Write, 256 KiB | 5 | -- | -- | -- | -- | -- | -- |
| Edit, 256 KiB | 5 | -- | -- | -- | -- | -- | -- |

Use the maximum observed gauge for peak memory, per-trial counter deltas for
CPU and block I/O, and the before/after allocated-byte delta for workspace
storage. If the runtime cannot provide a metric, render `unavailable` and
explain why; never substitute a different scope.

## Aggregation and formatting contract

- Latency is reported in milliseconds with enough precision to avoid rounding
  materially different values together.
- Throughput is completed operation requests divided by batch makespan.
- Byte values use binary units: KiB and MiB.
- p50/p95/p99 are computed from exactly the reportable measured samples.
- Warmups are excluded.
- Table captions state `n`, environment scope, timing boundary, and whether the
  value is a percentile, maximum, or counter delta.
- No number is manually edited after generation.
- Raw values, selectors, analysis command, and output hash are retained.

## Evidence mapping

| Table | Required inputs | Blocking acceptance gate |
|---|---|---|
| Table 1 | Preflight, expanded plan, Git/binary/image/fixture hashes | Gate 1 |
| Table 2 | Workspace lifecycle samples and optional sandbox-create timing | Gate 3 |
| Table 3 | Reportable operation trials | Gate 5 |
| Table 4 | Resource samples correlated to reportable trials | Gate 5 |

Placeholder dashes in this document are schema markers, not zero values and not
illustrative results.

## Simulated preview - not experimental evidence

Everything in this section is fabricated solely to preview table density,
attributes, units, and plausible-looking formatting. These values must never be
copied into the manuscript, numeric-evidence records, plots, or analysis tests.

### Simulated Table 1

| Field | Simulated example value |
|---|---|
| Host OS | Ubuntu Server 24.04 LTS |
| Kernel | `6.8.0-example` |
| Architecture | x86-64 |
| CPU | Example 8-vCPU host |
| Memory | 16 GiB |
| Storage | Example local NVMe, ext4 |
| Docker Engine | `29.x (example)` |
| Cgroup | v2 |
| Product commit/tag | `example-final-commit` |
| Benchmark commit | `example-benchmark-commit` |
| Sandbox image | pinned Ubuntu 24.04 digest |
| Sandbox limits | 1 vCPU, 512 MiB, 256 PIDs |
| Workspace | 4,000 files, 100 MiB, depth 100 |
| Seed/trials | `20260712`; 2 warmups + 100 measured |

### Simulated Table 2

| Stage | Concurrent creates | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ready/s) |
|---|---:|---:|---:|---:|---:|---:|
| Sandbox create + base mount | 1 | 100 | 631.0 | 824.0 | 967.0 | 1.6 |
| Session create to ready | 1 | 100 | 38.2 | 55.7 | 69.4 | 26.2 |
| Session create to ready | 5 | 100 | 78.5 | 106.3 | 132.8 | 63.7 |
| First no-op command | 1 | 100 | 11.8 | 17.6 | 22.4 | 84.7 |

### Simulated Table 3

| Operation | Case | Size | Concurrency | Samples | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (ops/s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `exec_command` | no-op | -- | 1 | 100 | 12.1 | 18.7 | 24.9 | 82.6 |
| `exec_command` | no-op | -- | 5 | 100 | 19.8 | 31.4 | 43.8 | 252.5 |
| `exec_command` | fixture read | 4 KiB | 1 | 100 | 14.7 | 21.9 | 28.6 | 68.0 |
| `exec_command` | fixture read | 4 KiB | 5 | 100 | 23.6 | 36.8 | 49.5 | 211.9 |
| Read | snapshot | 4 KiB | 1 | 100 | 3.2 | 4.8 | 6.1 | 312.5 |
| Read | snapshot | 4 KiB | 5 | 100 | 7.4 | 10.9 | 14.6 | 675.7 |
| Read | snapshot | 256 KiB | 1 | 100 | 8.9 | 12.8 | 16.3 | 112.4 |
| Read | snapshot | 256 KiB | 5 | 100 | 23.5 | 34.1 | 43.7 | 212.8 |
| Write | session-local | 4 KiB | 1 | 100 | 4.6 | 7.1 | 9.4 | 217.4 |
| Write | session-local | 4 KiB | 5 | 100 | 11.8 | 18.9 | 25.7 | 423.7 |
| Write | session-local | 256 KiB | 1 | 100 | 12.7 | 18.6 | 24.8 | 78.7 |
| Write | session-local | 256 KiB | 5 | 100 | 36.2 | 54.7 | 72.1 | 138.1 |
| Edit | one replacement | 4 KiB | 1 | 100 | 6.8 | 10.4 | 13.9 | 147.1 |
| Edit | one replacement | 4 KiB | 5 | 100 | 17.2 | 26.8 | 35.6 | 290.7 |
| Edit | one replacement | 256 KiB | 1 | 100 | 21.5 | 33.2 | 44.7 | 46.5 |
| Edit | one replacement | 256 KiB | 5 | 100 | 63.8 | 94.5 | 121.7 | 78.4 |

### Simulated Table 4

| Operation/case | Concurrency | Peak daemon RSS (MiB) | Peak sandbox memory (MiB) | Sandbox CPU (ms/trial) | Block read (MiB/trial) | Block write (MiB/trial) | Workspace allocated delta (MiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Workspace create, 100 MiB/depth 100 | 1 | 91 | 146 | 31 | 4.2 | 0.8 | 0.0 |
| Workspace create, 100 MiB/depth 100 | 5 | 118 | 238 | 96 | 11.7 | 2.4 | 0.0 |
| `exec_command`, no-op | 1 | 88 | 139 | 7 | 0.1 | 0.0 | 0.0 |
| `exec_command`, no-op | 5 | 103 | 194 | 24 | 0.3 | 0.0 | 0.0 |
| Read, 256 KiB | 5 | 101 | 188 | 19 | 1.4 | 0.0 | 0.0 |
| Write, 256 KiB | 5 | 109 | 207 | 38 | 0.2 | 1.6 | 1.3 |
| Edit, 256 KiB | 5 | 116 | 221 | 71 | 0.9 | 1.8 | 1.4 |

Again, all values in these four preview tables are simulated. The real tables
remain empty until Gates 1-6 in the experiment specification pass.
