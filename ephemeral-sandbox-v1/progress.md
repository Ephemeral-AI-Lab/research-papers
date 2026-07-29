# Ephemeral Sandbox v1 — Paper Progress

**Last updated:** 2026-07-30  
**Overall status:** Discovery complete; evidence and manuscript work not yet started.  
**Submission gate:** Not ready for arXiv.

Use this tracker as the authoritative task list for the preprint. A checked item means its stated acceptance condition has been met; it does not imply that later claims are validated.

## 1. Foundation

- [x] Identify the paper’s primary contribution: leased, copy-on-write workspaces with conflict-aware atomic publication.
- [x] Freeze the implementation reference: `ephemeral-sandbox` `main` at `2a43eb07767304a4c77ac019cedb2992b3335e35`.
- [x] Inventory the v1 architecture and its claim boundaries.
- [x] Review initial related work: DeltaBox, Shepherd, and AgentBay.
- [x] Create the evidence-gated [PRD](PRD.md).
- [ ] Create `paper_story.md` with the final thesis, reader, contribution, and section arc.
- [ ] Create `project_inventory.md` with source paths, tests, experiments, environments, and known limitations.
- [ ] Create `claim_evidence_map.md` that maps every intended claim to code, data, or a limitation.

## 2. Design evidence

- [ ] Record the LayerStack/manifest/lease model with source citations.
- [ ] Record OverlayFS workspace creation and private upper-layer behavior with source citations.
- [ ] Record holder/runner namespace execution and the isolation boundary with source citations.
- [ ] Record capture, validation, merge/reject policy, and atomic publication with source citations.
- [ ] Record squash/remount and lease-safety behavior with source citations.
- [ ] Review all narrative claims against the frozen v1 source snapshot.

## 3. Correctness evaluation

- [ ] Define reproducible environment, build/image digest, configuration, and random seeds.
- [ ] Run and archive private-write isolation tests for simultaneous workspaces.
- [ ] Run and archive three-namespace connectivity/isolation tests.
- [ ] Run and archive non-overlapping concurrent-publication tests.
- [ ] Run and archive overlapping publication tests: merge, reject, and retry paths.
- [ ] Run and archive cleanup/interrupted-path/manifest-integrity tests.
- [ ] Run and archive lease-protected squash/remount tests.

## 4. Performance evaluation

- [ ] Choose and document a Linux cgroup-v2 test platform.
- [ ] Implement or verify a fair independent-container/worktree-per-agent baseline.
- [ ] Measure 1, 5, and 20 agents across 4 KiB, 256 KiB, and 3 MiB payloads.
- [ ] Measure layer depths 1, 10, 50, and 100.
- [ ] Archive raw samples for creation, execution, publication, squash, and remount latency.
- [ ] Analyze p50/p95/p99, CPU/RSS, physical disk, throughput, failures, and confidence intervals.
- [ ] Re-run the scripted ten-lane demonstration with source and binary/image provenance.

## 5. Manuscript and artifacts

- [ ] Create arXiv-compatible `main.tex` and a reproducible local build command.
- [ ] Create verified `references.bib`; check that every citation supports its sentence.
- [ ] Create a source-grounded architecture figure.
- [ ] Create a workspace-to-publication sequence figure.
- [ ] Generate result figures/tables from archived measurement data.
- [ ] Write core sections: system model, design, implementation, and evaluation.
- [ ] Write framing sections: abstract, introduction, related work, limitations, conclusion.
- [ ] Create `ARTIFACTS.md` and archive code/data needed to reproduce every result.

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
- The Windows Docker Desktop/WSL 2 reflink experiment failed with `errno=95`; do not make Windows reflink or performance claims.
- The implemented isolation layers are not a formal security evaluation, and `rfc1918_egress=deny` is currently rejected.