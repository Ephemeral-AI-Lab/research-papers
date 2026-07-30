# Manuscript build

## Required tools

- User-local TinyTeX at `C:\Users\yifan\AppData\Roaming\TinyTeX`.
- `latexmk`, `pdflatex`, and `bibtex` available through the user `PATH`.

PW0 was built with:

- Latexmk 4.88, dated 2026-03-09.
- pdfTeX 3.141592653-2.6-1.40.29 from TeX Live 2026.
- BibTeX 0.99e from TeX Live 2026.

No generated figure, result table, benchmark output, or other external asset is required for the PW0 scaffold.

## Local build

Run from the paper folder:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The declared machine build command in `paper_state.json` is exactly:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Clean build

```powershell
latexmk -C main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Outputs

- PDF: `main.pdf`
- Primary LaTeX log: `main.log`
- Skill build-attestation log: `plan/pw0-build-attempt.log`
- Auxiliary files: `main.aux`, `main.bbl`, `main.blg`, `main.fdb_latexmk`, `main.fls`, and `main.out` when produced by the installed toolchain

## PW0 recorded build

The skill build recorder executed the declared command successfully on 2026-07-30 at `2026-07-30T00:23:10.503310+00:00`.

- Exit code: 0.
- PDF SHA-256: `dd63976a4714299aa99f564e2669c1e8a438dad6fe6eeaf1f4eeaadd50ef4406`.
- Attested input SHA-256: `e0c64365a445533c8efdb74068d5d5d28945871853d26c06692d0f791b48868e`.
- Build-log SHA-256: `b0ad2eb77266611365f2af42a8b146fa25d8fdbd29d4cce599d7106b8b1d1e94`.
- PDF size and format: 192,209 bytes, four US-letter pages, PDF 1.7.

The log contains no build errors, undefined citations or references, missing files, or overfull boxes. It contains five underfull-box warnings in the provisional source-derived cost table and an empty-bibliography warning. The latter produces an intentionally empty References page while `references.bib` remains comment-only.
