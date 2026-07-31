# Ephemeral Sandbox v1 — Paper Progress

**Last updated:** 2026-07-31
**Overall status:** Baseline design, interface, story, related-work, and source-derived complexity audits are complete; PW0--PW3 are reproducibly built and attested; EXP1 Gates 0--4 passed with a frozen CLI-only treatment, but the sole final attempt failed during a mandatory resource boundary and is permanently ineligible.
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
- [x] Create a focused RQ3 practical-performance draft with phase gates,
  environment preflight, expected table schemas, simulated previews, and an
  append-only experiment log.
- [x] Paper PW0: scaffold, vocabulary, planning artifacts, and later PW3/PW4 evolution of Sections 7--9 are preserved; the declared build completed with an executed tool/version/hash attestation on 2026-07-30.
- [x] Paper PW1: Sections 2--3 now define Goals/Non-goals, the System Model, and four evidence-bounded invariants; the recorder-generated build and required PW1 checks pass.
- [x] Paper PW2: Sections 4--5 now explain leased OverlayFS execution, implicit/explicit/sessionless paths, typed capture, current-head reconciliation, whole-changeset rejection, durable manifest publication, and the post-commit attribution/cleanup boundary; the recorder-generated build and required PW2 checks pass.
- [x] Paper PW3: Sections 6–7 now cover Lifecycle/Recovery and Implementation/Interface, preserve the source-derived operational cost model, integrate four unchanged review-draft figures, and pass the recorded build and PDF inspection.
- [ ] Paper PW4: write Section 8 methodology and Section 9 related-work/source limitations/future evolution after protocol lock.
- [ ] Paper PW5: write results and measured failure analysis after evidence lock.
- [ ] Paper PW6: rewrite Introduction, Conclusion, contributions, title, and Abstract.
- [ ] Paper PW7: complete whole-paper verification, build, and packaging.
- [x] Experiment lane: create `experiment_inventory.md`.
- [x] Experiment lane: review and approve the focused RQ3 protocol, implement
  the `product_cli` benchmark cohort, and complete the five-sample exploratory
  pilot defined by
  [`plan/task-packets/exp1-cli-performance-campaign.md`](plan/task-packets/exp1-cli-performance-campaign.md).

EXP1 Gates 0--4 passed and protocol v1.0 was frozen. The sole eligible
`paper-good-pass`, run `019fb6e5-c00b-7b02-8a3c-d76bd1346eb4`, failed after
853 of 1,938 batches when a mandatory observability CLI connection hit Windows
socket error 10048; TCP/IP Event 4227 confirms local endpoint-reuse pressure.
The verified corpus is `failed_ineligible`. Gates 5--7 fail, no numeric result
may enter the paper, and v1.0 must not be rerun. The broader RQ1--RQ5
experiment lane still requires its own accepted-work, workload, baseline,
fault, and useful-work decisions.

A read-only v1.1 remediation audit is complete. It found 7,993 identifiable
client-to-gateway TCP attempts, of which only 210 were optional periodic
samples; removing sampling therefore cannot remedy the mandatory failure. The
recommended campaign-preserving path is a temporary active-store IPv4
dynamic-port expansion, followed by a same-rate ineligible qualifier, fresh
smoke/pilot, new protocol/environment freeze, and one newly authorized final.
No host/source setting was changed and no live probe was run. The exact
proposal and alternatives are in
[`experiments/analysis/exp1-v1.1-remediation-decision.md`](experiments/analysis/exp1-v1.1-remediation-decision.md);
explicit author authorization and an elevated host action remain required.

Detailed section dependencies, work packages, and evidence gates are in [`paper_skeleton.md`](paper_skeleton.md).

## 3. Correctness evaluation

- [x] Define and qualify the focused RQ3 environment, product release, binary
  and image digests, configuration, and seed. Broader RQ1/RQ2 correctness and
  fault campaigns remain unexecuted.
- [ ] Run and archive private-write isolation tests for simultaneous workspaces.
- [ ] Run and archive three-namespace connectivity/isolation tests.
- [ ] Run and archive non-overlapping concurrent-publication tests.
- [ ] Run and archive overlapping publication tests: merge, reject, and retry paths.
- [ ] Run and archive cleanup/interrupted-path/manifest-integrity tests.
- [ ] Run and archive lease-protected squash/remount tests.
- [ ] Run and archive CLI contract tests for scope, request IDs, JSON envelopes, and exit statuses.

## 4. Performance evaluation

- [x] Choose and document the final focused RQ3 platform: native Windows x64
  host with Docker Desktop 29.0.1 providing a Linux AMD64 `overlayfs`,
  cgroup-v2 engine and the pinned Ubuntu 24.04 sandbox image.
- [x] Implement and review a `product_cli` subprocess cohort for every paper
  performance operation; `direct_client` and `cli_e2e` are prohibited.
- [x] Apply the deterministic `paper-100m` base to every measured cell and add
  explicit manager-CLI sandbox-create-to-ready timing.
- [x] Run and archive a five-sample exploratory pilot over all 19 final cells;
  its numbers remain outside paper tables.
- [x] Lock protocol `v1.0`, freeze product/benchmark/image/binary identities,
  and launch the sole 19-cell `paper-good-pass` after every prior gate passed.
  The run failed and therefore produced no eligible final result.
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

- [x] Create arXiv-compatible `main.tex` and a reproducible local build command; execute it through the skill build recorder and retain the PDF, log, tool versions, and hashes.
- [ ] Create verified `references.bib`; check that every citation supports its sentence.
- [x] Create a source-grounded architecture review draft; final visual repair is deferred to PW7.
- [x] Create a workspace-to-publication sequence review draft; final visual repair is deferred to PW7.
- [x] Create lifecycle and reconciliation review drafts; lifecycle is revalidated against Section 6 and final visual repair is deferred to PW7.
- [ ] Complete PW7 submission-final figure normalization, topology review, label audit, and style-family decision.
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

- There is no eligible v1 final performance corpus. The sole final archive is
  `failed_ineligible`; do not state performance conclusions from it.
- Existing test source is not proof of a passing v1 test run; rerun and archive results.
- The prior scripted ten-lane run predates v1 and has incomplete provenance; it is exploratory only.
- The accepted-work unit, structured-team and exploratory-swarm workloads, matched baseline policy, and final experiment protocol are not yet locked.
- The reviewed `product_cli` cohort exists and its smoke/pilot passed, but the
  sole frozen final hit Windows TCP endpoint-reuse pressure during a mandatory
  observability boundary. Any new final requires an amended protocol, a new
  freeze, and explicit author authorization.
- Focused RQ3 timing is end-to-end native CLI subprocess latency, including
  process launch and CLI-to-gateway transport. Product-reported internal timing
  may be retained only as a separate secondary field.
- The selected environment is already qualified. Do not reintroduce the
  superseded native-Ubuntu-host, SSH, ext4-host, or CPython-host requirements;
  Ubuntu 24.04 is the pinned sandbox image.
- Attribution is best-effort after data publication rather than transactionally coupled to it; narrow the claim or strengthen and test the implementation before freeze.
- Explicit/implicit protected-drop semantics and lease/substitution behavior across daemon restart need resolution.
- The Windows Docker Desktop/WSL 2 reflink experiment failed with `errno=95`; do not make Windows reflink or performance claims.
- The LayerStack 2.0 A/B/C protocol is future-work only. Its pending thresholds are not results, and reflink must not be described as \(O(1)\) or universally available.
- The current 8 MiB text-merge byte limit does not independently bound its retained line-diff trace; adversarial CPU/RSS testing or a stricter implementation bound is required before freeze.
- The implemented isolation layers are not a formal security evaluation, and `rfc1918_egress=deny` is currently rejected.
- Source work uses the existing `ephemeral-sandbox` checkout on `main` because its `AGENTS.md` and `CLAUDE.md` prohibit side branches and worktrees; it was fast-forwarded cleanly to baseline commit `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- PW0 now builds through user-local TinyTeX/TeX Live 2026. The recorded `latexmk` run produced and attested `main.pdf`; this removes the PW0 build blocker but does not satisfy the later full-manuscript submission build gate.
