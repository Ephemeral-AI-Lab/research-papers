# EXP1 final evidence handoff

Status date: 2026-07-31.

## Outcome

EXP1 protocol v1.0 was frozen and its sole eligible `paper-good-pass` was run
once. Run `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4` failed at the mandatory
post-response resource boundary after 853 of 1,938 trial batches. The immutable
archive is verified and classified `failed_ineligible`.

Gates 0 through 4 pass. Gate 5 fails. Gates 6 and 7 consequently fail because
the protocol forbids aggregating a partial final corpus or inserting its
numbers into the paper.

## Claim mapping

| Claim target | Safe wording | Evidence boundary |
|---|---|---|
| RQ3 final latency/resource result | “EXP1 v1.0 did not produce a paper-eligible final performance result.” | The sole final attempt failed before all 19 cells reached 100 reportable trials. |
| Campaign execution | “The frozen native-Windows `product_cli` smoke and five-sample pilot completed, but both remain qualification/exploratory evidence.” | Smoke and pilot values are permanently ineligible for manuscript tables. |
| Final failure | “The sole final attempt stopped during a required resource observation after the measured file-read request itself succeeded.” | Failed trial 34 is `infrastructure_failed`, `product_succeeded: true`, `reportable: false`, and cleanup restored the baseline. |
| Failure cause | “A new observability CLI connection hit Windows TCP endpoint-reuse pressure: the CLI recorded WSAEADDRINUSE 10048 and the System log emitted TCP/IP Event 4227 at the same instant.” | This is a scoped failure diagnosis, not a product-throughput or universal Windows limit. |
| Cleanup/provenance | “The failed corpus, frozen source/tag identities, and clean post-run proof were preserved and independently verified.” | The archive is `failed_ineligible`; preservation does not make partial metrics eligible. |

The WSAEADDRINUSE connection failure is primary archive evidence. Event 4227
was retrieved read-only from the Windows System log after the run and preserved
separately in `exp1-final-system-event-4227.json`; it was not retroactively
inserted into the immutable run archive.

## Wording that remains unsafe

- Any latency, throughput, p99, RSS, CPU, I/O, storage, or scaling number from
  the failed final corpus.
- Any table or aggregate derived from the smoke, pilot, or partial final.
- “Ephemeral Sandbox is fast,” “scales,” “is cheap,” “beats a baseline,” or
  any broader superiority statement.
- A claim that Windows has a universal 6,760-connection or 16,384-connection
  ceiling. The run establishes one endpoint-reuse failure in the frozen host
  and workload only.
- A claim that all dynamic ports were simultaneously exhausted. The evidence
  establishes WSAEADDRINUSE and Event 4227 endpoint-reuse pressure, not complete
  instantaneous occupancy of the range.
- A claim that the product file-read operation failed or returned incorrect
  content. The product request succeeded; the mandatory evidence boundary
  failed before verification.

## Numeric-evidence decision

No final table or numeric-evidence v2 record is generated. There is no eligible
numeric selector to hand to LaTeX. The diagnostic counts in
`exp1-final-failure-diagnostic.json` describe campaign completion and failure
provenance only; they are not performance results.

## Evidence-group disclosure

The archive contains 7,992 committed CLI invocation records and one additional
incomplete raw projection group. Basename
`766ed434998f2dc7c002bac6dd08c3d642cf1ec416eb2d2cc7df65a6906471a0`
has a valid cgroup JSON stdout and empty stderr, but no metadata commit marker.
This is consistent with its concurrent cgroup request finishing while the
snapshot exception unwound the resource-boundary gather, but the exact race is
not directly logged and is not claimed as proven. It does not restore the
missing snapshot boundary or make the trial reportable.

## Immutable evidence

- Archive:
  `experiments/runs/019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`
- Archive content tree:
  `sha256:7efa643b12aba09f0ba5ecfbed5b5692a166a5c12931490402d3992d92f3ae6a`
- Archive manifest:
  `sha256:5e0a3c4f7c864df8070a668d2f373b75bece3c2a57cc4340cd89ece292cc7927`
- Campaign manifest:
  `sha256:8eefbec9772406943bb1baa2476b181c7436a6fafd7a6d7984874e8889f96982`
- Failure diagnostic:
  `experiments/analysis/exp1-final-failure-diagnostic.json`
- Post-run primary System-event capture:
  `experiments/analysis/exp1-final-system-event-4227.json`,
  `sha256:b6eac476b6ecf8c20de529be5c5ca8de297874ae9273c65a4baaf6ffc34ac89d`
- Frozen paper commit:
  `eb10c26d1bfd632772baf1bc331c985d0231f52d`
- Frozen product commit:
  `0392b299ecaf3a75c8b6d04ed94d5a15593ca6a3`
- Annotated product tag object:
  `0b4aaec5f13b0e52772b2adb7ca2807ee2223e6d`

## Required next decision

Do not relaunch v1.0. A future attempt must first choose and document a
scientifically acceptable remedy for high-rate CLI connection churn, create a
new protocol/source/environment freeze, and receive explicit author
authorization. The failed archive must remain immutable and cannot be replaced.
