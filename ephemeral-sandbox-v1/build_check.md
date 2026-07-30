# PW3 build check

**Status:** Passed with executed attestation.

The declared command is:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The skill build recorder executed the declared command successfully at
`2026-07-30T03:22:41.491473+00:00` using the user-local TinyTeX installation
at `C:\Users\yifan\AppData\Roaming\TinyTeX`.

## Tool versions

- Latexmk 4.88, dated 2026-03-09.
- pdfTeX 3.141592653-2.6-1.40.29, TeX Live 2026.
- BibTeX 0.99e, TeX Live 2026.

## Attestation

- Exit code: 0.
- PDF: `main.pdf`.
- PDF SHA-256: `bf893a5ac17e396233232b18d552e77ddddfc2bcba50786d457fd58db71604eb`.
- Input SHA-256: `e31aa83e7db9c45cdf0c3c1f731fe66670fc6641dc20d755704a7673a552e18a`.
- Build log: `plan/pw3-build.log`.
- Build-log SHA-256: `39a836a6226fc9b8007dd23fda5deb9e2cd8bf3c453faf17539c9b356871e59f`.
- Attestation: executed.

The parsed LaTeX log contains zero errors, emergency stops, undefined
citations, undefined references, missing files, or overfull boxes. It reports
seven underfull boxes in the two narrow Section 7 tables and one expected
empty-bibliography warning.

The full-paper quality gate and citation-key checker pass at the current
`full-paper` / `drafting` state. All ten section inputs appear exactly once
and in order; the Section 6 and 7 headings and labels are stable; all four
figure hashes and references pass; all relative Markdown links resolve; PDF
and log hashes match `paper_state.json`; and Git whitespace checks pass.

The 14-page PDF was rendered in color and grayscale. Figures appear on pages
3, 6, 8, and 10, the two Section 7 tables remain after their introductions,
and no clipping, overlap, broken glyph, or page-number defect was found.
Because `references.bib` remains comment-only, the sparse References page is
expected.

PW3's manuscript build gate is closed. Figure disparities are explicitly
deferred to PW7; scientific, author, source-freeze, citation, and evaluation
blockers remain recorded in `paper_state.json`.
