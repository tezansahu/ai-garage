# The arXiv submission web form

The ordered flow, the license decision, and field-by-field guidance for every metadata field, plus
endorsement, timing, and post-submission. A worked example is at the end.

## Contents
- [1. The submission flow (in arXiv's order)](#1-the-submission-flow-in-arxivs-order)
- [2. License selection](#2-license-selection)
- [3. Metadata fields, one by one](#3-metadata-fields-one-by-one)
- [4. The abstract field (rules + failure modes)](#4-the-abstract-field-rules--failure-modes)
- [5. Endorsement](#5-endorsement)
- [6. Timing & announcement](#6-timing--announcement)
- [7. After submitting (hold, v2, withdraw)](#7-after-submitting-hold-v2-withdraw)
- [8. Worked example](#8-worked-example)

---

## 1. The submission flow (in arXiv's order)

Walk the user through these steps in this order. Do not let them skip the preview.

1. **Start a submission** — from the user's arXiv account (`arxiv.org` → *Submit*).
2. **License** — pick the license (§2). Irrevocable for this version.
3. **Upload files** — upload the `_arXiv_source.zip` built in Phase 1.
4. **Process / check files** — arXiv extracts and lists the files. Confirm the top-level `.tex` is
   detected and the `.bbl`/figures are present.
5. **Preview PDF — mandatory.** arXiv compiles server-side; the user must open and eyeball the PDF
   (fonts, figures, references, no missing glyphs). If it fails or looks wrong, fix the source
   (see [source-prep.md](source-prep.md)), rebuild the ZIP, and re-upload.
6. **Add/verify metadata** — Title, Authors, Abstract, Comments, categories, optional class codes,
   and the mostly-blank fields (§3).
7. **Categories** — set the primary category and cross-lists (see [categories.md](categories.md)).
   arXiv pre-guesses a primary from the text; override it if wrong.
8. **Submit / confirm** — final review, then confirm. Note the timing rules (§6).

---

## 2. License selection

The license governs **reuse**, not **citeability or discoverability** — a paper is cited, indexed by
Google Scholar / Semantic Scholar, and assigned a permanent arXiv ID under **every** option. So choose
on reuse policy, not on visibility.

**Default recommendation — `arXiv.org perpetual, non-exclusive license`**
(`arxiv.org/licenses/nonexclusive-distrib/1.0/`). The conservative choice for a paper owned by an
employer or headed to a formal venue: the author/employer keeps all rights beyond arXiv's right to
distribute. Safe when internal approval may constrain reuse.

**`CC BY 4.0`** — the de-facto standard for AI/ML preprints; permits redistribution, adaptation, and
text/data-mining with attribution. Choose it if you *want* to maximize reuse or a funder mandates it.
Fine for most academic preprints; confirm employer approval allows it for corporate papers.

Avoid unless specifically required:
- **`CC0`** waives all rights — wrong for an employer-owned paper.
- **`CC BY-SA / BY-NC-SA / BY-NC-ND`** add ShareAlike/NonCommercial/NoDerivatives friction with no
  upside unless a funder requires them.

**Irrevocable per version.** You can pick a different (usually more open) license on a later v2, but
never change a version already posted.

---

## 3. Metadata fields, one by one

Derive each value from the paper; don't ask the user for what you can read.

| Field | How to fill it |
|---|---|
| **Title** | Copy the paper title as **plain text**. Strip LaTeX line breaks (`\\`), `\thanks{}`, and math markup; keep it human-readable. Match the PDF's capitalization. |
| **Authors** | Comma-separated, in paper order: `First Last, First Last`. Use the same name forms as the PDF. Affiliations are **not** entered here (they live in the paper). |
| **Abstract** | See §4. Must be ASCII and under the length limit. Start from the paper's `\begin{abstract}`, strip LaTeX, clean characters. |
| **Comments** | Free text for reviewers/readers. Put page/figure counts and any venue note here, e.g. `12 pages, 3 figures. Extended abstract accepted at <Venue> <Year> (Industry Track).` Do **not** claim peer-reviewed publication if it isn't; "accepted at" is fine when true. |
| **Primary category** | The single best-fit subject class. See [categories.md](categories.md). Override arXiv's guess if needed. |
| **Cross-list categories** | 1–3 adjacent classes for extra audiences. See [categories.md](categories.md). Don't over-cross-list. |
| **ACM classification** | Optional. Semicolon-separated CCS-1998 codes, e.g. `D.2.5; I.2.6; I.2.11`. See [acm-classification.md](acm-classification.md). |
| **MSC classification** | Optional; math subject codes. Leave blank for typical CS/ML papers. |
| **Report number** | Your institution's internal report ID, if any (e.g., `MSR-TR-2026-xx`). Usually blank. |
| **Journal reference** | Only once/if formally published in a journal/proceedings (`Journal, vol(iss):pp, year`). Blank for a fresh preprint. |
| **DOI** | A DOI already assigned by a publisher for the *same* work. Blank if none. (arXiv issues its own DOI regardless.) |

---

## 4. The abstract field (rules + failure modes)

The abstract is entered in the web form (not read from the `.tex`) and is the **most common cause of
a failed submission**. Two hard constraints:

1. **Length**: at most **~1,920 characters** (arXiv rejects longer with
   *"cannot be longer than 1,920 characters"*). Count characters, not words.
2. **ASCII-only**: any non-ASCII byte triggers *"Bad character(s)"* — **one error per offending
   character**. Usual culprits, and their fixes:

   | Bad (non-ASCII) | Replace with |
   |---|---|
   | `—` em-dash (U+2014) | `--` |
   | `–` en-dash (U+2013) | `-` |
   | `"` `"` `'` `'` smart quotes | straight `"` `'` |
   | `…` ellipsis | `...` |
   | non-breaking space (U+00A0) | normal space |
   | ligatures `ﬁ ﬂ`, accented letters | ASCII equivalents (`fi`, `fl`, ...) |

**Preparation steps:**
1. Start from the paper's `\begin{abstract} ... \end{abstract}`.
2. Strip LaTeX: unwrap `\emph{x}\textbf{x}\textit{x}\texttt{x}` → `x`; drop `\cite{}/\ref{}/\label{}`;
   convert escapes `\% \& \_ \$ \#` → `% & _ $ #`; `~` → space; `\\` → space.
3. Run the cleaner, which does the character substitutions and reports length + any remaining
   non-ASCII:
   ```
   python scripts/clean_abstract.py --file "<abstract.txt>"
   ```
   or pipe text: `... | python scripts/clean_abstract.py`.
4. If it's over the limit, trim wording (tighten phrasing; cut redundant clauses) — don't drop
   substance — and re-run until `within limit = True` and `non-ASCII = 0`.

Straight ASCII apostrophes, hyphens, parentheses, `~`, and `%` are all fine; only non-ASCII bytes and
length are enforced.

---

## 5. Endorsement

arXiv gates first-time contributors to a subject area with an **endorsement** system to prevent spam.

- **Already published in the target group?** You're **auto-endorsed** for that whole group. Example:
  a prior `cs.*` paper (any CS subclass) auto-endorses you across all of Computer Science, so
  submitting `cs.LG`/`cs.AI`/`cs.SE` needs no endorsement request.
- **New to the group?** arXiv prompts you to obtain an endorsement code from an established author in
  that group before the paper can be announced. Plan for the delay.
- Endorsement is **per submission group**, not per paper. Picking a category in a *different* group
  (e.g., a `math.*` or `physics.*` cross-list) can trigger a separate prompt — keep cross-lists within
  groups you're endorsed for unless you have a reason.

---

## 6. Timing & announcement

- Submissions **finalized before 14:00 US Eastern (Mon–Fri)** are announced the **same day** at
  ~20:00 ET; later ones roll to the next business day.
- Weekend/holiday submissions queue for the next business day.
- New submissions pass through **moderation**; established authors from known institutions rarely see
  delays, but a mis-categorized paper can be reclassified or held.

---

## 7. After submitting (hold, v2, withdraw)

- **On hold / moderation**: if flagged, respond to arXiv's note; often it's a category correction.
- **Replace (v2)**: you can upload a new version anytime; the old version stays citable at its
  version tag. Use this for camera-ready updates or fixes. You may also switch to a more open license
  on a new version.
- **Withdraw**: you can withdraw a paper, but prior versions remain publicly listed (arXiv is an
  archive) — which is exactly why the Phase-0 clearances matter.

---

## 8. Worked example

For "Who Belongs in the Eval Set? A Capability-Taxonomy-Driven Pipeline for Curating Regression Eval
Sets in Agent-Extensibility Platforms" — use as a *model of the reasoning*, not values to copy:

- **Title**: `Who Belongs in the Eval Set? A Capability-Taxonomy-Driven Pipeline for Curating Regression Eval Sets in Agent-Extensibility Platforms` (LaTeX `\\` removed).
- **Authors**: `Tezan Sahu, Aritra Das, Pankaj Mittal, Sudipta Das`.
- **Comments**: `Extended abstract accepted at SERI 2026 (Industry Track). <N> pages, <M> figures.`
- **Primary**: `cs.LG`; **Cross-list**: `cs.AI`, `cs.SE` (arXiv's `cs.CL` guess overridden — see
  [categories.md](categories.md)).
- **ACM class**: `D.2.5; I.2.6; I.2.11` (see [acm-classification.md](acm-classification.md)).
- **Report number / Journal ref / DOI / MSC**: blank.
- **License**: arXiv perpetual non-exclusive (conservative for a Microsoft-owned paper); CC BY if
  internal approval encourages open reuse.
- **Abstract**: reduced from ~2,000 chars with 3 em-dashes to **1,898 chars, pure ASCII** by
  replacing `—` with `--`/`:` and tightening phrasing — which cleared the "Bad character(s)" (×3) and
  ">1,920 characters" errors.
