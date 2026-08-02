#!/usr/bin/env python3
"""
Web Article Extraction Pipeline

Fetches an article URL and extracts clean body text using trafilatura
(best-in-class) with a BeautifulSoup fallback. Saves to raw/articles/.

Usage:
    python scripts/fetch_article.py "https://example.com/some-article"

Output files (relative to workspace root):
    raw/articles/<slug>.md    Extracted article content in markdown

Stdout: summary (Title, Author, Words, Saved path)
        → used by the LLM to know the title and file path.

Exit codes:
    0  success
    1  unrecoverable network error
    2  content insufficient — Playwright MCP fallback needed
       (LLM should follow references/web-article.md → Playwright Fallback)

Requirements (at least one):
    pip install trafilatura       # Best: handles most sites, extracts metadata
    pip install beautifulsoup4    # Fallback: basic HTML parsing
"""

import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Fetch raw HTML
# ---------------------------------------------------------------------------

def fetch_html(url: str) -> tuple:
    """Fetch HTML. Returns (html_str, final_url_after_redirects)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
        final_url = resp.url
    return html, final_url


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

def extract_with_trafilatura(html: str, url: str) -> dict:
    """Primary: trafilatura — best article extractor, handles most sites."""
    import trafilatura

    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=True,
        output_format="txt",
    )
    meta = trafilatura.extract_metadata(html, default_url=url)
    return {
        "text": text or "",
        "title": (meta.title if meta and meta.title else ""),
        "author": (meta.author if meta and meta.author else ""),
        "date": (meta.date if meta and meta.date else ""),
    }


def extract_with_beautifulsoup(html: str, url: str) -> dict:
    """Fallback: BeautifulSoup-based extraction."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["nav", "header", "footer", "aside", "script", "style",
                     "noscript", "iframe", "form", "button"]):
        tag.decompose()

    # Title
    title = ""
    if soup.title:
        title = soup.title.get_text().strip()
    for h in soup.find_all(["h1", "h2"], limit=3):
        candidate = h.get_text().strip()
        if 5 < len(candidate) < 200:
            title = candidate
            break

    # Article body — try semantic elements first
    body = (
        soup.find("article")
        or soup.find(class_=re.compile(r"article|post|content|entry", re.I))
        or soup.find("main")
        or soup.body
    )
    text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    # Clean whitespace
    lines = [l.strip() for l in text.splitlines()]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(l for l in lines if l))

    return {"text": text, "title": title, "author": "", "date": ""}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80]


def slug_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.rstrip("/")
    stem = path.split("/")[-1] if "/" in path else path
    stem = re.sub(r"\.(html?|php|aspx?)$", "", stem, flags=re.I)
    return slugify(stem) or slugify(urllib.parse.urlparse(url).netloc.split(".")[0])


def format_markdown(data: dict, url: str) -> str:
    parts = []
    if data["title"]:
        parts.append(f"# {data['title']}")
    meta = [f"Source: {url}"]
    if data["author"]:
        meta.append(f"Author: {data['author']}")
    if data["date"]:
        meta.append(f"Published: {data['date']}")
    parts.append("\n".join(f"> {l}" for l in meta))
    parts.append("---")
    parts.append(data["text"])
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: fetch_article.py <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    out_dir = Path("raw/articles")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Fetch HTML ---
    print(f"[Article] Fetching {url} ...", file=sys.stderr)
    try:
        html, final_url = fetch_html(url)
    except Exception as e:
        print(f"[Article] HTTP fetch failed: {e}", file=sys.stderr)
        print()
        print("FALLBACK REQUIRED — use Playwright MCP (see references/web-article.md).")
        sys.exit(1)

    # --- Step 2: Extract content ---
    data = None

    # Try trafilatura (best)
    try:
        import trafilatura  # noqa: F401
        print("[Article] Extracting with trafilatura...", file=sys.stderr)
        data = extract_with_trafilatura(html, final_url)
    except ImportError:
        print("[Article] trafilatura not installed, trying BeautifulSoup...", file=sys.stderr)

    # Fallback: BeautifulSoup
    if not data or len(data.get("text", "")) < 300:
        try:
            print("[Article] Trying BeautifulSoup fallback...", file=sys.stderr)
            data = extract_with_beautifulsoup(html, final_url)
        except ImportError:
            pass

    if not data or len(data.get("text", "")) < 200:
        print("[Article] Insufficient content — page may be JS-rendered or paywalled.", file=sys.stderr)
        print()
        print("FALLBACK REQUIRED — use Playwright MCP (see references/web-article.md).")
        sys.exit(2)

    # --- Step 3: Save to raw/articles/ ---
    slug = slugify(data["title"]) if data.get("title") else slug_from_url(url)
    out_path = out_dir / f"{slug}.md"
    out_path.write_text(format_markdown(data, final_url), encoding="utf-8")
    print(f"[Article] Saved → {out_path}", file=sys.stderr)

    # --- Summary (stdout — read by the LLM) ---
    word_count = len(data["text"].split())
    print(f"Title:    {data.get('title') or '(unknown — check file)'}")
    print(f"Author:   {data.get('author') or '(unknown)'}")
    print(f"Words:    ~{word_count:,}")
    print(f"Saved:    {out_path}")


if __name__ == "__main__":
    main()
