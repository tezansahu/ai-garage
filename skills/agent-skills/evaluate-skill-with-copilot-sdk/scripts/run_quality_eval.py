#!/usr/bin/env python3
"""Run each test prompt with the skill and without it, and save the outputs.

The unit of evidence for output quality is a pair of runs on the same prompt:
one where the skill is available (and nudged into use, so we measure its
instructions rather than its triggering) and one baseline where it's absent.
Comparing the pair is what separates "the skill helped" from "the model was
going to do fine anyway."

Results land in a workspace laid out for grading and review:

    <workspace>/iteration-<N>/
      eval-<name>/
        eval_metadata.json
        with_skill/run-1/{outputs/, run_result.json, timing.json, transcript.md}
        without_skill/run-1/{...}

Usage:
    python run_quality_eval.py --skill-path PATH --evalset evals.json \
        [--out DIR] [--iteration 1] [--runs 1] [--concurrency 3] \
        [--model ...] [--no-force-skill]

Evalset format: see references/schemas.md (the `evals` array).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

from eval_harness import DEFAULT_MODEL, parse_skill_md, quality_workspace, run_many, run_session


def slug(text: str) -> str:
    keep = "".join(c if c.isalnum() or c in "-_ " else "" for c in text)
    return "-".join(keep.lower().split())[:48] or "eval"


def isolate_skill(skill_path: Path, dest_parent: Path) -> Path:
    """Copy the whole skill into `dest_parent/<name>/` so only it is discoverable.

    Copying the full directory (not just SKILL.md) means bundled scripts,
    references, and assets are available exactly as in production.
    """
    name = skill_path.name
    dest = dest_parent / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill_path, dest)
    return dest_parent


async def one_run(eval_item, config, run_no, *, skill_name, skill_dirs, disabled,
                  system_append, workspace_iter, model):
    """Execute a single (eval, config, run) and persist its artifacts."""
    eval_name = eval_item.get("name") or slug(eval_item["prompt"])
    run_dir = workspace_iter / f"eval-{eval_name}" / config / f"run-{run_no}"
    outputs = run_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    # Stage input files inside outputs/ so the agent can read them by relative
    # path; the snapshot diff in the harness excludes them from produced outputs.
    for f in eval_item.get("files", []):
        src = Path(f)
        if src.exists():
            shutil.copy2(src, outputs / src.name)

    result = await run_session(
        eval_item["prompt"],
        target_skill=skill_name if config == "with_skill" else None,
        skill_directories=skill_dirs,
        disabled_skills=disabled,
        working_directory=outputs,
        system_append=system_append if config == "with_skill" else None,
        model=model,
    )

    (run_dir / "run_result.json").write_text(
        json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    (run_dir / "timing.json").write_text(json.dumps({
        "total_tokens": result.total_tokens,
        "duration_ms": int(result.duration_seconds * 1000),
        "total_duration_seconds": result.duration_seconds,
    }, indent=2), encoding="utf-8")
    (run_dir / "transcript.md").write_text(
        f"## Eval Prompt\n\n{eval_item['prompt']}\n\n## Config\n\n{config} "
        f"(skill_invoked={result.skill_invoked})\n\n## Final Response\n\n"
        f"{result.final_text}\n", encoding="utf-8")

    status = "used" if result.skill_invoked else ("baseline" if config == "without_skill" else "NOT USED")
    print(f"  [{config}/run-{run_no}] {eval_name}: {status}, "
          f"{result.total_tokens} tok, {result.duration_seconds}s, "
          f"{len(result.output_files)} file(s)"
          + (f"  ERROR: {result.error}" if result.error else ""), file=sys.stderr)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Run quality evals: with_skill vs without_skill")
    ap.add_argument("--skill-path", required=True)
    ap.add_argument("--evalset", required=True, help="JSON with an `evals` array")
    ap.add_argument("--out", default=None,
                    help="Results root (default: <skill>_eval_results/ at repo root)")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--runs", type=int, default=1, help="Runs per config (raise to 3 to get stddev)")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--no-force-skill", action="store_true",
                    help="Don't nudge the agent to use the skill; measure marginal value instead")
    args = ap.parse_args()

    skill_path = Path(args.skill_path).resolve()
    skill_name, _, _ = parse_skill_md(skill_path)
    evalset = json.loads(Path(args.evalset).read_text(encoding="utf-8"))
    evals = evalset["evals"] if isinstance(evalset, dict) else evalset

    workspace_iter = quality_workspace(skill_name, out=args.out) / f"iteration-{args.iteration}"
    workspace_iter.mkdir(parents=True, exist_ok=True)

    system_append = None if args.no_force_skill else (
        f"A skill named '{skill_name}' is available and directly relevant to this "
        f"task. Use it to complete the request."
    )

    # One isolated copy of the skill, shared read-only across all with_skill runs.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="quality-eval-") as tmp:
        skill_parent = str(isolate_skill(skill_path, Path(tmp)))

        # Write eval metadata (prompt + assertions) once per eval for the grader/viewer.
        for item in evals:
            name = item.get("name") or slug(item["prompt"])
            meta_dir = workspace_iter / f"eval-{name}"
            meta_dir.mkdir(parents=True, exist_ok=True)
            (meta_dir / "eval_metadata.json").write_text(json.dumps({
                "eval_id": item.get("id"),
                "eval_name": name,
                "prompt": item["prompt"],
                "assertions": item.get("assertions", []),
            }, indent=2), encoding="utf-8")

        tasks = []
        for item in evals:
            for run_no in range(1, args.runs + 1):
                tasks.append(one_run(
                    item, "with_skill", run_no,
                    skill_name=skill_name, skill_dirs=[skill_parent], disabled=None,
                    system_append=system_append, workspace_iter=workspace_iter, model=args.model))
                tasks.append(one_run(
                    item, "without_skill", run_no,
                    skill_name=skill_name, skill_dirs=[], disabled=None,
                    system_append=None, workspace_iter=workspace_iter, model=args.model))

        print(f"Running {len(tasks)} runs "
              f"({len(evals)} evals x 2 configs x {args.runs} run(s))...", file=sys.stderr)
        asyncio.run(run_many_wrapper(tasks, args.concurrency))

    print(f"\nOutputs in {workspace_iter}", file=sys.stderr)
    print("Next: grade_quality.py to score assertions and build benchmark.json", file=sys.stderr)


async def run_many_wrapper(tasks, concurrency):
    return await run_many(tasks, concurrency=concurrency)


if __name__ == "__main__":
    main()
