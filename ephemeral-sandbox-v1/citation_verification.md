# Citation verification

All scholarly entries used by `main.tex` have a terminal record in
`citation_lock.json`. The lock was regenerated from `citation_requests.json`
on 2026-08-02 with the arXiv and Crossref primary providers. Sentence-level
claim support is intentionally limited to the relationship stated in the
manuscript.

| Key | Status | Primary provenance | Manuscript relation |
| --- | --- | --- | --- |
| `swe_minisandbox_2026` | verified | arXiv | Isolated-execution contrast. |
| `agentbay_2025` | verified | arXiv | Hybrid sandbox-session contrast. |
| `deltabox_2026` | verified | arXiv | Checkpoint/rollback contrast. |
| `shepherd_2026` | verified | arXiv | Reversible-trace contrast. |
| `caid_2026` | verified | arXiv | Asynchronous coding-orchestration contrast. |
| `coagent_2026` | verified | arXiv | Shared-state concurrency-control contrast. |
| `claimplane_2026` | verified | arXiv | Intent-admission/control-plane contrast. |
| `palantir_2012` | verified | Crossref | Early conflict-awareness background. |
| `crystal_2013` | verified | Crossref | Collaboration-risk diagnosis background. |
| `threewaymerge_2018` | verified | Crossref | Semantic-merge limitation boundary. |
| `occ_1981` | verified | Crossref | Optimistic-validation background. |
| `snapshot_isolation_1995` | verified | Crossref | Terminology guardrail. |
| `cooperbench_2026` | verified | arXiv | Collaborative-coding evaluation context. |
| `agenticflict_2026` | verified | Crossref | Narrow textual-conflict motivation. |
| `teambench_2026` | verified | arXiv | Role-separation evaluation context. |
| `swebench_2024` | verified | arXiv | Repository-task evaluation context. |
| `paperbench_2025` | verified | arXiv | Long-horizon workload context. |

The union-mount primary proceedings record is cited as an official URL in a
footnote because its bibliographic identity is not a DOI or arXiv identifier,
the two identifier forms supported by the lock contract. Its official USENIX
record is listed in `literature/paper_inventory.md`.
