#!/usr/bin/env python3
"""Lint a LaTeX source tree for the arXiv gotchas that block a first submission.

Usage:
    python lint_source.py <source-dir-or-main.tex>

Checks: document class; bibliography mechanism (inline vs external) and whether a required .bbl is
present; every \\includegraphics target (exists? extension OK for pdfLaTeX?); \\today; minted /
shell-escape; absolute \\input/\\include paths; filenames with disallowed characters; leftover
compiler/editor junk. Prints PASS / WARN / FAIL per check and a summary. Exit code 1 if any FAIL.
"""
from __future__ import annotations

import os
import re
import sys

ALLOWED_FILENAME = re.compile(r"^[A-Za-z0-9_+\-.,=]+$")   # arXiv-permitted characters (per path part)
PDFLATEX_IMG_OK = {".pdf", ".png", ".jpg", ".jpeg"}
IMG_NEEDS_CONVERT = {".eps", ".ps"}
JUNK_EXT = {".aux", ".log", ".out", ".synctex.gz", ".fls", ".fdb_latexmk", ".toc", ".lof",
            ".lot", ".bcf", ".blg", ".nav", ".snm", ".vrb", ".run.xml", ".spl", ".idx"}
JUNK_NAME = {".ds_store", "thumbs.db"}

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
_results: list[tuple[str, str, str]] = []


def rec(level: str, check: str, detail: str = "") -> None:
    _results.append((level, check, detail))


def find_main_tex(root: str) -> str | None:
    """The .tex containing \\documentclass; prefer main.tex on ties."""
    candidates = []
    for dp, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".tex"):
                p = os.path.join(dp, f)
                try:
                    if "\\documentclass" in open(p, encoding="utf-8", errors="ignore").read():
                        candidates.append(p)
                except OSError:
                    pass
    if not candidates:
        return None
    candidates.sort(key=lambda p: (os.path.basename(p).lower() != "main.tex", len(p)))
    return candidates[0]


def check_documentclass(tex: str) -> None:
    m = re.search(r"\\documentclass(\[[^\]]*\])?\{([^}]*)\}", tex)
    if m:
        rec(PASS, "documentclass", (m.group(1) or "") + "{" + m.group(2) + "}")
    else:
        rec(FAIL, "documentclass", "none found in the main .tex")


def check_bibliography(tex: str, root: str) -> None:
    inline = bool(re.search(r"\\begin\{thebibliography\}", tex))
    external = bool(re.search(r"\\bibliography\{", tex))
    biblatex = bool(re.search(r"\\addbibresource\{|\\printbibliography", tex))
    bbls = [f for dp, _, fs in os.walk(root) for f in fs if f.lower().endswith(".bbl")]

    if inline and not (external or biblatex):
        rec(PASS, "bibliography", "inline \\begin{thebibliography} -> no .bbl needed")
    elif external or biblatex:
        kind = "biblatex" if biblatex else "BibTeX (\\bibliography{})"
        if bbls:
            rec(PASS, "bibliography", f"external ({kind}); .bbl present: {', '.join(bbls)}")
        else:
            rec(FAIL, "bibliography",
                f"external ({kind}) but NO .bbl in the tree — arXiv will not run BibTeX. "
                f"Include the generated .bbl (Overleaf: Submit -> arXiv, or copy output.bbl).")
    else:
        rec(WARN, "bibliography", "no bibliography mechanism detected — is that intended?")


def check_figures(tex: str, root: str, main_dir: str) -> None:
    targets = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)
    if not targets:
        rec(PASS, "figures", "no \\includegraphics")
        return
    for t in targets:
        t = t.strip()
        base = os.path.normpath(os.path.join(main_dir, t))
        _, ext = os.path.splitext(t)
        found = None
        if ext:
            found = base if os.path.isfile(base) else None
        else:
            for e in (".pdf", ".png", ".jpg", ".jpeg", ".eps"):
                if os.path.isfile(base + e):
                    found, ext = base + e, e
                    break
        if not found:
            rec(FAIL, "figure-missing", f"{t}  (no matching file under source)")
            continue
        el = ext.lower()
        if el in PDFLATEX_IMG_OK:
            rec(PASS, "figure", t)
        elif el in IMG_NEEDS_CONVERT:
            rec(WARN, "figure-format", f"{t}  ({el} needs conversion to PDF for pdfLaTeX)")
        else:
            rec(WARN, "figure-format", f"{t}  (unusual extension {el})")


def check_today(tex: str) -> None:
    rec((WARN if "\\today" in tex else PASS), "no-\\today",
        "\\today present — arXiv stamps the server date; hard-code instead" if "\\today" in tex else "")


def check_minted(tex: str) -> None:
    hits = []
    if re.search(r"\\usepackage(\[[^\]]*\])?\{minted\}", tex):
        hits.append("minted")
    if re.search(r"\\usepackage(\[[^\]]*\])?\{[^}]*shellesc[^}]*\}", tex):
        hits.append("shellesc")
    rec((WARN if hits else PASS), "no-shell-escape",
        (", ".join(hits) + " require shell-escape (unsupported) — use listings/verbatim") if hits else "")


def check_abs_includes(tex: str) -> None:
    abs_inc = re.findall(r"\\(?:input|include)\{(/[^}]*|[A-Za-z]:[\\/][^}]*)\}", tex)
    rec((FAIL if abs_inc else PASS), "relative-includes",
        ("absolute paths: " + ", ".join(abs_inc)) if abs_inc else "")


def check_filenames(root: str) -> None:
    bad, junk, hidden = [], [], []
    for dp, dirs, files in os.walk(root):
        for name in files:
            low = name.lower()
            _, ext = os.path.splitext(low)
            if name.startswith("."):
                hidden.append(name)
            if ext in JUNK_EXT or low in JUNK_NAME or low.endswith(".synctex.gz"):
                junk.append(name)
            if not ALLOWED_FILENAME.match(name):
                bad.append(name)
    rec((FAIL if bad else PASS), "filenames",
        ("disallowed chars/spaces: " + ", ".join(sorted(set(bad)))) if bad else "all filename chars OK")
    if junk or hidden:
        rec(WARN, "junk-files",
            "will be excluded by build_source_zip.py: " + ", ".join(sorted(set(junk + hidden))))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    if os.path.isdir(target):
        root = target
        main_tex = find_main_tex(root)
    elif os.path.isfile(target) and target.lower().endswith(".tex"):
        main_tex = target
        root = os.path.dirname(os.path.abspath(target)) or "."
    else:
        print(f"error: {target} is not a directory or .tex file")
        return 2
    if not main_tex:
        print(f"error: no .tex with \\documentclass found under {root}")
        return 2

    tex = open(main_tex, encoding="utf-8", errors="ignore").read()
    main_dir = os.path.dirname(os.path.abspath(main_tex))

    print(f"main .tex : {os.path.relpath(main_tex, root) if os.path.isdir(target) else main_tex}")
    print(f"root      : {root}\n")

    check_documentclass(tex)
    check_bibliography(tex, root)
    check_figures(tex, root, main_dir)
    check_today(tex)
    check_minted(tex)
    check_abs_includes(tex)
    check_filenames(root)

    width = max(len(c) for _, c, _ in _results)
    for level, check, detail in _results:
        print(f"[{level}] {check.ljust(width)}  {detail}")

    n_fail = sum(1 for l, _, _ in _results if l == FAIL)
    n_warn = sum(1 for l, _, _ in _results if l == WARN)
    print(f"\nsummary: {n_fail} FAIL, {n_warn} WARN, "
          f"{sum(1 for l, _, _ in _results if l == PASS)} PASS")
    if n_fail:
        print("Fix all FAILs before packaging.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
