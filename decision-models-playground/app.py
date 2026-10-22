from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Literal

import pandas as pd
import streamlit as st
from openai import APIError
from pydantic import ValidationError
from typesafe_sdk import TypeSafeError

from playground.config import Settings
from playground.engine import ConfigurationError, Provider, connection, error_message, run_provider
from playground.examples import BLANK, PRESETS, QUESTION_TEMPLATES, batch_presets
from playground.metrics import summary, wall_ratio
from playground.models import (
    Answer,
    Run,
    Task,
    parse_upload,
    read_json,
    validate_tasks,
)

st.set_page_config(page_title="Decision Models Playground", page_icon="⚡", layout="wide")


def pretty(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def load_example() -> None:
    if st.session_state["example"] == BLANK:
        st.session_state["state_format"] = "Text"
        st.session_state["state_editor"] = ""
        st.session_state["questions_editor"] = "{}"
        return
    task = PRESETS[st.session_state["example"]]
    st.session_state["state_format"] = "Text" if isinstance(task.state, str) else "JSON"
    st.session_state["state_editor"] = (
        task.state if isinstance(task.state, str) else pretty(task.state)
    )
    st.session_state["questions_editor"] = pretty(
        task.model_dump(mode="json", exclude_none=True)["questions"]
    )


def add_question(kind: str) -> None:
    try:
        questions = read_json(st.session_state.get("questions_editor", "").strip() or "{}")
    except (ValueError, RecursionError):
        questions = None
    if not isinstance(questions, dict):
        st.session_state["editor_notice"] = "Fix the question JSON before adding a question."
        return
    number = 1
    while f"{kind}_{number}" in questions:
        number += 1
    questions[f"{kind}_{number}"] = read_json(json.dumps(QUESTION_TEMPLATES[kind]))
    st.session_state["questions_editor"] = pretty(questions)


def load_batch() -> None:
    tasks = batch_presets()[st.session_state["batch_example"]]
    st.session_state["batch_editor"] = pretty(
        [task.model_dump(mode="json", exclude_none=True) for task in tasks]
    )


def clear_jev_key() -> None:
    st.session_state["jev_key"] = ""


def render_answer(name: str, answer: Answer, threshold: float) -> None:
    with st.container(border=True):
        st.caption(f"{name}  /  {answer.type.upper()}")
        if answer.type == "noul" and answer.noul is not None:
            st.metric("Probability of yes", f"{answer.noul:.3f}")
            st.progress(answer.noul)
            verdict = "YES" if answer.noul >= threshold else "NO"
            st.caption(f"{verdict} at your threshold of {threshold:.2f}")
        elif answer.type == "choice":
            st.metric("Selected option", answer.choice or "—")
        elif answer.type == "score" and answer.score is not None:
            top = len(answer.legend or {}) - 1
            st.metric("Weighted score", f"{answer.score:.3f} / {top}")
            if top > 0:
                st.progress(min(1.0, answer.score / top))
            st.caption("Scale: " + pretty(answer.legend))
        if answer.confidence is not None:
            st.caption(f"Reported confidence: {answer.confidence:.3f}")
        if answer.probabilities:
            frame = pd.DataFrame(
                {"Probability": answer.probabilities.values()},
                index=list(answer.probabilities),
            )
            st.bar_chart(frame, color="#0d9488", horizontal=True)


def render_single(runs: list[Run], threshold: float) -> None:
    columns = st.columns(len(runs))
    for column, run in zip(columns, runs, strict=True):
        with column:
            st.subheader(run.provider)
            if run.provider == "GPT-5-mini":
                st.caption(
                    "GPT generates probability estimates, not decision-model label probabilities. "
                    "Its confidence below is the top generated probability."
                )
            outcome = run.outcomes[0]
            st.metric("Request latency", f"{outcome.latency_ms:,.0f} ms")
            if outcome.error:
                st.error(outcome.error)
            if outcome.response:
                st.caption(f"Responded model: {outcome.response.model}")
                for name, answer in outcome.response.answers.items():
                    render_answer(name, answer, threshold)
                with st.expander("Response + token usage"):
                    st.json(outcome.response.model_dump(mode="json", exclude_none=True))
    if len(runs) == 2:
        left, right = runs
        if all(item.response is not None for run in runs for item in run.outcomes):
            denominator = left.outcomes[0].latency_ms
            if denominator > 0:
                st.info(
                    f"Observed GPT / {left.provider} request-time ratio: "
                    f"{right.outcomes[0].latency_ms / denominator:.2f}×. "
                    "One observation, not a benchmark guarantee."
                )


NOUL_CUTOFF = 0.5


def run_label(run: Run) -> str:
    return f"{run.provider} · c={run.concurrency}"


def decision_text(answer: Answer | None) -> str:
    if answer is None:
        return "—"
    if answer.type == "noul" and answer.noul is not None:
        return f"{'YES' if answer.noul >= NOUL_CUTOFF else 'NO'} ({answer.noul:.2f})"
    if answer.type == "choice" and answer.choice is not None:
        return answer.choice + (f" ({answer.confidence:.2f})" if answer.confidence else "")
    if answer.type == "score" and answer.score is not None:
        return f"{answer.score:.2f}"
    return "—"


def decision_bucket(answer: Answer) -> str | int | bool | None:
    """The discrete decision used to decide whether two models agree."""
    if answer.type == "noul":
        return None if answer.noul is None else answer.noul >= NOUL_CUTOFF
    if answer.type == "choice":
        return answer.choice
    return None if answer.score is None else round(answer.score)


def render_decisions(tasks: list[Task], primary: list[Run]) -> None:
    providers = [run.provider for run in primary]
    compare = len(primary) == 2
    rows: list[dict[str, str]] = []
    agreement: dict[str, list[int]] = {}
    for index, task in enumerate(tasks):
        row = {"Task": task.id}
        all_match = True
        for name in task.questions:
            answers: list[Answer | None] = []
            for run in primary:
                response = run.outcomes[index].response
                answer = response.answers.get(name) if response else None
                answers.append(answer)
                row[f"{name} · {run.provider}"] = decision_text(answer)
            if compare:
                first, second = answers
                if first is None or second is None:
                    row[f"{name} · match"] = "—"
                    all_match = False
                    continue
                same = decision_bucket(first) == decision_bucket(second)
                counts = agreement.setdefault(name, [0, 0])
                counts[0] += same
                counts[1] += 1
                row[f"{name} · match"] = "✅" if same else "❌"
                all_match &= same
        row["_all_match"] = "yes" if all_match else "no"
        rows.append(row)
    if compare and agreement:
        st.caption(f"Agreement between {providers[0]} and {providers[1]} per question")
        columns = st.columns(min(len(agreement) + 1, 5))
        full = sum(row["_all_match"] == "yes" for row in rows)
        columns[0].metric("All questions agree", f"{full}/{len(rows)} tasks")
        for i, (name, (agreed, total)) in enumerate(agreement.items(), 1):
            columns[i % len(columns)].metric(name, f"{agreed}/{total}")
        if st.toggle("Show only tasks where the models disagree", key="only_disagreements"):
            rows = [row for row in rows if row["_all_match"] == "no"]
    frame = pd.DataFrame(rows).drop(columns="_all_match", errors="ignore").fillna("")
    if frame.empty:
        st.success("The models agree on every decision.")
    else:
        st.dataframe(frame, hide_index=True, width="stretch")
    st.caption(
        f"Noul agrees when both are on the same side of {NOUL_CUTOFF}; Choice when both pick the "
        "same label; Score when both round to the same level. Values in parentheses are the "
        "Noul probability or Choice confidence."
        + (
            " Decisions come from each provider's highest-concurrency run."
            if any(run.concurrency > 1 for run in primary)
            else ""
        )
    )


def render_latency(tasks: list[Task], runs: list[Run]) -> None:
    rows: list[dict[str, object]] = []
    pairs = [
        (gpt, other)
        for gpt in runs
        if gpt.provider == "GPT-5-mini"
        for other in runs
        if other.provider != "GPT-5-mini" and other.concurrency == gpt.concurrency
    ]
    for index, task in enumerate(tasks):
        row: dict[str, object] = {"Task": task.id}
        for run in runs:
            outcome = run.outcomes[index]
            row[f"{run_label(run)} (ms)"] = (
                round(outcome.latency_ms) if outcome.response is not None else None
            )
        for gpt, other in pairs:
            fast, slow = other.outcomes[index], gpt.outcomes[index]
            ok = fast.response is not None and slow.response is not None and fast.latency_ms > 0
            row[f"GPT ÷ {other.provider} · c={gpt.concurrency}"] = (
                f"{slow.latency_ms / fast.latency_ms:.1f}×" if ok else "—"
            )
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    chart = pd.DataFrame(
        {
            run_label(run): [
                item.latency_ms if item.response is not None else None for item in run.outcomes
            ]
            for run in runs
        },
        index=[task.id for task in tasks],
    )
    st.bar_chart(chart, stack=False, y_label="Request latency (ms)")
    st.caption("Failed calls are left blank and excluded from ratios.")


def render_errors(tasks: list[Task], runs: list[Run], failures: int) -> None:
    if not failures:
        st.success(f"All {sum(len(run.outcomes) for run in runs)} measured calls succeeded.")
        return
    rows = [
        {
            "Task": task.id,
            **{run_label(run): run.outcomes[index].error or "✓" for run in runs},
        }
        for index, task in enumerate(tasks)
        if any(run.outcomes[index].error for run in runs)
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def render_batch(tasks: list[Task], runs: list[Run]) -> None:
    st.dataframe(pd.DataFrame([summary(run) for run in runs]), hide_index=True, width="stretch")
    st.bar_chart(
        pd.DataFrame(
            {"Wall time (s)": [run.wall_ms / 1000 for run in runs]},
            index=[run_label(run) for run in runs],
        ),
        color="#0d9488",
        horizontal=True,
    )
    for run in runs:
        if run.provider == "GPT-5-mini":
            for candidate in runs:
                if candidate.provider != "GPT-5-mini":
                    ratio = wall_ratio(run, candidate)
                    if ratio is not None:
                        st.info(
                            f"c={run.concurrency}: GPT / {candidate.provider} batch-time "
                            f"ratio = {ratio:.2f}× ({len(run.outcomes)} successful matched tasks)."
                        )
    for parallel in runs:
        if parallel.concurrency > 1:
            serial = next(
                (run for run in runs if run.provider == parallel.provider and run.concurrency == 1),
                None,
            )
            if serial and all(
                item.response is not None for run in (serial, parallel) for item in run.outcomes
            ):
                st.caption(
                    f"{parallel.provider}: serial / concurrent wall time = "
                    f"{serial.wall_ms / parallel.wall_ms:.2f}×. "
                    "Concurrency improves throughput; it does not make each decision faster."
                )
    failures = sum(item.error is not None for run in runs for item in run.outcomes)
    if failures:
        st.warning("Some calls failed. Ratios are suppressed for incomplete provider comparisons.")

    st.subheader("Per task")
    labels = {"Decisions": "Decisions", "Latency": "Latency", "Errors": f"Errors ({failures})"}
    view = (
        st.pills(
            "Per-task view",
            list(labels),
            default="Decisions",
            format_func=labels.__getitem__,
            key="batch_view",
            label_visibility="collapsed",
        )
        or "Decisions"
    )
    # Runs are ordered c=1 then c=N per provider; the last one is the headline run.
    primary = list({run.provider: run for run in runs}.values())
    if view == "Decisions":
        render_decisions(tasks, primary)
    elif view == "Latency":
        render_latency(tasks, runs)
    else:
        render_errors(tasks, runs, failures)
    st.caption(
        "p50/p95 use successful calls only, excluding time waiting for a concurrency slot. "
        "Wall time includes all tasks and failures. Small samples have noisy percentiles."
    )


def export_result(result: dict[str, object], filename: str) -> None:
    st.download_button(
        "Download run JSON",
        pretty(result),
        file_name=filename,
        mime="application/json",
        key=f"download_{filename}",
    )


def main() -> None:
    try:
        settings = Settings.load()
    except ValidationError:
        st.error(
            "Invalid server configuration. Check the HTTPS endpoints and deployment names in .env."
        )
        st.stop()

    with st.sidebar:
        st.title("Playground")
        st.caption("Decision models vs. general-purpose LLMs")
        provider: Provider = st.selectbox("Decision model", ["Decision-1", "Jev"], key="provider")
        jev_key = ""
        azure_ready = settings.azure_ready
        if provider == "Jev":
            st.info("Bring Your Own API Key. Jev API calls are billable to your TypeSafe account.")
            jev_key = st.text_input("Your Jev API key", type="password", key="jev_key")
            st.button("Clear Jev key", on_click=clear_jev_key)
            st.caption("Kept only in this browser session's server memory. Never saved to config.")
        elif azure_ready:
            st.success("Microsoft Decision-1: Azure credential configured")
            st.caption(
                f"Foundry deployment: {settings.azure_decision_deployment}. Calls are billable. "
                "The key is never sent to the browser or displayed in the UI."
            )
        else:
            st.warning("Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in the server's .env.")

        compare = st.toggle("Compare with GPT-5-mini", disabled=not azure_ready)
        if not azure_ready:
            st.caption(
                "To enable comparison, set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in .env."
            )
        else:
            st.caption(f"Foundry deployment: {settings.azure_gpt_deployment}. Calls are billable.")
        reasoning: Literal["minimal", "low", "medium", "high"] = st.selectbox(
            "GPT reasoning effort",
            ["minimal", "low", "medium", "high"],
            index=2,
            disabled=not compare,
            help="Medium is the default. Minimal is the lowest-latency setting. "
            "The selected deployment must support the chosen effort.",
        )
        with st.expander("Measurement controls"):
            timeout = st.slider("Request timeout (seconds)", 5, 180, 60)
            warmup = st.checkbox(
                "Warm up each run",
                help="One extra paid call per run, excluded from measured results. "
                "This warms the client connection, not necessarily the model server.",
            )
            st.caption("Automatic retries are disabled for both providers.")
        st.divider()
        st.caption(
            "Local demo only. Inputs go to the selected provider; do not upload sensitive data."
        )
        st.markdown("[TypeSafe SDK](https://docs.typesafe.ai/sdk/python)")

    st.title("Decision Models Playground")
    st.markdown(
        "**Decision models vs. general-purpose LLMs, on the same task.** A decision model is "
        "purpose-built to answer typed questions directly with label probabilities; a "
        "general-purpose LLM such as GPT-5-mini reasons and generates its answer as text."
    )
    st.caption("Noul → is it true?   ·   Choice → which option?   ·   Score → how much?")
    explore, batch, guide = st.tabs(["Playground", "Batch race", "How it works"])

    def execute(tasks: list[Task], levels: list[int]) -> list[Run]:
        targets = [connection(settings, provider, jev_key)]
        if compare:
            targets.append(connection(settings, "GPT-5-mini"))
        runs: list[Run] = []
        progress = st.progress(0.0, text="Preparing requests…")
        total = len(tasks) * len(targets) * len(levels)
        done = 0
        for target in targets:
            for concurrency in levels:
                prefix = f"{target.provider} / c={concurrency}"

                def update(
                    completed: int, count: int, offset: int = done, label: str = prefix
                ) -> None:
                    progress.progress(
                        (offset + completed) / total,
                        text=f"{label}: {completed}/{count} tasks",
                    )

                run = asyncio.run(
                    run_provider(
                        tasks, target, concurrency, float(timeout), reasoning, warmup, update
                    )
                )
                runs.append(run)
                done += len(tasks)
        progress.empty()
        return runs

    def record(tasks: list[Task], runs: list[Run]) -> dict[str, object]:
        return {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "tasks": [task.model_dump(mode="json", exclude_none=True) for task in tasks],
            "runs": [run.model_dump(mode="json", exclude_none=True) for run in runs],
            "measurement": {
                "timeout_seconds": timeout,
                "warmup": warmup,
                "retries": 0,
                "gpt_reasoning_effort": reasoning if compare else None,
            },
        }

    with explore:
        if "example" not in st.session_state:
            st.session_state["example"] = next(iter(PRESETS))
            load_example()
        options = [BLANK, *PRESETS]
        st.selectbox(
            "Start from a template (simple → complex) or a blank slate",
            options,
            key="example",
            on_change=load_example,
        )
        left, right = st.columns([1, 1])
        with left:
            st.subheader("1 / State")
            st.radio("State format", ["Text", "JSON"], horizontal=True, key="state_format")
            state_text = st.text_area(
                "Text or structured data to evaluate", key="state_editor", height=250
            )
        with right:
            st.subheader("2 / Typed questions")
            questions_text = st.text_area(
                "Editable question map (JSON)", key="questions_editor", height=300
            )
            add = st.columns(3)
            for column, kind in zip(add, QUESTION_TEMPLATES, strict=True):
                column.button(
                    f"+ {kind.capitalize()}",
                    on_click=add_question,
                    args=(kind,),
                    width="stretch",
                    key=f"add_{kind}",
                )
            notice = st.session_state.pop("editor_notice", None)
            if notice:
                st.warning(notice)
        threshold = st.slider(
            "Noul decision threshold",
            0.0,
            1.0,
            0.5,
            0.01,
            help="Changes only the displayed YES/NO decision; does not make another API call.",
        )
        task = None
        try:
            state = (
                read_json(state_text) if st.session_state["state_format"] == "JSON" else state_text
            )
            task = Task.model_validate(
                {"id": "interactive", "state": state, "questions": read_json(questions_text)}
            )
        except (ValueError, RecursionError):
            if not state_text.strip() or questions_text.strip() in ("", "{}"):
                st.info(
                    "Enter a state, then add at least one question with + Noul, + Choice, "
                    "or + Score and edit its instructions and criteria."
                )
            else:
                st.error(
                    "Invalid request. Use non-empty state and a valid question map. "
                    "See How it works."
                )
        if task:
            with st.expander("Exact decision-model request preview (no credentials)"):
                request = task.model_dump(mode="json", exclude={"id"}, exclude_none=True)
                st.json(
                    {
                        "model": settings.azure_decision_deployment
                        if provider == "Decision-1"
                        else settings.jev_model,
                        **request,
                    }
                )
        st.caption(
            f"Run makes {2 if compare else 1} measured API call(s)"
            + (" plus one warm-up per provider." if warmup else ".")
        )
        if st.button("Make a decision", type="primary", disabled=task is None):
            st.session_state.pop("single_result", None)
            if task:
                try:
                    with st.spinner("Scoring…"):
                        runs = execute([task], [1])
                    st.session_state["single_result"] = record([task], runs)
                except (TypeSafeError, APIError) as exc:
                    st.error("Run aborted before completion. " + error_message(exc))
                except ConfigurationError as exc:
                    st.error(str(exc))
                except ValueError:
                    st.error("Check credentials and model configuration. Warm-up may have failed.")
        if "single_result" in st.session_state:
            result = st.session_state["single_result"]
            st.divider()
            st.caption(f"Last run: {result['timestamp_utc']} · retained until you submit again.")
            if task and result["tasks"] != [task.model_dump(mode="json", exclude_none=True)]:
                st.warning(
                    "You edited the input. Results below belong to the last submitted request."
                )
            render_single([Run.model_validate(run) for run in result["runs"]], threshold)
            export_result(result, "decision-run.json")

    with batch:
        if "batch_example" not in st.session_state:
            st.session_state["batch_example"] = next(iter(batch_presets()))
            load_batch()
        st.subheader("10 realistic tasks. One shared client. Your concurrency.")
        st.caption(
            "This is client-side fan-out: one request per independent state, not an offline Batch "
            "API. Several questions about one state are bundled into that state's request."
        )
        st.selectbox(
            "Batch preset", list(batch_presets()), key="batch_example", on_change=load_batch
        )
        with st.expander("Edit the batch task array", expanded=False):
            batch_text = st.text_area("Tasks (JSON array)", key="batch_editor", height=400)
        upload = st.file_uploader("Or upload custom tasks", type=["json", "jsonl", "csv"])
        st.caption(
            "JSON / JSONL: id, state, questions. CSV: id,state and optional questions (JSON). "
            "Omitted CSV questions use the selected batch preset's first task. "
            "Limit: 50 tasks / 2 MB."
        )
        selected = batch_presets()[st.session_state["batch_example"]]
        st.download_button(
            "Download example batch",
            pretty([item.model_dump(mode="json", exclude_none=True) for item in selected]),
            "example-batch.json",
            "application/json",
        )
        tasks = None
        try:
            if upload:
                tasks = parse_upload(upload.getvalue(), upload.name, selected[0])
            else:
                rows = read_json(batch_text)
                if not isinstance(rows, list):
                    raise ValueError("Batch must be an array.")
                tasks = validate_tasks([Task.model_validate(row) for row in rows])
        except (ValueError, RecursionError):
            st.error(
                "Invalid batch. Check file format, unique ids, task limits, and question shapes."
            )
        if tasks:
            st.success(
                f"{len(tasks)} tasks ready · "
                f"{sum(len(item.questions) for item in tasks)} typed decisions"
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Task": item.id,
                            "State": str(item.state)[:160],
                            "Questions": ", ".join(item.questions),
                        }
                        for item in tasks
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        c1, c2 = st.columns(2)
        with c1:
            concurrency = st.slider("Concurrent requests per provider", 1, 10, 5)
        with c2:
            race_serial = st.checkbox(
                "Also measure sequential (c=1)",
                help="Runs the same tasks again. Doubles API usage when concurrency > 1.",
            )
        levels = [1, concurrency] if race_serial and concurrency > 1 else [concurrency]
        if tasks:
            requests = len(tasks) * len(levels) * (2 if compare else 1)
            extra = len(levels) * (2 if compare else 1) if warmup else 0
            st.caption(
                f"Submission makes {requests} measured API calls + {extra} warm-up calls. "
                "Providers run in sequence, with identical tasks and concurrency; calls may cost."
            )
        if st.button("Run batch race", type="primary", disabled=tasks is None):
            st.session_state.pop("batch_result", None)
            if tasks:
                try:
                    runs = execute(tasks, levels)
                    st.session_state["batch_result"] = record(tasks, runs)
                except (TypeSafeError, APIError) as exc:
                    st.error("Run aborted before completion. " + error_message(exc))
                except ConfigurationError as exc:
                    st.error(str(exc))
                except ValueError:
                    st.error("Check credentials and model configuration. Warm-up may have failed.")
        if "batch_result" in st.session_state:
            result = st.session_state["batch_result"]
            st.divider()
            st.caption(f"Last run: {result['timestamp_utc']} · snapshot, not a live benchmark.")
            if tasks and result["tasks"] != [
                item.model_dump(mode="json", exclude_none=True) for item in tasks
            ]:
                st.warning("Current batch differs from the last submitted batch shown below.")
            render_batch(
                [Task.model_validate(item) for item in result["tasks"]],
                [Run.model_validate(run) for run in result["runs"]],
            )
            export_result(result, "batch-run.json")

    with guide:
        st.subheader("Three primitives, not three chat prompts")
        st.markdown(
            """
| Primitive | Question | Output | Example use |
|---|---|---|---|
| **Noul** | Is this true? | Probability of yes, 0–1 | Relevance, policy gates |
| **Choice** | Which option? | Label + distribution over 2–255 options | Ticket or agent routing |
| **Score** | How much? | Weighted index over 2–10 ordered levels | Severity, ranking |

**State** can be text, a JSON object, or an array. **Questions** are named independently;
the response uses the same names. Edit the templates, keep questions narrow,
and give clear criteria.
Score levels go from lowest to highest. A four-level score ranges from 0 to 3, not 1 to 4.

**Thresholds are your policy**, not a model guarantee. Lower a Noul threshold to favor recall;
raise it to favor precision. Validate on labeled examples before automating routing or blocking.
Choice confidence need not equal the top option probability.
"""
        )
        st.subheader("An honest latency comparison")
        st.markdown(
            """
- Both providers receive the same state and typed questions. GPT uses Responses API structured
  output, with no rationale and the reasoning effort chosen in the sidebar.
- GPT generates probability estimates as text. They are **not** decision-model next-token label
  probabilities or calibrated uncertainty. The adapter derives Choice/Score from these estimates;
  its displayed confidence is the highest generated probability.
- Request latency uses a monotonic clock around the SDK call, parsing, and validation. It includes
  network time, excludes client creation and time waiting for a concurrency slot. Batch wall time
  measures dispatch through completion; throughput counts successful tasks, not questions.
- Clients are shared within a run. Automatic retries are off. Optional connection warm-up is one
  extra call, excluded from measurements. Provider runs are sequential, not racing for
  local resources.
- Network geography, prompt caching, service load, rate limits, reasoning effort, and
  cold connections affect results. Repeat runs; do not present a 10-task demo as a universal
  latency or quality claim.
- Failures remain visible; incomplete runs do not receive a provider speed ratio. Token usage is
  shown, but costs are not estimated because rates and billing arrangements differ.
"""
        )
        st.subheader("Minimal request template")
        st.code(
            PRESETS["All three / on-call alert triage"].model_dump_json(
                indent=2, exclude_none=True
            ),
            language="json",
        )
        st.markdown(
            "[SDK](https://docs.typesafe.ai/sdk/python) · "
            "[Primitives](https://docs.typesafe.ai/primitives) · "
            "[Parallel questions cookbook]"
            "(https://docs.typesafe.ai/cookbooks/parallel_questions) · "
            "[RAG reranking cookbook](https://docs.typesafe.ai/cookbooks/rerank_typesafe) · "
            "[Azure Responses API]"
            "(https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses)"
        )


main()
