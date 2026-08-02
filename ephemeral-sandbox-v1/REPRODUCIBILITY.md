# Reproducibility instructions

## Prerequisites

- Python with the repository's analysis dependencies.
- TinyTeX or another LaTeX installation with `latexmk`, `pdflatex`, and
  `bibtex` available on `PATH`.
- Read access to the immutable archive and frozen Table-A output directories
  listed in `ARTIFACTS.md`.

No gateway, Docker daemon, product build, network request, or experiment rerun
is required for the paper projection and build.

## Rebuild the manuscript projection

Run from this paper directory:

```text
python scripts/generate_latex_results.py
python scripts/generate_bibliography.py
python C:\Users\yifan\.codex\skills\ai-research-writing\scripts\check_citations.py main.tex references.bib
python C:\Users\yifan\.codex\skills\ai-research-writing\scripts\check_citation_lock.py . --max-age-days 180
python C:\Users\yifan\.codex\skills\ai-research-writing\scripts\check_numeric_evidence.py .
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The numeric checker validates the manuscript-side registry against selectors in
the frozen `numeric-provenance.csv`; it is not a trust-by-copy check. If the
citations must be refreshed, set the local CA-bundle path when necessary and
run the verifier before regenerating the bibliography:

```text
set SSL_CERT_FILE=<path-to-certifi-cacert.pem>
python C:\Users\yifan\.codex\skills\ai-research-writing\scripts\verify_citations.py .
python scripts/generate_bibliography.py
```

Refreshing the citation lock changes only bibliographic metadata and requires a
subsequent paper build. It does not authorize any experiment action.

## Verify frozen evidence

Use the archive verifier documented in the experiment package, then compare
the resulting content-tree and output-tree hashes against `ARTIFACTS.md`.
The expected Table-A generator sources, table JSON, provenance CSV, and output
manifest are already included in the frozen output directory.
