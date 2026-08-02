#!/usr/bin/env python3
"""Generate an HTML dashboard from triggering eval results.

Works for both single-skill and multi-skill (batch/plugin) evaluations. Scans
the results root for `trigger_results.json` files, aggregates them, and writes
a self-contained HTML dashboard using the template.

For a single skill, pass the skill's results root (contains `triggering/`).
For a batch/plugin, pass the parent results root (contains `<skill>/triggering/`
for each skill).

Usage:
    # After a single-skill eval:
    python generate_trigger_dashboard.py --out RESULTS/my-skill

    # After a batch eval (multiple skills under one root):
    python generate_trigger_dashboard.py --out RESULTS/

    # Using skill-path instead of --out:
    python generate_trigger_dashboard.py --skill-path PATH/TO/skill
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from eval_harness import parse_skill_md, results_root


def discover_results(root: Path) -> list[dict]:
    """Find all trigger_results.json under root and load them.

    Searches for:
    - root/triggering/trigger_results.json (single-skill layout)
    - root/*/triggering/trigger_results.json (batch layout)
    """
    found = []

    # Single-skill: root/triggering/trigger_results.json
    single = root / "triggering" / "trigger_results.json"
    if single.is_file():
        found.append(json.loads(single.read_text(encoding="utf-8")))

    # Batch: root/<skill>/triggering/trigger_results.json
    if root.is_dir():
        for child in sorted(root.iterdir()):
            candidate = child / "triggering" / "trigger_results.json"
            if child.is_dir() and candidate.is_file() and candidate != single:
                found.append(json.loads(candidate.read_text(encoding="utf-8")))

    return found


def build_dashboard_data(results: list[dict]) -> dict:
    """Build the data payload for the HTML template."""
    # Extract common settings from first result
    runs_per_query = results[0].get("runs_per_query", 3) if results else 3
    threshold = results[0].get("threshold", 0.5) if results else 0.5
    model = "unknown"

    # Try to find model info (not stored in trigger_results.json by default,
    # but we include it if present)
    for r in results:
        if "model" in r:
            model = r["model"]
            break

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "model": model,
        "runs_per_query": runs_per_query,
        "threshold": threshold,
        "skills": results,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate a triggering eval dashboard from results")
    ap.add_argument("--out", default=None,
                    help="Results root to scan for trigger_results.json files")
    ap.add_argument("--skill-path", default=None,
                    help="Skill path — used to locate default results root when --out is omitted")
    ap.add_argument("--output", default=None,
                    help="Output HTML path (default: <root>/trigger_dashboard.html)")
    args = ap.parse_args()

    # Resolve the results root
    if args.out:
        root = Path(args.out).resolve()
    elif args.skill_path:
        name = parse_skill_md(Path(args.skill_path))[0]
        root = results_root(name)
    else:
        sys.exit("Provide --out or --skill-path so I can locate trigger results.")

    if not root.is_dir():
        sys.exit(f"Results root not found: {root}")

    results = discover_results(root)
    if not results:
        sys.exit(f"No trigger_results.json found under {root}")

    data = build_dashboard_data(results)

    # Load template and inject data
    template_path = Path(__file__).resolve().parent.parent / "assets" / "trigger_dashboard_template.html"
    template = template_path.read_text(encoding="utf-8")
    html = template.replace("__DATA__", json.dumps(data))

    # Write output
    out_path = Path(args.output) if args.output else root / "trigger_dashboard.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    print(f"Dashboard: {out_path}", file=sys.stderr)
    print(f"Contains {len(results)} skill(s). Open in a browser to review.", file=sys.stderr)
    print(str(out_path))


if __name__ == "__main__":
    main()
