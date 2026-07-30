# Ephemeral Sandbox v1 — Paper Progress

**Last updated:** 2026-07-30  
**Overall status:** Baseline design, interface, story, related-work, and source-derived complexity audits are complete; the PW0 LaTeX scaffold exists, but its local build and all frozen evaluation evidence remain pending.
**Submission gate:** Not ready for arXiv.

Use this tracker as the authoritative task list for the preprint. A checked item means its stated acceptance condition has been met; it does not imply that later claims are validated.

## 1. Foundation

- [x] Identify the paper’s primary contribution: leased, copy-on-write workspaces with conflict-aware atomic publication.
- [x] Define the initial experimental baseline: upstream `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- [ ] Freeze the final paper snapshot with an annotated `paper-v1-freeze` tag after paper-specific fixes and benchmarks.
- [x] Complete an initial design inventory and claim-boundary review.
- [ ] Revalidate the design inventory against the final paper snapshot.
- [x] Review initial related work: DeltaBox, Shepherd, and AgentBay.
- [x] Review the CLI contract: separate management, runtime, and observability clients.
- [x] Create the evidence-gated [PRD](PRD.md).
- [x] Create `paper_story.md` with the provisional thesis, contribution, abstracts, introduction opening, and section arc.
- [x] Create `project_inventory.md` with source paths, tests, experiments, environments, documentation trust levels, and known limitations.
- [x] Create `claim_evidence_map.md` that maps every intended claim to code, data, required measurement, or a limitation.
- [x] Create `paper_skeleton.md` with the manuscript outline, five research questions, figure/table plan, work packages, dependencies, and blockers.
- [x] Create `complexity_and_evolution.md` with the v1 operational time/space cost model, concurrency implications, limitations, measurement matrix, and bounded LayerStack 2.0 future-work position.

## 2. Design evidence

- [x] Record the baseline LayerStack/manifest/lease model with source citations.
- [x] Record baseline OverlayFS workspace creation and private upper-layer behavior with source citations.
- [x] Record baseline holder/runner namespace execution and the isolation boundary with source citations.
- [x] Record baseline capture, validation, merge/reject policy, and atomic publication with source citations.
- [x] Record baseline squash/remount and lease-safety behavior with source citations.
- [x] Create `cli_contract_matrix.md` for client roles, operations, scopes, JSON/error behavior, and source references.
- [ ] Review all narrative claims against the final paper snapshot.

## Parallel workflow and next gate

Two primary lanes should advance concurrently:

1. **[Paper writing](lanes/paper-writing.md):** draft the source-grounded systems core now; keep Results and final framing provisional until evidence lock.
2. **[Experiments](lanes/experiments.md):** lock the protocol, resolve required source behavior/instrumentation, pilot, freeze source and benchmark configurations, run final experiments, analyze, and hand claim-mapped results to the paper lane.

Claim mapping, citation verification, provenance, and skeptical review are shared controls across both lanes rather than a third production lane.

- [x] Create the paper-writing lane charter.
- [x] Create the experiment lane charter.
- [ ] Paper PW0: scaffold, vocabulary, and planning artifacts were created on 2026-07-30; the later PW3/PW4 evolution of Sections 7--9 is preserved, and completion remains blocked because the follow-up recheck found no compatible local LaTeX tool for the required recorded build.
- [ ] Paper PW1: write Sections 2–3, Goals/Non-goals and System Model.
- [ ] Paper PW2: write Sections 4–5, Workspace Execution and Capture/Publication.
- [ ] Paper PW3: write Sections 6–7, Lifecycle/Recovery and Implementation/Interface, including the source-derived operational cost table.
- [ ] Paper PW4: write Section 8 methodology and Section 9 related-work/source limitations/future evolution after protocol lock.
- [ ] Paper PW5: write results and measured failure analysis after evidence lock.
- [ ] Paper PW6: rewrite Introduction, Conclusion, contributions, title, and Abstract.
- [ ] Paper PW7: complete whole-paper verification, build, and packaging.
- [ ] Experiment lane: create and review `experiment_inventory.md`.

The next synchronization gate is **protocol lock**. Before final source freeze, create `experiment_inventory.md` (or an equivalent benchmark protocol) that fixes RQ1–RQ5, the accepted-work unit, workloads, baselines, worker grid, metrics, uncertainty method, seeds/repeats, integration/verification policy, and required runtime instrumentation.

Detailed section dependencies, work packages, and evidence gates are in [`paper_skeleton.md`](paper_skeleton.md).

## 3. Correctness evaluation

- [ ] Define reproducible environment, build/image digest, configuration, and random seeds.
- [ ] Run and archive private-write isolation tests for simultaneous workspaces.
- [ ] Run and archive three-namespace connectivity/isolation tests.
- [ ] Run and archive non-overlapping concurrent-publication tests.
- [ ] Run and archive overlapping publication tests: merge, reject, and retry paths.
- [ ] Run and archive cleanup/interrupted-path/manifest-integrity tests.
- [ ] Run and archive lease-protected squash/remount tests.
- [ ] Run and archive CLI contract tests for scope, request IDs, JSON envelopes, and exit statuses.

## 4. Performance evaluation

- [ ] Choose and document a Linux cgroup-v2 test platform.
- [ ] Implement or verify a fair independent-container/worktree-per-agent baseline.
- [ ] Measure 1, 5, and 20 agents across 4 KiB, 256 KiB, and 3 MiB payloads.
- [ ] Measure layer depths 1, 10, 50, and 100.
- [ ] Measure session-start latency and daemon/session memory over live-session count × layer depth; record per-lease metadata behavior.
- [ ] Measure capture over upperdir entry count, fan-out, path depth, xattrs, and changed logical bytes.
- [ ] Measure publication planning, writer-lock wait, writer-lock hold, resolve/merge, hash, copy, sync, manifest, and end-to-end time over publisher count, paths, bytes, and depth.
- [ ] Stress eligible merge over file bytes, line count, similarity, and edit distance; archive CPU, peak RSS, outcome, and daemon health.
- [ ] Measure logical, allocated, shared, and exclusive bytes for upper/work/staging/published/history state, including small edits to large files.
- [ ] Measure squash plan/build/commit/GC and residual storage over layer count, live leases, lease age, and retained history.
- [ ] Archive raw samples for creation, execution, publication, squash, and remount latency.
- [ ] Analyze p50/p95/p99, CPU/RSS, physical disk, throughput, failures, and confidence intervals.
- [ ] Re-run the scripted ten-lane demonstration with source and binary/image provenance.

## 5. Manuscript and artifacts

- [ ] Create arXiv-compatible `main.tex` and a reproducible local build command. The source scaffold and command exist; local build verification is blocked on a compatible LaTeX tool.
- [ ] Create verified `references.bib`; check that every citation supports its sentence.
- [ ] Create a source-grounded architecture figure.
- [ ] Create a workspace-to-publication sequence figure.
- [ ] Generate result figures/tables from archived measurement data.
- [ ] Write core sections: system model, design, implementation, and evaluation.
- [ ] Write framing sections: abstract, introduction, related work, limitations/future evolution, conclusion.
- [ ] Create `ARTIFACTS.md` and archive code/data needed to reproduce every result.
- [x] Create `cli_contract_matrix.md` for command families, state effects, and contract-test evidence at the baseline commit; regenerate at final freeze.

## 6. Submission readiness

- [ ] Confirm every number traces to raw data and analysis code.
- [ ] Confirm no unsupported security, performance, Windows, or LLM-benchmark claim remains.
- [ ] Complete a skeptical technical review and resolve or disclose high-risk objections.
- [ ] Compile the full arXiv package and retain build logs/tool versions/hashes.
- [ ] Perform final author review of names, affiliations, licensing, and arXiv categories.
- [ ] Submit to arXiv and record the identifier.
- [ ] Publish or link artifacts on Hugging Face after the arXiv record is available.

## Active blockers and constraints

- There are no v1-specific archived performance measurements yet; do not state performance conclusions.
- Existing test source is not proof of a passing v1 test run; rerun and archive results.
- The prior scripted ten-lane run predates v1 and has incomplete provenance; it is exploratory only.
- The accepted-work unit, structured-team and exploratory-swarm workloads, matched baseline policy, and final experiment protocol are not yet locked.
- Attribution is best-effort after data publication rather than transactionally coupled to it; narrow the claim or strengthen and test the implementation before freeze.
- Explicit/implicit protected-drop semantics and lease/substitution behavior across daemon restart need resolution.
- The Windows Docker Desktop/WSL 2 reflink experiment failed with `errno=95`; do not make Windows reflink or performance claims.
- The LayerStack 2.0 A/B/C protocol is future-work only. Its pending thresholds are not results, and reflink must not be described as \(O(1)\) or universally available.
- The current 8 MiB text-merge byte limit does not independently bound its retained line-diff trace; adversarial CPU/RSS testing or a stricter implementation bound is required before freeze.
- The implemented isolation layers are not a formal security evaluation, and `rfc1918_egress=deny` is currently rejected.
- Source work uses the existing `ephemeral-sandbox` checkout on `main` because its `AGENTS.md` and `CLAUDE.md` prohibit side branches and worktrees; it was fast-forwarded cleanly to baseline commit `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- The PW0 manuscript build blocker was rechecked after Sections 7--9 advanced: `latexmk`, a compatible TeX engine, and BibTeX remain unavailable on `PATH`, in the checked conventional local installations, and in WSL. No toolchain was installed and no `main.pdf` was produced.
