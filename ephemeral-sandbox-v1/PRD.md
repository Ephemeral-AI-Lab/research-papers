# Product Requirements Document - Ephemeral Sandbox v1 paper

**Status:** PW4--PW7 scope reconciled on 2026-08-02
**Target:** arXiv `cs.OS` preprint; cross-lists are an author decision
**Measured product revision:** [`5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`](https://github.com/Ephemeral-AI-Lab/ephemeral-sandbox/tree/5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8), annotated tag `paper-v1.1-freeze` (object `834c84534359f37653fb25ac45304091e82c37a6)
**Eligible quantitative evidence:** only EXP1 v1.1 final `019fb86c-096e-7589-a0a4-a6d6ef5d7f8b`

## Objective

Produce a reproducible systems preprint about a source-grounded workspace-session
and publication protocol, with a focused, descriptive RQ3 measurement study.
The paper must distinguish implementation evidence, contract tests, and the
completed performance corpus. It is not a security certification, competitive
benchmark, or multi-agent productivity study.

## Final thesis

Ephemeral Sandbox provides private executable workspace sessions over leased
LayerStack history and a controlled capture-to-publication path; on one
disclosed Windows/Docker Desktop treatment, EXP1 v1.1 describes end-to-end
public-CLI startup, operation, and selected resource observations without
claiming general performance or correctness.

## Contribution boundary

1. A source-grounded LayerStack workspace-session protocol: a sessionless
   `exec_command` uses an implicit private session, while explicit sessions
   retain private state across selected command/file operations.
2. A source-grounded capture and current-head publication protocol with bounded
   text reconciliation, whole-changeset reject behavior, and an active-manifest
   data-visibility boundary.
3. A regenerated 8/10/8 role-separated CLI contract at the measured tag,
   including endpoint selection and request-ID behavior.
4. A fully archived focused RQ3 campaign describing startup, public-CLI, and
   preregistered resource values for the disclosed treatment.

## Evaluation question

**EQ1 (completed):** Under the frozen native-Windows/Docker Desktop treatment,
with `product_cli`, a pinned Ubuntu 24.04 image, the `paper-100m` fixture, and
concurrency 1 or 5, what end-to-end CLI startup, operation, and preregistered
resource observations are recorded by EXP1 v1.1?

The following remain limitations and future evaluation, not answered research
questions: isolation correctness (former RQ1), publication/fault correctness
(former RQ2), competitive/deeper scaling and useful work (former RQ4), and
attribution/restart recovery completeness (former RQ5).

## Evidence rules

- Numbers may originate only from the final v1.1 archive through the two
  byte-identical output trees and their 153 selector-bound entries.
- Do not use v1.0, qualifier, smoke, pilot, projection, setup, verification,
  teardown, partial, simulated, or unavailable values as results.
- Describe source implementation and test existence as source/contract evidence,
  never as a measured correctness result.
- Scope every EXP1 statement to its host, Docker Desktop engine, pinned image,
  fixture, product/benchmark revisions, public CLI boundary, payloads, and
  concurrency 1/5.

## Claims excluded from this paper

- superiority, speedup, broad scalability, efficiency, production readiness,
  reliability, security, isolation correctness, or multi-agent productivity;
- semantic merge correctness, serializable snapshot isolation, process rollback,
  universal egress control, or cross-platform durability;
- measured publication/fault, baseline, useful-work, or recovery behavior;
- Windows reflink support, `O(1)` reflink behavior, or LayerStack 2.0 results.

## Required limitations

The final paper preserves the post-commit best-effort attribution boundary,
protected-drop-policy uncertainty, lease/substitution restart gap,
source-derived diff-trace memory risk, Linux/OverlayFS implementation boundary,
Windows/Docker Desktop measurement boundary, unavailable resource metrics, and
the narrow Windows reflink feasibility failure. LayerStack 2.0 is future work.

## Acceptance criteria

The preprint can be called submission-ready only when its source package builds
from declared inputs; every displayed number resolves to the frozen registry;
cited keys have terminal citation-lock records and sentence-level support;
figures receive final visual decisions; artifact documentation avoids
local-path-only reproduction; and author names, affiliations, licensing,
category, availability links, and any required AI-assistance disclosure are
provided by the author. Until then, the manuscript remains a buildable draft
with explicit blockers.
