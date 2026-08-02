#!/usr/bin/env python3
"""Measure how reliably a skill's description triggers on a set of queries.

Triggering is decided entirely by the skill's `name` + `description`: the agent
sees only those at startup and reads the full SKILL.md only if it decides the
skill is relevant. So this script isolates the skill under test in a temp
directory containing just its frontmatter, runs each labeled query several times
(triggering is nondeterministic), and reports the trigger rate.

A should-trigger query passes if its trigger rate is at or above the threshold;
a should-not-trigger query passes if it's below. Running each query multiple
times and averaging is what makes the signal stable enough to act on.

Usage:
    python run_trigger_eval.py --skill-path PATH --queryset queries.json \
        [--runs 3] [--threshold 0.5] [--concurrency 3] [--model ...] \
        [--description "override to test"] [--in-context] [--out DIR]

Queryset format: a JSON list of {"query": str, "should_trigger": bool}.
See references/schemas.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

from eval_harness import DEFAULT_MODEL, load_queryset, parse_skill_md, results_root, run_many, run_session


def write_isolated_skill(name: str, description: str, root: Path) -> Path:
    """Write a minimal skill (frontmatter + stub body) under `root`.

    Only name + description matter for triggering, so a stub body is faithful
    and keeps runs fast. Returns `root` to use as `skill_directories`.
    """
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    # Block scalar for the description so quotes/newlines never break the YAML.
    indented = "\n  ".join(description.split("\n"))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: |\n  {indented}\n---\n\n"
        f"# {name}\n\nInvoke this skill when the request matches its description.\n",
        encoding="utf-8",
    )
    return root


async def measure(
    queryset: list[dict],
    skill_name: str,
    description: str,
    *,
    skill_directories: list[str],
    runs: int = 3,
    threshold: float = 0.5,
    concurrency: int = 3,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Run every query `runs` times and score trigger rates against the label."""
    # Flatten to (index, query) tasks so runs of the same query execute in parallel.
    flat = [(i, item) for i, item in enumerate(queryset) for _ in range(runs)]
    coros = [
        run_session(
            item["query"],
            target_skill=skill_name,
            skill_directories=skill_directories,
            stop_on_trigger=True,
            model=model,
        )
        for _, item in flat
    ]
    results = await run_many(coros, concurrency=concurrency)

    per_query: list[list[bool]] = [[] for _ in queryset]
    for (idx, _), res in zip(flat, results):
        per_query[idx].append(bool(res.skill_invoked))

    scored = []
    for item, triggers in zip(queryset, per_query):
        n = len(triggers)
        rate = sum(triggers) / n if n else 0.0
        should = bool(item["should_trigger"])
        passed = (rate >= threshold) if should else (rate < threshold)
        scored.append({
            "query": item["query"],
            "should_trigger": should,
            "triggers": sum(triggers),
            "runs": n,
            "trigger_rate": round(rate, 3),
            "pass": passed,
        })

    # Confusion matrix over individual runs (not per-query) for precision/recall.
    tp = sum(r["triggers"] for r in scored if r["should_trigger"])
    pos_runs = sum(r["runs"] for r in scored if r["should_trigger"])
    fn = pos_runs - tp
    fp = sum(r["triggers"] for r in scored if not r["should_trigger"])
    neg_runs = sum(r["runs"] for r in scored if not r["should_trigger"])
    tn = neg_runs - fp
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0

    passed_q = sum(1 for r in scored if r["pass"])
    return {
        "skill_name": skill_name,
        "description": description,
        "threshold": threshold,
        "runs_per_query": runs,
        "results": scored,
        "summary": {
            "queries": len(scored),
            "passed": passed_q,
            "failed": len(scored) - passed_q,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "accuracy": round(accuracy, 3),
        },
    }


def print_table(output: dict) -> None:
    s = output["summary"]
    print(f"\nSkill: {output['skill_name']}   (threshold={output['threshold']}, "
          f"runs/query={output['runs_per_query']})", file=sys.stderr)
    print(f"Description: {output['description']}\n", file=sys.stderr)
    for r in output["results"]:
        status = "PASS" if r["pass"] else "FAIL"
        want = "trigger" if r["should_trigger"] else "no-trig"
        print(f"  [{status}] {r['triggers']}/{r['runs']} want={want}: {r['query'][:64]}",
              file=sys.stderr)
    print(f"\n  {s['passed']}/{s['queries']} queries pass  |  "
          f"precision={s['precision']:.0%} recall={s['recall']:.0%} "
          f"accuracy={s['accuracy']:.0%}\n", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description="Measure skill triggering accuracy")
    ap.add_argument("--skill-path", required=True, help="Path to the skill directory")
    ap.add_argument("--queryset", required=True, help="JSON list of {query, should_trigger}")
    ap.add_argument("--description", default=None, help="Override description to test")
    ap.add_argument("--runs", type=int, default=3, help="Runs per query (default 3)")
    ap.add_argument("--threshold", type=float, default=0.5, help="Trigger-rate threshold")
    ap.add_argument("--concurrency", type=int, default=3, help="Max parallel sessions")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Model id")
    ap.add_argument("--in-context", action="store_true",
                    help="Test with sibling skills present (real parent dir) instead of isolating")
    ap.add_argument("--out", default=None,
                    help="Results root (default: <skill>_eval_results/ at repo root)")
    args = ap.parse_args()

    skill_path = Path(args.skill_path).resolve()
    name, original_desc, _ = parse_skill_md(skill_path)
    description = args.description or original_desc
    queryset = load_queryset(args.queryset)

    with tempfile.TemporaryDirectory(prefix="trigger-eval-") as tmp:
        if args.in_context:
            skill_dirs = [str(skill_path.parent)]
        else:
            skill_dirs = [str(write_isolated_skill(name, description, Path(tmp)))]

        output = asyncio.run(measure(
            queryset, name, description,
            skill_directories=skill_dirs,
            runs=args.runs, threshold=args.threshold,
            concurrency=args.concurrency, model=args.model,
        ))

    print_table(output)
    trig_dir = results_root(name, out=args.out) / "triggering"
    trig_dir.mkdir(parents=True, exist_ok=True)
    out_file = trig_dir / "trigger_results.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}", file=sys.stderr)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
