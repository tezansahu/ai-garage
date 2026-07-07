#!/usr/bin/env python3
"""
YouTube Insight Extraction Pipeline

Fetches video title (oEmbed) and transcript (captions API), parses the
WebVTT karaoke format to clean text, and saves both to raw/transcripts/.

Usage:
    python scripts/fetch_youtube.py "https://www.youtube.com/watch?v=XXXX"
    python scripts/fetch_youtube.py "https://youtu.be/XXXX"

Output files (created relative to cwd = workspace root):
    raw/transcripts/<videoID>.vtt   Raw WebVTT from the API
    raw/transcripts/<videoID>.txt   Clean plain-text transcript (with title header)

Stdout: one-line summary per field (Title, Video ID, Language, Words, files)
        → used by the LLM to know the title (for insight file naming) and file paths.

Exit codes:
    0  success
    1  unrecoverable error (bad URL, no captions, network failure)
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure utils/ is importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from parse_vtt import parse_vtt  # noqa: E402

OEMBED_URL = "https://www.youtube.com/oembed"
CAPTIONS_API = "https://website-tools-dot-maestro-218920.uk.r.appspot.com/getYoutubeCaptions"


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def fetch_title(video_url: str) -> str:
    """Fetch video title via YouTube oEmbed (no API key required)."""
    params = urllib.parse.urlencode({"url": video_url, "format": "json"})
    req = urllib.request.Request(f"{OEMBED_URL}?{params}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get("title", "Untitled Video")


def fetch_captions(video_url: str) -> dict:
    """
    Fetch transcript via the captions API.
    Returns dict with keys: videoID, defaultLanguage, selectedCaptions.
    """
    body = json.dumps({"videoUrl": video_url}).encode("utf-8")
    req = urllib.request.Request(
        CAPTIONS_API,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")[:80]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: fetch_youtube.py <youtube_url>", file=sys.stderr)
        sys.exit(1)

    video_url = sys.argv[1]
    out_dir = Path("raw/transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Fetch title ---
    print("[YouTube] Fetching title...", file=sys.stderr)
    try:
        title = fetch_title(video_url)
    except Exception as e:
        print(f"[YouTube] Warning: could not fetch title ({e}). Using fallback.", file=sys.stderr)
        title = "Untitled Video"

    # --- Step 2: Fetch transcript ---
    print("[YouTube] Fetching transcript...", file=sys.stderr)
    try:
        captions_data = fetch_captions(video_url)
    except Exception as e:
        print(f"[YouTube] Error fetching captions: {e}", file=sys.stderr)
        sys.exit(1)

    video_id = captions_data.get("videoID") or slugify(title) or "unknown"
    vtt_text = captions_data.get("selectedCaptions", "")
    language = captions_data.get("defaultLanguage", "unknown")

    if not vtt_text.strip():
        print("[YouTube] Error: API returned no captions for this video.", file=sys.stderr)
        print("[YouTube] The video may have no captions or captions may be disabled.", file=sys.stderr)
        sys.exit(1)

    # --- Step 3: Save raw VTT ---
    vtt_path = out_dir / f"{video_id}.vtt"
    vtt_path.write_text(vtt_text, encoding="utf-8")
    print(f"[YouTube] Saved raw VTT → {vtt_path}", file=sys.stderr)

    # --- Step 4: Parse VTT to clean transcript ---
    print("[YouTube] Parsing VTT...", file=sys.stderr)
    clean_text = parse_vtt(vtt_text)

    if not clean_text.strip():
        print("[YouTube] Warning: VTT parsed to empty text. Check the raw VTT file.", file=sys.stderr)

    # --- Step 5: Save clean transcript (with title header) ---
    txt_path = out_dir / f"{video_id}.txt"
    txt_path.write_text(f"TITLE: {title}\n\n{clean_text}", encoding="utf-8")
    print(f"[YouTube] Saved clean transcript → {txt_path}", file=sys.stderr)

    # --- Summary (stdout — read by the LLM) ---
    word_count = len(clean_text.split())
    print(f"Title:       {title}")
    print(f"Video ID:    {video_id}")
    print(f"Language:    {language}")
    print(f"Words:       ~{word_count:,}")
    print(f"VTT file:    {vtt_path}")
    print(f"Transcript:  {txt_path}")


if __name__ == "__main__":
    main()
