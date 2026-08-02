#!/usr/bin/env python3
"""
Parse WebVTT transcript to clean plain text.

Handles YouTube's karaoke-style VTT (where each word appears incrementally
in overlapping cues), stripping timing metadata and deduplicating text.

Usage:
    # Pipe VTT JSON field:
    echo '...vtt text...' | python parse_vtt.py

    # From file:
    python parse_vtt.py transcript.vtt

    # From argument (inline text):
    python parse_vtt.py "WEBVTT\nKind: captions\n..."

Output: Clean transcript text printed to stdout.
"""

import re
import sys


def parse_vtt(vtt_text: str) -> str:
    """
    Parse WebVTT format to clean transcript text.

    YouTube's VTT format uses karaoke cues: each cue extends the previous
    line with one more word, e.g.:
        cue 1: "Hello"
        cue 2: "Hello world"       <- overlaps cue 1
        cue 3: "Hello world this"  <- overlaps cue 2

    Strategy: extract the last (most complete) text from each timestamp group,
    then deduplicate adjacent identical or prefix-subset lines.
    """
    lines = vtt_text.split('\n')
    segments = []   # (start_ms, text)
    current_start = None
    current_text = None

    def parse_timestamp(ts_str: str) -> int:
        """Convert HH:MM:SS.mmm or MM:SS.mmm to milliseconds."""
        ts_str = ts_str.strip().split(' ')[0]  # remove align/position tags
        parts = ts_str.split(':')
        try:
            if len(parts) == 3:
                h, m, s = parts
            else:
                h, m, s = 0, parts[0], parts[1]
            s_int, ms = s.split('.')
            return int(h) * 3600000 + int(m) * 60000 + int(s_int) * 1000 + int(ms.ljust(3, '0')[:3])
        except Exception:
            return 0

    def clean_cue_text(text: str) -> str:
        """Strip inline timing tags and HTML-like tags from a cue text line."""
        # Remove inline timestamp tags like <00:00:01.280>
        text = re.sub(r'<\d{1,2}:\d{2}:\d{2}\.\d{3}>', '', text)
        # Remove <c> and </c> and <c.color> tags
        text = re.sub(r'</?c(?:\.[^>]*)?>', '', text)
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip WEBVTT header and metadata
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or line.startswith('X-TIMESTAMP'):
            i += 1
            continue

        # Cue numeric identifier (optional line before timestamp)
        if line.isdigit():
            i += 1
            continue

        # Timestamp line
        if '-->' in line:
            parts = line.split('-->')
            start_ms = parse_timestamp(parts[0])
            if current_start != start_ms:
                current_start = start_ms
                current_text = None
            i += 1
            continue

        # Empty line = end of cue block
        if not line:
            i += 1
            continue

        # Text line: clean and accumulate (take last/most-complete line per cue)
        cleaned = clean_cue_text(line)
        if cleaned:
            current_text = cleaned
            # Check if next non-empty line is still part of this cue
            # For multi-line cues, we want to collect all lines
            # But for YouTube karaoke format, we want just the last (complete) line
            segments.append((current_start or 0, cleaned))

        i += 1

    # Deduplicate: remove lines that are exact prefixes of the immediately next line
    # This collapses the karaoke duplicates
    filtered = []
    for idx, (ts, text) in enumerate(segments):
        if idx + 1 < len(segments):
            next_text = segments[idx + 1][1]
            # Skip if current text is a leading substring of the next
            if next_text.startswith(text) and next_text != text:
                continue
            # Skip exact duplicates
            if text == next_text:
                continue
        filtered.append(text)

    # Further dedup: collapse consecutive identical lines
    deduped = []
    prev = None
    for text in filtered:
        if text != prev:
            deduped.append(text)
            prev = text

    # Join into paragraphs - use space, since these are flowing speech segments
    return ' '.join(deduped)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Try to open as file
        try:
            with open(arg, 'r', encoding='utf-8') as f:
                vtt_text = f.read()
        except (FileNotFoundError, OSError):
            # Treat as raw VTT text (unescape \n if passed as single argument)
            vtt_text = arg.replace('\\n', '\n')
    else:
        vtt_text = sys.stdin.read()

    if not vtt_text.strip():
        print("Error: No VTT content provided.", file=sys.stderr)
        sys.exit(1)

    result = parse_vtt(vtt_text)
    print(result)


if __name__ == '__main__':
    main()
