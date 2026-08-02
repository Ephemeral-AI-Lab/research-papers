# Related-work inventory

This inventory is the submission-stage review set for the manuscript's narrow
runtime-publication claim.  `citation_lock.json` records a terminal primary
metadata check for every identifier that can be represented by the paper's
DOI/arXiv verifier.  The remaining union-mount record was checked at the
official USENIX proceedings page; its identifier is a proceedings URL rather
than a DOI or arXiv record.

| Cluster | Primary record | Verification | Manuscript role |
| --- | --- | --- | --- |
| Isolated SWE execution | `swe_minisandbox_2026` | arXiv lock | Contrast: isolated execution and low-overhead environments are not introduced here. |
| Hybrid sandbox session | `agentbay_2025` | arXiv lock | Contrast: human/agent session control is distinct from durable code publication. |
| Checkpoint/rollback | `deltabox_2026` | arXiv lock | Contrast: process-state rollback exceeds this paper's filesystem-only claim. |
| Reversible execution traces | `shepherd_2026` | arXiv lock | Contrast: a trace/replay substrate is not a publication protocol. |
| Asynchronous SWE delegation | `caid_2026` | arXiv lock | Closest orchestration comparison: Git worktrees and manager policies. |
| Multi-agent concurrency control | `coagent_2026` | arXiv lock | Closest shared-state contrast: speculative in-place effects plus repair. |
| Change-intent control | `claimplane_2026` | arXiv lock | Closest admission-control comparison: authority and scope before writes. |
| Private-workspace awareness | `palantir_2012` | Crossref lock | Historical contrast: detect and communicate conflict, rather than enforce a runtime transition. |
| Collaboration-risk detection | `crystal_2013` | Crossref lock | Historical contrast: diagnose textual/build/test risks before merge. |
| Semantic merge | `threewaymerge_2018` | Crossref lock | Limitation boundary: a bounded text merge is not semantic merge correctness. |
| Union filesystem mechanism | Pendry and McKusick, *Union Mounts in 4.4BSD-Lite* | Official USENIX record | Background only: upper/lower views, copy-up, and whiteouts predate this system. |
| Optimistic validation | `occ_1981` | Crossref lock | Background only: tentative work plus validation is a general pattern, not a serializability claim. |
| Snapshot-isolation terminology | `snapshot_isolation_1995` | Crossref lock | Guardrail: do not call the system serializable snapshot isolation. |
| Collaborative coding evaluation | `cooperbench_2026` | arXiv lock | Candidate workload/motivation; not evidence for this system. |
| Historical conflict dataset | `agenticflict_2026` | Crossref lock | Narrow motivation only; no universal conflict-rate inference. |
| Role-separated teamwork | `teambench_2026` | arXiv lock | Evaluation context; role separation is not workspace publication. |
| Repository issue resolution | `swebench_2024` | arXiv lock | Workload context; it is not a concurrent-session benchmark. |
| Long-horizon research replication | `paperbench_2025` | arXiv lock | Workload context; it does not isolate integration effects. |

No product blog, tool documentation, or unreviewed summary is used as scholarly
evidence.  Current product interfaces may motivate engineering choices, but
they are not citations for empirical performance or correctness claims.
