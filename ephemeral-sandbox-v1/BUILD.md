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
- PW0 skill build-attestation log: `plan/pw0-build-attempt.log`
- PW1 skill build-attestation log: `plan/pw1-build.log`
- PW2 skill build-attestation log: `plan/pw2-build.log`
- PW3 skill build-attestation log: `plan/pw3-build.log`
- Auxiliary files: `main.aux`, `main.bbl`, `main.blg`, `main.fdb_latexmk`, `main.fls`, and `main.out` when produced by the installed toolchain

## PW0 recorded build

The skill build recorder executed the declared command successfully on 2026-07-30 at `2026-07-30T00:23:10.503310+00:00`.

- Exit code: 0.
- PDF SHA-256: `dd63976a4714299aa99f564e2669c1e8a438dad6fe6eeaf1f4eeaadd50ef4406`.
- Attested input SHA-256: `e0c64365a445533c8efdb74068d5d5d28945871853d26c06692d0f791b48868e`.
- Build-log SHA-256: `b0ad2eb77266611365f2af42a8b146fa25d8fdbd29d4cce599d7106b8b1d1e94`.
- PDF size and format: 192,209 bytes, four US-letter pages, PDF 1.7.

The log contains no build errors, undefined citations or references, missing files, or overfull boxes. It contains five underfull-box warnings in the provisional source-derived cost table and an empty-bibliography warning. The latter produces an intentionally empty References page while `references.bib` remains comment-only.

## PW1 recorded build

After drafting Sections 2 and 3, the skill build recorder executed the same declared command successfully on 2026-07-30 at `2026-07-30T00:48:19.855325+00:00`.

- Toolchain: Latexmk 4.88 (2026-03-09); pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026); BibTeX 0.99e (TeX Live 2026).
- Exit code: 0.
- PDF: `main.pdf`, 209,575 bytes and six US-letter pages.
- PDF SHA-256: `ba4963d3d5f6352e1829946290265671599432e9984e301d5626de7316435327`.
- Attested input SHA-256: `8a9d0f97487ccf937efd82eb6a5726b2c7c8b5e3e31be1434945826a00731708`.
- Build log: `plan/pw1-build.log`.
- Build-log SHA-256: `719696c0aa0efb9fce4796efaab3cce5b27dd17563c4b60d7f4951b539aa7f30`.
- Attestation: executed.

The parsed LaTeX log contains zero errors, emergency stops, undefined citations, undefined references, missing files, or overfull boxes. The five underfull boxes remain confined to the pre-existing provisional cost table in Section 7, and the comment-only bibliography still produces the expected empty-bibliography warning.

## PW2 recorded build

After drafting Sections 4 and 5, the skill build recorder executed the same declared command successfully on 2026-07-30 at `2026-07-30T01:10:40.550071+00:00`.

- Toolchain: Latexmk 4.88 (2026-03-09); pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026); BibTeX 0.99e (TeX Live 2026).
- Exit code: 0.
- PDF: `main.pdf`, 221,013 bytes and eight US-letter pages.
- PDF SHA-256: `801ac91c302ae3ea7d5827d34dd4da09278e8f537409e3426fd4ff30c8ed36e7`.
- Attested input SHA-256: `36877891dbce1e066589d8a295e436654ccb097970620003cdaf45871f74311b`.
- Build log: `plan/pw2-build.log`.
- Build-log SHA-256: `9fc4261ab327472e004f4f62466bf2266218d1b17a66cc5b852ee5dbe7b23265`.
- Attestation: executed.

The final LaTeX pass contains zero errors, emergency stops, undefined citations, undefined references, missing files, or overfull boxes. The five underfull boxes remain confined to the pre-existing provisional cost table in Section 7, and the comment-only bibliography still produces the expected empty-bibliography warning.

## PW3 recorded build

After completing Sections 6--7 and integrating the four author-supplied
concept figures, the skill build recorder executed the declared command
successfully on 2026-07-30 at
`2026-07-30T03:22:41.491473+00:00`.

- Toolchain: Latexmk 4.88 (2026-03-09); pdfTeX 1.40.29 (TeX Live
  2026); BibTeX 0.99e (TeX Live 2026).
- Exit code: 0.
- PDF: `main.pdf`, 4,485,845 bytes and 14 US-letter pages.
- PDF SHA-256:
  `bf893a5ac17e396233232b18d552e77ddddfc2bcba50786d457fd58db71604eb`.
- Attested input SHA-256:
  `e31aa83e7db9c45cdf0c3c1f731fe66670fc6641dc20d755704a7673a552e18a`.
- Build log: `plan/pw3-build.log`.
- Build-log SHA-256:
  `39a836a6226fc9b8007dd23fda5deb9e2cd8bf3c453faf17539c9b356871e59f`.
- Attestation: executed.

The final LaTeX pass contains zero errors, emergency stops, undefined
citations, undefined references, missing files, or overfull boxes. Seven
underfull boxes occur in the two narrow Section 7 tables, and the comment-only
bibliography produces the expected empty-bibliography warning.

All 14 pages were rendered at 144 dpi for visual review, with an additional
96 dpi grayscale pass. The four figures appear on pages 3, 6, 8, and 10; both
Section 7 tables remain after their introducing prose. No clipping, overlap,
broken glyph, or page-number defect was found. The figures remain unchanged
drafting-stage review assets, and their recorded topology, resolution,
grayscale-contrast, and style-family disparities remain PW7 work.
