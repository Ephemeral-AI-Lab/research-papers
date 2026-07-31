# Ephemeral Sandbox v1 — Paper Progress

**Last updated:** 2026-07-31
**Overall status:** Baseline design, interface, story, related-work, and source-derived complexity audits are complete; PW0--PW3 are reproducibly built and attested; the v1.0 final is permanently failed/ineligible; and the focused EXP1 v1.1 local-IPC campaign has completed Gates 0--7, including its sole final, immutable archive, deterministic tables, numeric-evidence v2, and claim handoff. Broader paper experiments and manuscript work remain.
**Submission gate:** Not ready for arXiv.

Use this tracker as the authoritative task list for the preprint. A checked item means its stated acceptance condition has been met; it does not imply that later claims are validated.

## 1. Foundation

- [x] Identify the paper’s primary contribution: leased, copy-on-write workspaces with conflict-aware atomic publication.
- [x] Define the initial experimental baseline: upstream `main` at `b22862550e0a7cb4fe61ce581831e9244cc492b5`.
- [x] Freeze the active EXP1 v1.1 paper snapshot with an annotated
  `paper-v1.1-freeze` tag after qualification, smoke, pilot, and projection.
  Preserve the existing v1.0 `paper-v1-freeze` tag unchanged.
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

The author authorized a permanent CLI-focused remedy and campaign resumption.
The product candidate at clean direct `main` commit
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8` uses Windows named pipes for
local CLI traffic, retains explicit TCP compatibility outside the paper
treatment, and is staged as `target/windows-exp1-5c48dae1`. The earlier
active-store IPv4 proposal is superseded without execution; no host network
setting changed. The
[`v1.1 protocol amendment`](experiments/exp1-v1.1-protocol-amendment.md)
preregisters an ineligible 25,000-call concurrency-5 qualifier before fresh
smoke, pilot, a no-more-than-1,400-second projection, a new freeze, and exactly
one final.

The exact v1.1 qualifier subsequently passed: all 25,000 invocations completed
successfully in 5,000 concurrency-5 batches, with zero gateway-owned TCP
endpoints, zero new TCP/IP 4227/4231 events, bounded gateway resource growth,
and validated cleanup. Fresh v1.1 smoke
`019fb83a-54bc-79db-b6ac-6189fb28f5f2` then passed all 19 cells, 19 batches,
55 issued requests, correctness, warning, transport, and cleanup gates; its
verified archive content tree is
`sha256:c8e0e872d42c0df2ce2c19c4b030a29b615a7d250c95097dac9bff66fa4405e4`.
Both artifacts remain qualification-only. Fresh five-sample pilot
`019fb84e-aef1-7fdc-9a56-1adbe712f30d` subsequently passed all 19 cells, 133
trial batches, 95 measured trials, 385 issued requests, correctness, resource
correlation, warning, transport, cleanup, archive, and deterministic
exploratory-analysis gates. The conservative observed-envelope projection is
1303.732241600 seconds against the fixed 1400-second limit. Pilot and projected
values remain exploratory and ineligible. Gate 3 passed and authorized the
subsequent scoped v1.1 freeze.

The authorized v1.1 freeze then passed at paper measurement commit
`1680b599129532f72e706b6acb12ef62c63759e2`, product commit
`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`, and annotated tag object
`834c84534359f37653fb25ac45304091e82c37a6`. The sole final
`019fb86c-096e-7589-a0a4-a6d6ef5d7f8b` completed all 19 cells and 1,900
measured trials without a classified failure. Its immutable archive tree is
`sha256:606863f2843a7b19f04e27e2ba5b736d544dd143f56f6d3626611cb29bb44986`.
After a disclosed post-freeze Table-1 host-schema compatibility erratum, two
final nine-file analyses are byte-identical at output tree
`sha256:27b53ee5acc049899b4e5821f8d92b14488c7d08ed076ba379af4799c765ad04`;
all 153 numeric values have raw selectors. EXP1 Gates 0--7 pass. Author review
before LaTeX import is the next editorial action, not an experiment blocker.

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
- [x] Pass and retain the preregistered v1.1 local-IPC qualifier.
- [x] Run and archive a fresh v1.1 smoke.
- [x] Run and archive a fresh v1.1 five-sample pilot, deterministically
  regenerate exploratory tables, review anomalies, and pass the fixed
  no-more-than-1,400-second projection.
- [x] Freeze v1.1, pass strict frozen preflight, execute exactly one eligible
  final, verify its immutable archive, regenerate all four tables twice, and
  complete numeric-evidence/claim handoff.
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
- [x] Generate the four focused EXP1 v1.1 result tables from archived data;
  retain numeric-evidence v2 and a byte-identical independent regeneration.
- [ ] Generate result figures from archived data if the manuscript uses them.
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

- The focused EXP1 v1.1 final corpus is eligible within its bounded RQ3 scope;
  the earlier v1.0 final remains `failed_ineligible` and must not be pooled or
  quoted as a result.
- Existing test source is not proof of a passing v1 test run; rerun and archive results.
- The prior scripted ten-lane run predates v1 and has incomplete provenance; it is exploratory only.
- The accepted-work unit, structured-team and exploratory-swarm workloads, matched baseline policy, and final experiment protocol are not yet locked.
- The reviewed `product_cli` cohort and permanent local named-pipe treatment
  passed qualification, smoke, pilot, projection, freeze, strict preflight,
  sole final, archive, deterministic analysis, and handoff. EXP1 has no
  remaining execution/analysis blocker; author review is required before
  importing selected result rows into the manuscript.
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
