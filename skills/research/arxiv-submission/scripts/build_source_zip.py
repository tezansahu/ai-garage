#!/usr/bin/env python3
"""Build a clean arXiv submission ZIP from a source directory (excludes compiler/editor junk).

Usage:
    python build_source_zip.py <source-dir> --out path/to/Name_arXiv_source.zip
    python build_source_zip.py <source-dir>                 # default out: <dir>/<dir>_arXiv_source.zip
    python build_source_zip.py --verify <zip> <source-dir>  # hash-compare a zip against the dir

Excludes hidden files, VCS dirs, __MACOSX/.DS_Store, and LaTeX aux/log outputs, while KEEPING .bbl.
Prints the manifest with sizes and warns about arXiv-illegal filenames. Uses zipfile via context
managers (no lingering file handles / Windows locks).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import zipfile

ALLOWED_FILENAME = re.compile(r"^[A-Za-z0-9_+\-.,=]+$")
EXCLUDE_EXT = {".aux", ".log", ".out", ".synctex.gz", ".fls", ".fdb_latexmk", ".toc", ".lof",
               ".lot", ".bcf", ".blg", ".nav", ".snm", ".vrb", ".run.xml", ".spl", ".idx", ".ilg",
               # archives: never nest a zip/tarball inside the submission (e.g. a prior build's zip)
               ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".bz2", ".xz"}
EXCLUDE_NAME = {".ds_store", "thumbs.db"}
EXCLUDE_DIR = {".git", ".svn", "__macosx", ".idea", ".vscode", "__pycache__"}


def is_excluded(rel: str, name: str) -> bool:
    low = name.lower()
    if name.startswith("."):
        return True
    if low in EXCLUDE_NAME:
        return True
    if low.endswith(".synctex.gz"):
        return True
    _, ext = os.path.splitext(low)
    if ext in EXCLUDE_EXT:
        return True
    parts = {p.lower() for p in rel.split(os.sep)}
    return bool(parts & EXCLUDE_DIR)


def collect(root: str) -> list[tuple[str, str]]:
    """Return (absolute, arcname) pairs to include, arcname using forward slashes."""
    out = []
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIR and not d.startswith(".")]
        for name in files:
            ap = os.path.join(dp, name)
            rel = os.path.relpath(ap, root)
            if is_excluded(rel, name):
                continue
            out.append((ap, rel.replace(os.sep, "/")))
    return sorted(out, key=lambda t: t[1])


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build(root: str, out: str) -> int:
    items = collect(root)
    if not items:
        print("error: no includable files found")
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for ap, arc in items:
            z.write(ap, arc)

    print(f"wrote {out}\n\nmanifest ({len(items)} files):")
    total = 0
    warned = False
    has_bbl = False
    for ap, arc in items:
        size = os.path.getsize(ap)
        total += size
        base = os.path.basename(arc)
        flag = "" if ALLOWED_FILENAME.match(base) else "  <-- ILLEGAL arXiv filename"
        if flag:
            warned = True
        if base.lower().endswith(".bbl"):
            has_bbl = True
        print(f"  {size:>9,d}  {arc}{flag}")
    print(f"  {'-' * 9}\n  {total:>9,d}  total bytes")

    tex = [a for _, a in items if a.lower().endswith(".tex")]
    print(f"\n.tex files: {', '.join(tex) or 'NONE (?)'}")
    print(f".bbl present: {'yes' if has_bbl else 'no (fine only if inline bibliography)'}")
    if warned:
        print("WARNING: rename files flagged ILLEGAL (allowed: A-Z a-z 0-9 _ + - . , =) and "
              "update the corresponding \\includegraphics/\\input, then rebuild.")
    return 0


def verify(zip_path: str, root: str) -> int:
    """Compare files common to the zip and the directory by SHA256."""
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        mism, miss = [], []
        for n in names:
            disk = os.path.join(root, n.replace("/", os.sep))
            if not os.path.isfile(disk):
                miss.append(n)
                continue
            zh = hashlib.sha256(z.read(n)).hexdigest()
            if zh != sha256(disk):
                mism.append(n)
    print(f"zip files: {len(names)}")
    print(f"missing on disk: {len(miss)}" + (("  -> " + ", ".join(miss)) if miss else ""))
    print(f"content mismatches: {len(mism)}" + (("  -> " + ", ".join(mism)) if mism else ""))
    ok = not mism and not miss
    print("RESULT:", "IN SYNC" if ok else "OUT OF SYNC (rebuild the zip)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Build/verify a clean arXiv source ZIP.")
    ap.add_argument("--verify", metavar="ZIP", help="verify this zip against the source dir")
    ap.add_argument("source", help="source directory")
    ap.add_argument("--out", help="output zip path (build mode)")
    args = ap.parse_args()

    if not os.path.isdir(args.source):
        print(f"error: {args.source} is not a directory")
        return 2
    if args.verify:
        return verify(args.verify, args.source)

    out = args.out
    if not out:
        base = os.path.basename(os.path.abspath(args.source.rstrip("/\\")))
        out = os.path.join(args.source, f"{base}_arXiv_source.zip")
    return build(args.source, out)


if __name__ == "__main__":
    raise SystemExit(main())
