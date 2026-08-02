# Web Article Extraction

Most articles are handled fully by `scripts/fetch_article.py` (uses `trafilatura` or
`beautifulsoup4`). For JS-rendered or paywalled pages (exit code 2), fall back to
Playwright MCP.

---

## Run the pipeline

```bash
python .claude/skills/insight-extractor/scripts/fetch_article.py "<URL>"
```

Example output (stdout):
```
Title:    How I Stopped Optimizing and Started Shipping
Author:   Jane Doe
Words:    ~2,800
Saved:    knowledge/raw/articles/how-i-stopped-optimizing.md
```

Install requirements if needed:
```bash
pip install trafilatura       # Recommended — handles most sites + extracts metadata
pip install beautifulsoup4    # Fallback (used automatically if trafilatura missing)
```

---

## After the script completes

- Use the **Title** field to derive the insight file's slug.
- Read `knowledge/raw/articles/<slug>.md` as the content for insight generation.

---

## Playwright MCP Fallback (exit code 2)

Used when the script can't extract enough content (JS-rendered, soft paywall, cookie wall):

```
mcp__playwright__browser_navigate   →  url: "<article_url>"
```

If a consent/cookie banner appears:
```
mcp__playwright__browser_click      →  target the "Accept" or "Agree" button
```

For lazy-loaded or paginated content:
```
mcp__playwright__browser_scroll_down   →  repeat until end of article
mcp__playwright__browser_get_visible_text  →  collect all text
```

After collecting the full text via Playwright:
1. Strip nav, sidebars, cookie banners, comment sections, "read more" prompts.
2. Derive a slug from the article title.
3. Save the cleaned content to `knowledge/raw/articles/<slug>.md` using the Write tool.
4. Use that file as the content for insight generation.

---

## Failures

| Symptom | Cause | Fix |
|---|---|---|
| Exit code 1 | Network error / DNS failure | Check URL; retry |
| Exit code 2 | JS-rendered or paywalled | Use Playwright MCP fallback above |
| `< 200 words` extracted | Thin page or redirect to login | Playwright fallback |

---

## Insight guidance for web articles

- Capture the central thesis explicitly — blogs often bury the lead.
- Flag surprising statistics or counter-data, noting the author's cited source.
- For listicle-style posts, evaluate which items are genuinely non-obvious vs. filler.
- For opinion pieces, capture what the author argues *against* (counter-intuitive angle) as well as *for*.
- Note author and publication in the metadata header if available.
