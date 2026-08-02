---
name: arxiv-submission
description: Submit a paper to arXiv as a preprint. Use when the user wants to submit, post, or publish a paper, article, or extended abstract to arXiv, whether the source is an Overleaf project, a local LaTeX folder, or a source ZIP.
---

# arXiv Submission

Take a paper from its source to a submitted arXiv preprint. Two deliverables:

1. A **source archive** arXiv's server-side compiler accepts on the first try.
2. A filled worksheet — the exact value for every submission-form field, ready to paste.

Do the **legwork**: read the paper and derive every value yourself. The user only previews the PDF,
pastes, and clicks — never ask them for a value you could read from the source.

## Phase 0 — Pre-flight

Flag these, then proceed (don't block the workflow on them):

- **Clearance.** Employer publication approval (e.g. Microsoft internal) and co-author sign-off to
  post a permanent, public preprint — this gate is *before* submission, never after.
- **Venue policy.** If the paper is accepted at / under review at a venue, confirm the venue allows
  an arXiv preprint.
- **Endorsement.** Confirm the author can post to the target arXiv group — see "Endorsement" in
  [references/web-form.md](references/web-form.md).

## Phase 1 — Get & validate the source

Route on what the user hands over:

| Input | Action |
|---|---|
| **Overleaf** (link or "it's in Overleaf") | You can't reach it — give the export path from [references/source-prep.md](references/source-prep.md) and have the user drop the ZIP/folder locally. |
| **Local folder** (`.tex` + figures) | Work in place. |
| **ZIP** | Extract to a working dir. |

Then, for any source:

1. **Lint:** `python scripts/lint_source.py "<source-dir-or-main.tex>"`. The **bibliography / `.bbl`**
   finding is the top submission-killer; [references/source-prep.md](references/source-prep.md)
   explains every finding and how to fix it.
2. **Package:** `python scripts/build_source_zip.py "<source-dir>" --out "<source-dir>/<Title_Underscored>_arXiv_source.zip"`.

**Done when** `lint_source.py` reports **0 FAIL** and the manifest holds only the `.tex`, the `.bbl`
(only if the linter says one is needed), any `.sty`/`.cls`, and figures.

## Phase 2 — Derive every field value

Read the paper (title block, abstract, intro, contributions) and fill a copy of
[assets/field-values-template.md](assets/field-values-template.md):

- **Abstract** — `python scripts/clean_abstract.py --file "<abstract.txt>"`; must reach `RESULT: OK`.
  Rules and failure modes: [references/web-form.md](references/web-form.md).
- **Primary + cross-list categories** — [references/categories.md](references/categories.md).
- **ACM classification** (optional) — [references/acm-classification.md](references/acm-classification.md).
- **Title, authors, comments, license, and every remaining field** — [references/web-form.md](references/web-form.md).

**Done when** every field in the worksheet is filled or explicitly marked blank, and the abstract
cleared `clean_abstract.py`.

## Phase 3 — Walk the user through the form

Present the filled worksheet, then drive the arXiv form in its own order: start → license → upload →
process → **preview the compiled PDF (mandatory)** → metadata → categories → submit. The flow, the
license choice, and every field are in [references/web-form.md](references/web-form.md).

**Done when** the user has previewed the PDF, pasted every worksheet value, and submitted within
arXiv's announcement window (see "Timing" in [references/web-form.md](references/web-form.md)).
