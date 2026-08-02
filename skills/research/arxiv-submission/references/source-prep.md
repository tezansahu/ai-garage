# Source preparation for arXiv

How to get a paper's source into a clean, arXiv-acceptable archive. Covers: getting source out of
Overleaf, the bibliography/`.bbl` decision, arXiv's compile engine and its constraints, running the
linter, and packaging + naming.

## Contents
- [1. Getting the source](#1-getting-the-source)
- [2. The bibliography / `.bbl` decision (most common trap)](#2-the-bibliography--bbl-decision-most-common-trap)
- [3. arXiv's compile engine (what actually runs)](#3-arxivs-compile-engine-what-actually-runs)
- [4. Source constraints & gotchas](#4-source-constraints--gotchas)
- [5. Linting the source](#5-linting-the-source)
- [6. Packaging & naming](#6-packaging--naming)

---

## 1. Getting the source

### From Overleaf
You cannot reach Overleaf directly — instruct the user to export, then work from the file they drop
locally (Downloads is fine). Give them the **exact** path:

> **Menu (top-left) → Submit → arXiv → "Download project ZIP with submission files"**

Why this specific route: it bundles the **generated `.bbl`** (and other compile outputs) alongside
the `.tex` and figures. The plain **Menu → Download → Source** route gives you the editable sources
only and **omits the `.bbl`**, which breaks any paper that uses an external `.bib` (see §2).

- If the "Submit → arXiv" item isn't present in a given Overleaf instance, use **Download → Source**
  and then verify a `.bbl` is present (or that the paper uses an inline bibliography — §2).
- The user can also copy the `output.bbl` manually: **Overleaf → Logs and output files (the
  page/list icon next to Recompile) → Other logs & files → `output.bbl`**, rename it to match the
  main file (e.g., `main.bbl`), and add it to the source folder.

### From a local folder
A valid arXiv source folder is self-contained: the main `.tex`, any `\input`-ed `.tex`, custom
`.sty`/`.cls`, the `.bbl` (if external bib), and all figures — with **relative paths only**. Lint and
package it directly.

### From a ZIP
Extract to a working directory first (do **not** lint the zipped bytes). On Windows, prefer Python's
`zipfile` (via `build_source_zip.py`'s round-trip) or `Expand-Archive`; note the repo's ZIP
file-lock gotcha — never leave a `[IO.Compression.ZipFile]::OpenRead` handle undisposed.

---

## 2. The bibliography / `.bbl` decision (most common trap)

arXiv's server **does not run BibTeX/Biber**. It compiles LaTeX (typically two pdfLaTeX passes) and
expects the bibliography to already be resolved. There are two cases — identify which one applies
(the linter reports this):

### Case A — External bibliography (needs `.bbl`)
The main `.tex` contains `\bibliography{refs}` + `\bibliographystyle{...}`, **or** biblatex
(`\addbibresource{...}` + `\printbibliography`). BibTeX/Biber normally generates a `.bbl` at compile
time. **You must include that `.bbl`** in the submission (same basename as the main file). Without it,
arXiv produces a paper with no references or fails.

- Get the `.bbl` from Overleaf (§1) or by compiling locally once.
- You may omit the raw `.bib` from the upload — the `.bbl` is what's used. (Including it is harmless
  but unnecessary; excluding it avoids any chance of arXiv mis-detecting a BibTeX run.)

### Case B — Inline bibliography (no `.bbl` needed)
The main `.tex` contains a hand-written `\begin{thebibliography}{..} \bibitem{...} ... \end{thebibliography}`
block and **no** `\bibliography{}` command. Nothing is generated; arXiv compiles the block directly.
This is complete as-is — **do not go hunting for a `.bbl`**.

> A `\bibliographystyle{...}` line can appear in Case B and is inert (it only matters if BibTeX runs).
> Its presence alone does **not** mean you need a `.bbl` — look for `\bibliography{}` /
> `\printbibliography` to decide.

**Quick check in Overleaf:** open *Logs and output files → Other logs & files*. If `output.bbl`
exists → Case A (include it). If it does not → Case B (inline; nothing to include).

---

## 3. arXiv's compile engine (what actually runs)

Working knowledge of the current submission system (v1.5, rolled out April 2025). If the live form
differs, defer to arxiv.org's help pages.

- **Server-side compile only.** You upload source; arXiv compiles it. There is no "upload a PDF and
  skip" path for TeX submissions, and the legacy **AutoTeX** auto-reprocessing loop is retired.
- **You must preview the compiled PDF** before you can submit. Get the compile clean first.
- **TeX Live 2025** is the default toolchain (older TeX Live selectable as a fallback).
- **Processor**: default **pdfLaTeX**. LuaLaTeX/XeLaTeX are available but have thinner package
  coverage; prefer pdfLaTeX unless the paper genuinely needs Unicode fonts/fontspec.
- Two LaTeX passes run; cross-references resolve, but **BibTeX/Biber do not run** (see §2).

---

## 4. Source constraints & gotchas

- **Figures must match the processor.** pdfLaTeX takes `.pdf`, `.png`, `.jpg/.jpeg`. It does **not**
  take `.eps` directly — convert EPS to PDF first. Make sure every `\includegraphics` target file is
  actually present (case-sensitive) in the archive.
- **No `\today`.** arXiv would render the *server's* compile date. Hard-code any date you need.
- **No `minted`** (needs shell-escape/Pygments) and no other `\write18`/shell-escape packages. Use
  `listings` or `verbatim` instead.
- **Self-contained, relative paths.** No `\input{/absolute/path}`, no reaching outside the archive.
- **Filenames**: only `A–Z a–z 0–9 _ + - . , =`. No spaces, no Unicode, case-sensitive. Rename
  offenders and update the corresponding `\includegraphics`/`\input`.
- **TeX comments are archival and public.** Everything after `%` ships in the source and is viewable
  by anyone. Strip internal notes, reviewer rebuttals, TODOs, and anything sensitive.
- **Hidden files** (`.*`) and compiler junk are unnecessary — the packager drops them (§6).
- **One top-level `.tex`.** If several files have `\documentclass`, arXiv may pick the wrong root;
  keep a single main file (or be ready to tell arXiv which is the top-level file).

---

## 5. Linting the source

Run the bundled linter, which checks all of §2 and §4 at once:

```
python scripts/lint_source.py "<path-to-source-dir-or-main.tex>"
```

It reports, per check, `PASS` / `WARN` / `FAIL`:
- the detected `\documentclass`;
- the **bibliography mechanism** (Case A vs B) and, for Case A, whether a `.bbl` is present;
- every `\includegraphics` target, whether the file exists, and whether its extension suits pdfLaTeX;
- `\today`, `minted`/shell-escape, absolute `\input`/`\include` paths;
- filenames with disallowed characters;
- leftover compiler/editor junk and hidden files.

Fix every `FAIL` and review each `WARN` before packaging. The `.bbl` result is the one that most
often blocks a first submission.

---

## 6. Packaging & naming

Build the upload archive with the bundled packager (it excludes `.aux/.log/.out/.synctex.gz/.fls/`
`.fdb_latexmk/.bcf/.run.xml/.blg/...`, hidden files, `__MACOSX`, `.DS_Store`, and VCS dirs, and
prints a manifest):

```
python scripts/build_source_zip.py "<source-dir>" --out "<source-dir>/<Title_Underscored>_arXiv_source.zip"
```

Confirm the manifest contains only what arXiv needs: the `.tex`(s), the `.bbl` (Case A), any custom
`.sty`/`.cls`/`.bst`, and figures.

### Repo organization convention
Keep arXiv materials beside the paper, isolated from presentation artifacts:

```
<paper-folder>/
├── <Title>.pdf                 # compiled PDF (reference)
├── poster/ , deck/             # presentation artifacts (not for arXiv)
└── source/                     # arXiv submission materials
    ├── main.tex
    ├── figures/
    ├── main.bbl                # only if Case A
    └── <Title_Underscored>_arXiv_source.zip
```

- **ZIP name**: `<Paper_Title_Underscored>_arXiv_source.zip` (spaces/hyphens → underscores), e.g.
  `Who_Belongs_in_the_Eval_Set_arXiv_source.zip`.
- Keep the **loose** `main.tex` + `figures/` next to the ZIP so the source stays editable and
  diff-able; rebuild the ZIP after any edit so the two stay in sync.
