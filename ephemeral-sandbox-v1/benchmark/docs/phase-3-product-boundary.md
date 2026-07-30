# Phase 3 product boundary and isolated lifecycle

Status: complete.

## Files changed

- `backend/benchmark_lab/catalog.py`: strict schema-1 catalog models, relationship validation, canonical prebuilt exporter invocation, exact-byte and executable digests, and required-operation admission.
- `backend/benchmark_lab/transport.py`: loopback-only authenticated JSONL, compact one-line requests, unique request IDs, 16 MiB caps, distinct product/transport failures, credential-echo rejection, exactly-one-response enforcement, and `time.monotonic_ns()` around only socket send/read.
- `backend/benchmark_lab/gateway.py`: fixed prebuilt gateway and Linux daemon selection, benchmark-owned effective configuration, private runtime/token/PID/log files, process groups, authenticated readiness, sandbox sweep, labeled Docker cleanup, bounded shutdown, process-identity proof, and stale recovery.
- `backend/benchmark_lab/redaction.py`: recursive secret filtering and bounded line/total process-log capture with persisted sanitized JSONL.
- `backend/benchmark_lab/resources.py`: closed resource kinds, duplicate rejection, LIFO cleanup, retained failures, and aggregated sanitized errors.
- `defaults/gateway.yml`: benchmark-owned deployment template; only documented runtime paths, loopback bind, daemon package, workspace root, gateway identity, and remount width are filled.
- `backend/tests/contract/test_catalog.py`, `backend/tests/integration/test_gateway_transport.py`, `backend/tests/integration/test_gateway_lifecycle.py`, and `backend/tests/unit/test_redaction.py`: exporter, socket, lifecycle, PID-reuse, cancellation, redaction, caps, malformed-response, and cleanup failure injection.

## Behavior and safety results

The catalog exporter is selected only from the explicit canonical product binary directory. The reader rejects unknown schema fields and inconsistent domains, families, routes, or operations. A real prebuilt exporter returned 20 operations and passed admission for every product operation required by Quick Smoke; the exact export digest was `sha256:2f89829ef68ea96f36354507478f2f36bb2f4e4918f7292f4190d4cdd6e07be6`, and the exporter digest was `sha256:07948f5ae3b5c52ca49aeff310f9061f49d6ba688eb05a24024b20046f8d1da3`.

Gateway requests use a new connection and request ID for each operation. Connection setup and response verification are outside the primary latency; the clock begins immediately before write/drain/read and ends as soon as the complete first response line arrives. The client then verifies EOF so a second response is rejected. Product error envelopes remain distinct from transport failures, and neither registered credentials nor sensitive diagnostics enter exceptions or logs.

An isolated campaign requires an exact marker-owned run directory, canonical gateway binary, fixed architecture-specific Linux ELF daemon package, and canonical Git toolchain archives. Startup creates a marker-owned `runtime/<run-id>` with mode-0600 token, config, owner-process metadata, and sanitized JSONL logs. Readiness requires both the gateway-owned PID file and an authenticated `list_sandboxes` response. Shutdown attempts the final sandbox sweep, process-group termination, labeled container/volume cleanup, log persistence, token deletion, and runtime removal independently; any failure blocks cleanup and preserves marker-owned evidence.

Stale recovery validates the exact runtime marker, metadata schema, binary path and digest, process-group identity, and OS process birth identity before sending a signal. A reused PID is never signaled. Once identity is proven, recovery aggregates gateway, process, labeled Docker, credential, and runtime cleanup. Failed recovery deletes credentials when safe but retains the owned runtime directory and blocks completion.

## Commands and results

- Catalog plus zero-Rust guard: 7 passed in 0.88 seconds.
- Transport, redaction, catalog, and guard: 21 passed in 1.97 seconds.
- Product-boundary failure-injection suite after stale-recovery tightening: 30 passed in 2.94 seconds.
- Complete offline backend suite: 68 passed in 29.32 seconds.
- Real prebuilt catalog export: 20 operations; required Quick Smoke product operations present.
- Python bytecode compilation and `git diff --check`: clean.
- Product repository status and diff: clean.

## Gaps and deviations

No migration-spec deviation. Phase 3 deliberately stops at fake process/socket and offline prebuilt-exporter proof, which is its specified gate. The first live isolated Docker gateway and feature-by-feature product operations belong to Phase 4; expensive passing live slices will not be repeated until the final proof. The exact catalog export will be stored in each run definition snapshot when Phase 4 creates authoritative run artifacts.
