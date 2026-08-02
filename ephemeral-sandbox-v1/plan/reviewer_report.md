# PW8 skeptical reviewer report

**Review outcome:** evidence-bounded manuscript is suitable for owner review;
external submission remains blocked by author and venue metadata.

## Strengths

- The contribution is stated as a runtime publication composition, not as a new
  filesystem, merge, or coordination primitive.
- The only numerical displays are generated from the frozen Table-A output and
  pass selector-level numeric verification.
- The evaluation names what it cannot establish: no baseline, workload suite,
  useful-work result, security result, fault campaign, or cross-platform claim.
- Closest coordination, sandbox, reversibility, conflict-awareness, and merge
  work is cited with terminal primary metadata records.

## Findings and disposition

| Severity | Finding | Disposition |
| --- | --- | --- |
| Release blocker | The manuscript uses `Anonymous authors`; no owner-approved author list, affiliations, venue/category, or disclosure text exists. | Remains an external owner action and is recorded in `SUBMISSION.md` and `paper_state.json`. |
| Major claim risk | A reader could mistake the local treatment for a comparative or team-productivity result. | Resolved by the abstract, Section 8 scope/threats text, table captions, claim map, and reviewer guide. |
| Major novelty risk | The implementation combines established isolated-workspace, optimistic-validation, and merge mechanisms. | Resolved by explicit positioning against CAID, CoAgent, Claim Plane, Palantir, Crystal, semantic merge, union mounts, and OCC. |
| Minor presentation issue | Sample-count cells used prose rather than the archived numeric display. | Resolved before the final build: the generated tables now render the frozen `100` sample value, verified by `check_numeric_evidence.py`. |
| Minor visual risk | Existing concept rasters differ in layout and palette density. | Resolved by final color/grayscale inspection and explicit non-evidence waivers in `figures/concept-figure-review.md`. |

## Recommendation

Do not broaden the claim set during authoring. After the owner supplies the
metadata listed above, rerun the documented projection, verification, build,
visual QA, and submission-readiness checks before deciding whether to mark the
paper submission-ready.
