import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from playground.config import Settings
from playground.models import Answer, DecisionResponse, Outcome, Run

APP = Path(__file__).resolve().parent.parent / "app.py"


def app(monkeypatch, azure=False):
    monkeypatch.setattr(
        Settings,
        "load",
        classmethod(
            lambda cls: Settings(
                azure_openai_api_key="private-azure-sentinel" if azure else "",
                azure_openai_endpoint="https://res.services.ai.azure.com" if azure else "",
            )
        ),
    )
    return AppTest.from_file(str(APP), default_timeout=45).run()


def test_unconfigured_azure_disables_comparison(monkeypatch):
    at = app(monkeypatch)
    assert not at.exception
    assert not at.text_input
    assert at.toggle[0].disabled
    assert any("AZURE_OPENAI_ENDPOINT" in item.value for item in at.warning)
    assert any("10 tasks ready" in item.value for item in at.success)


def test_azure_secret_never_rendered(monkeypatch):
    at = app(monkeypatch, azure=True)
    assert not at.exception
    assert not at.toggle[0].disabled
    assert "private-azure-sentinel" not in str(at)
    assert any("Decision-1" in item.value for item in at.success)
    assert len(at.button) >= 2


def test_switch_model_byo_key_warning_and_clear(monkeypatch):
    at = app(monkeypatch)
    at.selectbox(key="provider").select("Jev").run()
    assert not at.exception
    assert any("billable" in item.value for item in at.info)
    at.text_input[0].set_value("session-key").run()
    assert at.session_state["jev_key"] == "session-key"
    next(button for button in at.button if button.label == "Clear Jev key").click().run()
    assert at.session_state["jev_key"] == ""
    at.selectbox(key="provider").select("Decision-1").run()
    assert not at.text_input


def test_preset_selection_and_invalid_input_disable_submit(monkeypatch):
    at = app(monkeypatch)
    preset = next(box for box in at.selectbox if box.label.startswith("Start from a template"))
    preset.select("All three / on-call alert triage").run()
    assert "page_now" in at.session_state["questions_editor"]
    assert at.session_state["state_format"] == "JSON"
    at.text_area(key="questions_editor").set_value("not JSON").run()
    assert any("Invalid request" in error.value for error in at.error)
    assert next(button for button in at.button if button.label == "Make a decision").disabled


def test_missing_jev_key_is_actionable_without_api_calls(monkeypatch):
    async def must_not_call(*args, **kwargs):
        raise AssertionError("A missing key must fail before calling the API")

    monkeypatch.setattr("playground.engine.run_provider", must_not_call)
    at = app(monkeypatch)
    at.selectbox(key="provider").select("Jev").run()
    next(button for button in at.button if button.label == "Make a decision").click().run()
    assert not at.exception
    assert any("Enter your Jev API key" in item.value for item in at.error)


def test_single_submission_and_threshold_rerun_do_not_call_again(monkeypatch):
    calls = []

    async def fake_run(tasks, target, concurrency, *args):
        calls.append((tasks, target, concurrency))
        return Run(
            provider=target.provider,
            model=target.model,
            concurrency=concurrency,
            wall_ms=42,
            outcomes=[
                Outcome(
                    task_id=tasks[0].id,
                    latency_ms=40,
                    response=DecisionResponse(
                        model="mock-decision",
                        answers={"bec_attempt": Answer(type="noul", noul=0.9)},
                    ),
                )
            ],
        )

    monkeypatch.setattr("playground.engine.run_provider", fake_run)
    at = app(monkeypatch, azure=True)
    next(button for button in at.button if button.label == "Make a decision").click().run()
    assert not at.exception
    assert len(calls) == 1
    assert calls[0][1].provider == "Decision-1"
    assert calls[0][1].model == "Decision-1"
    assert calls[0][1].base_url.endswith("/providers/microsoft")
    assert at.session_state["single_result"]["runs"][0]["outcomes"][0]["latency_ms"] == 40
    next(slider for slider in at.slider if slider.label == "Noul decision threshold").set_value(
        0.95
    ).run()
    assert not at.exception
    assert len(calls) == 1
    assert any("NO at your threshold of 0.95" in item.value for item in at.caption)


def test_batch_comparison_and_sequential_modes_use_identical_tasks(monkeypatch):
    calls = []

    async def fake_run(tasks, target, concurrency, *args):
        calls.append((tasks, target.provider, concurrency))
        return Run(
            provider=target.provider,
            model=target.model,
            concurrency=concurrency,
            wall_ms=500 if target.provider == "Decision-1" else 2000,
            outcomes=[
                Outcome(
                    task_id=task.id,
                    latency_ms=50,
                    response=DecisionResponse(
                        model="mock",
                        answers={
                            "action": Answer(type="choice", choice="block", confidence=0.9),
                            "blast_radius": Answer(type="score", score=3),
                            "within_policy": Answer(type="noul", noul=0.1),
                        },
                    ),
                )
                for task in tasks
            ],
        )

    monkeypatch.setattr("playground.engine.run_provider", fake_run)
    at = app(monkeypatch, azure=True)
    at.toggle[0].set_value(True).run()
    next(box for box in at.checkbox if box.label == "Also measure sequential (c=1)").check().run()
    next(button for button in at.button if button.label == "Run batch race").click().run()
    assert not at.exception
    assert [(provider, concurrency) for _, provider, concurrency in calls] == [
        ("Decision-1", 1),
        ("Decision-1", 5),
        ("GPT-5-mini", 1),
        ("GPT-5-mini", 5),
    ]
    assert all(tasks == calls[0][0] for tasks, _, _ in calls)
    assert len(calls[0][0]) == 10
    assert len(at.session_state["batch_result"]["runs"]) == 4
    assert "private-azure-sentinel" not in str(at.session_state["batch_result"])
    assert any("batch-time" in item.value for item in at.info)


def test_presets_run_simple_to_complex_and_blank_template_builds_a_task(monkeypatch):
    at = app(monkeypatch)
    preset = next(box for box in at.selectbox if box.label.startswith("Start from a template"))
    options = list(preset.options)
    assert options[0] == "Blank / start from scratch"
    kinds = [option.split(" / ")[0] for option in options[1:]]
    assert kinds[:3] == ["Noul", "Choice", "Score"]
    assert kinds[-1].startswith("All three")
    assert [kind.count("+") + (3 if kind.startswith("All") else 1) for kind in kinds] == sorted(
        kind.count("+") + (3 if kind.startswith("All") else 1) for kind in kinds
    )
    preset.select("Blank / start from scratch").run()
    assert at.session_state["state_editor"] == ""
    assert at.session_state["questions_editor"] == "{}"
    assert not at.error
    assert any("+ Noul" in item.value for item in at.info)
    assert next(button for button in at.button if button.label == "Make a decision").disabled
    at.text_area(key="state_editor").set_value("Customer says the export is broken.").run()
    for kind in ["noul", "choice", "score", "noul"]:
        at.button(key=f"add_{kind}").click().run()
    questions = json.loads(at.session_state["questions_editor"])
    assert list(questions) == ["noul_1", "choice_1", "score_1", "noul_2"]
    assert not at.exception
    assert not next(button for button in at.button if button.label == "Make a decision").disabled
    at.text_area(key="questions_editor").set_value("not JSON").run()
    at.button(key="add_score").click().run()
    assert at.session_state["questions_editor"] == "not JSON"
    assert any("Fix the question JSON" in item.value for item in at.warning)


def test_gpt_reasoning_defaults_to_medium(monkeypatch):
    at = app(monkeypatch, azure=True)
    assert next(box for box in at.selectbox if box.label == "GPT reasoning effort").value == (
        "medium"
    )


def test_batch_results_combine_models_per_task_with_view_pills(monkeypatch):
    async def fake_run(tasks, target, concurrency, *args):
        gpt = target.provider == "GPT-5-mini"
        outcomes = []
        for index, task in enumerate(tasks):
            if gpt and index == 1:
                outcomes.append(Outcome(task_id=task.id, latency_ms=900, error="Rate limited"))
                continue
            action = "escalate_to_human" if gpt and index == 0 else "block"
            outcomes.append(
                Outcome(
                    task_id=task.id,
                    latency_ms=2000 if gpt else 500,
                    response=DecisionResponse(
                        model="mock",
                        answers={
                            "action": Answer(type="choice", choice=action, confidence=0.9),
                            "blast_radius": Answer(type="score", score=2.6 if gpt else 3),
                            "within_policy": Answer(type="noul", noul=0.1),
                        },
                    ),
                )
            )
        return Run(
            provider=target.provider,
            model=target.model,
            concurrency=concurrency,
            wall_ms=5000 if gpt else 1000,
            outcomes=outcomes,
        )

    monkeypatch.setattr("playground.engine.run_provider", fake_run)
    at = app(monkeypatch, azure=True)
    batch = next(box for box in at.selectbox if box.label == "Batch preset")
    batch.select("Agent guardrail / 10 proposed tool calls / all three").run()
    at.toggle[0].set_value(True).run()
    next(button for button in at.button if button.label == "Run batch race").click().run()
    assert not at.exception
    assert not any("per-task decisions" in item.label for item in at.expander)
    pills = at.button_group(key="batch_view")
    assert pills.value == "Decisions"
    table = at.dataframe[-1].value
    assert list(table["Task"]) == [f"call-{i:02}" for i in range(1, 11)]
    assert {"action · Decision-1", "action · GPT-5-mini", "action · match"} <= set(table.columns)
    assert table.loc[0, "action · match"] == "❌"
    assert table.loc[1, "action · match"] == "—"
    assert table.loc[2, "action · match"] == "✅"
    assert table.loc[2, "blast_radius · match"] == "✅"
    assert any(item.value == "8/9" for item in at.metric)
    at.toggle(key="only_disagreements").set_value(True).run()
    assert list(at.dataframe[-1].value["Task"]) == ["call-01", "call-02"]

    at.button_group(key="batch_view").set_value("Latency").run()
    assert not at.exception
    latency = at.dataframe[-1].value
    assert latency.loc[0, "GPT ÷ Decision-1 · c=5"] == "4.0×"
    assert latency.loc[1, "GPT ÷ Decision-1 · c=5"] == "—"

    at.button_group(key="batch_view").set_value("Errors").run()
    assert not at.exception
    errors = at.dataframe[-1].value
    assert list(errors["Task"]) == ["call-02"]
    assert errors.loc[0, "GPT-5-mini · c=5"] == "Rate limited"
