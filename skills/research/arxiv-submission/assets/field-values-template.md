<!--
  Per-paper worksheet. Fill every [ ... ] with the exact value for THIS paper, delete this comment,
  and hand the result to the user. This is the primary deliverable of the arxiv-submission skill.
-->

# arXiv submission worksheet — [Paper short title]

## Pre-flight
- [ ] Employer / co-author approval to post a public preprint: **[confirmed / pending — who]**
- [ ] Venue preprint policy allows arXiv: **[confirmed / N.A. / pending]**
- [ ] Endorsement: **[auto-endorsed via prior <group> paper / endorsement needed for <group>]**

## Source package
- **Archive**: `[path/to/<Title_Underscored>_arXiv_source.zip]`
- **Bibliography**: `[inline thebibliography — no .bbl / external .bib — .bbl included]`
- **Manifest**: `[main.tex, figures/..., main.bbl?, .sty/.cls?]`
- **Lint**: `[all PASS / list any WARNs the user should know]`

## Web-form values (copy-paste)

| Field | Value |
|---|---|
| **License** | `[arXiv perpetual non-exclusive / CC BY 4.0 / ...]` |
| **Title** | `[plain-text title, LaTeX stripped]` |
| **Authors** | `[First Last, First Last, ...]` |
| **Primary category** | `[cs.XX]` |
| **Cross-list** | `[cs.YY, cs.ZZ]` |
| **ACM class** *(optional)* | `[X.n.k; X.n.k; ...]` |
| **MSC class** | `[blank unless math]` |
| **Report number** | `[blank / internal ID]` |
| **Journal ref** | `[blank unless already published]` |
| **DOI** | `[blank unless publisher DOI exists]` |
| **Comments** | `[N pages, M figures. <venue note if any>]` |

### Abstract  *(ASCII-only, [NNNN] chars — within the ~1,920 limit ✓)*

```
[Paste the cleaned, ASCII abstract here. Verified with clean_abstract.py:
 length = NNNN, non-ASCII = 0.]
```

## Submit steps (in order)
1. arxiv.org → **Submit** → start a new submission.
2. **License**: select the value above.
3. **Upload** the source ZIP.
4. **Process/check files** — confirm top-level `.tex`, figures, and `.bbl` (if any) are listed.
5. **Preview the PDF** — verify figures, fonts, and references render. Fix + re-upload if not.
6. **Metadata** — paste Title, Authors, Abstract, Comments; set primary + cross-list categories;
   add ACM class.
7. **Submit** — confirm. To be announced same day, finalize before **14:00 US Eastern (Mon–Fri)**;
   announced ~20:00 ET.
