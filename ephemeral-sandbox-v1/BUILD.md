# Manuscript build

## Required tools

- A current arXiv-compatible TeX Live or MiKTeX installation.
- `latexmk` with `pdflatex` and `bibtex` available on `PATH`.

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

## PW0 tool record and limitations

The 2026-07-30 skill build attempt stopped with `Build executable does not exist: latexmk` (recorder exit code 2). Preflight found no `latexmk`, `tectonic`, `pdflatex`, `xelatex`, `lualatex`, or `bibtex` executable on `PATH`; checked conventional MiKTeX, TeX Live, and TinyTeX locations and WSL exposed no compatible alternative. The build therefore used no LaTeX tool version and produced no `main.pdf`. PW0 does not install a toolchain or change system configuration. The scaffold bibliography is intentionally comment-only and contains no citations.
