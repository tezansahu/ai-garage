#!/usr/bin/env python3
"""Shared harness for evaluating skills with the GitHub Copilot SDK.

Every other script in this skill imports `run_session` from here. It runs a
single prompt inside an isolated Copilot CLI session and captures the signals
an evaluation cares about:

- whether the skill under test was invoked (the definitive triggering signal)
- which tools ran, how many, and how many failed
- token usage and wall-clock duration
- the assistant's final text and any files written to the working directory

The design goal is reproducibility: every run gets its own CLI subprocess and
config discovery is disabled, so the only skills in play are the ones you point
at explicitly via `skill_directories` / `disabled_skills`. That isolation is what
lets you attribute a behavior change to the skill rather than to ambient state.

Requires: `pip install 'github-copilot-sdk>=1.0.0'`, then `python -m copilot
download-runtime`, plus a logged-in Copilot CLI.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

try:
    from copilot import CopilotClient
    from copilot.session import PermissionHandler, SystemMessageCustomizeConfig
    from copilot.session_events import (
        AssistantMessageData,
        AssistantMessageDeltaData,
        AssistantUsageData,
        SessionErrorData,
        SessionIdleData,
        SessionSkillsLoadedData,
        SkillInvokedData,
        ToolExecutionCompleteData,
        ToolExecutionStartData,
    )
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "The Copilot SDK is not installed. Run:\n"
        "    pip install 'github-copilot-sdk>=1.0.0'\n"
        "and then: python -m copilot download-runtime\n"
        "Make sure the GitHub Copilot CLI is installed and you are logged in.\n"
        f"(import error: {exc})"
    )

# Default model: a fast, cheap Claude that keeps large eval fan-outs affordable.
# Override per-run with --model or globally via COPILOT_EVAL_MODEL; resolve a fuzzy
# name to an id with list_models.py. For triggering evals, match the model your
# users actually run, since triggering behavior is model-dependent. For quality
# grading/judging a stronger model (Sonnet/Opus) gives sharper verdicts.
DEFAULT_MODEL = os.environ.get("COPILOT_EVAL_MODEL", "claude-haiku-4.5")

# How long a single run may take before we give up on it (seconds).
DEFAULT_TIMEOUT = 240


def repo_root(start: Path | None = None) -> Path:
    """The results base: nearest ancestor of `start` (cwd) holding a .git, else cwd.

    Eval output lands under here so it sits at the project root, not wherever a
    script happened to be invoked from.
    """
    start = (start or Path.cwd()).resolve()
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return start


def results_root(skill_name: str | None = None, *, out: str | Path | None = None) -> Path:
    """Where a skill's eval results live.

    `out` wins when given (the user picked a location). Otherwise results go to
    `<repo_root>/<skill_name>_eval_results/`, keyed to the skill under test so
    evaluating several skills never collides.
    """
    if out:
        return Path(out).resolve()
    if not skill_name:
        raise ValueError("results_root needs skill_name when --out is not given")
    return repo_root() / f"{skill_name}_eval_results"


def quality_workspace(skill_name: str | None = None, *, out: str | Path | None = None) -> Path:
    """The quality-eval workspace `<results_root>/quality/` (holds iteration-N/)."""
    return results_root(skill_name, out=out) / "quality"


def load_queryset(path: str | Path) -> list[dict]:
    """Load a triggering queryset from either shape and normalize it.

    Accepts a flat list `[{"query", "should_trigger"}, ...]` or an envelope
    `{"evals": [...]}` / `{"queries": [...]}` — the same `evals` shape a quality
    evalset uses, so one authoring style covers both. Extra per-item fields (id,
    rationale, complexity, ...) are ignored; each item needs `query` and
    `should_trigger`.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        items = data.get("evals") or data.get("queries") or []
    else:
        items = data
    out = [
        {"query": it["query"], "should_trigger": bool(it["should_trigger"])}
        for it in items
        if isinstance(it, dict) and "query" in it and "should_trigger" in it
    ]
    if not out:
        raise ValueError(f"No {{query, should_trigger}} items found in {path}")
    return out


@dataclass
class RunResult:
    """Everything one session tells us. Serializable via `asdict`."""

    prompt: str
    target_skill: str | None = None
    skill_invoked: bool = False
    skills_invoked: list[str] = field(default_factory=list)
    skills_loaded: list[str] = field(default_factory=list)
    tool_calls: dict[str, int] = field(default_factory=dict)
    total_tool_calls: int = 0
    errors: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration_seconds: float = 0.0
    final_text: str = ""
    output_files: list[str] = field(default_factory=list)
    timed_out: bool = False
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _snapshot(directory: Path) -> dict[str, tuple[int, float]]:
    """Map each file under `directory` to (size, mtime). Used to diff outputs."""
    snap: dict[str, tuple[int, float]] = {}
    if not directory or not directory.is_dir():
        return snap
    for p in directory.rglob("*"):
        if p.is_file():
            try:
                st = p.stat()
                snap[str(p.relative_to(directory))] = (st.st_size, st.st_mtime)
            except OSError:
                pass
    return snap


async def run_session(
    prompt: str,
    *,
    target_skill: str | None = None,
    skill_directories: list[str] | None = None,
    disabled_skills: list[str] | None = None,
    working_directory: str | Path | None = None,
    attachments: list[dict] | None = None,
    system_append: str | None = None,
    stop_on_trigger: bool = False,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> RunResult:
    """Run one prompt in an isolated Copilot session and capture the result.

    Args:
        prompt: The user message to send.
        target_skill: Name of the skill you're evaluating. `skill_invoked` is
            True only if a skill with this exact name fires.
        skill_directories: Parent dirs to scan for skills. Each subdir that
            contains a SKILL.md is one discoverable skill. Pass the parent of
            the skill under test (e.g. the temp dir holding just that skill for
            an isolated triggering test).
        disabled_skills: Skills to load-but-disable. This is how you build a
            clean baseline: keep everything identical but make the target skill
            unusable, so any quality delta is attributable to the skill.
        working_directory: Where the agent runs. For quality evals, point this
            at the run's output dir (with input files pre-copied in) so newly
            written files are captured as outputs.
        attachments: SDK attachment dicts, e.g. [{"type": "file", "path": ...}].
        system_append: Extra text appended to the system message. Quality evals
            use this to nudge the agent to actually exercise the skill, so the
            run measures the skill's instructions rather than its triggering.
        stop_on_trigger: For triggering evals only. Stream, and abort the run the
            moment the outcome is known — True when the target skill is invoked,
            False when the agent starts its final answer without it — instead of
            waiting for the whole response we don't need. Leave False for quality
            evals, which need the full trajectory.
        model: Model id. Defaults to COPILOT_EVAL_MODEL or claude-haiku-4.5.
        timeout: Seconds before the run is abandoned and marked timed_out.

    Returns:
        A RunResult. Harness-level failures land in `.error` rather than raising,
        so a single bad run never kills a batch.
    """
    result = RunResult(prompt=prompt, target_skill=target_skill)
    work = Path(working_directory).resolve() if working_directory else None
    before = _snapshot(work) if work else {}

    start = time.monotonic()
    try:
        system_message = None
        if system_append:
            system_message = SystemMessageCustomizeConfig(
                mode="customize",
                sections={"custom_instructions": {"action": "append", "content": system_append}},
            )

        async with CopilotClient(use_logged_in_user=True) as client:
            session = await client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model=model,
                streaming=stop_on_trigger,
                # Deterministic isolation: only the skills we point at are in play.
                enable_config_discovery=False,
                infinite_sessions={"enabled": False},
                skill_directories=skill_directories or [],
                disabled_skills=disabled_skills or [],
                working_directory=str(work) if work else None,
                system_message=system_message,
            )

            done = asyncio.Event()
            text_parts: list[str] = []

            def on_event(event: Any) -> None:
                match event.data:
                    case SessionSkillsLoadedData() as d:
                        result.skills_loaded = [s.name for s in d.skills]
                    case SkillInvokedData() as d:
                        result.skills_invoked.append(d.name)
                        if target_skill and d.name == target_skill:
                            result.skill_invoked = True
                            if stop_on_trigger:
                                done.set()  # triggered — skip generating the answer
                    case AssistantMessageDeltaData():
                        # First streamed answer content with no skill invoked yet
                        # means the agent is answering without it. (Reasoning is a
                        # separate delta event and doesn't count as answering.)
                        if stop_on_trigger and not result.skill_invoked:
                            done.set()
                    case ToolExecutionStartData() as d:
                        name = d.tool_name or "unknown"
                        result.tool_calls[name] = result.tool_calls.get(name, 0) + 1
                        result.total_tool_calls += 1
                    case ToolExecutionCompleteData() as d:
                        if d.success is False:
                            result.errors += 1
                    case AssistantUsageData() as d:
                        result.input_tokens += int(d.input_tokens or 0)
                        result.output_tokens += int(d.output_tokens or 0)
                    case AssistantMessageData() as d:
                        content = getattr(d, "content", None)
                        if content:
                            text_parts.append(str(content))
                    case SessionErrorData() as d:
                        result.error = str(getattr(d, "message", None) or "session error")
                    case SessionIdleData():
                        done.set()

            unsubscribe = session.on(on_event)
            try:
                await session.send(prompt, attachments=attachments or None)
                try:
                    await asyncio.wait_for(done.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    result.timed_out = True
                    result.error = result.error or f"timed out after {timeout}s"
            finally:
                unsubscribe()
                # For stop_on_trigger we've already decided; disconnecting here
                # tears down this run's dedicated CLI subprocess, which stops any
                # still-running generation without needing a separate abort call.
                await session.disconnect()

            result.final_text = "\n".join(text_parts).strip()
    except Exception as exc:  # noqa: BLE001 - surface, don't crash the batch
        result.error = f"{type(exc).__name__}: {exc}"

    result.total_tokens = result.input_tokens + result.output_tokens
    result.duration_seconds = round(time.monotonic() - start, 2)

    if work:
        after = _snapshot(work)
        result.output_files = sorted(
            rel for rel, meta in after.items() if before.get(rel) != meta
        )

    return result


async def run_many(
    coros: Iterable, concurrency: int = 3
) -> list:
    """Run awaitables with a bounded number in flight at once.

    Each run spawns its own CLI subprocess, so unbounded parallelism can swamp
    the machine. A small semaphore keeps throughput high without thrashing;
    3-4 is a good default on a laptop.

    Uses return_exceptions=True so that a single session failure (e.g. from
    asyncio subprocess cleanup race conditions on Windows) cannot cancel the
    entire batch via CancelledError propagation.
    """
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _guarded(coro):
        async with sem:
            return await coro

    results = await asyncio.gather(
        *(_guarded(c) for c in coros), return_exceptions=True
    )
    # Replace exceptions with a RunResult carrying the error, so callers
    # always get a list of RunResult (never bare exceptions).
    cleaned = []
    for r in results:
        if isinstance(r, BaseException):
            cleaned.append(RunResult(
                prompt="",
                error=f"{type(r).__name__}: {r}",
            ))
        else:
            cleaned.append(r)
    return cleaned


def parse_skill_md(skill_path: str | Path) -> tuple[str, str, str]:
    """Return (name, description, full_content) from a skill's SKILL.md.

    Handles the common YAML frontmatter cases: quoted single-line values and
    block scalars (`>`, `|`, and their chomping variants). Kept dependency-free
    on purpose so the skill runs with only the stdlib plus the SDK.
    """
    skill_path = Path(skill_path)
    md = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path
    content = md.read_text(encoding="utf-8")
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{md} is missing YAML frontmatter (no opening '---')")

    end = next((i for i, ln in enumerate(lines[1:], start=1) if ln.strip() == "---"), None)
    if end is None:
        raise ValueError(f"{md} has no closing '---' for its frontmatter")

    name, description = "", ""
    fm = lines[1:end]
    i = 0
    while i < len(fm):
        line = fm[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip("\"'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-", ">+", "|+"):
                block: list[str] = []
                i += 1
                while i < len(fm) and (fm[i].startswith("  ") or fm[i].startswith("\t") or not fm[i].strip()):
                    block.append(fm[i].strip())
                    i += 1
                description = " ".join(b for b in block if b)
                continue
            description = value.strip("\"'")
        i += 1

    return name, description, content


if __name__ == "__main__":  # tiny smoke test
    import sys

    async def _demo():
        r = await run_session(
            sys.argv[1] if len(sys.argv) > 1 else "Reply with exactly: PONG",
        )
        print(r.to_dict())

    asyncio.run(_demo())
