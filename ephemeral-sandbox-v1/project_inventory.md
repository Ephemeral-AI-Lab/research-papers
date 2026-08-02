# Ephemeral Sandbox v1 final project inventory

**Revalidated:** 2026-08-02
**Product source for manuscript claims:**
[`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8),
annotated tag `paper-v1.1-freeze` object
`834c84534359f37653fb25ac45304091e82c37a6`
**Historical comparison only:** baseline `b22862550e0a7cb4fe61ce581831e9244cc492b5`

## Evidence inventory

| Area | Measured-source evidence | Paper use | Boundary |
|---|---|---|---|
| LayerStack/history/leases | `crates/sandbox-runtime/layerstack` | Source-grounded logical view, publication, and lease description | No serializable-isolation, crash, or physical-storage claim. |
| Overlay workspace/capture | `crates/sandbox-runtime/workspace`, `overlay` | Private upper/work projection and typed capture description | Linux/OverlayFS implementation; not security or measured isolation. |
| Namespace execution | `namespace-process`, `namespace-execution`, workspace holder | Holder/runner implementation description | Shared-network profile is not egress isolation; restart behavior is unmeasured. |
| Runtime operations | `sandbox-runtime/operation` | Explicit/implicit session and lifecycle behavior | Test presence is not a paper correctness result. |
| CLI projections | `sandbox-cli/src/projection/{manager,runtime,observability}.rs` | Measured-source 8/10/8 contract | Contract evidence only. |
| Endpoint/client/gateway | `sandbox-operations/client/{config,endpoint,client}.rs`, gateway listener/config/lifecycle | Windows named-pipe default, TCP compatibility, URI resolution, optional request IDs | EXP1 treatment is local Windows named pipe per execution block only. |
| Resource sampler | daemon observability resource source | Defines available sampled metrics/`upperdir_bytes` | Does not make unavailable allocated-block or LayerStack metrics zero. |

## Baseline-to-measured source reconciliation

The measured revision preserves the core workspace, capture, reconciliation,
and manifest-publication concepts used in the manuscript, while changing the
operational treatment in ways that must be reflected in paper prose:

1. Gateway endpoints became typed TCP, Windows named-pipe, or Unix-socket
   endpoints. Windows defaults to a local named pipe; TCP compatibility remains
   explicit rather than removed.
2. `--gateway-endpoint` became the canonical global CLI flag with
   `--gateway-socket` as a visible compatibility alias.
3. Optional validated request IDs moved from runtime-only use to all three
   CLI clients.
4. Base-workspace handling and resource sampling changed to support the frozen
   benchmark treatment; the paper treats these as implementation/provenance,
   not general performance mechanisms.
5. Holder/supervisor and Docker-executor changes affect implementation details
   but do not justify new correctness/recovery claims.

`cli_contract_matrix.md` is the authoritative regenerated public-interface
summary. The manuscript must link source-derived statements to this measured
snapshot, not to the historical baseline.

## Experiment inventory

| Artifact | Identity and use |
|---|---|
| Protocol | `ephemeral-sandbox-v1-practical-performance-v1.1`; methodology in `experiment_inventory.md`. |
| Sole eligible final | `experiments/runs/019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`; immutable content tree `606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`. |
| Measurement commit | paper `1680b599129532f72e706b6acb12ef62c63759e2`; product `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`. |
| Final analysis | output trees `final-v11-019fb86c-tables-a` and `-b`, byte-identical tree `27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`. |
| Numeric provenance | `numeric-evidence.json` plus `numeric-provenance.csv`: 153 unique selector-bound values. |
| Erratum | analysis-only commit `538f6c98233863957082620329203348ddaa781c`; canonical-host compatibility correction, with Tables 2--4 numeric neutrality validated. |

The 3.1-GB archive is immutable and local/ignored. The failed v1.0 final,
qualifier, smoke, pilot, projection, setup, verification, teardown, partial,
and unavailable observations are retained for provenance but ineligible for
manuscript results.

## Known limitations to preserve

- Post-commit attribution is best effort and may be `unknown`.
- Explicit/implicit protected-drop behavior needs maintainer clarification.
- Lease/substitution state across daemon restart lacks a final fault evaluation.
- Merge trace memory remains line/edit-distance dependent despite the 8 MiB
  input gate.
- EXP1 does not evaluate isolation, publication faults, baselines, deeper
  scaling, useful work, or multi-agent quality.
- LayerStack 2.0 and reflink remain future work; the stock Windows/Docker/WSL
  feasibility cell failed direct `FICLONE` with `errno=95`.
