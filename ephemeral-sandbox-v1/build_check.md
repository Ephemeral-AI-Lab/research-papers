# PW0 build check

**Status:** Passed with executed attestation.

The declared command is:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The skill build recorder executed the declared command successfully at `2026-07-30T00:23:10.503310+00:00` using the user-local TinyTeX installation at `C:\Users\yifan\AppData\Roaming\TinyTeX`.

## Tool versions

- Latexmk 4.88, dated 2026-03-09.
- pdfTeX 3.141592653-2.6-1.40.29, TeX Live 2026.
- BibTeX 0.99e, TeX Live 2026.

## Attestation

- Exit code: 0.
- PDF: `main.pdf`.
- PDF SHA-256: `dd63976a4714299aa99f564e2669c1e8a438dad6fe6eeaf1f4eeaadd50ef4406`.
- Input SHA-256: `e0c64365a445533c8efdb74068d5d5d28945871853d26c06692d0f791b48868e`.
- Build log: `plan/pw0-build-attempt.log`.
- Build-log SHA-256: `b0ad2eb77266611365f2af42a8b146fa25d8fdbd29d4cce599d7106b8b1d1e94`.
- Attestation: executed.

The parsed LaTeX log contains zero errors, emergency stops, undefined citations, undefined references, missing files, or overfull boxes. It reports five underfull boxes in the provisional cost table and one expected empty-bibliography warning.

Visual verification rendered all four US-letter pages. Text, headings, equations, table borders, page numbers, and draft markers are legible with no clipping, overlap, or broken glyphs. Because `references.bib` is intentionally comment-only, page 4 is an empty References page at this scaffold stage.

PW0's build blocker is closed. Other scientific, author, source-freeze, and evaluation blockers remain recorded in `paper_state.json`.
