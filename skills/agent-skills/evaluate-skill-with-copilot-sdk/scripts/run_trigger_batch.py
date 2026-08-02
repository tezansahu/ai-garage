#!/usr/bin/env python3
"""Run triggering evals for all skills in a plugin directory.

Discovers skills by scanning the plugin directory for subdirectories containing
a SKILL.md, matches each to a queryset file (by skill name), and runs the
triggering eval for each. Results are written per-skill under the output root,
then a dashboard is generated covering all skills.

Usage:
    python run_trigger_batch.py \
        --plugin-path PATH/TO/plugin \
        --querysets-dir PATH/TO/querysets/ \
        [--runs 3] [--threshold 0.5] [--concurrency 3] \
        [--model claude-sonnet-4.6] [--out RESULTS/]

Queryset matching: for a skill named "foo", looks for "foo.json" in the
querysets directory.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
import tempfile
from pathlib import Path

from eval_harness import DEFAULT_MODEL, load_queryset, parse_skill_md, results_root
from run_trigger_eval import measure, print_table, write_isolated_skill


async def run_batch(
    plugin_path: Path,
    querysets_dir: Path,
    *,
    out_root: Path,
    runs: int = 3,
    threshold: float = 0.5,
    concurrency: int = 3,
    model: str = DEFAULT_MODEL,
) -> list[dict]:
    """Run triggering eval for every skill that has a matching queryset."""

    # Discover skills in plugin
    skills = []
    for child in sorted(plugin_path.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            try:
                name, desc, _ = parse_skill_md(child)
                skills.append((name, desc, child))
            except Exception as e:
                print(f"  SKIP {child.name}: {e}", file=sys.stderr)

    if not skills:
        print(f"No skills found in {plugin_path}", file=sys.stderr)
        return []

    print(f"Found {len(skills)} skills: {', '.join(s[0] for s in skills)}",
          file=sys.stderr, flush=True)

    all_results = []
    for i, (name, description, skill_path) in enumerate(skills, 1):
        queryset_path = querysets_dir / f"{name}.json"
        if not queryset_path.is_file():
            print(f"\n[{i}/{len(skills)}] {name} — SKIP (no queryset at {queryset_path.name})",
                  file=sys.stderr, flush=True)
            continue

        print(f"\n[{i}/{len(skills)}] {name}", file=sys.stderr, flush=True)
        queryset = load_queryset(queryset_path)

        # Run in-context with the full plugin directory
        output = await measure(
            queryset, name, description,
            skill_directories=[str(plugin_path)],
            runs=runs, threshold=threshold,
            concurrency=concurrency, model=model,
        )

        # Print per-skill summary
        s = output["summary"]
        print(f"  => {s['passed']}/{s['queries']} pass | "
              f"accuracy={s['accuracy']:.0%} precision={s['precision']:.0%} "
              f"recall={s['recall']:.0%}", file=sys.stderr, flush=True)

        # Write per-skill results
        skill_out = out_root / name / "triggering"
        skill_out.mkdir(parents=True, exist_ok=True)
        out_file = skill_out / "trigger_results.json"
        out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
        all_results.append(output)

    return all_results


def main() -> None:
    # On Windows, tearing down a CLI subprocess mid-generation (what the
    # early-exit triggering path does) can deliver a spurious CTRL_C to this
    # process. asyncio's runner turns that into a KeyboardInterrupt and cancels
    # the entire batch. Setting SIGINT to SIG_IGN before the event loop starts
    # both ignores the stray signal and stops asyncio from installing its own
    # interrupt-counting handler, so the run survives. Genuine hangs are still
    # bounded by the per-run timeout in run_session.
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    # The same early teardown races make the SDK log noisy post-disconnect
    # JSON-RPC "unknown session" tracebacks. They don't affect verdicts
    # (skill_invoked is decided before we disconnect), so keep the logs readable.
    logging.getLogger("copilot").setLevel(logging.CRITICAL)

    ap = argparse.ArgumentParser(
        description="Run triggering evals for all skills in a plugin")
    ap.add_argument("--plugin-path", required=True,
                    help="Path to the plugin directory containing skill subdirectories")
    ap.add_argument("--querysets-dir", required=True,
                    help="Directory containing <skill-name>.json queryset files")
    ap.add_argument("--runs", type=int, default=3, help="Runs per query (default 3)")
    ap.add_argument("--threshold", type=float, default=0.5, help="Trigger-rate threshold")
    ap.add_argument("--concurrency", type=int, default=3, help="Max parallel sessions")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Model id")
    ap.add_argument("--out", required=True,
                    help="Results root (each skill gets a subdirectory)")
    args = ap.parse_args()

    plugin_path = Path(args.plugin_path).resolve()
    querysets_dir = Path(args.querysets_dir).resolve()
    out_root = Path(args.out).resolve()

    if not plugin_path.is_dir():
        sys.exit(f"Plugin path not found: {plugin_path}")
    if not querysets_dir.is_dir():
        sys.exit(f"Querysets directory not found: {querysets_dir}")

    print(f"{'=' * 70}", file=sys.stderr, flush=True)
    print(f"Batch Triggering Eval — {args.model}, {args.runs} runs/query",
          file=sys.stderr, flush=True)
    print(f"{'=' * 70}", file=sys.stderr, flush=True)
    print(f"Plugin:    {plugin_path}", file=sys.stderr, flush=True)
    print(f"Querysets: {querysets_dir}", file=sys.stderr, flush=True)
    print(f"Output:    {out_root}", file=sys.stderr, flush=True)

    all_results = asyncio.run(run_batch(
        plugin_path, querysets_dir,
        out_root=out_root,
        runs=args.runs, threshold=args.threshold,
        concurrency=args.concurrency, model=args.model,
    ))

    if not all_results:
        print("\nNo results collected.", file=sys.stderr)
        sys.exit(1)

    # Print final summary table
    print(f"\n{'=' * 70}", file=sys.stderr, flush=True)
    print(f"{'Skill':<24} {'Passed':<10} {'Accuracy':<10} {'F1':<10} "
          f"{'Precision':<10} {'Recall':<10}", file=sys.stderr, flush=True)
    print(f"{'-' * 70}", file=sys.stderr, flush=True)
    for r in all_results:
        s = r["summary"]
        p, rec = s["precision"], s["recall"]
        f1 = 2 * p * rec / (p + rec) if (p + rec) > 0 else 0.0
        print(f"{r['skill_name']:<24} {s['passed']}/{s['queries']:<7} "
              f"{s['accuracy']:<10.0%} {f1:<10.0%} {s['precision']:<10.0%} "
              f"{s['recall']:<10.0%}", file=sys.stderr, flush=True)
    print(f"{'=' * 70}", file=sys.stderr, flush=True)

    # Generate dashboard
    from generate_trigger_dashboard import discover_results, build_dashboard_data
    results = discover_results(out_root)
    if results:
        data = build_dashboard_data(results)
        data["model"] = args.model  # inject model since we know it
        template_path = Path(__file__).resolve().parent.parent / "assets" / "trigger_dashboard_template.html"
        template = template_path.read_text(encoding="utf-8")
        html = template.replace("__DATA__", json.dumps(data))
        dashboard_path = out_root / "trigger_dashboard.html"
        dashboard_path.write_text(html, encoding="utf-8")
        print(f"\nDashboard: {dashboard_path}", file=sys.stderr, flush=True)

    # Output JSON summary to stdout for scripting
    print(json.dumps([r["summary"] | {"skill_name": r["skill_name"]} for r in all_results], indent=2))


if __name__ == "__main__":
    main()
