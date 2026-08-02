#!/usr/bin/env python3
"""Normalize an abstract for arXiv's web form: strip LaTeX, force ASCII, check the length limit.

Usage:
    python clean_abstract.py --file abstract.txt          # read from a file
    echo "..." | python clean_abstract.py                 # read from stdin
    python clean_abstract.py --file a.tex --out clean.txt  # also write cleaned text
    python clean_abstract.py --file a.txt --max 1920       # override the length limit

Exit code is 0 when the cleaned text is pure ASCII AND within the limit, else 1 — so it can gate a
submission step. The cleaned abstract is printed to stdout (between markers); the report goes to
stderr.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata

# arXiv's abstract field limit observed in the submission form.
DEFAULT_MAX = 1920

# Non-ASCII -> ASCII substitutions for the characters that actually show up in abstracts and trigger
# arXiv "Bad character(s)" errors.
UNICODE_MAP = {
    "\u2014": "--",  # em dash
    "\u2013": "-",   # en dash
    "\u2012": "-",   # figure dash
    "\u2015": "--",  # horizontal bar
    "\u2018": "'", "\u2019": "'",            # single smart quotes
    "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"',            # double smart quotes
    "\u201e": '"', "\u201f": '"',
    "\u2026": "...",                          # ellipsis
    "\u00a0": " ", "\u2009": " ", "\u2007": " ", "\u202f": " ",  # nbsp / thin / figure / narrow-nbsp
    "\u2003": " ", "\u2002": " ",            # em / en space
    "\u00d7": "x",                            # multiplication sign
    "\u2212": "-",                            # minus sign
    "\u2032": "'", "\u2033": '"',            # prime / double prime
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",  # ligatures
    "\u2192": "->", "\u2190": "<-", "\u21d2": "=>",  # arrows
    "\u00b7": ".", "\u2022": "*",            # middle dot / bullet
    "\u2264": "<=", "\u2265": ">=", "\u2260": "!=", "\u2248": "~",  # relations
}

# LaTeX formatting macros to UNWRAP: \macro{content} -> content.
_UNWRAP = ("emph", "textbf", "textit", "texttt", "textsc", "textrm", "textsf",
           "text", "mbox", "mathrm", "mathbf", "mathit")
# LaTeX macros to DROP entirely, including their {...} argument.
_DROP_WITH_ARG = ("cite", "citep", "citet", "citeauthor", "citeyear", "ref", "eqref",
                  "label", "footnote", "thanks", "url", "href")
# Escaped specials: \x -> x.
_ESCAPES = {r"\%": "%", r"\&": "&", r"\_": "_", r"\$": "$", r"\#": "#", r"\{": "{", r"\}": "}"}


def strip_latex(text: str) -> str:
    """Best-effort conversion of a LaTeX abstract to plain prose."""
    # Remove the abstract environment wrapper if present.
    text = re.sub(r"\\begin\{abstract\}|\\end\{abstract\}", "", text)
    # Line comments (unescaped %). Keep escaped \% for now (handled below).
    text = re.sub(r"(?<!\\)%.*", "", text)
    # Drop macros with their single argument (run twice for nested cases).
    for _ in range(2):
        for m in _DROP_WITH_ARG:
            text = re.sub(r"\\" + m + r"\s*\{[^{}]*\}", "", text)
            text = re.sub(r"\\" + m + r"\s*\[[^\]]*\]\s*\{[^{}]*\}", "", text)
    # Unwrap formatting macros (run twice for nesting).
    for _ in range(2):
        for m in _UNWRAP:
            text = re.sub(r"\\" + m + r"\s*\{([^{}]*)\}", r"\1", text)
    # Escaped specials.
    for k, v in _ESCAPES.items():
        text = text.replace(k, v)
    # Inline math $...$ -> keep inner text without the dollars (usually short symbols).
    text = re.sub(r"\$(.+?)\$", r"\1", text)
    # Common spacing/braces.
    text = text.replace("~", " ").replace("\\\\", " ").replace("\\,", " ").replace("\\ ", " ")
    text = text.replace("``", '"').replace("''", '"').replace("`", "'")
    # Strip leftover simple \macro (no args) but keep the following word.
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)
    text = text.replace("{", "").replace("}", "")
    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_ascii(text: str) -> str:
    """Apply the substitution map, then strip diacritics (accents) to ASCII.

    Any *unmapped* non-ASCII character (e.g. a Greek letter or math symbol with no ASCII
    decomposition) is intentionally left in place so non_ascii_report flags it for manual review,
    rather than being silently deleted and corrupting the text.
    """
    for bad, good in UNICODE_MAP.items():
        text = text.replace(bad, good)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def non_ascii_report(text: str) -> list[str]:
    out = []
    for i, ch in enumerate(text):
        if ord(ch) > 127:
            ctx = text[max(0, i - 20):i + 20].replace("\n", " ")
            out.append(f"  pos {i}: U+{ord(ch):04X} {unicodedata.name(ch, '?')!r}  ...{ctx}...")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean an abstract for arXiv (ASCII + length).")
    ap.add_argument("--file", help="path to a file containing the abstract; omit to read stdin")
    ap.add_argument("--out", help="also write the cleaned abstract to this path")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX, help=f"length limit (default {DEFAULT_MAX})")
    ap.add_argument("--no-latex", action="store_true", help="skip LaTeX stripping (plain text input)")
    args = ap.parse_args()

    raw = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()

    text = raw if args.no_latex else strip_latex(raw)
    cleaned = to_ascii(text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    remaining = non_ascii_report(cleaned)
    length = len(cleaned)
    within = length <= args.max
    ok = within and not remaining

    print("----- CLEANED ABSTRACT -----")
    print(cleaned)
    print("----- END -----")

    r = sys.stderr
    print(f"\nlength           = {length} chars", file=r)
    print(f"within limit     = {within}  (limit {args.max})", file=r)
    print(f"non-ASCII chars  = {len(remaining)}", file=r)
    if remaining:
        print("remaining non-ASCII (fix manually):", file=r)
        print("\n".join(remaining), file=r)
    if not within:
        print(f"OVER by {length - args.max} chars — trim wording and re-run.", file=r)
    print(f"\nRESULT: {'OK' if ok else 'NEEDS WORK'}", file=r)

    if args.out:
        with open(args.out, "w", encoding="ascii") as f:
            f.write(cleaned)
        print(f"wrote {args.out}", file=r)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
