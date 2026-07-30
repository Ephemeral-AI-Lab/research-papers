# Ephemeral Sandbox v1: project and evidence inventory

Last audited: 2026-07-30.

## Provenance and evidence policy

The source checkout is `C:\Users\yifan\code\Ephemeral-AI-Lab\ephemeral-sandbox`. Its existing `main` was fast-forwarded from `origin/main` and remained clean at the requested initial baseline, commit [`b22862550e0a7cb4fe61ce581831e9244cc492b5`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5). The repository's `AGENTS.md` and `CLAUDE.md` require direct work on `main` and prohibit side branches/worktrees. The requested `paper-v1-freeze` tag does not yet exist. Every source-backed statement below is therefore **baseline evidence, not final paper provenance**; it must be rechecked and relinked to the commit named by the final annotated tag.

The authoritative [`PRD.md`](./PRD.md) and [`progress.md`](./progress.md) were read from the `research-papers` checkout at commit [`57777979f3988e3005717da833bea37b95552a99`](https://github.com/Ephemeral-AI-Lab/research-papers/tree/57777979f3988e3005717da833bea37b95552a99/ephemeral-sandbox-v1). They define the evidence gates, baseline, required paper artifacts, and progress checklist. An earlier loose-folder audit incorrectly reported them missing; this repository copy supersedes that statement.

Evidence labels used here:

- **S — source-proven:** implemented in the audited commit.
- **T — tested:** exercised by a named test at that commit.
- **D — documented:** public or maintainer description; not a substitute for frozen source.
- **E — experiment needed:** a proposed empirical claim or an existing exploratory protocol without v1-freeze results.
- **O — out of scope:** deliberately not claimed.

The live site is useful product and architecture context, but it is not the frozen v1 interface contract. In particular, its [CLI overview](https://ephemeral-sandbox.com/docs/cli) currently lists 8 management, 7 runtime, and 5 observability operations, whereas the baseline projections contain 8, 10, and 8. The final CLI reference must be regenerated from the tagged projection sources.

## Repository and evidence map

| Area | Primary implementation | Principal tests | Paper use |
|---|---|---|---|
| Semantic operation catalog and routing | [`crates/sandbox-operations/catalog`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog), especially [`routed.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/routed.rs) | [`catalog/tests/integrity.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/tests/integrity.rs) | Operation identity, authority, visibility, scope, and routing. |
| CLI projections and contracts | [`projection/manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/manager.rs), [`runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/runtime.rs), [`observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/src/projection/observability.rs) | [`projection_integrity.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/projection_integrity.rs), client-specific CLI tests | Frozen operational interface; contract evidence only. |
| Gateway/client protocol | [`sandbox-operations/client`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client), [`sandbox-operations/contract`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/contract) | [`client/tests/request.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/client/tests/request.rs), [`contract/tests/contract.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/contract/tests/contract.rs) | Request envelope, scope, connection discovery, token field, response envelope. |
| Layer history, leases, publish, squash | [`sandbox-runtime/layerstack`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack) | [`layerstack/tests/unit`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/unit) | Snapshot and publication mechanism; primary systems evidence. |
| Workspace lifecycle and overlay capture | [`sandbox-runtime/workspace`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace) | [`workspace/tests/unit/overlay_capture.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/tests/unit/overlay_capture.rs) | Private writable view, capture, lifecycle teardown. |
| Namespace execution | [`namespace-process`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-process), [`namespace-execution`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-execution) | Crate unit/integration tests | Holder-owned namespaces and namespace-joined operations. |
| Runtime orchestration and explicit sessions | [`sandbox-runtime/operation`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation) | [`workspace_session_publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session_publish.rs), [`layerstack_publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/layerstack_publish.rs) | Admission, capture/publish/destroy sequencing, retry and partial-success behavior. |
| Architecture narrative | [`docs/maintainer-architecture.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/docs/maintainer-architecture.md) | Source tree above | Maintainer-authored map; use source/tests for individual claims. |

The request path is CLI or MCP adapter → semantic catalog/projection → operation client → authenticated newline-delimited JSON gateway → manager or sandbox daemon → runtime/workspace/layer services. This ownership map is described in the [maintainer architecture](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/docs/maintainer-architecture.md) and instantiated by the catalog routing sources above. **S/D**

## System inventory

### 1. Private executable workspace over shared history

What is shared:

- The project base, promoted layer directories, and ordered active history are shared runtime state. A manifest records a version, ordered layer references, and schema version; a root hash is derived from the serialized layer references ([model](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/model/mod.rs)). **S**
- Session creation first acquires a LayerStack snapshot and then opens a workspace over that lease ([create service](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/service/impls/create_workspace.rs), [lifecycle create](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/lifecycle/create.rs)). **S**
- The host checkout is copied into the initial base layer; it is not used as the agents' shared mutable working directory ([base build](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/workspace_base/build.rs), [base layer copy](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/workspace_base/layer.rs)). **S**

What is private:

- Each session gets fresh run, upper, and work directories ([overlay directories](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/dirs.rs)). The Linux overlay mounts shared read-only lowers with that private upper/work pair ([kernel mount](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/overlay/src/kernel_mount.rs)). **S**
- A sessionless `exec_command` tool call creates one implicit workspace session with `PublishThenDestroy`; after its command ledger drains, the runtime captures and publishes or rejects the session delta, then destroys the session ([command execution](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/command/service/exec_command.rs), [finalization policy](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/model.rs), [implicit publication tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/layerstack_publish.rs)). **S/T**
- An explicit workspace session can carry private live state across multiple command and file tool calls until `publish_workspace_session` merges its captured delta back or `destroy_workspace_session` discards it ([session catalog](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/runtime/workspace_session.rs), [explicit-session tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session.rs)). **S/T**
- Each session carries user, mount, and PID namespace handles. A separate network namespace exists only for the isolated-network profile; the shared-network profile joins the host network namespace while retaining the other namespace separations ([workspace network model](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/model.rs), [namespace creation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-process/src/holder/namespace.rs)). Commands join user → mount → PID → network handles ([setns sequence](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/namespace-process/src/runner/setns/namespaces.rs)). **S**
- Commands and file operations using the same explicit session ID observe the same live upperdir. Distinct sessions have distinct writable upperdirs. This is workspace isolation, not a formal security proof. **S/O**

The “isolated workspace session per tool call” description is exact for sessionless `exec_command`, not for every runtime operation. A sessionless `file_read` projects the current LayerStack without a session, and sessionless `file_write`/`file_edit` amend the current head directly through one-layer operations ([read](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/read.rs), [write](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/write.rs), [edit](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/service/impls/edit.rs)). **S**

The implementation uses the Linux overlay and namespace APIs; non-Linux overlay mounting returns unsupported ([kernel mount fallback](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/overlay/src/kernel_mount.rs)). No v1 claim should be made for Windows overlay execution, reflink cloning, universal egress denial, or process-state rollback. **O**

### 2. Snapshot leases and compaction

- A lease captures the exact manifest value and the resolved ordered layer paths ([LayerStack and Lease](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/mod.rs)). **S**
- Releasing a lease removes a candidate layer only when it is absent from both the active manifest and every remaining lease ([lease cleanup](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/cleanup.rs)). **S**
- Squash plans compactable runs around the base and live-lease boundaries, builds replacements outside the writer lock, then rechecks and commits under an exclusive lock ([squash implementation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/squash.rs)). Replacement acquisition pins a substituted layer before the superseded lease is released ([lease rewrite](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/rewrite.rs)). **S**
- Tests cover lease boundaries, GC safety, racing publication, abort/crash shapes, and retention until the last lease releases ([squash tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/unit/squash.rs)). **T**

Bounded claim: leases preserve the captured logical snapshot and constrain compaction/garbage collection. They do not forbid all compaction while a session exists, and the audited code does not justify calling the protocol serializable snapshot isolation. The lease/substitution registries are in memory; daemon-restart ordering should be fault-tested before a broad crash-recovery claim. **S/E**

### 3. Capture

- Capture walks only the private overlay upperdir and interprets kernel overlay metadata for deletions and opaque directories. It emits regular-file writes, directories, symlinks, deletes, and opaque-directory changes; unsupported special entries and invalid paths are reported as protected drops ([capture implementation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/capture.rs)). **S**
- Tests distinguish genuine kernel whiteouts and opaque markers from literal `.wh.*` filenames and cover unsupported/non-UTF-8 entries ([capture tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/tests/unit/overlay_capture.rs)). **T**
- Explicit publication serializes capture with command admission, requires no active command, and restores the session to active state after a precommit capture or publication failure ([explicit publish service](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/impls/publish_session.rs)). **S**

An unresolved semantic asymmetry needs a maintainer decision: explicit session publication rejects every protected capture drop, whereas generic LayerStack planning permits an unsupported-special-file drop while retaining safe changes ([explicit drop gate](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/impls/publish_session.rs), [publish planner](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/plan.rs)). Confirm whether implicit and explicit policies are intentionally different. **E**

### 4. Conflict-aware merge/reject

- Planning checks the caller's base revision, protects runtime-owned paths, classifies source versus ignored changes, and expands opaque directories within a configured bound ([publish plan](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/plan.rs), [route policy](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/route.rs)). **S**
- Under the writer lock, every change resolves or one structured rejection aborts the whole data changeset; no resolved subset is published ([resolver](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/resolve.rs)). **S**
- Source paths compare a fingerprint from the leased base with the active head. Divergent exact-file writes can invoke a line-oriented three-way text merge; structural differences, conflicting edits, binary/invalid UTF-8 input, and files above the 8 MiB merge bound reject ([resolver](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/resolve.rs), [merge implementation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/merge.rs)). **S**
- Tests cover disjoint concurrent publication, stale structural conflicts, all-or-none rejection, binary divergence, and retryable structured merge conflict ([LayerStack publish tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/unit/publish.rs), [explicit publication tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session_publish.rs)). **T**

“Conflict-aware” in the paper must mean these exact fingerprint, structure, protected-path, and bounded text-merge rules. A clean publication is not evidence of semantic conflict-freedom or test correctness. **O**

### 5. Atomic durable publication and its boundaries

- Publication plans outside the writer lock, rereads and resolves against the active manifest under the exclusive lock, writes a staged layer, syncs it, renames it into the layer directory, writes its digest, rechecks the active manifest, prepends the layer, and atomically replaces the manifest ([publish operation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs), [atomic file helper](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/storage/fs.rs)). **S**
- After success, the durable data state is the promoted layer/digest plus the active manifest reference to it. Layer-byte accounting is written best-effort after commit. Audit attribution is also appended after the data commit and is explicitly best-effort; it can resolve to `unknown` ([publish service](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/layerstack/service/impls/publish_changes.rs), [audit implementation](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/file/audit.rs)). **S**
- Session cleanup is a later, fallible phase. If publication commits but destruction fails, the layer remains durable and the session reports partial success/finalize failure; tests prevent retry from duplicating the committed layer ([explicit publication lifecycle tests](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session_publish.rs)). **S/T**

The defensible paper claim is **atomic durable data publication of one resolved changeset at the manifest visibility boundary**. Do not claim that data, attribution, accounting, and cleanup form one transaction, or make a generic cross-platform crash-durability claim: directory sync is a no-op on Windows in the audited helper. **S/O**

### 6. Lifecycle and observability

- Explicit CLI-created sessions use no automatic finalization; implicit command sessions use publish-then-destroy after the final command ([session model](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/model.rs)). **S**
- Explicit publication retains a rejected/precommit-failed session for retry and closes it only after commit/no-op; destruction is separately exposed ([runtime session catalog](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-operations/catalog/src/runtime/workspace_session.rs), [publish service](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/src/workspace_session/service/impls/publish_session.rs)). **S**
- The read-only observability catalog exposes aggregate or sandbox views without placing mutation operations in that client; exact operations and scopes are recorded in `cli_contract_matrix.md`. This is a role-specific interface and reduces accidental exposure, not by itself an authorization or security boundary. **S/O**

## Public documentation inventory and trust level

| Page | Useful description | Paper treatment |
|---|---|---|
| [Architecture](https://ephemeral-sandbox.com/architecture) | Layer history, leased snapshot, private overlay, publish/reject pipeline | Framing/diagram source; re-prove each behavior from tagged code and tests. |
| [LayerStack](https://ephemeral-sandbox.com/architecture/layerstack) | Newest-first history, leases, publish, squash | Do not reuse live performance figures. |
| [Overlay mount](https://ephemeral-sandbox.com/architecture/overlay-mount) | Shared lowers, private upper/work, capture | Public description; Linux support boundary agrees with source. |
| [Namespace runtime](https://ephemeral-sandbox.com/architecture/namespace-runtime) | Holder and one-operation runner pattern | Public description; network isolation is optional. |
| [Workspace coordination](https://ephemeral-sandbox.com/architecture/workspace-coordination) | Capture → plan → lock/resolve → commit/attribute | Useful system narrative, but it elides the best-effort attribution boundary found in source. |
| [Squash/remount](https://ephemeral-sandbox.com/architecture/squash-remount) | Background compaction and remount description | Do not use its observed timings without frozen-run provenance. |
| [CLI overview](https://ephemeral-sandbox.com/docs/cli) and [management](https://ephemeral-sandbox.com/docs/cli/management), [runtime](https://ephemeral-sandbox.com/docs/cli/runtime), [observability](https://ephemeral-sandbox.com/docs/cli/observability) | Current public commands and shell contracts | Known operation-count drift; not the v1-freeze contract. |
| [Publish/export guide](https://ephemeral-sandbox.com/docs/guides/publish-and-export) | Operator workflow | Background only; exact semantics come from source/tests. |
| [Operation reference](https://ephemeral-sandbox.com/docs/reference/operations) | Catalog concepts | Regenerate from final tag. |

### Operating-system and worktree framing sources

These sources support the problem model, not an empirical claim that native operating systems fail at a particular agent count:

| Primary source | Source-proven primitive | Paper-safe inference |
|---|---|---|
| Linux [`rename(2)`](https://www.man7.org/linux/man-pages/man2/rename.2.html) | Atomic pathname replacement with existing open descriptors continuing to reference their objects. | Per-path atomicity does not create an atomic multi-file coding changeset or agent publication boundary. |
| Linux [`flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html) | Advisory file locks. | Locks coordinate agents only when every participating tool follows the same application protocol. |
| Linux [`inotify(7)`](https://man7.org/linux/man-pages/man7/inotify.7.html) | Filesystem event queues can overflow and report `IN_Q_OVERFLOW`. | Native filesystem watching should not be treated as a lossless coordination or audit ledger. |
| Linux [OverlayFS](https://docs.kernel.org/filesystems/overlayfs.html) | Copy-up, whiteout, opaque-directory, and upper/work-directory rules. | Unique session upper/work directories and faithful capture are correctness requirements; OverlayFS alone does not supply shared version history or publication semantics. |
| [Git worktree](https://git-scm.com/docs/git-worktree) | Distinct working trees share repository state. | Worktrees reduce direct file overwrite but do not define service ownership, current-head reconciliation, verification ordering, or agent-level attribution. |

The paper should say that conventional operating systems expose human/application-oriented process, file, lock, and resource primitives but lack a first-class coding-agent workspace-session and publication abstraction. Avoid the broader historical claim that operating systems were built only for humans or are generally “incompetent.”

## Interface inventory summary

At the baseline commit the three source projections expose:

- 8 system-scoped management operations;
- 10 sandbox-required runtime operations;
- 8 read-only observability operations, of which `snapshot` and `resources` accept system or sandbox scope and the remaining six require sandbox scope.

The exact operation matrix, CLI usage, mutation status, routing scope, help derivation, request correlation, connection/token discovery, JSON streams, and exit codes are in [`cli_contract_matrix.md`](./cli_contract_matrix.md), with the projection files as primary evidence.

## Test inventory: do not mix evidence classes

### CLI/interface contract tests

These test the adapter contract, not isolation or publication:

- Catalog/projection completeness and uniqueness: [`projection_integrity.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/projection_integrity.rs).
- Catalog-derived help/search: [`help.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/help.rs).
- Manager operation set, system scope, JSON/progress streams, and errors: [`manager.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/manager.rs).
- Runtime selector, explicit request ID, JSON and exit behavior: [`runtime.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/runtime.rs), [`request_builder.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/request_builder.rs).
- Observability aggregate/scoped routing and rejection of other authority sets: [`observability.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/observability.rs).
- Compatibility fixtures and unknown-operation behavior: [`compatibility.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-cli/tests/compatibility.rs).

### Runtime correctness tests

- Capture semantics: [`workspace/tests/unit/overlay_capture.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/tests/unit/overlay_capture.rs).
- OCC, merge/reject, all-or-none data changeset, and no-op behavior: [`layerstack/tests/unit/publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/unit/publish.rs).
- Explicit publish, retry, commit-versus-cleanup partial success, and admission serialization: [`operation/tests/workspace_session_publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/workspace_session_publish.rs).
- Implicit capture/publish/destroy sequencing: [`operation/tests/layerstack_publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/operation/tests/layerstack_publish.rs).
- Lease-constrained squash and GC: [`layerstack/tests/unit/squash.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/unit/squash.rs).

The six-thread disjoint-publication test is correctness evidence, not a throughput or concurrency-ceiling measurement.

### Checks run during this audit

- The source checkout remained clean at `b22862550e0a7cb4fe61ce581831e9244cc492b5`; `paper-v1-freeze` was absent.
- On Windows, 50 distinct CLI contract tests passed across compatibility, help, manager, runtime, observability, projection integrity, and request building. Two exact-fixture comparisons were observed to fail solely because generated output used LF while checked-in fixtures used CRLF: the compatibility aggregate and the management catalog-help snapshot. The analogous runtime and observability snapshot tests were then skipped while all of their other tests ran. The semantic strings, JSON, and exits in the observed diffs matched; no source file was changed.
- The Windows-compatible LayerStack unit subset passed 27 tests. The publication and squash modules are gated by `cfg(unix)`, so this run did not validate those mechanisms.
- The workspace runtime test target did not compile natively because `sandbox-observability-telemetry` imports non-Windows `rustix::fs`. Ubuntu WSL was present but had no Rust toolchain, so Linux-only capture, publication, squash, and operation tests were not rerun in this audit.
- Both abstract drafts in [`paper_story.md`](./paper_story.md) are within the requested 150–200 words (184 and 193 by the current audit's tokenization), and every relative Markdown link in the six maintained paper documents resolves locally.

These checks do not replace the required frozen Linux test run. The final artifact should archive exact test commands, full logs, OS/kernel/filesystem, toolchain, and binary digests.

## Source-derived complexity inventory

The stage-by-stage derivation and symbols are maintained in [`complexity_and_evolution.md`](./complexity_and_evolution.md). The source supports the following cost-driver statements, but no performance conclusion:

- Lease acquisition clones the active manifest and resolves every layer path; the in-memory registry retains one full manifest per lease ([`stack/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/mod.rs), [`lease/registry.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/registry.rs)). **S**
- Overlay creation validates, opens, and configures each lower layer; direct merged-view reads scan layers newest-first ([`kernel_mount.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/overlay/src/kernel_mount.rs), [`projection/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/projection/mod.rs)). **S**
- Capture walks the private upperdir, sorts each directory, and retains metadata/source-path references rather than copying regular-file payload into memory ([`capture.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/capture.rs)). **S**
- Validated publication holds the exclusive writer guard across current-head resolution, merge, regular-file hashing/copy/sync, promotion, and manifest replacement ([`ops/publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs), [`layer/write.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/layer/write.rs)). This motivates writer wait/hold measurement; it does not prove a bottleneck. **S/E**
- Text merge admits at most 8 MiB per input but stores a Myers frontier trace whose memory still depends on line count and edit distance ([`merge.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/merge.rs)). Adversarial CPU/RSS characterization or a tighter implementation bound is required. **S/E**
- Squash hardlinks regular-file winners, while lease boundaries constrain eligible blocks and lease release retains layers referenced by active history or any other lease ([`squash.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/squash.rs), [`flatten.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/squash/flatten.rs), [`lease/cleanup.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/cleanup.rs)). **S**

## Experimental and writing assets

### In the v1 source repository

- [`.github/workflows/benchmark-boundary.yml`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/.github/workflows/benchmark-boundary.yml) keeps the benchmark lab outside the runtime repository.
- [`config/bench.yml`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/config/bench.yml) is a benchmark configuration template, not a result.
- [`occ_merge_bench.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/tests/occ_merge_bench.rs) is an ignored experimental harness. Its own comments distinguish directly measured scenarios from modeled scenarios; no number from it is paper-ready without a frozen rerun and raw artifact.
- No LaTeX manuscript, BibTeX database, or paper-ready result bundle was found in this checkout.

### In the paper folder

- [`progress.md`](./progress.md) is the current readiness and execution tracker, including parallel manuscript/source/benchmark/evidence lanes and synchronization gates.
- [`paper_skeleton.md`](./paper_skeleton.md) maps the planned manuscript sections to claims, source evidence, experiments, figures/tables, work packages, dependencies, and completion gates.
- [`paper_story.md`](./paper_story.md), [`claim_evidence_map.md`](./claim_evidence_map.md), [`complexity_and_evolution.md`](./complexity_and_evolution.md), and [`cli_contract_matrix.md`](./cli_contract_matrix.md) are the current story, evidence, cost-model, and interface sources for that skeleton.

### External benchmark/test repository

The sibling checkout `ephemeral-sandbox-test` was clean at commit [`d45618733c8bfe75466947fdb9c47bea67f74b78`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-test/tree/d45618733c8bfe75466947fdb9c47bea67f74b78). Its [`benchmark/README.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-test/blob/d45618733c8bfe75466947fdb9c47bea67f74b78/benchmark/README.md) describes an external lab; [`concurrency-scaling.yml`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-test/blob/d45618733c8bfe75466947fdb9c47bea67f74b78/benchmark/presets/concurrency-scaling.yml) and [`publication.yml`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-test/blob/d45618733c8bfe75466947fdb9c47bea67f74b78/benchmark/presets/publication.yml) are protocols, not results.

The deterministic ten-lane FlashCart demo and its recorded runs under [`demo/multi-agent`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-test/tree/d45618733c8bfe75466947fdb9c47bea67f74b78/demo/multi-agent) predate the paper freeze. They may inform workload design, but every current run is **exploratory** until reproduced with the final source commit, exact binaries/images, environment, command line, seeds, raw event log, and analysis version.

The sibling `ephemeral-sandbox-layerstack-2-experiment` checkout was clean on `windows_experiment` at commit [`6e486fca75cf3afebd091f5ba8a2e48e77d9d05e`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/tree/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e). Its [`README.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/README.md) and [`EXPERIMENT.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/EXPERIMENT.md) preregister a single-storage-domain/reflink candidate and A/B/C acceptance protocol; pending tables and thresholds are not results. The pinned stock Windows Docker Desktop/WSL 2 feasibility run failed direct `FICLONE` with `errno=95`, so A-Windows failed and B-Windows remained blocked ([`CONCLUSION.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/CONCLUSION.md), [sealed report](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/reports/20260719T100800Z-x86_64-6af011f4-s0001.md)). This is future-work and narrow negative feasibility evidence, not a v1 capability or a universal Windows result.

## Required final-freeze checklist

Before a source claim or number enters the paper:

1. Create the annotated `paper-v1-freeze` tag and record its exact commit, tag object, source-tree status, Rust toolchain, lockfile digest, and build command.
2. Regenerate the CLI catalog/help from that tag and diff it against this matrix and the public site.
3. Replace every baseline source link in the paper artifacts with the final commit link.
4. Run and archive the separated CLI-contract and runtime-correctness test suites.
5. Record for every experiment: source commit/tag, benchmark-repository commit, OS/kernel/filesystem, hardware, cgroup/runtime configuration, compiler/toolchain, binary and container/image digests, command line, environment variables, workload commit, seeds/repeats, raw event data, exclusions, and analysis-code commit.
6. Label pre-freeze scripted data exploratory; do not combine it with final measurements.
7. Re-audit attribution wording, explicit-versus-implicit protected-drop policy, and restart/lease recovery.
8. Re-verify every 2026 preprint version and every sentence-level citation immediately before submission.

## Present evidence gaps

- Missing source freeze: no `paper-v1-freeze` tag.
- Missing paper-ready measurements: isolation matrix, publication/fault matrix, latency/resource scaling, and multi-agent workflow comparison.
- Missing source-derived cost validation: no frozen measurements yet test the predicted layer-depth, live-lease, upperdir-entry, changed-path/byte, merge-shape, writer-queue, or retained-history terms.
- Missing formal boundary: no proof of sandbox security, serializability, semantic merge correctness, universal egress denial, or cross-platform durability.
- Attribution is not transactionally coupled to data publication.
- Restart ordering for in-memory leases/substitutions needs explicit fault testing.
- Claim Plane's full design needs a deeper sentence-level audit because of strong novelty overlap.
