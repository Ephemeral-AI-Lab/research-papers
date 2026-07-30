# PW0 build check

**Status:** Blocked before LaTeX execution.

The declared command is:

```text
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

On 2026-07-30, the skill build recorder attempted to execute the declared command and returned exit code 2 before LaTeX execution:

```text
Cannot record build: Build executable does not exist: latexmk
```

The same preflight found no `tectonic`, `pdflatex`, `xelatex`, `lualatex`, or `bibtex` on `PATH`; no `latexmk` was found in the checked conventional MiKTeX, TeX Live, or TinyTeX locations; and WSL exposed none of those tools. No toolchain was installed and no system configuration was changed. No `main.pdf` was produced.

- Tool version used: unavailable; no compatible executable started.
- Expected PDF: `main.pdf`.
- Attempt record: `plan/pw0-build-attempt.log`.
- PW0 disposition: incomplete until the declared command runs successfully and its hashes are recorded.
