# Submission-stage positioning

## Claim that remains

Ephemeral Sandbox is presented as a source-defined runtime publication protocol
for coding-agent tool calls and explicit workspace sessions.  A private view is
derived from leased LayerStack history; on close or publication, the system
captures a delta, validates it against the active head, and either publishes a
new durable layer or returns a structured rejection.  The contribution is this
bounded composition and operational contract, not a new filesystem primitive,
an agent planner, a universal coordination algorithm, or a semantic merge
theory.

## Distinctions required in the manuscript

- From CAID: the manager/worktree orchestration policy is external here; the
  paper defines runtime capture and publication semantics.
- From CoAgent and Claim Plane: the paper neither keeps all effects live and
  repairable nor performs pre-write task-intent admission.  It isolates a
  session's workspace effects and validates at publication.
- From DeltaBox and Shepherd: there is no claim of complete process-state
  checkpointing, rollback, replay, or reversible execution trace.
- From Palantir and Crystal: awareness or early diagnosis is distinct from
  enforcing a durable publish-or-reject transition.
- From semantic merge work: the bounded text merge is not proof that a clean
  merge is semantically correct.
- From union mounts and optimistic concurrency control: copy-up, validation,
  and restart/abort patterns are established mechanisms.  The manuscript does
  not call its lease behavior serializable snapshot isolation.

## Prohibited novelty and evidence language

Do not say that the system invents isolation, copy-on-write workspaces,
immutable histories, validation before commit, three-way merge, optimistic
concurrency, or multi-agent coordination.  Do not infer throughput, coding-task
success, resource capacity, security, or cross-platform behavior from the
single frozen local treatment.  Cite preprints as preprints and attach their
reported results only to their stated version, workload, and setting.
