# Ephemeral Sandbox v1 CLI contract matrix

**Measured-source audit:** 2026-08-02 against annotated
[`paper-v1.1-freeze`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8), commit
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`. This replaces the provisional
baseline matrix. It is source/contract evidence, not a runtime-correctness or
security result.

## Final snapshot differences that affect the paper

Relative to historical baseline `b22862550e0a7cb4fe61ce581831e9244cc492b5`,
the measured snapshot preserves the 8/10/8 operation sets but changes the
gateway interface. All three CLIs accept an optional validated `--request-id`;
`--gateway-endpoint URI` is the canonical global flag and
`--gateway-socket` remains a visible compatibility alias. Endpoint parsing
accepts TCP, local Windows named-pipe, and Unix-domain-socket forms. On Windows,
the default endpoint is `npipe://./pipe/ephemeral-sandbox-gateway`; TCP remains
an explicit compatibility endpoint. The EXP1 treatment used per-execution-block
local named pipes and must not be generalized to every deployment.

Primary source: [`manager`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/manager.rs),
[`runtime`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/runtime.rs),
[`observability`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/observability.rs),
[`endpoint parser`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-operations/client/src/endpoint.rs),
and [`gateway listener`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-gateway/src/gateway/listener.rs).

## Management client: 8 system-scoped operations

| Operation | Measured-source usage | Effect |
|---|---|---|
| `create_sandbox` | `sandbox-manager-cli create_sandbox --image IMAGE --workspace-bind-root PATH [--count N]` | Creates sandbox records and daemons. |
| `list_docker_images` | `sandbox-manager-cli list_docker_images` | Reads image choices. |
| `list_workspace_directories` | `sandbox-manager-cli list_workspace_directories [--path PATH]` | Reads workspace choices. |
| `destroy_sandbox` | `sandbox-manager-cli destroy_sandbox --sandbox-id ID` | Removes the selected sandbox. |
| `list_sandboxes` | `sandbox-manager-cli list_sandboxes` | Reads manager records. |
| `inspect_sandbox` | `sandbox-manager-cli inspect_sandbox --sandbox-id ID` | Reads one manager record. |
| `squash_layerstacks` | `sandbox-manager-cli squash_layerstacks --sandbox-id ID` | Requests compaction/remount work. |
| `export_changes` | `sandbox-manager-cli export_changes --sandbox-id ID --dest PATH [--format dir\|tar\|tar-zst]` | Exports a published delta; it does not publish a session. |

Projection source: [`projection/manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/projection/manager.rs).

## Runtime client: 10 sandbox-scoped operations

Every runtime request requires `--sandbox-id`; it becomes the envelope scope.
The operation set is:

`exec_command`, `write_command_stdin`, `read_command_lines`, `file_read`,
`file_write`, `file_edit`, `file_blame`, `create_workspace_session`,
`publish_workspace_session`, and `destroy_workspace_session`.

`exec_command` may use `--workspace-session-id`; a sessionless command has the
documented implicit-session path. Sessionless `file_read` projects the active
LayerStack, while sessionless `file_write` and `file_edit` amend the current
head directly. Do not generalize the implicit-session rule to every runtime
operation. Projection source: [`projection/runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/projection/runtime.rs).

## Read-only observability client: 8 operations

| Operation | Scope |
|---|---|
| `snapshot` | System when `--sandbox-id` is omitted; sandbox otherwise. |
| `trace` | Sandbox required. |
| `events` | Sandbox required. |
| `resources` | System when `--sandbox-id` is omitted; sandbox otherwise. |
| `daemon` | Sandbox required. |
| `topology` | Sandbox required. |
| `cgroup` | Sandbox required. |
| `layerstack` | Sandbox required. |

Projection source: [`projection/observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8/crates/sandbox-cli/src/projection/observability.rs).

## Shared contract and evidence boundary

The envelope contains operation, request ID, scope, and arguments. Successful
operations produce a JSON result on stdout with exit 0. Remote or transport
failures use a JSON stderr envelope and exit 1; local usage/configuration
errors use JSON stderr and exit 2. Manager progress can share stderr with a
successful stdout result. Contract tests exercise catalog/projection integrity,
CLI input validation, output conventions, and endpoint parsing. They do not
measure workspace isolation, publication correctness, security, recovery, or
performance.

The client division exposes narrower role-specific operation sets but does not
implement task intent, ownership, handoffs, service/port leases, admission,
semantic verification, or a general coordination plane. The public website is
not the paper authority because its operation counts may drift from this
measured source snapshot.
