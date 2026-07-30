# Ephemeral Sandbox v1 CLI contract matrix

Audited 2026-07-30 against baseline commit [`b22862550e0a7cb4fe61ce581831e9244cc492b5`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5). This is a provisional source snapshot: regenerate it from the eventual annotated `paper-v1-freeze` tag.

## Contract authority and known documentation drift

The primary interface evidence is the requested source projection directory:

- Management: [`crates/sandbox-cli/src/projection/manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/manager.rs) — 8 operations.
- Runtime: [`crates/sandbox-cli/src/projection/runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/runtime.rs) — 10 operations.
- Observability: [`crates/sandbox-cli/src/projection/observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/observability.rs) — 8 operations.

The live [CLI documentation](https://ephemeral-sandbox.com/docs/cli) lists 8/7/5. Relative to the baseline source, its runtime page omits `create_workspace_session`, `publish_workspace_session`, and `destroy_workspace_session`; its observability page omits `resources`, `daemon`, and `topology`. The source projection and semantic catalog, not the live site, define the paper interface.

The semantic catalog supplies operation names, descriptions, argument types/defaults, visibility, and routing. The CLI projection supplies the shell path, flags/positionals, usage, and examples. [`projection_integrity.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/projection_integrity.rs) tests a bidirectional match between public catalog routes and projections.

## Why three clients

The baseline builds three feature-gated executables and no combined CLI ([`sandbox-cli/Cargo.toml`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/Cargo.toml), [`sandbox-cli/src/lib.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/lib.rs)):

- **Management** owns host/fleet lifecycle, selection, compaction, and export. Requests use system envelope scope even when a target sandbox ID is an operation argument.
- **Runtime** owns stateful work inside one selected sandbox: execution, file operations, and explicit workspace-session lifecycle. Every request requires sandbox envelope scope.
- **Observability** contains read-only inspection operations. `snapshot` and `resources` can aggregate at system scope or target one sandbox; the other operations target a sandbox.

This separation gives an orchestrator smaller role-specific operation sets and makes accidental cross-authority invocation testable ([manager rejection tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/manager.rs), [observability rejection tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/observability.rs)). It is an interface/least-exposure property, not by itself an authorization or sandbox-security guarantee.

## Boundary: operational contract versus coordination plane

The three-client division exposes lifecycle, runtime work, request correlation, and read-only inspection in role-specific surfaces. It does **not** make the baseline a complete agent-team or swarm control plane. The audited source contract does not establish:

- declared coding intent or path/interface claims before execution;
- agent roles, task dependencies, ownership transfers, or handoff acceptance;
- port leases, discoverable service endpoints, or general resource-budget admission;
- semantic test compatibility or automated integration-lane scheduling;
- transactionally complete attribution across data publication, audit, accounting, and cleanup.

These are relevant public-coordination facts in high-concurrency agent systems, but they remain external orchestration concerns or future runtime work unless they are implemented and source-proven before `paper-v1-freeze`. The paper can claim that the current interfaces provide typed building blocks for orchestration; it cannot claim that v1 implements the full coordination plane proposed by the concurrency-ceiling article.

## Management client: 8 system-scoped operations

Primary evidence: [`manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/manager.rs); semantics: [`catalog/src/manager`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/manager); tests: [`cli/tests/manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/manager.rs).

| Operation | Source-projected usage | Effect | Envelope scope |
|---|---|---|---|
| `create_sandbox` | `sandbox-manager-cli create_sandbox --image IMAGE --workspace-bind-root PATH [--count N]` | Creates manager/runtime sandbox records and daemon(s); mutating. `--workspace-root` remains an accepted alias. | System |
| `list_docker_images` | `sandbox-manager-cli list_docker_images` | Reads available images. | System |
| `list_workspace_directories` | `sandbox-manager-cli list_workspace_directories [--path PATH]` | Reads host directory choices. | System |
| `destroy_sandbox` | `sandbox-manager-cli destroy_sandbox --sandbox-id ID` | Stops and removes the selected sandbox; mutating/destructive. | System; ID is an argument |
| `list_sandboxes` | `sandbox-manager-cli list_sandboxes` | Reads manager records. | System |
| `inspect_sandbox` | `sandbox-manager-cli inspect_sandbox --sandbox-id ID` | Reads one manager record. | System; ID is an argument |
| `squash_layerstacks` | `sandbox-manager-cli squash_layerstacks --sandbox-id ID` | Requests compaction and live-session migration; mutating representation while preserving the intended logical history. | System; ID is an argument |
| `export_changes` | `sandbox-manager-cli export_changes --sandbox-id ID --dest PATH [--format dir\|tar\|tar-zst]` | Reads a published delta and writes the requested destination artifact. It does not publish a workspace session. | System; ID is an argument |

Manager `--progress` writes progress records to stderr while retaining the final JSON result on stdout; this separation is tested in [`manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/manager.rs).

## Runtime client: 10 sandbox-scoped operations

Primary evidence: [`runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/runtime.rs); semantics: [`catalog/src/runtime`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/runtime); tests: [`cli/tests/runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/runtime.rs).

All runtime invocations require the global `--sandbox-id ID`; the selector becomes the request-envelope scope and is removed from operation arguments ([request builder tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/request_builder.rs)).

The workspace-session model has two source-distinct paths:

- A sessionless `exec_command` creates one implicit private workspace session with `publish_then_destroy`; after its command ledger drains, the runtime captures the session delta, publishes or rejects it against LayerStack, and destroys the session ([`exec_command.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/command/service/exec_command.rs), [`service/model.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/model.rs)).
- An explicit `create_workspace_session` returns an ID that multiple command and file calls can share before deliberate `publish_workspace_session` merge-back or `destroy_workspace_session` discard ([session catalog](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/runtime/workspace_session.rs)).

This should not be generalized to every sessionless file operation: `file_read` projects the current LayerStack, while `file_write` and `file_edit` amend the current head directly ([read](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/read.rs), [write](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/write.rs), [edit](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/edit.rs)).

| Operation | Source-projected usage | Effect |
|---|---|---|
| `exec_command` | `sandbox-runtime-cli --sandbox-id ID exec_command [--workspace-session-id ID] [--timeout-ms N] [--yield-time-ms N] COMMAND` | Runs a command in a workspace view. It can mutate private state; without an explicit session, implicit finalization can publish then destroy. |
| `write_command_stdin` | `... write_command_stdin --command-session-id ID [--yield-time-ms N] TEXT` | Mutates a live command session's input/process state. |
| `read_command_lines` | `... read_command_lines --command-session-id ID [--start-offset N] [--limit N]` | Reads buffered command output. |
| `file_read` | `... file_read --path FILE [--offset N] [--limit N] [--workspace-session-id ID]` | Reads file contents from an implicit or explicit workspace view. |
| `file_write` | `... file_write --path FILE --content TEXT [--workspace-session-id ID]` | Writes the private view; an implicit operation can finalize through publication. |
| `file_edit` | `... file_edit --path FILE --edits JSON [--workspace-session-id ID]` | Applies validated string edits to the private view; an implicit operation can finalize through publication. |
| `file_blame` | `... file_blame --path FILE` | Reads best-effort publication attribution. It must not be presented as transactionally complete provenance. |
| `create_workspace_session` | `... create_workspace_session [--network-profile PROFILE]` | Creates a persistent private workspace session. `isolated` requests a network namespace; shared networking is otherwise possible. |
| `publish_workspace_session` | `... publish_workspace_session --workspace-session-id ID [--grace-s SECONDS]` | Captures and performs all-or-none data publication, then closes. Rejection/precommit failure preserves the session for retry; committed cleanup failure is reported as partial success. |
| `destroy_workspace_session` | `... destroy_workspace_session --workspace-session-id ID [--grace-s SECONDS]` | Tears down the session and discards unpublished private state; destructive to that session. |

An operation-level command exit status is response data. The CLI exit status reports whether the requested runtime operation/protocol succeeded; a gateway-returned runtime failure envelope exits 1 even when its details contain a command exit code ([runtime CLI test](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/runtime.rs)).

## Observability client: 8 read-only operations

Primary evidence: [`observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/observability.rs); semantics: [`catalog/src/observability`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/observability); routing tests: [`catalog/tests/observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/tests/observability.rs).

| Operation | Source-projected usage | View | Envelope scope |
|---|---|---|---|
| `snapshot` | `sandbox-observability-cli snapshot [--sandbox-id ID]` | Aggregate manager/gateway snapshot or one sandbox snapshot. | System if omitted; sandbox if supplied |
| `trace` | `... trace --sandbox-id ID [--trace-id TRACE\|last]` | One request trace, defaulting to the latest. | Sandbox required |
| `events` | `... events --sandbox-id ID [--name NAME] [--since-ms MS] [--last-n N]` | Bounded/filterable event records. | Sandbox required |
| `resources` | `... resources [--sandbox-id ID] [--window-ms MS]` | Fleet current-usage map at system scope or daemon-sampled sandbox history. | System if omitted; sandbox if supplied |
| `daemon` | `... daemon --sandbox-id ID` | Bounded daemon self/process/ownership diagnostics. | Sandbox required |
| `topology` | `... topology --sandbox-id ID` | Explicit bounded workspace process-topology collection. | Sandbox required |
| `cgroup` | `... cgroup --sandbox-id ID [--scope SCOPE] [--window-ms MS]` | Host/daemon resource counters for the sandbox or workspace scope. It is exposed read-only even though catalog routing can be manager-owned. | Sandbox required |
| `layerstack` | `... layerstack --sandbox-id ID [--workspace-id WS] [--window-ms MS]` | LayerStack/session history and current view. | Sandbox required |

Only `snapshot` and `resources` are aggregate-capable in the baseline; this is asserted in [`catalog/tests/observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/tests/observability.rs). Aggregate/scoped request construction and one-request behavior are tested in [`cli/tests/observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/observability.rs).

## Shared request, connection, and authentication discovery

The request envelope is `{op, request_id, scope, args}` ([request contract](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/contract/src/request.rs)).

- Default request IDs are UUIDv4. Only the runtime CLI exposes `--request-id`; it accepts 1–128 ASCII alphanumeric characters plus `.`, `_`, `:`, and `-` ([runtime CLI input](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/runtime.rs), [request builder](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client/src/request.rs), [tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/request_builder.rs)).
- Gateway connection resolution is CLI override (`--gateway-socket`, `--gateway-auth-token`) → `SANDBOX_GATEWAY_SOCKET` / `SANDBOX_GATEWAY_AUTH_TOKEN` → default socket `127.0.0.1:7878`; a blank configured value is rejected ([client configuration](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client/src/config.rs), [config tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client/tests/config.rs)).
- The direct client opens a TCP connection per request, inserts the token field, and exchanges newline-framed JSON ([client](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client/src/client.rs), [protocol auth field](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-protocol/src/auth.rs)).
- The CLI client does **not** automatically discover a token file. Setup documentation shows an operator reading a token file into the environment, for example [Linux setup](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/docs/linux-setup.md). The token check is an implemented gateway authentication mechanism, not a general sandbox-security guarantee.

## JSON streams and process exits

[`sandbox-cli/src/output.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/output.rs) and the client-specific tests establish:

| Condition | stdout | stderr | CLI exit |
|---|---|---|---:|
| Help or successful operation | Help text, or one JSON result line | Empty, except manager progress if requested | 0 |
| Gateway operation failure | Empty | Gateway JSON error envelope | 1 |
| Transport/protocol failure | Empty | Local JSON error envelope | 1 |
| Local syntax, unknown operation, invalid argument, or configuration/build error | Empty | Local JSON error envelope | 2 |

The response envelope is defined in [`sandbox-operations/contract/src/response.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/contract/src/response.rs). Compatibility fixtures cover unknown operations and exit 2 ([`compatibility.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/compatibility.rs)).

## Catalog-derived help contract

Help joins semantic catalog entries with the CLI projection to render usage, arguments, defaults, examples, and related operations ([`help.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/help.rs)). Exact help snapshots and operation sets are tested in [`manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/manager.rs), [`runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/runtime.rs), and [`observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/observability.rs). These are CLI contract tests; they do not establish workspace isolation, publication correctness, or performance.

## Freeze actions

1. At `paper-v1-freeze`, export the semantic catalog and all three help snapshots from the tagged binary.
2. Record the tag object, exact commit, build toolchain, binary digests, command line, and raw exported JSON/text.
3. Diff tagged counts/usage/defaults against this matrix and the live site.
4. Treat any site discrepancy as documentation drift, not as permission to edit the paper contract.

