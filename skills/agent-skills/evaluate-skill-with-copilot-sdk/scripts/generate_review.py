#!/usr/bin/env python3
"""Build a self-contained HTML page for reviewing quality-eval results.

Assertion grading only checks what you thought to assert. A human skimming the
actual outputs catches the rest — the technically-correct-but-misses-the-point
cases, the awkward formatting, the subtly wrong number. This page puts the
with-skill and baseline outputs side by side for each test case, shows the
grades, and collects a note per case.

It's a single static file (data embedded, images inlined as data URIs), so it
works without a server. "Submit All Reviews" downloads feedback.json; drop that
next to the iteration dir and the improvement step reads it.

Usage:
    python generate_review.py [--out DIR | --skill-path PATH] [--iteration 1] [--skill-name NAME]
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

from eval_harness import parse_skill_md, quality_workspace

TEXT_EXT = {".txt", ".md", ".json", ".csv", ".tsv", ".py", ".js", ".ts", ".html",
            ".css", ".yaml", ".yml", ".xml", ".sql", ".sh", ".ini", ".toml"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
MAX_TEXT = 20000  # chars to embed per text file


def load_run(run_dir: Path) -> dict | None:
    """Assemble one run's response, output files, grades, and metrics for the UI."""
    rr_path = run_dir / "run_result.json"
    if not rr_path.exists():
        return None
    rr = json.loads(rr_path.read_text(encoding="utf-8"))
    timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8")) \
        if (run_dir / "timing.json").exists() else {}
    grading = json.loads((run_dir / "grading.json").read_text(encoding="utf-8")) \
        if (run_dir / "grading.json").exists() else None

    files = []
    outputs = run_dir / "outputs"
    for rel in rr.get("output_files", []):
        p = outputs / rel
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in IMAGE_EXT:
            mime = mimetypes.guess_type(str(p))[0] or "image/png"
            data = base64.b64encode(p.read_bytes()).decode("ascii")
            files.append({"name": rel, "kind": "image", "data": f"data:{mime};base64,{data}"})
        elif ext in TEXT_EXT:
            text = p.read_text(encoding="utf-8", errors="replace")[:MAX_TEXT]
            files.append({"name": rel, "kind": "text", "text": text})
        else:
            files.append({"name": rel, "kind": "binary",
                          "note": f"binary, {p.stat().st_size} bytes — open from disk"})

    return {
        "response": rr.get("final_text", ""),
        "skill_invoked": rr.get("skill_invoked", False),
        "output_files": files,
        "grading": grading,
        "tokens": timing.get("total_tokens", rr.get("total_tokens", 0)),
        "time": timing.get("total_duration_seconds", rr.get("duration_seconds", 0)),
    }


def build_data(iteration_dir: Path, skill_name: str, iteration: int) -> dict:
    evals = []
    for eval_dir in sorted(iteration_dir.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        meta = json.loads((eval_dir / "eval_metadata.json").read_text(encoding="utf-8")) \
            if (eval_dir / "eval_metadata.json").exists() else {}
        # Show run-1 of each config (the common case); more runs still grade/aggregate.
        with_dir = eval_dir / "with_skill" / "run-1"
        without_dir = eval_dir / "without_skill" / "run-1"
        evals.append({
            "name": eval_dir.name.removeprefix("eval-"),
            "prompt": meta.get("prompt", ""),
            "with_skill": load_run(with_dir) if with_dir.is_dir() else None,
            "without_skill": load_run(without_dir) if without_dir.is_dir() else None,
        })

    benchmark = {}
    bpath = iteration_dir / "benchmark.json"
    if bpath.exists():
        benchmark = json.loads(bpath.read_text(encoding="utf-8"))

    return {"skill_name": skill_name, "iteration": iteration, "evals": evals, "benchmark": benchmark}


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate an HTML review page for quality evals")
    ap.add_argument("--out", default=None, help="Results root used by run_quality_eval")
    ap.add_argument("--skill-path", default=None,
                    help="Skill under test — locates the default results root when --out is omitted")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--skill-name", default=None, help="Label for the page")
    ap.add_argument("--output", default=None, help="Output HTML path (default: <iteration>/review.html)")
    args = ap.parse_args()

    name = parse_skill_md(Path(args.skill_path))[0] if args.skill_path else None
    try:
        workspace = quality_workspace(name, out=args.out)
    except ValueError:
        sys.exit("Provide --out or --skill-path so I can locate the quality workspace.")
    iteration_dir = workspace / f"iteration-{args.iteration}"
    if not iteration_dir.is_dir():
        sys.exit(f"No such iteration dir: {iteration_dir}")

    skill_name = args.skill_name or name or workspace.parent.name
    data = build_data(iteration_dir, skill_name, args.iteration)
    if not data["evals"]:
        sys.exit("No eval runs found — run run_quality_eval.py first.")

    template = (Path(__file__).resolve().parent.parent / "assets" / "quality_review_template.html").read_text(encoding="utf-8")
    html = template.replace("__DATA__", json.dumps(data))

    out = Path(args.output) if args.output else iteration_dir / "review.html"
    out.write_text(html, encoding="utf-8")
    print(f"Review page: {out}", file=sys.stderr)
    print("Open it in a browser, review each case, then click 'Submit All Reviews'.", file=sys.stderr)
    print(f"That downloads feedback.json — move it to {iteration_dir} for the next step.", file=sys.stderr)
    print(str(out))


if __name__ == "__main__":
    main()
