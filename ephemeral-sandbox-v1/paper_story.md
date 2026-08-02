# Paper story: Ephemeral Sandbox v1

**Status:** final scope reconciled for PW4--PW7 on 2026-08-02.
**Source snapshot:** product commit [`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8), tag `paper-v1.1-freeze`.
**Measurement:** sole eligible EXP1 final `019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`.

## Title

**Ephemeral Sandbox: Private LayerStack Workspaces with Controlled Publication
for Coding Agents**

The title describes a protocol and does not imply a general-purpose OS,
security guarantee, performance win, or improved agent productivity.

## One-sentence thesis

Ephemeral Sandbox implements private executable workspace sessions over leased
LayerStack history and a controlled capture-to-publication boundary; EXP1 v1.1
describes public-CLI startup, operation, and selected resource observations in
one explicitly bounded Windows/Docker Desktop treatment.

## Task boundary

- **Inputs:** a selected sandbox, a leased LayerStack view, session-scoped or
  sessionless runtime operations, and a captured private filesystem delta.
- **Output:** either a source-defined current-head publication outcome or a
  structured non-publication/lifecycle outcome.
- **Measured setting:** native Windows build 26200, Docker Desktop 29.0.1,
  pinned Ubuntu 24.04 image, `paper-100m`, native `product_cli`, local named
  pipes, concurrency 1/5, two warmups and 100 measured trials per cell.
- **Out of scope:** isolation correctness, publication/fault correctness,
  competitive baselines, deeper scaling, useful-work, attribution completeness,
  restart recovery, security, and multi-agent quality.

## Gap and method insight

Private copies alone defer the question of how a private execution view relates
to a changing shared project head. Ephemeral's system-level contribution is to
make that boundary explicit: **one recorded project history, private executable
sessions, controlled publication.** A lease fixes the logical source view;
capture produces a filesystem candidate; current-head reconciliation either
resolves the complete data changeset under source-defined rules or rejects it;
only an accepted layer becomes visible through active-manifest replacement.

This is a composition and lifecycle/operational-contract claim. Union mounts,
copy-on-write views, leases, optimistic validation, and text merges are not
claimed as individual inventions. The Related Work section must position the
composition against DeltaBox, Shepherd, AgentBay, CAID, CoAgent, Claim Plane,
private-workspace conflict work, and foundational filesystem/concurrency work.

## Contributions and evidence

1. **Workspace-session protocol.** Source inspection establishes leased
   LayerStack projection, private upper/work directories, sessionless command
   finalization, and explicit-session lifecycle. This is not a measured
   isolation or security claim.
2. **Controlled publication protocol.** Source inspection establishes capture,
   current-head validation, bounded text merge eligibility, whole-candidate
   rejection, and the active-manifest data-visibility boundary. This is not a
   semantic-correctness, fault-tolerance, or full-transaction claim.
3. **Operational contract.** The measured source exposes 8 management, 10
   runtime, and 8 observability operations; all three accept an optional
   validated request ID and use endpoint URI resolution with a legacy
   `--gateway-socket` alias. This is contract evidence, not correctness proof.
4. **Focused RQ3 evidence.** The immutable 19-cell EXP1 v1.1 archive and
   deterministic tables describe end-to-end public-CLI timings and seven
   preregistered resource rows in one fixed treatment. No comparison is made.

## Completed evaluation question

Under the disclosed EXP1 v1.1 treatment, what startup, public-CLI operation,
and preregistered resource observations are recorded at concurrency 1 and 5?
Results answer this question descriptively. They do not establish why values
change, whether individual latency improves, or what happens in another host,
workload, product revision, or agent workflow.

## Claims to make

- The measured source implements the bounded workspace/session/publication and
  role-separated-interface mechanisms stated in the claim map.
- The final archive completed 1,900/1,900 reportable measured trials in its
  bounded campaign, without generalizing that outcome to product reliability.
- Tables 2--4 report selector-bound end-to-end public-CLI and resource values
  for the disclosed setting.
- The v1.0 endpoint-exhaustion failure motivated a preregistered local named-
  pipe treatment; it is qualitative failure analysis, never a competing row.

## Claims to avoid

- speed, scalability, superiority, reliability, security, production readiness,
  useful-work productivity, or universal concurrency claims;
- source inspection or test presence as measured correctness evidence;
- correctness of publication, isolation, recovery, or semantic integration;
- a general Windows/Linux equivalence, physical-storage advantage, or reflink
  result.

## Required limitations and reviewer risks

The paper must foreground the missing baseline, narrow environment, one final
run, unmeasured correctness/recovery, post-commit attribution, protected-drop
asymmetry, daemon-restart lease gap, unbounded-in-practice merge trace risk,
unavailable storage metrics, and analysis compatibility erratum. The highest
novelty risk is Claim Plane; the story must distinguish pre-write intent and
authority from Ephemeral's execution-to-publication boundary without claiming
that either system subsumes the other.
