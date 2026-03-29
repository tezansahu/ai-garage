---
name: insight-extractor
description: Extract key, actionable insights from knowledge resources and save as structured markdown files in the knowledge/insights/ folder. Handles YouTube video URLs (youtube.com/watch or youtu.be), web blog/article URLs, local PDF file paths, and remote PDF URLs (including arxiv.org, semanticscholar, etc.). Trigger on phrases like "extract insights from", "summarize this", "key ideas in", "mine this for insights", "what's in this", "give me a digest of", followed by any URL or file path. Also triggers when the user shares a link and wants a quick takeaway without reading the full content. For multiple resources in one request, ask standalone vs. consolidated output before extracting.
---

# Insight Extractor

Extract crisp, actionable insights from YouTube videos, web articles, and research papers.
Outputs go to `knowledge/insights/`; raw fetched content is preserved in `knowledge/raw/`.

**Always read `references/output-format.md`** for the required output structure, insight
categories, file naming, and quality bar.

---

## Workflow

```
1. Detect resource type  (table below)
2. Multiple resources? → ask standalone vs. consolidated first, then proceed
3. Ensure workspace folders exist
4. Extract content  (follow the reference file for the detected type)
5. Generate insights  (per references/output-format.md)
6. Save to knowledge/insights/<slug>.md and confirm path to user
```

---

## Step 1 — Detect Resource Type

| Input pattern | Type | Reference |
|---|---|---|
| `youtube.com/watch`, `youtu.be/` | YouTube video | `references/youtube.md` |
| `arxiv.org`, `semanticscholar.org`, `openreview.net`, `dl.acm.org`, `ieeexplore.ieee.org`, or any URL ending in `.pdf` | PDF (remote) | `references/pdf.md` |
| Local file path ending in `.pdf` | PDF (local) | `references/pdf.md` |
| Any other `http/https` URL | Web article / blog | `references/web-article.md` |

---

## Step 3 — Ensure Workspace Folders Exist

```bash
mkdir -p knowledge/insights knowledge/raw/transcripts knowledge/raw/articles knowledge/raw/pdfs
```

---

## Step 4 — Extract Content

Read the reference file for the detected type and follow it exactly. Each reference file
specifies where to save intermediate raw content within the `knowledge/raw/` folder.

---

## Step 5 — Generate Insights

Read `references/output-format.md`. Key principles:
- Every bullet = something worth remembering or acting on — no padding.
- Extract the *implication*, not a restatement of what the resource says.
- Skip categories with nothing meaningful.
- Add diagrams (Mermaid / ASCII) only where they compress a concept better than bullets.

---

## Multiple Resources

When the user provides 2+ resources in one request:
1. List detected types (don't extract yet).
2. Ask: **"Separate insight files for each, or one consolidated file grouped by theme?"**
   - Standalone: different topics, or resources will be referenced independently.
   - Consolidated: shared theme, cross-referencing adds value.
3. Extract all (parallelize where possible).
4. Consolidated output: group by insight category, tag each insight's source in brackets.

---

## Extensibility

To add a new resource type:
1. Add a row to the detection table above, pointing to a new reference file.
2. Create `references/<type>.md` — follow the same pattern as existing reference files:
   acquire content → save raw to `knowledge/raw/<type>/` → produce clean plain text.
3. Steps 5–6 require no changes.

Future candidates: podcasts (audio transcript API), GitHub repos, Notion exports, newsletter issues, Twitter/X threads.
