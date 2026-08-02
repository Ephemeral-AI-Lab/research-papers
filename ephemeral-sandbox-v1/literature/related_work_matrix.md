# Related-work matrix

| Work family | Private executable state | Durable-state rule | What it does not establish for this paper |
| --- | --- | --- | --- |
| SWE-MiniSandbox and AgentBay | Isolated execution environments or sessions | Environment/session management | Validation of a captured filesystem delta against the current project head. |
| DeltaBox and Shepherd | Checkpoints, rollback, forks, or replayable traces | Reversible agent/environment state | A filesystem-only publication contract or semantic merge guarantee. |
| CAID | Isolated Git worktrees managed by an orchestrator | Commit/merge plus executable verification | An orchestrator-independent runtime protocol for tool-call sessions. |
| CoAgent | Shared mutable state with order-filtered reads and speculative effects | Repair and reordering at quiescence | Private copy-on-write execution followed by publish-or-reject. |
| Claim Plane | Intent-bound execution scope and authority | Admission, fencing, and scope promotion | The operating-system/runtime mechanics of private overlays and capture. |
| Palantir and Crystal | Developer-private branches/workspaces | Awareness and speculative conflict diagnosis | Atomic data publication, structured rejection, or runtime session lifecycle. |
| Verified Three-Way Program Merge | Program variants | Semantic conflict-freedom reasoning | The bounded line-oriented merge in this implementation. |
| Union mounts | Writable upper over shared lower namespace | Copy-up and whiteouts | Leased version history, active-head validation, and multiwriter reconciliation. |
| Optimistic concurrency control | Tentative work | Validation and abort/restart | Filesystem serializability, semantic correctness, or fairness. |

The matrix is intentionally asymmetric.  It identifies established pieces from
which Ephemeral Sandbox composes its design, then confines the paper claim to
the source-defined composition: leased LayerStack history, a private executable
view, captured-delta validation, bounded reconciliation, and one controlled
durable transition.  The paper does not claim ownership of the constituent
mechanisms.
