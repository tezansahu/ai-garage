# PDF Extraction

All PDF handling is done by `scripts/process_pdf.py`. It downloads the PDF to
`knowledge/raw/pdfs/` (if given a URL), extracts structured text, and saves the result.
Accepts both local file paths and remote URLs.

---

## Run the pipeline

```bash
# Local file
python .claude/skills/insight-extractor/scripts/process_pdf.py "path/to/paper.pdf"

# Remote URL (downloads first, then extracts)
python .claude/skills/insight-extractor/scripts/process_pdf.py "https://arxiv.org/pdf/2301.00001"

# Limit pages (useful for long papers — most signal is in first 25-30 pages)
python .claude/skills/insight-extractor/scripts/process_pdf.py --pages 1-30 "https://arxiv.org/pdf/2301.00001"
```

> **ArXiv note:** use the `/pdf/` URL form, not `/abs/`.
> `https://arxiv.org/pdf/2301.00001` ✓ → `https://arxiv.org/abs/2301.00001` ✗

Example output (stdout):
```
Source:     https://arxiv.org/pdf/2301.00001
PDF:        knowledge/raw/pdfs/2301-00001.pdf
Extracted:  knowledge/raw/pdfs/2301-00001.txt
Pages:      all
Words:      ~12,400
```

Install requirements if needed:
```bash
pip install pymupdf      # Primary — best multi-column layout handling
pip install pdfplumber   # Fallback — good table extraction
```

---

## After the script completes

- The paper title is usually the first line(s) of the extracted text — use it for the slug.
- Read `knowledge/raw/pdfs/<slug>.txt` as the content for insight generation.

---

## Failures

| Symptom | Cause | Fix |
|---|---|---|
| Download fails (SSL/403) | Auth-gated or SSL issue | `curl -L -k -o knowledge/raw/pdfs/<name>.pdf "<url>"` then rerun with local path |
| `No meaningful text` | Scanned/image PDF | Cannot extract without OCR — note this limitation to the user |
| Wrong reading order | Complex layout edge case | Try `--pages` on a smaller range to verify; output is best-effort |

---

## What the extractor handles

- **2-column layouts**: detects and reads left column top-to-bottom, then right column
- **Tables**: converted to markdown table format
- **Equations**: replaced with `[EQUATION]` placeholder
- **Headers/footers**: filtered by vertical position heuristic
- **Hyphenated line breaks**: reassembled (`con-\ntext` → `context`)

---

## Insight guidance for research papers

- Lead with the core contribution — what does this paper do that wasn't done before?
- Flag key results with their metric and baseline (e.g., "+3.2% over BERT on SQuAD v2").
- Note the dataset and evaluation setup — this contextualizes how general the findings are.
- Call out methodological innovations separately from empirical findings.
- Capture stated limitations — they often reveal the most interesting open problems.
- `[EQUATION]` in the text marks mathematical content; describe the concept in words if it's a key contribution.
