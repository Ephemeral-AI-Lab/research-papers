# Ephemeral Sandbox v1: final paper skeleton

**Scope status:** reconciled on 2026-08-02. Design/interface claims refer to
product commit `5c48dae10847fb9e46ba2bea7675bcf2f5a6f4c8`; quantitative claims
refer only to final EXP1 v1.1 output selectors.

## Core contract

- **Thesis:** Ephemeral Sandbox makes a private execution-to-shared-history
  publication boundary explicit through leased LayerStack workspaces, capture,
  current-head reconciliation, and active-manifest publication; EXP1 v1.1
  describes bounded public-CLI observations for one treatment.
- **System contribution:** a source-defined runtime protocol and interface,
  not a claim to invent union mounts, leases, optimistic validation, or merge.
- **Completed evaluation question:** what startup, public operation, and
  preregistered resource observations occur in the fixed EXP1 v1.1 treatment?
- **Claims to avoid:** competitive results, security/correctness evaluation,
  broad reliability, useful-work, agent productivity, and extrapolation beyond
  the 19-cell campaign.

## Section plan

### 1. Introduction

State the workspace/publication gap; introduce the bounded protocol; present
the source-grounded contributions and completed RQ3 evidence; state the narrow
evaluation boundary on the first page. Do not promise answers to RQ1/RQ2/RQ4/
RQ5 or describe source/test inspection as an empirical result.

### 2. Goals and non-goals

Retain stable private execution, controlled data publication, lifecycle
outcomes, and role-separated operations as implementation goals. State the
security, semantic merge, process rollback, egress, coordination, and
cross-platform boundaries.

### 3. System model and invariants

Define LayerStack history, lease, private upper/work pair, implicit command
session, explicit session, candidate changeset, reconciliation, publication,
and lifecycle outcomes. Qualify that data visibility, attribution, and cleanup
are different phases.

### 4. Workspace execution

Describe source-defined OverlayFS projection and holder/runner execution.
Distinguish sessionless `exec_command` from sessionless file paths and shared
from isolated networking. State Linux/OverlayFS support accurately.

### 5. Capture and publication

Describe protected drops, routing, current-head validation, narrow merge
eligibility, whole-candidate rejection, staging, and manifest replacement.
Do not call the protocol semantic merge correctness or a complete transaction.

### 6. Lifecycle and recovery

Cover retryable precommit failure, discard, no-op, committed publication,
published-but-not-closed, holder exit artifacts, and conservative cleanup.
State restart/lease/substitution behavior as unmeasured.

### 7. Implementation and operational interface

Use the measured-source 8/10/8 matrix. Explain all-client request IDs, endpoint
URI resolution, local named-pipe default on Windows, and TCP compatibility.
Keep the operational cost model source-derived rather than measured.

### 8. Evaluation: Methodology and bounded results

Open with the completed EQ1 and state why broader RQs are not evaluated.
Describe the Windows/Docker Desktop environment, pinned image, `product_cli`,
named-pipe treatment, 19 cells, fixture, concurrency/payloads, warmups,
trials, randomized blocks, no-retry rule, correctness inclusion gate, cleanup,
and resource sampling. Explain v1.0 qualitatively, v1.1 remediation, and the
Table-1 reader compatibility erratum. Include only deterministic tables
generated from the frozen registry and selector-bound numeric prose.

### 9. Limitations and related work

Open with evaluation and system limitations, then position execution isolation,
reversible state, coding-agent coordination, conflict work, and foundational
filesystem/concurrency work from the verified literature matrix. Related Work
must not make numerical comparisons.

### 10. Conclusion

Recap the source-grounded protocol and one-treatment descriptive evidence,
then restate the unmeasured correctness, baseline, generalization, recovery,
and coordination questions.

## Final result assets

| Asset | Source | Disposition |
|---|---|---|
| Environment/provenance table | frozen Table 1 | deterministic LaTeX conversion |
| Startup table | frozen Table 2 | deterministic LaTeX conversion |
| Public CLI table | frozen Table 3 | deterministic LaTeX conversion |
| Resource table | frozen Table 4 | deterministic LaTeX conversion; call its workspace column `upperdir` delta |
| Numerical figure | none | omitted; tables retain exact values without adding a decorative plot |
| Four concept figures | prompt sources plus reviewed PNGs | repair, regenerate, waive, or remove each issue after final-width color/grayscale QA |

## Claims moved out of the core

Former RQ1 isolation, RQ2 publication/fault behavior, RQ4 competitive
useful-work scaling, and RQ5 attribution/restart recovery are limitations and
future evaluation. The source-derived cost-model variables (layer depth,
leases, upperdir shape, publication bytes/queueing, merge shape, and retained
history) are hypotheses for future measurement, not EXP1 conclusions.
