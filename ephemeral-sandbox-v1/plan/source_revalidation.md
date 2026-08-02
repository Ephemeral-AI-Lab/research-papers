# P2 measured-source revalidation

**Audit date:** 2026-08-02
**Historical baseline:** `b22862550e0a7cb4fe61ce581831e9244cc492b5`
**Measured source:** `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`
**Tag:** `paper-v1.1-freeze`, annotated object
`834c84534359f37653fb25ac45304091e82c37a6`

## Revalidation outcome

The manuscript retains only source-grounded behavior that exists at the
measured revision. Workspace/session, lease, capture, current-head resolution,
active-manifest publication, and lifecycle claims remain implementation claims.
They are not promoted to empirical correctness claims merely because source or
tests exist. `cli_contract_matrix.md` was regenerated from measured projection
sources and replaces the baseline matrix.

## Material baseline-to-measured differences

| Area | Measured-source change | Paper decision |
|---|---|---|
| Gateway transport | Typed `tcp`, `npipe`, and `unix` endpoint support; Windows defaults to local named pipe. | State that EXP1 used local named pipes per execution block and that TCP compatibility remains. |
| CLI configuration | Canonical `--gateway-endpoint URI`; `--gateway-socket` is a compatibility alias. | Use endpoint terminology in prose and contract matrix. |
| Request identity | Optional validated `--request-id` is accepted by management, runtime, and observability CLIs. | Replace the old runtime-only assertion. |
| Resource sampling | Workspace sampling adds available upperdir-byte observation. | Table 4 labels its field as `upperdir` delta and preserves unavailable allocated-block fields. |
| Workspace base | Measured revision can hash/reuse the shared base instead of always rebuilding it. | Treat as experiment implementation/provenance, not a general efficiency result. |
| Holder/supervisor and Docker executor | Completion polling/executor implementation changed. | Preserve lifecycle limits; make no new restart or reliability claim. |

## Source anchors

- CLI projections: `crates/sandbox-cli/src/projection/{manager,runtime,observability}.rs`.
- CLI behavior: `crates/sandbox-cli/src/{manager,runtime,observability,input,output}.rs`.
- Endpoint/client: `crates/sandbox-operations/client/src/{config,endpoint,client}.rs`.
- Gateway: `crates/sandbox-config/src/configs/gateway.rs` and
  `crates/sandbox-gateway/src/gateway/{config,listener,lifecycle}.rs`.
- Workspace/session/publication: the existing LayerStack, workspace,
  namespace-process, and runtime-operation source anchors now resolve at the
  measured commit through the updated inventory and final manuscript snapshot.

No historical freeze record, run archive, generated output tree, or v1.0
evidence was edited in this revalidation.
