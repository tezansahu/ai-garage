#!/usr/bin/env python3
"""
Extract structured text from a local PDF file for insight extraction.

Handles research papers with:
- Multi-column layouts (2-column detection and correct reading order)
- Tables (converted to markdown format)
- Mathematical equations (represented as [EQUATION])
- Headers/footers filtering
- Hyphenated word reassembly

Usage:
    python extract_pdf.py paper.pdf
    python extract_pdf.py --pages 1-10 paper.pdf   (first 10 pages only)

Note: accepts local files only. Download remote PDFs to raw/pdfs/ first
      (see references/pdf.md for the download procedure).

Output: Structured text printed to stdout.

Requirements (install at least one):
    pip install pymupdf      # Recommended: best layout handling
    pip install pdfplumber   # Good fallback with table extraction
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# PyMuPDF extraction (primary — best for complex layouts)
# ---------------------------------------------------------------------------

def _is_two_column(page, threshold: float = 0.55) -> bool:
    """
    Heuristic: if most text blocks span < threshold * page_width,
    it's likely a 2-column layout.
    """
    try:
        page_w = page.rect.width
        blocks = page.get_text("blocks")
        text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
        if len(text_blocks) < 4:
            return False
        narrow = sum(1 for b in text_blocks if (b[2] - b[0]) < threshold * page_w)
        return narrow / len(text_blocks) > 0.6
    except Exception:
        return False


def _sort_blocks_for_reading_order(blocks, page_width: float):
    """
    Sort text blocks for correct 2-column reading order:
    left column top-to-bottom, then right column top-to-bottom.
    """
    midpoint = page_width / 2

    def col_key(b):
        col = 0 if b[0] < midpoint else 1
        return (col, b[1])

    return sorted(blocks, key=col_key)


def _block_is_header_footer(block, page_height: float, margin: float = 0.06) -> bool:
    """Filter likely headers/footers (top/bottom 6% of page)."""
    y0, y1 = block[1], block[3]
    return y1 < margin * page_height or y0 > (1 - margin) * page_height


def extract_with_pymupdf(pdf_path: str, max_pages: int = None) -> str:
    """Extract text using PyMuPDF with layout-aware block ordering."""
    try:
        import fitz
    except ImportError:
        return None

    doc = fitz.open(pdf_path)
    pages_to_process = list(doc)[:max_pages] if max_pages else list(doc)
    output_parts = []

    for page in pages_to_process:
        page_w = page.rect.width
        page_h = page.rect.height

        blocks = page.get_text("blocks")  # (x0,y0,x1,y1,text,block_no,block_type)
        text_blocks = [
            b for b in blocks
            if b[6] == 0  # text block (not image)
            and b[4].strip()
            and not _block_is_header_footer(b, page_h)
        ]

        if _is_two_column(page):
            text_blocks = _sort_blocks_for_reading_order(text_blocks, page_w)
        else:
            text_blocks = sorted(text_blocks, key=lambda b: (b[1], b[0]))

        page_text = [b[4].strip() for b in text_blocks if b[4].strip()]
        if page_text:
            output_parts.append('\n'.join(page_text))

    doc.close()
    return '\n\n'.join(output_parts)


# ---------------------------------------------------------------------------
# pdfplumber extraction (fallback — better table extraction)
# ---------------------------------------------------------------------------

def extract_with_pdfplumber(pdf_path: str, max_pages: int = None) -> str:
    """Extract text and tables using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        return None

    output_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[:max_pages] if max_pages else pdf.pages

        for page in pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ''
            if text.strip():
                output_parts.append(text.strip())

            for table in (page.extract_tables() or []):
                if not table:
                    continue
                rows = [[str(cell or '').strip().replace('\n', ' ') for cell in row] for row in table]
                if not rows:
                    continue
                header = rows[0]
                col_count = len(header)
                md = [
                    '| ' + ' | '.join(header) + ' |',
                    '| ' + ' | '.join(['---'] * col_count) + ' |',
                ]
                for row in rows[1:]:
                    padded = (row + [''] * col_count)[:col_count]
                    md.append('| ' + ' | '.join(padded) + ' |')
                output_parts.append('\n'.join(md))

    return '\n\n'.join(output_parts)


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _looks_like_equation(line: str) -> bool:
    """Heuristic: line is likely a math equation if dominated by special chars."""
    if len(line) < 3:
        return False
    special = sum(1 for c in line if c in '∑∫∂∇√±×÷≤≥≠≈∈∉⊂⊃∪∩∀∃λσμΔΩαβγδεζηθ')
    if special > 2:
        return True
    alpha = sum(1 for c in line if c.isalpha())
    return alpha / len(line) < 0.2 and len(line) > 10


def clean_extracted_text(text: str) -> str:
    """Post-process extracted PDF text for readability."""
    # Reassemble hyphenated words broken across lines
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # Replace equation-heavy lines with placeholder
    lines = text.split('\n')
    text = '\n'.join('[EQUATION]' if _looks_like_equation(l.strip()) and l.strip() else l for l in lines)

    # Collapse 3+ newlines → 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)

    # Remove lone page-number lines
    text = re.sub(r'(?m)^\s*\d+\s*$', '', text)
    text = re.sub(r'(?mi)^\s*page\s+\d+\s*(of\s+\d+)?\s*$', '', text)

    return text.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_path: str, max_pages: int = None) -> str:
    """Extract text from a local PDF. Tries PyMuPDF first, falls back to pdfplumber."""
    if not Path(pdf_path).exists():
        print(f"[PDF] File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    text = extract_with_pymupdf(pdf_path, max_pages)
    if not text or len(text.strip()) < 100:
        print("[PDF] PyMuPDF returned little/no text, trying pdfplumber...", file=sys.stderr)
        text = extract_with_pdfplumber(pdf_path, max_pages)

    if not text or len(text.strip()) < 50:
        print("[PDF] Error: Could not extract meaningful text.", file=sys.stderr)
        print("[PDF] Install: pip install pymupdf  (or: pip install pdfplumber)", file=sys.stderr)
        sys.exit(1)

    return clean_extracted_text(text)


def parse_page_range(arg: str) -> int:
    """Parse '1-10' or '10' → max page count."""
    try:
        return int(arg.split('-')[-1])
    except ValueError:
        return None


def main():
    args = sys.argv[1:]
    max_pages = None

    if '--pages' in args:
        idx = args.index('--pages')
        if idx + 1 < len(args):
            max_pages = parse_page_range(args[idx + 1])
            args = [a for i, a in enumerate(args) if i not in (idx, idx + 1)]

    if not args:
        print("Usage: extract_pdf.py [--pages N-M] <local_pdf_path>", file=sys.stderr)
        sys.exit(1)

    print(extract_pdf_text(args[0], max_pages))


if __name__ == '__main__':
    main()
