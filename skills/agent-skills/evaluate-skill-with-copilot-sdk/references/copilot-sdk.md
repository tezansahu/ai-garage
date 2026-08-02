# How the harness drives the Copilot SDK

Read this when modifying the scripts, debugging a run, or adapting the harness to
a new eval. It documents the specific SDK behaviors the eval scripts rely on —
the ones that were verified by actually running them, not assumed.

Everything funnels through one function, `run_session()` in
`scripts/eval_harness.py`. It runs a single prompt in an isolated session and
returns a `RunResult`. The other scripts are thin orchestration on top of it.

## The session pattern

```python
async with CopilotClient(use_logged_in_user=True) as client:
    session = await client.create_session(
        on_permission_request=PermissionHandler.approve_all,
        model="claude-haiku-4.5",
        streaming=False,
        enable_config_discovery=False,      # isolation — see below
        infinite_sessions={"enabled": False},
        skill_directories=[parent_dir],     # which skills are discoverable
        disabled_skills=[],                 # which discovered skills are off
        working_directory=str(work),        # where the agent runs / writes
    )
    done = asyncio.Event()
    def on_event(event):
        match event.data:
            case SessionIdleData():
                done.set()
    unsubscribe = session.on(on_event)
    await session.send(prompt)
    await done.wait()
    unsubscribe()
    await session.disconnect()
```

- **One client per run.** Each `CopilotClient` is its own CLI subprocess, which
  gives clean isolation between runs and lets many run in parallel. The tradeoff
  is startup cost per run; that's why concurrency is bounded rather than
  unbounded.
- **`use_logged_in_user=True`** authenticates as the signed-in Copilot user and
  auto-locates the CLI binary. No token handling needed.
- **`on_permission_request=PermissionHandler.approve_all`** is required on every
  session. Evals need the agent to freely read/write in its working dir and run
  tools; approving all is appropriate for a sandboxed eval run.
- **`SessionIdleData` is the "turn done" signal.** Set an `asyncio.Event` in the
  handler and await it. Always pair `session.on(...)` with its returned
  `unsubscribe()` — handlers accumulate otherwise.

## Controlling which skills are in play

This is the crux of skill evaluation, and it's done with three `create_session`
knobs:

| Goal | Setting |
|------|---------|
| Suppress the user's global/ambient skills | `enable_config_discovery=False` |
| Make specific skills discoverable | `skill_directories=[parent]` — each subdir with a `SKILL.md` becomes one skill |
| Load a skill but make it unusable | `disabled_skills=["name"]` |

**Isolation matters for attribution.** With config discovery off and only the
skill under test in `skill_directories`, any behavior change is attributable to
that skill rather than to whatever else happened to be installed. The triggering
and quality scripts both copy the skill into a fresh temp parent to guarantee
this.

**Isolation also makes triggering lenient.** When exactly one skill is present,
the agent reaches for it readily — so an isolated pass rate is optimistic. Point
`skill_directories` at the skill's *real* parent (its siblings included) via
`--in-context` when you want the competitive, production-like signal.

## The events the harness listens to

The SDK emits a rich event stream (`copilot.session_events`). The
harness cares about these:

- **`SkillInvokedData`** — fired when a skill is invoked. `.name` is the skill
  that fired. This is *the* triggering signal: exact and reliable, no text
  parsing. `run_session` sets `skill_invoked=True` when `.name` matches the
  `target_skill`.
- **`SessionSkillsLoadedData`** — lists the skills discovered at startup
  (`.skills[].name`, `.enabled`). Useful to confirm the skill under test was
  actually found. (Expect a built-in like `customize-cloud-agent` to appear
  alongside it — harmless.)
- **`ToolExecutionStartData`** — `.tool_name` per tool call; the harness counts
  these for the tool-usage metric.
- **`ToolExecutionCompleteData`** — `.success` is `False` on a failed tool call;
  counted as an error.
- **`AssistantUsageData`** — `.input_tokens` / `.output_tokens` per model call,
  summed into the token metric.
- **`AssistantMessageData`** — `.content` is the assistant's message text,
  accumulated into `final_text`.
- **`SessionErrorData`** — surfaced into `RunResult.error`.
- **`SessionIdleData`** — end of turn.

If you need a signal the harness doesn't capture (reasoning traces, sub-agent
events, compaction), add a `case` to the `on_event` matcher and a field to
`RunResult`. List the full set with:

```bash
python -c "import copilot.session_events as e; print([n for n in dir(e) if n.endswith('Data')])"
```

## Capturing output files

For quality evals the agent writes files into `working_directory`. The harness
snapshots the directory (path → size+mtime) before the run and diffs it after;
new or modified files become `output_files` (paths relative to the working dir).
Input files copied in beforehand and left untouched are naturally excluded. This
is why `run_quality_eval.py` sets `working_directory` to each run's `outputs/`
folder and pre-copies the eval's input files there.

## Forcing skill use in quality runs

A quality eval should measure the skill's *instructions*, not re-litigate its
triggering (that's Path A's job). So `run_quality_eval.py` passes a
`system_append` nudge on with-skill runs — appended to the system message via
`SystemMessageCustomizeConfig` — telling the agent the skill is relevant and to
use it. The baseline gets no skill and no nudge. If you'd rather measure the
skill's *marginal* value in realistic use (agent decides for itself), pass
`--no-force-skill` and the nudge is dropped.

## Reliability notes

- **Timeouts** are per run (`DEFAULT_TIMEOUT`, 240s). A timed-out run is marked
  `timed_out=True` with an `error`, not raised — one slow run never kills a batch.
- **Harness-level exceptions** land in `RunResult.error` for the same reason.
  Always check `error` when a run's metrics look empty.
- **Triggering runs stop early.** With `stop_on_trigger=True` (used by
  run_trigger_eval), the harness streams and returns the instant the outcome is
  known — the moment `SkillInvokedData` names the target skill (triggered), or the
  first `AssistantMessageDeltaData` arrives with no skill invoked yet (not
  triggered) — then disconnects, killing the run's subprocess so the rest of the
  generation never happens. Reasoning deltas don't count as answering. Quality
  runs leave it False and wait for the full trajectory, which they need.
- **Model choice** defaults to `claude-haiku-4.5` (fast and cheap for large
  fan-outs). Override with `--model` or `COPILOT_EVAL_MODEL`, and resolve a fuzzy
  name to an id with `list_models.py`. For triggering, use the model your users
  actually run; for quality grading/judging, prefer a stronger model.
- **Concurrency** is a semaphore in `run_many()`. 3-4 is comfortable on a laptop;
  each unit is a full CLI subprocess.
