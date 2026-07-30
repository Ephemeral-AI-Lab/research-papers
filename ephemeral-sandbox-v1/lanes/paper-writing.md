# Lane 1: paper writing

Status: **ready to start the evidence-bearing systems core**

This lane turns frozen or clearly provisional evidence into manuscript text. It can advance before performance and multi-agent results exist, but it must not convert hypotheses, test source, public product descriptions, or exploratory runs into demonstrated results.

## Objective

Produce an arXiv-ready systems manuscript whose claims remain synchronized with the source snapshot, correctness evidence, experiment artifacts, and explicit limitations.

The central method statement is:

> **One durable project truth, many private executable sessions, controlled publication.**

## Inputs

- [`PRD.md`](../PRD.md) — scope, required structure, evidence rules, and submission criteria.
- [`paper_story.md`](../paper_story.md) — provisional title, thesis, abstracts, introduction opening, contributions, and claim boundaries.
- [`paper_skeleton.md`](../paper_skeleton.md) — section plan, RQs, figures/tables, work packages, and blockers.
- [`project_inventory.md`](../project_inventory.md) — source, tests, public documentation, and evidence trust levels.
- [`claim_evidence_map.md`](../claim_evidence_map.md) — claim IDs, evidence status, required qualifiers, and missing evidence.
- [`cli_contract_matrix.md`](../cli_contract_matrix.md) — source-derived operational interface.
- [`references/related_work.md`](../references/related_work.md) — literature metadata, differentiation, citation safety, and novelty risks.
- [`experiments.md`](./experiments.md) — experiment-lane protocol, freeze, run, and handoff contract.

## What can be written before final experiments

These sections can be drafted from the baseline source and existing evidence inventory, with every source link marked provisional until `paper-v1-freeze`:

1. Problem statement and system model.
2. Goals, non-goals, and threat-model boundary.
3. Design overview.
4. LayerStack and workspace-session design.
5. Capture and conflict-aware publication.
6. Lifecycle and partial-failure semantics.
7. Operational interface and CLI contract.
8. Implementation organization and platform boundary.
9. Provisional evaluation methodology.
10. Related-work structure and bounded differentiation.
11. Limitations that are already source-proven.

## What remains gated

Do not finalize these parts until the experiment lane reaches evidence lock:

- numerical Results;
- performance, resource, or useful-work claims;
- statements that Ephemeral raises the concurrency ceiling;
- final contribution wording;
- final result figures and tables;
- final Introduction and Conclusion;
- final title and Abstract.

Working drafts may contain `[MEASURED RESULT NEEDED]` or equivalent visible markers. They must never contain invented numbers.

## Phased writing plan

The paper lane has eight phases. PW0–PW3 can start from baseline source evidence. PW4 partially depends on experiment protocol lock. PW5–PW7 depend on frozen experimental evidence.

### Phase status

| Phase | Manuscript work | Status | Entry gate |
|---|---|---|---|
| PW0 | Scaffold and terminology | Ready | Story and skeleton available |
| PW1 | Sections 2–3: goals/non-goals and system model | Ready | Baseline source inventory |
| PW2 | Sections 4–5: workspace execution and publication | Ready | C1/C2 design evidence |
| PW3 | Sections 6–7: lifecycle, implementation, and CLI | Ready | C3/C4 design evidence |
| PW4 | Section 8 methodology; Section 9 related work and source limitations | Partially ready | Protocol lock for Evaluation Methodology |
| PW5 | Section 8 results and measured failure analysis | Blocked | Evidence lock |
| PW6 | Sections 1 and 10; final framing synthesis | Blocked | PW5 complete |
| PW7 | Whole-paper review, build, and packaging | Blocked | Complete manuscript and verified citations |

### PW0. Manuscript scaffold and vocabulary

**Execution prompt:** [`prompts/pw0.md`](./prompts/pw0.md)

**Writes or creates:**

- `main.tex`;
- `sections/01-introduction.tex`;
- `sections/02-goals-nongoals.tex`;
- `sections/03-system-model.tex`;
- `sections/04-workspace-execution.tex`;
- `sections/05-capture-publication.tex`;
- `sections/06-lifecycle-recovery.tex`;
- `sections/07-implementation-interface.tex`;
- `sections/08-evaluation.tex`;
- `sections/09-limitations-related-work.tex`;
- `sections/10-conclusion.tex`;
- `references.bib` location and reproducible build command.

**Work:**

- establish arXiv `cs.OS` metadata and package layout;
- define canonical terms: LayerStack, manifest, lease, session, base, head, capture, changeset, publication, rejection, and useful work;
- add section inputs without writing numerical claims;
- add visible figure/table placeholders tied to [`paper_skeleton.md`](../paper_skeleton.md).

**Complete when:** the empty manuscript builds reproducibly and every planned section has one source file and stated purpose.

### PW1. Foundations

**Execution prompt:** [`lanes/prompts/pw1.md`](./prompts/pw1.md).

**Writes:**

- **Section 2 — Goals, Non-goals, and Threat-model Boundary** in `sections/02-goals-nongoals.tex`.
- **Section 3 — System Model and Invariants** in `sections/03-system-model.tex`.

**Section 2 content:**

- private execution and controlled integration goals;
- correctness, durability, lifecycle, and orchestration goals;
- formal-security, universal egress, process rollback, semantic merge, general coordination, and unsupported-platform non-goals;
- exact meaning of workspace OS.

**Section 3 content:**

- project history, active manifest, layers, leases, workspace sessions, captured deltas, and publication outcomes;
- shared, private, durable, and public operational state;
- agent team, exploratory swarm, orchestrator, and worker;
- useful-work definition and workload-dependent concurrency ceiling;
- four core design invariants.

**Evidence:** M0–M6 for framing; C1–C4 and D1–D9 for entities and invariants.

**Complete when:** a reviewer can answer what is shared, what is private, which state is durable, and which claims remain hypotheses.

### PW2. Core runtime design

**Writes:**

- **Section 4 — Workspace Execution** in `sections/04-workspace-execution.tex`.
- **Section 5 — Capture and Publication** in `sections/05-capture-publication.tex`.

**Section 4 content:**

- LayerStack projection and base selection;
- lease acquisition and snapshot stability;
- shared lowers and private upper/work directories;
- implicit command sessions and explicit multi-call sessions;
- holder/runner namespace execution;
- network-profile and sessionless-file-operation qualifiers.

**Section 5 content:**

- OverlayFS capture semantics;
- writes, deletes, symlinks, empty/opaque directories, and whiteouts;
- planning, current-head validation, path fingerprints, and protected paths;
- eligible bounded text merge;
- binary, oversized, structural, and conflicting rejection;
- stage, sync, promote, and atomic active-manifest transition;
- exact boundary between atomic data publication and later audit/cleanup.

**Evidence:** C1, C2, D1–D8 and their named source/tests.

**Complete when:** the section explains the full private-session-to-durable-head path without implying semantic correctness or a larger transaction than the source implements.

### PW3. Lifecycle, implementation, and operational interface

**Writes:**

- **Section 6 — Lifecycle and Recovery** in `sections/06-lifecycle-recovery.tex`.
- **Section 7 — Implementation and Operational Interface** in `sections/07-implementation-interface.tex`.

**Section 6 content:**

- publish, reject, retry, discard, no-op, and close behavior;
- precommit versus post-commit failures;
- published-but-not-closed outcome;
- lease-aware squash/GC and remount;
- cancellation, cleanup, restart, and unresolved recovery questions.

**Section 7 content:**

- Rust crate/component map and process boundaries;
- management, runtime, and read-only observability clients;
- source-derived 8/10/8 baseline operation inventory;
- sandbox scope, request IDs, connection/token discovery;
- JSON stdout/stderr and exit-status contracts;
- catalog-derived help;
- operational-interface versus full coordination-plane boundary;
- a compact source-derived operational cost table: layer depth, live leases, upperdir entries, changed paths/bytes, writer serialization, merge resource bounds, and squash/retention;
- Linux/platform assumptions.

**Evidence:** C3, C4, D8–D13, K1–K7, [`cli_contract_matrix.md`](../cli_contract_matrix.md), [`complexity_and_evolution.md`](../complexity_and_evolution.md), and final-tag contract tests when available.

**Complete when:** implementation detail is tied to architectural responsibilities, the paper separates source-derived cost drivers from measured scaling, and reviewers can distinguish CLI contract evidence from runtime correctness evidence.

### PW4. Evaluation plan, related work, and early limitations

**Writes:**

- the **methodology portion of Section 8 — Evaluation** in `sections/08-evaluation.tex`;
- the **related-work and source-proven limitation portions of Section 9** in `sections/09-limitations-related-work.tex`.

**Section 8 methodology content:**

- RQ1–RQ5;
- test platform and provenance contract;
- shared-directory, Git-worktree, and Ephemeral baselines;
- structured-team and exploratory-swarm workloads;
- worker/payload/layer-depth factors;
- live-session/lease-age, upperdir-shape, changed-path, merge-edit-distance, and writer-queue factors derived from the v1 cost model;
- primary and secondary metrics;
- seeds, repeats, stopping rules, uncertainty, and exclusions.

This subsection cannot be considered complete until [`experiments.md`](./experiments.md) reaches protocol lock and `experiment_inventory.md` exists.

**Section 9 early content:**

- related-work categories and source-safe differentiation;
- formal-security, network, process rollback, semantic merge, attribution, platform, and coordination limitations already established by source;
- writer serialization, byte-copy amplification, \(O(R)\) live lease-manifest metadata, repeated layered lookup, merge trace risk, and lease-retained history;
- LayerStack 2.0 as a capability-gated future path rather than a v1 result, including the narrow Windows `FICLONE` failure and required copy fallback;
- novelty-risk discussion for Claim Plane, CAID, CoAgent, DeltaBox, Shepherd, and underlying primitives.

**Complete when:** the evaluation section is an executable protocol rather than a wish list, and every related-work sentence has verified metadata and sentence-level support.

### PW5. Results and measured failure analysis

**Updates:**

- the **results portion of Section 8 — Evaluation** in `sections/08-evaluation.tex`;
- the **measured limitations portion of Section 9** in `sections/09-limitations-related-work.tex`.

**Writes:**

- isolation correctness results;
- publication and fault results;
- latency/resource scaling;
- structured-team and exploratory-swarm useful-work comparisons;
- attribution/recovery findings;
- conflict, retry, integration, verification, selection, and resource cost decomposition;
- negative, mixed, and limiting results.

**Gate:** experiment-lane evidence lock. Every number requires a result ID, raw-data path, analysis path, uncertainty, exclusions, and mapped claim IDs.

**Complete when:** all result prose and numerical assets can be reproduced from frozen artifacts and the observed workload-specific ceiling is stated without universalizing it.

### PW6. Framing synthesis

**Writes or rewrites:**

- **Section 1 — Introduction** in `sections/01-introduction.tex`;
- **Section 10 — Conclusion** in `sections/10-conclusion.tex`;
- final related-work positioning in Section 9;
- final contribution list;
- final title;
- final Abstract.

**Order:**

1. finalize Related Work;
2. rewrite Introduction around demonstrated results and limitations;
3. write Conclusion;
4. choose the final title;
5. rewrite the Abstract last.

**Complete when:** the title, Abstract, Introduction, contributions, Results, limitations, and Conclusion make the same bounded claim.

### PW7. Whole-paper verification and release

**Applies to all sections and assets:**

- terminology and reverse-outline pass;
- claim-to-evidence audit;
- source-link and final-tag audit;
- citation and bibliography verification;
- numeric recomputation;
- figure/table provenance review;
- skeptical systems, novelty, methodology, statistics, and reproducibility review;
- arXiv build, package, and artifact verification.

**Complete when:** the final package builds from recorded inputs and every high-risk objection is resolved or explicitly disclosed.

## Section evidence contract

| Section | Required evidence | Experiment dependency |
|---|---|---|
| Introduction | M0–M6, final contribution evidence, verified citations | Final useful-work and limiting results |
| System model | Source entities, leases, sessions, manifest/publication model | None for initial draft |
| Design | C1, C2, C4 and D1–D9 | Final correctness/fault confirmation |
| Operational interface | C3 and D10–D13 | Final-tag catalog regeneration and contract tests |
| Implementation | Final source paths and platform configuration | Final source freeze |
| Evaluation methodology | Locked RQ1–RQ5 protocol | Protocol lock |
| Results | Raw runs, deterministic analysis, uncertainty, run IDs | Evidence lock |
| Related work | Verified metadata and sentence-level support | Final measured differentiation where used |
| Limitations | Source boundaries plus observed negative/mixed results | Evidence lock for measured limits |
| Conclusion | Only demonstrated contributions and open limits | Evidence lock |

## Writing rules

1. Map every substantive design paragraph to one or more claim IDs.
2. Cite the exact source commit for implementation claims.
3. Distinguish catalog/CLI contract tests from runtime correctness tests and measurements.
4. Use public documentation for framing or diagrams only when source/tests do not establish the claim.
5. Label the Agent Infra Foundation concurrency article as motivation, not empirical proof.
6. Define “atomic,” “durable,” “isolated,” “immutable,” “conflict-aware,” and “attributable” at their exact v1 boundaries.
7. Treat structured teams and exploratory swarms as measured workload families, not universal product categories.
8. Keep process instructions in planning documents, not manuscript prose.
9. Rewrite affected paragraphs whenever the source, protocol, or evidence status changes.
10. Retain negative and limiting results.

## Experiment-lane handoff

The experiment lane must provide, for every result used in prose:

- stable result/run ID;
- source tag/commit and benchmark commit;
- workload and baseline identity;
- model, tools, budgets, worker count, seeds/repeats, and stopping rules;
- metric definition and direction;
- aggregate, uncertainty, and exclusions;
- raw-data and analysis paths;
- exact claim IDs supported or weakened;
- observed limitations and failure cases.

The paper lane must not copy a number from a console, chat, exploratory notebook, or draft table.

## Completion checklist

- [ ] Create `main.tex`, section files, and reproducible build command.
- [ ] Draft System Model and Invariants.
- [ ] Draft Goals, Non-goals, and Threat-model Boundary.
- [ ] Draft LayerStack and Workspace-session Design.
- [ ] Draft Capture and Publication.
- [ ] Draft Lifecycle and Recovery.
- [ ] Draft Operational Interface.
- [ ] Draft Implementation.
- [ ] Draft locked Evaluation Methodology.
- [ ] Draft source-proven Limitations.
- [ ] Create and verify concept figure specifications.
- [ ] Verify scholarly citations and sentence-level support.
- [ ] Replace baseline source links with `paper-v1-freeze`.
- [ ] Write Results from frozen artifacts.
- [ ] Complete skeptical systems/evidence review.
- [ ] Rewrite Introduction, Conclusion, title, and Abstract after evidence lock.
- [ ] Build and validate the arXiv package.

## Definition of done

This lane is complete only when the manuscript builds reproducibly, every technical and numerical claim maps to frozen evidence, citations have sentence-level verification, all placeholders are resolved or explicitly allowed, and no wording exceeds the measured security, performance, platform, or coordination boundary.
