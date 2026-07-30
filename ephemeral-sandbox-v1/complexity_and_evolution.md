# Ephemeral Sandbox v1 complexity, limitations, and evolution targets

Status date: 2026-07-30. This is a source-derived cost model, not a performance result. Every v1 link points to the initial baseline commit [`b22862550e0a7cb4fe61ce581831e9244cc492b5`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/b22862550e0a7cb4fe61ce581831e9244cc492b5); all links and bounds must be rechecked against the annotated `paper-v1-freeze` tag. The LayerStack 2.0 material is a separate migration experiment at commit [`6e486fca75cf3afebd091f5ba8a2e48e77d9d05e`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/tree/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e), not evidence for a v1 capability.

## Why the paper needs a cost model

The paper should not present one context-free “time complexity” or “space complexity” for the runtime. A workspace session is a pipeline whose stages scale with different quantities, and the operating system/filesystem contributes workload-dependent latency and physical allocation. The defensible paper treatment is therefore:

1. state a source-derived operational cost model;
2. identify the terms that may limit concurrency;
3. measure those terms over controlled worker, layer-depth, path-count, payload, and conflict grids; and
4. distinguish measured behavior from future mechanisms intended to change a term.

## Symbols

| Symbol | Meaning |
|---|---|
| \(L\) | Number of layers in the manifest used by an operation. |
| \(S\) | Number of live leased sessions. |
| \(U\) | Number of entries in one private overlay upperdir. |
| \(C\) | Number of captured or accepted changes in one publication. |
| \(F\) | Number of source paths fingerprinted or structurally validated, including expanded descendants. |
| \(B_u\) | Logical regular-file bytes present in the private upperdir. |
| \(B_p\) | Logical regular-file bytes written into a published layer. |
| \(n\) | Total line count in one pair of files passed to the line-diff routine. |
| \(D\) | Edit distance reached by the Myers-style line diff. |
| \(K\) | The implementation cap \(\min(n, 200{,}000)\) used by that diff. |
| \(Q\) | Concurrent publications waiting for the single LayerStack writer. |
| \(R\) | Total layer references held across live lease manifests, \(\sum_{i=1}^{S} L_i\). |
| \(E\) | Filesystem extent count relevant to a future reflink clone. |

Logical bytes are not physical allocated bytes. Compression, sparse files, page cache, filesystem metadata, OverlayFS copy-up behavior, and extent sharing can make them differ. Any storage result must record both logical and allocated/shared/exclusive bytes.

## Source-derived v1 cost model

| Stage | Time driver visible in source | Live or peak space driver | Evidence status and measurement need |
|---|---|---|---|
| Acquire lease and create session | Reading/cloning the manifest and resolving its layer paths are \(O(L)\). Overlay setup validates and opens every lower layer and submits one lowerdir per layer, also making its userspace setup \(O(L)\); kernel mount latency is not assigned an asymptotic guarantee. | The registry stores a cloned manifest for each lease and the returned session retains a manifest plus resolved paths, giving \(O(L)\) metadata per session and \(O(R)\), commonly \(O(SL)\), across similarly deep live sessions. Fresh upper/work directories do not copy the whole project at creation. | Source-proven structure: [`stack/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/mod.rs), [`lease/registry.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/registry.rs), [`kernel_mount.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/overlay/src/kernel_mount.rs), and [`create.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/lifecycle/create.rs). Measure start latency and daemon/session memory over \(S\) and \(L\). |
| Execute and read through the layered view | A direct LayerStack path lookup probes layers newest-first and is \(O(L)\) in the miss or oldest-winner case, plus bytes read for a file. Kernel OverlayFS execution-path lookup behavior is filesystem/kernel dependent and must be measured rather than inferred from this userspace reader. | Private writes and kernel copy-up consume upper/work storage. The logical session footprint is change-dependent rather than an eager full-project copy, but a modified lower file may materialize a full logical file in the upper; physical allocation is kernel/filesystem dependent. | Source-proven userspace lookup: [`projection/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/projection/mod.rs). Measure read/build/test latency and upper/work allocation over layer depth, file size, edit shape, and filesystem. |
| Capture private changes | Capture visits all upperdir entries and sorts each directory before emitting changes. Its comparison work is \(O(\sum_j d_j \log d_j)\) for per-directory entry counts \(d_j\), in addition to \(O(U)\) metadata, path, xattr, and symlink work. It does not read regular-file payload bytes. | It retains one pending/emitted record per captured entry plus per-directory lists, so metadata memory is \(O(U)\); regular-file payload remains on disk and is referenced by source path. | Source-proven: [`capture.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/workspace/src/overlay/capture.rs). Measure capture latency and RSS over entry count, directory fan-out, path depth, xattrs, and \(B_u\). |
| Plan and validate publication | Manifest hashing is \(O(L)\). Each changed path is routed; source paths are fingerprinted against a layered view, so worst-case metadata probes grow with \(F \times L\), plus bytes hashed for regular files. Gitignore routing rebuilds matchers along path ancestors, making path depth and ignore-file size additional factors. Opaque-directory expansion is rejected beyond 4,096 descendants. | Fingerprints, accepted changes, and validations scale with \(C+F\), plus bytes loaded while fingerprinting. Opaque expansion is explicitly bounded at 4,096 descendants. | Source-proven drivers: [`model/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/model/mod.rs), [`plan.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/plan.rs), [`fingerprint.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/fingerprint.rs), [`gitignore.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/gitignore.rs), and [`opaque_dir.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/opaque_dir.rs). Measure path-count, depth, ignore-tree, and layer-depth sweeps. |
| Resolve a text conflict | Each of base, active, and command inputs must be text and at most 8 MiB. For a pair with \(n\) total lines and edit distance \(D \le K\), the Myers-style routine has data-dependent \(O(nD)\) comparison time; because this implementation clones an \(O(K)\) frontier for each retained distance level, trace space is \(O(KD)\). If it reaches the cap, the source-level envelope approaches \(O(nK)\) time and \(O(K^2)\) trace space before falling back to whole-file delete/insert operations. | File bytes, split-line vectors, edit operations, regions, output, origins, and the retained diff trace are live during reconciliation. The 8 MiB byte limit does not by itself make the line-count trace small. | Algorithm and limits are source-proven in [`merge.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/merge.rs) and [`resolve.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/publish/resolve.rs). The practical envelope and adversarial safety require stress tests; do not describe merge as simply linear or safely bounded by 8 MiB. |
| Commit publication | Accepted changes are path-aggregated through a `BTreeMap`, giving \(O(C \log C)\) ordering work. Regular-file bytes are hashed, copied into staging, and synced, giving at least \(O(B_p)\) byte processing; the new manifest clones and serializes the prior \(L\) references. Current-head resolution, merge, payload hashing/copy, sync, promotion, and manifest replacement all run while the exclusive writer guard is held. | A live session can retain its upper payload while staging/final publication retains another logical copy. Peak logical data therefore includes \(B_u+B_p\) plus history and metadata; actual allocation requires measurement. Each successful publish prepends one manifest layer, so unsquashed manifest metadata grows by one layer per publication. | Source-proven data path and critical section: [`ops/publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs), [`layer/write.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/layer/write.rs), [`model/mod.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/model/mod.rs), and [`storage/fs.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/storage/fs.rs). Measure writer-lock hold/wait separately from plan, bytes, sync, and end-to-end publication over \(Q,C,B_p,L\). |
| Squash and lease-aware garbage collection | Squash planning scans the manifest and lease boundaries. Building walks directory entries across eligible layers outside the writer lock; regular-file winners are hardlinked rather than byte-copied. Commit briefly rechecks runs, promotes staged layers, syncs, and replaces the manifest under the writer lock. Lease release constructs retained sets from all live lease manifests, so its metadata work and temporary space grow with \(R\), then it deletes only layers referenced by neither active history nor another lease. | Squash stages replacement directory metadata while old layers remain. Hardlinks avoid a second regular-file payload copy within the same filesystem, but active leases can retain otherwise obsolete layers and therefore raise peak storage until release. | Source-proven structure: [`squash.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/squash.rs), [`flatten.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/squash/flatten.rs), [`lease/registry.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/registry.rs), and [`lease/cleanup.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/lease/cleanup.rs). Measure build/commit/GC separately over layer count, entry count, session count, lease age, and retained bytes. |

## Concurrency implications

The private execution phase is intentionally parallel, but the durable head transition is intentionally serialized. Consequently, a plausible v1 saturation mechanism is not merely CPU or model throughput: as \(Q\), \(B_p\), \(F\), or merge work grows, wait time can accumulate behind an exclusive section that includes reconciliation and durable payload work. This is a source-supported hypothesis from [`publish_validated_changes`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs), not a measured queueing result.

Layer depth is another cross-cutting term: it affects session metadata/setup, worst-case userspace path lookup, fingerprinting, manifest hashing/serialization, and per-lease metadata. Squash reduces eligible depth, but lease boundaries can preserve older runs and long-lived sessions can delay reclamation. The paper should therefore report concurrency curves jointly with layer depth and lease age instead of treating worker count as the only independent variable.

## Limitations exposed by the model

1. **Publication serialization can become the integration bottleneck.** Atomic head movement requires serialization, but v1 holds the writer guard during potentially expensive active-head validation, merge, hashing, copying, syncing, and manifest work. Whether this dominates is workload- and storage-dependent and must be measured.
2. **v1 publication is byte-moving.** Regular-file `WriteFile` changes use `std::fs::copy`, so small logical edits to large copied-up files can make publication cost scale with the resulting file size rather than the edited byte range. Physical allocation may be smaller on some filesystems, but no such optimization is a v1 contract.
3. **Live-lease metadata is depth-multiplied.** The in-memory registry stores a full manifest per lease, producing \(O(R)\) metadata and making session-count scaling sensitive to history depth.
4. **Path validation repeatedly traverses layered history.** Source fingerprinting, ignore routing, and structural validation can repeat layer probes and file reads across changed paths.
5. **The current merge resource bound is incomplete.** The 8 MiB input limit bounds file bytes but the retained Myers trace can still grow pathologically with line count and edit distance. Merge needs an adversarial CPU/RSS test and likely a stricter resource design before it can be described as robustly bounded.
6. **Leases trade consistency for retention.** They protect session-visible history and constrain squash/GC, but long-lived sessions can retain obsolete layers and increase physical storage.
7. **Physical storage complexity is filesystem-specific.** Logical bytes alone cannot establish copy-on-write savings, sparse behavior, page-cache cost, or extent sharing.
8. **This cost model does not imply a universal agent ceiling.** Model quality, task dependencies, semantic conflicts, verification, orchestration, and physical resources can dominate before or after these runtime terms.

## Next improvement targets

The paper should separate a v1 limitation from an implemented v2 feature. The following are improvement targets, not v1 contributions:

### Target 1: shorten the serialized publication path

Move safely precomputable payload work outside the exclusive writer section, then keep the commit critical section to current-head validation, promotion, and manifest transition. Any design must preserve all-or-none rejection, source-path immutability checks, crash old-or-new visibility, and idempotent retry; the current atomic boundary is evidenced by [`ops/publish.rs`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/blob/b22862550e0a7cb4fe61ce581831e9244cc492b5/crates/sandbox-runtime/layerstack/src/stack/ops/publish.rs).

### Target 2: reduce byte-copy and physical-allocation amplification

The LayerStack 2.0 migration protocol proposes co-locating relevant storage in one filesystem domain and comparing:

- A: the current separated/full-copy layout;
- B: a v2 single-storage-domain control with runtime publication cloning disabled; and
- C: the v2 candidate with reflink required.

Its intended test is whether the candidate lowers allocated storage and publication/copy-up latency while preserving image compatibility, exact file blame, squash, same-upperdir remount, active execution, crash behavior, memory bounds, daemon health, and privilege/security profiles. These are protocol goals in [`README.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/README.md) and [`EXPERIMENT.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/EXPERIMENT.md), not completed product results.

A reflink path should not be called \(O(1)\). Clone time and metadata scale with filesystem and extent structure, approximated by \(E\), while later writes allocate changed extents. Its defensible hypothesis is “replace byte-proportional initial transfer/allocation with extent-sharing behavior on a qualified storage backend,” followed by FIEMAP and allocated/shared/exclusive-byte measurements.

The current Windows result is negative and narrow: on the pinned stock Windows Docker Desktop/WSL 2 cell, direct `FICLONE` on Docker-managed storage returned `errno=95`, so A-Windows failed and B-Windows remained blocked. The migration report recommends capability detection and a correctness-preserving copy fallback, with no Windows reflink storage/performance claim ([`CONCLUSION.md`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/CONCLUSION.md), [sealed report](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox-layerstack-2-experiment/blob/6e486fca75cf3afebd091f5ba8a2e48e77d9d05e/reports/20260719T100800Z-x86_64-6af011f4-s0001.md)).

### Target 3: make metadata scale with shared history rather than session count times depth

Share immutable manifest structures across leases or store compact revision references, while preserving exact layer pinning and restart recovery. The target is to replace duplicated \(O(R)\) live metadata with a representation closer to shared \(O(L)\) history plus \(O(S)\) lease references; this is a design target, not an implemented bound.

### Target 4: bound merge CPU and memory independently

Use a resource-bounded or linear-space diff strategy, add line/edit-distance admission limits, and expose typed “merge resource limit” rejection rather than allowing pathological input to consume unbounded practical CPU/RSS. Preserve the current semantic boundary: a clean textual merge is still not proof of behavioral compatibility.

### Target 5: index repeated layered lookups

Cache or index manifest path resolution, content fingerprints, and parsed ignore rules with revision-keyed invalidation. The goal is to reduce repeated \(F \times L\) probing without weakening current-head validation.

## Required measurements before submission

| Question | Required controlled factors | Required outputs |
|---|---|---|
| Does session start follow the predicted layer/session terms? | \(S\), \(L\), network profile, warm/cold state | phase latency, daemon RSS/PSS, per-session RSS/cgroup memory, FDs, failures |
| Does capture follow upperdir structure rather than project size? | \(U\), fan-out, path depth, file sizes, xattrs, deletes/opaque dirs | capture latency, CPU, peak RSS, metadata/payload bytes read |
| Where is publication time spent? | \(Q\), \(C\), \(F\), \(B_p\), \(L\), conflict class, storage backend | plan time, writer wait, writer hold, resolve/merge, hash, copy, sync, manifest, end-to-end |
| Is merge safely bounded? | bytes, line count, edit distance, similarity, eligible/ineligible inputs | wall/CPU, peak RSS, rejection/outcome, daemon health |
| How much storage does a session/publication consume? | small edits in large files, many small files, sparse/incompressible data, session lifetime | logical, allocated, shared, exclusive, upper/work/staging/layer/history bytes |
| How do leases affect squash and retention? | \(S\), \(L\), lease ages/boundaries, published versions | squash plan/build/commit/GC latency, depth before/after, peak/residual storage |
| Does publication serialization define the measured ceiling? | worker grid and controlled payload/conflict mixes | throughput, writer queue, wait/hold ratio, accepted progress, retries, resource saturation |

## Manuscript placement

- **Implementation:** include a compact operational-complexity table with the symbols and source-derived terms above.
- **Evaluation methodology:** make RQ3 test the predicted variables, not just a generic worker-count sweep.
- **Results:** report observed scaling and identify which term becomes limiting under each workload; never substitute asymptotic notation for measurements.
- **Limitations and future work:** disclose writer serialization, byte-copy amplification, lease/depth metadata, merge resource risk, Linux/filesystem dependence, and LayerStack 2.0 as a gated candidate evolution path.
- **Abstract and contributions:** do not mention LayerStack 2.0 unless the paper explicitly labels it future work; do not claim reflink savings or improved concurrency without frozen measurements.
