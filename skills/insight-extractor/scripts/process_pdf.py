#!/usr/bin/env python3
"""
PDF Processing Pipeline

Downloads a remote PDF to raw/pdfs/ (if given a URL) then extracts
structured text using the layout-aware extractor. Saves both files.

Usage:
    python scripts/process_pdf.py paper.pdf
    python scripts/process_pdf.py https://arxiv.org/pdf/2301.00001
    python scripts/process_pdf.py --pages 1-30 https://arxiv.org/pdf/2301.00001

    For ArXiv: use the /pdf/ URL form, not /abs/.

Output files (relative to workspace root):
    raw/pdfs/<slug>.pdf    Downloaded PDF (only created for remote URLs)
    raw/pdfs/<slug>.txt    Extracted plain text

Stdout: summary (Source, PDF path, Extracted path, Words)
        → used by the LLM to know the file paths and title (if extractable).

Exit codes:
    0  success
    1  error (file not found, download failed, extraction failed)

Requirements (at least one):
    pip install pymupdf      # Primary: best multi-column layout handling
    pip install pdfplumber   # Fallback: good table extraction
"""

import re
import sys
import urllib.request
from pathlib import Path

# Ensure utils/ is importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from extract_pdf import extract_pdf_text  # noqa: E402


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def download_pdf(url: str, dest: Path) -> None:
    """Download PDF from URL to dest. Raises on failure."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; InsightExtractor/1.0)"}
    req = urllib.request.Request(url, headers=headers)
    print(f"[PDF] Downloading {url} ...", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=60) as resp:
        dest.write_bytes(resp.read())
    print(f"[PDF] Saved PDF → {dest}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80]


def slug_from_url(url: str) -> str:
    import urllib.parse
    path = urllib.parse.urlparse(url).path.rstrip("/")
    stem = path.split("/")[-1] if "/" in path else path
    stem = re.sub(r"\.pdf$", "", stem, flags=re.I)
    return slugify(stem) or "document"


def slug_from_path(path: str) -> str:
    return slugify(Path(path).stem) or "document"


def parse_page_range(arg: str) -> int:
    """Parse '1-30' or '30' → max page count (end of range)."""
    try:
        return int(arg.split("-")[-1])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    max_pages = None

    if "--pages" in args:
        idx = args.index("--pages")
        if idx + 1 < len(args):
            max_pages = parse_page_range(args[idx + 1])
            args = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]

    if not args:
        print("Usage: process_pdf.py [--pages N-M] <local_path_or_url>", file=sys.stderr)
        sys.exit(1)

    source = args[0]
    is_url = source.startswith("http://") or source.startswith("https://")

    out_dir = Path("raw/pdfs")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Resolve PDF to a local path ---
    if is_url:
        slug = slug_from_url(source)
        pdf_path = out_dir / f"{slug}.pdf"
        try:
            download_pdf(source, pdf_path)
        except Exception as e:
            print(f"[PDF] Download failed: {e}", file=sys.stderr)
            print(f"[PDF] Try manually: curl -L -o {pdf_path} \"{source}\"", file=sys.stderr)
            sys.exit(1)
    else:
        pdf_path = Path(source)
        if not pdf_path.exists():
            print(f"[PDF] File not found: {source}", file=sys.stderr)
            sys.exit(1)
        slug = slug_from_path(source)

    # --- Step 2: Extract text ---
    print("[PDF] Extracting text...", file=sys.stderr)
    text = extract_pdf_text(str(pdf_path), max_pages)

    # --- Step 3: Save extracted text ---
    txt_path = out_dir / f"{slug}.txt"
    txt_path.write_text(text, encoding="utf-8")
    print(f"[PDF] Saved extracted text → {txt_path}", file=sys.stderr)

    # --- Summary (stdout — read by the LLM) ---
    word_count = len(text.split())
    page_note = f"first {max_pages}" if max_pages else "all"
    print(f"Source:     {source}")
    print(f"PDF:        {pdf_path}")
    print(f"Extracted:  {txt_path}")
    print(f"Pages:      {page_note}")
    print(f"Words:      ~{word_count:,}")


if __name__ == "__main__":
    main()
