# EXP1 v1.1 endpoint-pressure remediation decision

Status: proposal awaiting explicit author authorization.

Date: 2026-07-31.

This document is failure analysis and protocol planning, not performance
evidence. It does not authorize a v1.0 rerun, alter the immutable failed
archive, change the host, or launch a live probe.

## Decision

For the shortest path to a scientifically usable EXP1 result, prefer a
temporary **active-store IPv4 dynamic-port range expansion** from
49,152–65,535 (16,384 ports) to 1,025–65,535 (64,511 ports), followed by a
same-rate qualification, fresh smoke/pilot, protocol/environment v1.1 freeze,
and exactly one newly authorized final.

This is not the ideal product architecture. Persistent connection reuse is the
long-term engineering fix. It is nevertheless the least disruptive EXP1
remediation because it preserves every measured request as a fresh native CLI
subprocess with its TCP transport inside the primary timing window. No product
operation, payload, cell, trial count, metric, exclusion, or table schema needs
to change.

The host mutation is global, elevated, and scientifically material. It must
not be applied without explicit author authorization. The current session is
not elevated, and no network setting was changed.

## What the failed corpus proves

- The immutable final contains 7,992 committed CLI metadata records plus one
  identifiable completed cgroup sibling without its metadata commit marker:
  7,993 client-to-gateway TCP attempts in total.
- Every frozen `GatewayClient` request opens a fresh `TcpStream`; the gateway
  reads one request and closes the connection.
- The failure-centered 240-second window contains 6,760 attempts, or 28.167
  attempts per second. The maximum rolling 240-second rate is 28.404 per
  second.
- Exactly one committed invocation failed: the mandatory post-response
  snapshot returned WSAEADDRINUSE 10048. Its concurrent cgroup sibling
  completed successfully, the measured file-read had already succeeded, and
  the gateway remained live.
- TCP/IP Event 4227 at the same instant records local-endpoint reuse under
  high-rate connection open/close churn.

This proves endpoint-reuse pressure and the proximate failed connection. It
does not prove that all 16,384 dynamic ports were simultaneously occupied, an
exact TIME_WAIT count, or a universal numerical failure threshold.

## Why reducing resource cadence is not a remedy

Of 3,836 observability connections, 3,626 (94.53%) are mandatory and only 210
are periodic. Periodic sampling is 2.63% of all identified attempts. The
failed snapshot belongs to the mandatory post-response boundary.

Removing periodic samples would therefore weaken the resource protocol while
removing only 210 attempts. Automatic retries are also prohibited because they
would hide a failed sample and can bias the retained distribution.

## Why per-cell gateway rotation is not accepted alone

One gateway per cell is an attractive paper-local change and would preserve
one-shot CLI timing. However, the accepted pilot’s trial-scoped CLI counts,
scaled diagnostically from seven to 102 trials, project:

| Scope | Projected trial-scoped CLI connections |
|---|---:|
| Complete final | 26,392 |
| Files family | 20,578 |
| Largest single cell | 4,532 |

The largest cell is the 256-KiB, concurrency-5 file-edit cell. Its projected
4,532 connections are slightly above the 4,398 committed connections already
observed at the failed files endpoint. The sole final never reached that cell,
so reasoning only from the largest completed cell would understate the risk.
Per-cell rotation remains a fallback to qualify, not a sufficient remedy on
current evidence.

## Other candidates

| Candidate | Decision | Reason |
|---|---|---|
| Merge cgroup and snapshot into one product request | Engineering option, not selected | Removes 1,918 observed attempts (24.00%) and the incomplete-pair failure mode, but requires a new product operation/schema and still leaves no validated safe churn level. |
| Persistent/multiplexed CLI transport | Long-term product fix | Both client and gateway are one-request-per-connection. Redesign is required, and using persistence for measured calls would change the defining process/transport timing construct. |
| Auto-reuse port range | Qualify only as fallback | The host reports zero/disabled auto-reuse ranges. Configuration requires elevation and stronger same-destination validation; it is not the first experiment remedy. |
| Shorter TIME_WAIT | Rejected initially | Host-wide safety/timing change with restart implications; no need to combine it with the first remedy. |
| `SO_REUSEADDR` | Rejected | Microsoft warns that ordinary use can be nondeterministic and vulnerable to port hijacking. |
| Reboot, pacing, sleeps, or retries | Rejected | Reboot is temporary; pacing changes scheduling/runtime; retries violate the protocol. |

## Proposed v1.1 authorization scope

If approved, the host change would be active-store only:

```powershell
netsh interface ipv4 set dynamicportrange protocol=tcp startport=1025 numberofports=64511 store=active
```

The exact active-store rollback would be:

```powershell
netsh interface ipv4 set dynamicportrange protocol=tcp startport=49152 numberofports=16384 store=active
```

Neither command has been run. IPv6, TIME_WAIT, auto-reuse, routing, firewall,
Docker, and protected resources would remain unchanged.

Approval must cover this complete sequence:

1. Capture active/persistent TCP ranges, excluded ranges, TCP profiles,
   transport filters, registry values, event-log cursor, Git identities, and
   protected baseline.
2. Apply and verify only the temporary IPv4 active-store range.
3. After prior endpoint states quiesce, run an ineligible strict native-CLI
   same-endpoint qualifier for at least 700 seconds and at least 20,000
   successful connections, sustaining at least the failed run’s 28.167
   attempts/second 240-second rate. Capture BOUND/TIME_WAIT counts and Event
   4227/4231 cursors. Any transport error or new event fails qualification.
4. Clean up and quiesce, then repeat the complete 19-cell smoke and
   five-sample pilot with no retries.
5. Require correctness, cleanup, deterministic exploratory regeneration, and
   a fresh projection no greater than the approved 1,400 seconds.
6. Freeze protocol/source/environment v1.1 in a new paper commit and record
   the exact active IPv4 range and qualification evidence.
7. Run exactly one newly authorized v1.1 final after a read-only preflight.
8. Archive and clean up even on failure, then restore the active IPv4 range.
   Only a complete eligible corpus may generate tables and numeric evidence.

The failed v1.0 archive remains immutable and cannot be replaced, pooled, or
numerically compared with v1.1.

## Evidence and references

- Machine-readable decision:
  `experiments/analysis/exp1-v1.1-remediation-decision.json`
- Failed archive:
  `experiments/runs/019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`
- Failed archive content tree:
  `sha256:7efa643b12aba09f0ba5ecfbed5b5692a166a5c12931490402d3992d92f3ae6a`
- Microsoft port-exhaustion and Event 4227 guidance:
  <https://learn.microsoft.com/en-us/troubleshoot/windows-client/networking/tcp-ip-port-exhaustion-troubleshooting>
- Microsoft dynamic-port-range support and syntax:
  <https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/default-dynamic-port-range-tcpip-chang>
- Microsoft active versus persistent `netsh interface` store:
  <https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-interface>
- Microsoft guidance to address connection creation/pooling before relying on
  range/TIME_WAIT workarounds:
  <https://learn.microsoft.com/en-us/troubleshoot/sql/database-engine/connect/intermittent-periodic-network-issue>
- Microsoft Winsock 10048 definition:
  <https://learn.microsoft.com/en-us/windows/win32/winsock/windows-sockets-error-codes-2>
- Microsoft `SO_REUSEADDR` safety guidance:
  <https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse>

## Exact blocker

The only remaining decision before any implementation or live work is explicit
author approval or rejection of the v1.1 temporary active-store IPv4 range
remediation and the complete qualification/refreeze/one-final sequence above.
