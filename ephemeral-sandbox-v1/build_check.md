# PW4--PW7 build check

**Status:** passed, executed attestation.

The declared build command completed with exit code zero:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

| Field | Recorded value |
| --- | --- |
| Attestation time | 2026-08-02T05:28:00.336951+00:00 |
| PDF | `main.pdf` |
| PDF SHA-256 | `6ffb429c6acb0f27af6dc493cd3fcc43a1710a22cba17fb669a11129ad06e8b2` |
| Build-input SHA-256 | `6f1675a8021bf6acc982d9b7dc9f6c4d5755832ca937334c6212eb15b867b6a7` |
| Attestation log | `plan/pw4-pw7-build-attestation.log` |
| Attestation-log SHA-256 | `cffe435373442861725c7ca42e572c0a33ea029f02d1031fa38ba731745157c1` |

The separate final log scan reports no overfull boxes and no unresolved
citations or references. Citation-key, citation-lock, numeric-evidence, and
full-paper quality gates pass. The PDF has 17 pages and was rendered in color
and grayscale for visual QA; the record and final figure waivers are in
`figures/concept-figure-review.md`.

The local LaTeX wrapper emitted only non-fatal locale and console-code-page
messages. They do not affect the recorded zero exit code, source digest, or PDF
digest.
