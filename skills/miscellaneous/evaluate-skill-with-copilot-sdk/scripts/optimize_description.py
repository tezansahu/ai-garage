#!/usr/bin/env python3
"""Optimize a skill's description for reliable triggering.

The loop: evaluate the current description on a train+validation split, feed the
train-set failures to a judge model that proposes a new description, re-evaluate,
and repeat. The winner is chosen by *validation* score, not train score, so we
don't reward a description that merely memorized the train phrasings.

Why a split at all? If you tune against every query you have, you tend to grow a
description that lists the exact wordings in your set and fails on fresh ones.
Holding out ~40% and selecting on it keeps the winner honest.

Usage:
    python optimize_description.py --skill-path PATH --queryset queries.json \
        [--runs 3] [--max-iterations 5] [--holdout 0.4] [--concurrency 3] \
        [--model ...] [--out DIR]

The script does NOT edit your SKILL.md. It prints the best description; you apply
it after reviewing (see references/triggering-evals.md).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
from pathlib import Path

from eval_harness import DEFAULT_MODEL, load_queryset, parse_skill_md, results_root, run_session
from run_trigger_eval import measure, write_isolated_skill
import tempfile

IMPROVE_PROMPT = """You are optimizing the `description` of an agent skill named "{name}".

A skill is loaded lazily: the agent sees only the name and description up front, \
and reads the full instructions only if it decides the skill is relevant. So the \
description alone decides triggering. Your goal: a description that triggers for \
relevant requests and stays quiet for irrelevant ones.

Current description:
<current>
{description}
</current>

Scores so far — {scores}

{failures}
{history}
Full skill body (for context on what it actually does):
<skill_body>
{body}
</skill_body>

Write a better description. Generalize from the failures to the underlying \
*category of intent* rather than pasting in the exact failing phrasings — a \
description that just lists specific queries overfits and bloats. Guidance that \
works well:
- Imperative voice: "Use this skill when..." not "This skill does...".
- Focus on what the user is trying to achieve, not how the skill works.
- If should-trigger queries are missing, widen the intent coverage or name \
contexts where it applies even when the user doesn't say the domain outright.
- If should-not-trigger queries are firing, sharpen the boundary against the \
adjacent thing they actually want.
- Keep it under 1024 characters. If earlier attempts plateaued, try a \
structurally different framing rather than small edits.

Respond with ONLY the new description inside <new_description></new_description> tags."""


def split(queryset: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Stratified train/validation split so both sets keep a mix of labels."""
    rng = random.Random(seed)
    pos = [q for q in queryset if q["should_trigger"]]
    neg = [q for q in queryset if not q["should_trigger"]]
    rng.shuffle(pos)
    rng.shuffle(neg)
    n_pos = max(1, int(len(pos) * holdout)) if pos else 0
    n_neg = max(1, int(len(neg) * holdout)) if neg else 0
    val = pos[:n_pos] + neg[:n_neg]
    train = pos[n_pos:] + neg[n_neg:]
    return train, val


def _format_failures(results: list[dict]) -> str:
    missed = [r for r in results if r["should_trigger"] and not r["pass"]]
    false_fire = [r for r in results if not r["should_trigger"] and not r["pass"]]
    out = []
    if missed:
        out.append("FAILED TO TRIGGER (should have, didn't):")
        out += [f'  - "{r["query"]}" ({r["triggers"]}/{r["runs"]})' for r in missed]
    if false_fire:
        out.append("FALSE TRIGGERS (fired but shouldn't have):")
        out += [f'  - "{r["query"]}" ({r["triggers"]}/{r["runs"]})' for r in false_fire]
    return "\n".join(out) + "\n" if out else "All train queries currently pass.\n"


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = ["PREVIOUS ATTEMPTS (do not repeat — try something different):"]
    for h in history:
        lines.append(f'  train={h["train_score"]}: "{h["description"]}"')
    return "\n".join(lines) + "\n"


async def propose(name: str, body: str, description: str, train_results: dict,
                  history: list[dict], model: str) -> str:
    """Ask a judge session (no skills loaded) for an improved description."""
    prompt = IMPROVE_PROMPT.format(
        name=name,
        description=description,
        scores=f"train {train_results['summary']['passed']}/{train_results['summary']['queries']}",
        failures=_format_failures(train_results["results"]),
        history=_format_history(history),
        body=body[:6000],
    )
    res = await run_session(prompt, model=model)
    text = res.final_text
    m = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    new = (m.group(1) if m else text).strip().strip("\"'")
    # Hard cap per the skill spec; a clumsy truncation still beats a rejected skill.
    if len(new) > 1024:
        new = new[:1021].rstrip() + "..."
    return new


async def optimize(queryset: list[dict], skill_path: Path, *, runs: int,
                   max_iterations: int, holdout: float, concurrency: int,
                   model: str, start_description: str | None = None) -> dict:
    name, original_desc, body = parse_skill_md(skill_path)
    train, val = split(queryset, holdout) if holdout > 0 else (queryset, [])
    print(f"Split: {len(train)} train / {len(val)} validation", file=sys.stderr)

    current = start_description or original_desc
    history: list[dict] = []

    for it in range(1, max_iterations + 1):
        print(f"\n=== Iteration {it}/{max_iterations} ===", file=sys.stderr)
        print(f"Testing: {current[:100]}...", file=sys.stderr)
        with tempfile.TemporaryDirectory(prefix="opt-desc-") as tmp:
            skill_dirs = [str(write_isolated_skill(name, current, Path(tmp)))]
            all_q = train + val
            scored = await measure(all_q, name, current, skill_directories=skill_dirs,
                                   runs=runs, concurrency=concurrency, model=model)

        train_qs = {q["query"] for q in train}
        tr = [r for r in scored["results"] if r["query"] in train_qs]
        va = [r for r in scored["results"] if r["query"] not in train_qs]
        train_res = {"results": tr, "summary": {
            "passed": sum(r["pass"] for r in tr), "queries": len(tr)}}
        val_passed = sum(r["pass"] for r in va)

        record = {
            "iteration": it,
            "description": current,
            "train_score": f"{train_res['summary']['passed']}/{len(tr)}",
            "val_score": f"{val_passed}/{len(va)}" if va else None,
            "train_passed": train_res["summary"]["passed"],
            "train_total": len(tr),
            "val_passed": val_passed,
            "val_total": len(va),
            "results": scored["results"],
        }
        history.append(record)
        print(f"  train={record['train_score']} val={record['val_score']}", file=sys.stderr)

        if train_res["summary"]["passed"] == len(tr):
            print("  All train queries pass — stopping.", file=sys.stderr)
            break
        if it == max_iterations:
            break

        # Blind the judge to validation results so it can't overfit to them.
        blind_history = [{"description": h["description"], "train_score": h["train_score"]}
                         for h in history]
        current = await propose(name, body, current, train_res, blind_history[:-1], model)

    # Pick winner by validation score (fall back to train when no holdout).
    if val:
        best = max(history, key=lambda h: (h["val_passed"], h["train_passed"]))
    else:
        best = max(history, key=lambda h: h["train_passed"])

    return {
        "skill_name": name,
        "original_description": original_desc,
        "best_description": best["description"],
        "best_train_score": best["train_score"],
        "best_val_score": best["val_score"],
        "iterations_run": len(history),
        "history": history,
    }


def write_report(output: dict, path: Path) -> None:
    rows = []
    for h in output["history"]:
        best = "★ " if h["description"] == output["best_description"] else ""
        rows.append(
            f"<tr><td>{best}{h['iteration']}</td><td>train {h['train_score']} | "
            f"val {h['val_score']}</td><td><code>{h['description']}</code></td></tr>"
        )
    path.write_text(
        "<!doctype html><meta charset=utf-8><title>Description optimization</title>"
        "<style>body{font:14px system-ui;margin:2rem;max-width:900px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;"
        "padding:8px;text-align:left;vertical-align:top}code{white-space:pre-wrap}"
        "th{background:#f4f4f4}</style>"
        f"<h1>Triggering optimization — {output['skill_name']}</h1>"
        f"<p><b>Best (by validation):</b> train {output['best_train_score']} | "
        f"val {output['best_val_score']}</p>"
        f"<blockquote><code>{output['best_description']}</code></blockquote>"
        "<table><tr><th>Iter</th><th>Score</th><th>Description</th></tr>"
        + "".join(rows) + "</table>",
        encoding="utf-8",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Optimize a skill description for triggering")
    ap.add_argument("--skill-path", required=True)
    ap.add_argument("--queryset", required=True)
    ap.add_argument("--description", default=None, help="Override the starting description to optimize from")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-iterations", type=int, default=5)
    ap.add_argument("--holdout", type=float, default=0.4, help="Validation fraction (0 to disable)")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out", default=None,
                    help="Results root (default: <skill>_eval_results/ at repo root)")
    args = ap.parse_args()

    queryset = load_queryset(args.queryset)
    output = asyncio.run(optimize(
        queryset, Path(args.skill_path).resolve(),
        runs=args.runs, max_iterations=args.max_iterations, holdout=args.holdout,
        concurrency=args.concurrency, model=args.model, start_description=args.description,
    ))

    print("\n" + "=" * 60, file=sys.stderr)
    print(f"BEST DESCRIPTION (train {output['best_train_score']} | "
          f"val {output['best_val_score']}):", file=sys.stderr)
    print(output["best_description"], file=sys.stderr)

    trig_dir = results_root(output["skill_name"], out=args.out) / "triggering"
    trig_dir.mkdir(parents=True, exist_ok=True)
    (trig_dir / "optimization.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    write_report(output, trig_dir / "optimization.html")
    print(f"Wrote {trig_dir / 'optimization.json'} and optimization.html", file=sys.stderr)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
