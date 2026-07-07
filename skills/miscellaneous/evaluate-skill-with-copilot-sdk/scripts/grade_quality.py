#!/usr/bin/env python3
"""Grade quality-eval outputs against assertions, then aggregate a benchmark.

Grading turns each assertion into a PASS/FAIL with concrete evidence. A judge
session (no skills loaded) inspects the run's output files and final response and
returns a verdict per assertion. We deliberately demand evidence and withhold the
benefit of the doubt: a section titled "Summary" that says nothing should fail an
"includes a summary" assertion, because the label being present isn't the point.

After every run is graded, the script aggregates mean/stddev/delta per
configuration into benchmark.json — the numbers that tell you what the skill buys
(higher pass rate) and what it costs (time, tokens).

Usage:
    python grade_quality.py [--out DIR | --skill-path PATH] [--iteration 1] [--concurrency 3] [--model ...]

Reads the workspace produced by run_quality_eval.py. Writes grading.json into each
run dir and benchmark.json at the iteration root. See references/schemas.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import sys
from pathlib import Path

from eval_harness import DEFAULT_MODEL, parse_skill_md, quality_workspace, run_many, run_session

GRADER_PROMPT = """You are grading the output of an AI agent task. Judge each \
assertion strictly and back every verdict with concrete evidence from the actual \
output — quote or reference it, don't guess. If an assertion is only superficially \
satisfied (right label, wrong or empty substance), that is a FAIL.

The task the agent was given:
<prompt>
{prompt}
</prompt>

The agent's final text response:
<response>
{response}
</response>

Output files are in your current working directory. Inspect them with your tools \
before judging — do not rely on the response text alone:
{files}

Assertions to grade:
{assertions}

Respond with ONLY a JSON object (no prose, no code fence) shaped like:
{{"assertion_results": [{{"text": "<assertion>", "passed": true, "evidence": "<what you found>"}}], "summary": {{"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0}}}}"""


def find_runs(iteration_dir: Path) -> list[Path]:
    """Return every run-* dir under the iteration that has an outputs/ folder."""
    return sorted(p.parent for p in iteration_dir.glob("eval-*/*/run-*/outputs") if p.is_dir())


def _parse_json(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)  # last-resort: first {...} block
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


async def grade_run(run_dir: Path, model: str) -> dict:
    """Grade one run's outputs against its eval's assertions; save grading.json."""
    meta_path = run_dir.parent.parent / "eval_metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    assertions = meta.get("assertions", [])
    prompt = meta.get("prompt", "")

    result = json.loads((run_dir / "run_result.json").read_text(encoding="utf-8")) \
        if (run_dir / "run_result.json").exists() else {}
    response = result.get("final_text", "")
    out_files = result.get("output_files", [])

    if not assertions:
        grading = {"assertion_results": [], "summary": {"passed": 0, "failed": 0,
                   "total": 0, "pass_rate": 0.0}, "note": "no assertions defined"}
        (run_dir / "grading.json").write_text(json.dumps(grading, indent=2), encoding="utf-8")
        return grading

    files_desc = "\n".join(f"  - {f}" for f in out_files) or "  (no files were produced)"
    assertions_desc = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(assertions))
    judge = await run_session(
        GRADER_PROMPT.format(prompt=prompt, response=response[:8000],
                             files=files_desc, assertions=assertions_desc),
        working_directory=run_dir / "outputs",
        model=model,
    )

    grading = _parse_json(judge.final_text) or {}
    ar = grading.get("assertion_results", [])
    passed = sum(1 for a in ar if a.get("passed"))
    total = len(ar) or len(assertions)
    grading.setdefault("summary", {})
    grading["summary"].update({"passed": passed, "failed": total - passed,
                               "total": total, "pass_rate": round(passed / total, 3) if total else 0.0})
    if not ar:
        grading["error"] = "judge did not return parseable assertion_results"

    (run_dir / "grading.json").write_text(json.dumps(grading, indent=2), encoding="utf-8")
    cfg = run_dir.parent.name
    print(f"  graded {run_dir.parent.parent.name}/{cfg}/{run_dir.name}: "
          f"{passed}/{total}", file=sys.stderr)
    return grading


def _stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    stddev = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    return {"mean": round(mean, 4), "stddev": round(stddev, 4),
            "min": round(min(values), 4), "max": round(max(values), 4)}


def aggregate(iteration_dir: Path) -> dict:
    """Roll graded runs up into per-config stats and a with/without delta."""
    by_config: dict[str, list[dict]] = {}
    runs_out: list[dict] = []
    # Track how often each assertion passes per config, to flag non-discriminating ones.
    assertion_pass: dict[str, dict[str, list[bool]]] = {}

    for run_dir in find_runs(iteration_dir):
        config = run_dir.parent.name
        eval_name = run_dir.parent.parent.name.removeprefix("eval-")
        grading = json.loads((run_dir / "grading.json").read_text(encoding="utf-8")) \
            if (run_dir / "grading.json").exists() else {}
        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8")) \
            if (run_dir / "timing.json").exists() else {}
        summ = grading.get("summary", {})
        rec = {
            "eval_name": eval_name,
            "configuration": config,
            "run_number": int(run_dir.name.split("-")[1]),
            "result": {
                "pass_rate": summ.get("pass_rate", 0.0),
                "passed": summ.get("passed", 0),
                "total": summ.get("total", 0),
                "time_seconds": timing.get("total_duration_seconds", 0.0),
                "tokens": timing.get("total_tokens", 0),
            },
        }
        runs_out.append(rec)
        by_config.setdefault(config, []).append(rec["result"])
        for a in grading.get("assertion_results", []):
            assertion_pass.setdefault(a.get("text", "?"), {}).setdefault(config, []).append(bool(a.get("passed")))

    summary = {}
    for config, results in by_config.items():
        summary[config] = {
            "pass_rate": _stats([r["pass_rate"] for r in results]),
            "time_seconds": _stats([r["time_seconds"] for r in results]),
            "tokens": _stats([float(r["tokens"]) for r in results]),
        }

    if "with_skill" in summary and "without_skill" in summary:
        w, wo = summary["with_skill"], summary["without_skill"]
        summary["delta"] = {
            "pass_rate": round(w["pass_rate"]["mean"] - wo["pass_rate"]["mean"], 4),
            "time_seconds": round(w["time_seconds"]["mean"] - wo["time_seconds"]["mean"], 4),
            "tokens": round(w["tokens"]["mean"] - wo["tokens"]["mean"], 1),
        }

    notes = _analyst_notes(assertion_pass, runs_out)
    return {"runs": runs_out, "run_summary": summary, "notes": notes}


def _analyst_notes(assertion_pass: dict, runs_out: list[dict]) -> list[str]:
    """Surface patterns the aggregate means hide (non-discriminating asserts, variance)."""
    notes = []
    for text, per_cfg in assertion_pass.items():
        w = per_cfg.get("with_skill", [])
        wo = per_cfg.get("without_skill", [])
        if w and wo and all(w) and all(wo):
            notes.append(f"Assertion always passes in both configs (non-discriminating): \"{text}\"")
        elif w and wo and not any(w) and not any(wo):
            notes.append(f"Assertion always fails in both configs (broken or too hard): \"{text}\"")
        elif w and wo and all(w) and not any(wo):
            notes.append(f"Assertion passes only with the skill (clear skill value): \"{text}\"")
    # Flag high pass-rate variance within a config for the same eval.
    from collections import defaultdict
    grp = defaultdict(list)
    for r in runs_out:
        grp[(r["eval_name"], r["configuration"])].append(r["result"]["pass_rate"])
    for (name, cfg), rates in grp.items():
        if len(rates) > 1 and (max(rates) - min(rates)) >= 0.5:
            notes.append(f"High variance for {name} ({cfg}): pass rates {rates} — possibly flaky")
    return notes


def main() -> None:
    ap = argparse.ArgumentParser(description="Grade quality-eval runs and aggregate a benchmark")
    ap.add_argument("--out", default=None, help="Results root used by run_quality_eval")
    ap.add_argument("--skill-path", default=None,
                    help="Skill under test — locates the default results root when --out is omitted")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    name = parse_skill_md(Path(args.skill_path))[0] if args.skill_path else None
    try:
        iteration_dir = quality_workspace(name, out=args.out) / f"iteration-{args.iteration}"
    except ValueError:
        sys.exit("Provide --out or --skill-path so I can locate the quality workspace.")
    if not iteration_dir.is_dir():
        sys.exit(f"No such iteration dir: {iteration_dir}")

    runs = find_runs(iteration_dir)
    print(f"Grading {len(runs)} runs...", file=sys.stderr)
    asyncio.run(run_many([grade_run(r, args.model) for r in runs], concurrency=args.concurrency))

    benchmark = aggregate(iteration_dir)
    (iteration_dir / "benchmark.json").write_text(json.dumps(benchmark, indent=2), encoding="utf-8")

    s = benchmark["run_summary"]
    print("\n=== Benchmark ===", file=sys.stderr)
    for cfg in ("with_skill", "without_skill"):
        if cfg in s:
            print(f"  {cfg:14s} pass_rate={s[cfg]['pass_rate']['mean']:.0%} "
                  f"(±{s[cfg]['pass_rate']['stddev']:.2f})  "
                  f"time={s[cfg]['time_seconds']['mean']:.1f}s  "
                  f"tokens={s[cfg]['tokens']['mean']:.0f}", file=sys.stderr)
    if "delta" in s:
        d = s["delta"]
        print(f"  delta          pass_rate={d['pass_rate']:+.2f}  "
              f"time={d['time_seconds']:+.1f}s  tokens={d['tokens']:+.0f}", file=sys.stderr)
    for n in benchmark["notes"]:
        print(f"  note: {n}", file=sys.stderr)
    print(f"\nWrote {iteration_dir / 'benchmark.json'}", file=sys.stderr)
    print("Next: generate_review.py to review outputs and give feedback", file=sys.stderr)


if __name__ == "__main__":
    main()
