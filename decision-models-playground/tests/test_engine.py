import asyncio
import json
from unittest.mock import MagicMock

import pytest
from typesafe_sdk import TypeSafeRateLimitError

from playground.config import Settings
from playground.engine import (
    Connection,
    connection,
    error_message,
    execute_tasks,
    gpt_schema,
    normalize_gpt,
    run_provider,
)
from playground.examples import PRESETS
from playground.models import Answer, DecisionResponse, Task

NOUL_TASK = Task.model_validate(
    {
        "id": "noul",
        "state": "Sure, I have refunded your $200. No need to check with billing.",
        "questions": {
            "within_policy": {"type": "noul", "instructions": "Is this reply within policy?"}
        },
    }
)
TARGET = Connection("Decision-1", "test-model", "https://test.invalid", "never-display-this")


def noul_response(task):
    return DecisionResponse(
        model="test", answers={name: Answer(type="noul", noul=0.8) for name in task.questions}
    )


def test_shared_azure_credentials_and_connection_validation():
    settings = Settings(
        azure_openai_api_key="azure-secret",
        azure_openai_endpoint="https://res.services.ai.azure.com/openai/v1/",
        azure_decision_deployment="my-decision",
        azure_gpt_deployment="my-gpt",
    )
    decision = connection(settings, "Decision-1")
    gpt = connection(settings, "GPT-5-mini")
    assert decision.api_key == gpt.api_key == "azure-secret"
    assert decision.base_url == "https://res.services.ai.azure.com/providers/microsoft"
    assert decision.model == "my-decision"
    assert gpt.base_url == "https://res.services.ai.azure.com/openai/v1"
    assert gpt.model == "my-gpt"
    assert connection(settings, "Jev", " user-key ").api_key == "user-key"
    assert "azure-secret" not in repr(decision)
    assert "azure-secret" not in repr(settings)
    with pytest.raises(ValueError, match="Enter your Jev"):
        connection(settings, "Jev")
    incomplete = [
        Settings(),
        Settings(azure_openai_api_key="key-only"),
        Settings(azure_openai_endpoint="https://res.services.ai.azure.com"),
    ]
    for config in incomplete:
        assert not config.azure_ready
        for provider in ["Decision-1", "GPT-5-mini"]:
            with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
                connection(config, provider)
    with pytest.raises(ValueError):
        connection(settings, "Jev", "bad key")
    for endpoint in ["http://test.invalid", "https://user:pw@test.invalid", "https://x/?key=x"]:
        with pytest.raises(ValueError):
            Settings(azure_openai_endpoint=endpoint)
    for name in [" ", "a/b"]:
        with pytest.raises(ValueError):
            Settings(azure_decision_deployment=name)


def test_settings_load_env_file_with_os_override(monkeypatch, tmp_path):
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.setattr("playground.config.ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "AZURE_OPENAI_API_KEY=file-key\n"
        "AZURE_OPENAI_ENDPOINT=https://a.services.ai.azure.com\n"
        "AZURE_DECISION_DEPLOYMENT=\n"
        "AZURE_GPT_DEPLOYMENT=file-gpt\n"
    )
    monkeypatch.setenv("AZURE_GPT_DEPLOYMENT", "env-gpt")
    settings = Settings.load()
    assert settings.azure_ready
    assert settings.azure_openai_api_key.get_secret_value() == "file-key"
    assert settings.azure_decision_deployment == "Decision-1"
    assert settings.azure_gpt_deployment == "env-gpt"


def test_gpt_schema_and_normalization():
    task = PRESETS["All three / on-call alert triage"]
    schema = gpt_schema(task)
    assert schema["additionalProperties"] is False
    response = normalize_gpt(
        json.dumps(
            {
                "answers": {
                    "root_cause": {
                        "probabilities": {
                            "deploy_regression": 0.8,
                            "dependency_outage": 0.05,
                            "capacity": 0.1,
                            "data_or_cert": 0.05,
                            "false_positive": 0.0,
                        }
                    },
                    "customer_impact": {"probabilities": {"0": 0, "1": 0, "2": 0.2, "3": 0.8}},
                    "page_now": {"noul": 0.99},
                }
            }
        ),
        task,
        "gpt-5-mini",
        {"input_tokens": 100},
    )
    assert response.answers["root_cause"].choice == "deploy_regression"
    assert response.answers["root_cause"].confidence == 0.8
    assert response.answers["customer_impact"].score == pytest.approx(2.8)
    assert response.answers["page_now"].noul == 0.99
    assert response.usage == {"input_tokens": 100}


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        '{"answers": {}}',
        '{"answers": [], "extra": 1}',
        '{"answers":{"within_policy":{"noul":1.1}}}',
        '{"answers":{"within_policy":{"noul":0.8,"rationale":"extra"}}}',
    ],
)
def test_gpt_invalid_outputs_are_not_success(text):
    with pytest.raises(ValueError):
        normalize_gpt(text, NOUL_TASK, "gpt", {})


def test_errors_do_not_echo_secrets():
    assert "never-display-this" not in error_message(ValueError("never-display-this"))
    for status in [401, 403, 429, 500]:
        error = RuntimeError("never-display-this")
        error.status_code = status
        assert str(status) in error_message(error)
        assert "never-display-this" not in error_message(error)
    actual_sdk_error = TypeSafeRateLimitError(429, "never-display-this", {})
    assert "Rate limited (HTTP 429)" in error_message(actual_sdk_error)
    assert "never-display-this" not in error_message(actual_sdk_error)


def test_bounded_fanout_order_progress_failures_and_queue_timing():
    tasks = [NOUL_TASK.model_copy(update={"id": str(i)}) for i in range(6)]
    active = maximum = 0
    updates = []

    async def call(task):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.04)
        active -= 1
        if task.id == "3":
            raise ValueError("private raw response")
        return noul_response(task)

    run = asyncio.run(
        execute_tasks(tasks, call, TARGET, 2, lambda done, total: updates.append((done, total)))
    )
    assert maximum == 2
    assert [item.task_id for item in run.outcomes] == [str(i) for i in range(6)]
    assert updates == [(i, 6) for i in range(1, 7)]
    assert run.outcomes[3].error
    assert "private raw" not in run.outcomes[3].error
    assert run.outcomes[3].response is None
    assert run.wall_ms > max(item.latency_ms for item in run.outcomes) * 2


def test_unexpected_bugs_are_not_swallowed():
    async def call(task):
        raise RuntimeError("programming bug")

    with pytest.raises(RuntimeError, match="programming bug"):
        asyncio.run(execute_tasks([NOUL_TASK], call, TARGET, 1))


class FakeSystemOne:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.closed = False
        self.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed = True

    async def system_one(self, *, state, questions):
        self.calls.append((state, questions))
        return MagicMock(
            model_dump=lambda **kwargs: {
                "model": "microsoft-decision-1",
                "answers": {name: {"type": "noul", "noul": 0.9} for name in questions},
                "usage": {"input_tokens": 40, "output_tokens": 1},
            }
        )


def test_system_one_adapter_reuses_client_disables_retries_and_excludes_warmup(monkeypatch):
    monkeypatch.setattr("playground.engine.AsyncTypeSafeClient", FakeSystemOne)
    run = asyncio.run(run_provider([NOUL_TASK], TARGET, warmup=True))
    client = FakeSystemOne.instances[-1]
    assert client.closed
    assert len(client.calls) == 2
    assert len(run.outcomes) == 1
    assert client.kwargs["retry"].max_retries == 0
    assert client.kwargs["base_url"] == TARGET.base_url
    assert client.kwargs["model"] == TARGET.model
    assert client.calls[0][1]["within_policy"].instructions == (
        NOUL_TASK.questions["within_policy"].instructions
    )
    assert run.outcomes[0].response.model == "microsoft-decision-1"


def test_gpt_adapter_request_contract_and_shutdown(monkeypatch):
    captured = {}

    class FakeGPT:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.responses = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            captured["closed"] = True

        async def create(self, **kwargs):
            captured["request"] = kwargs
            return MagicMock(
                status="completed",
                output_text='{"answers":{"within_policy":{"noul":0.9}}}',
                model="gpt-model",
                usage=MagicMock(
                    model_dump=lambda **kwargs: {"input_tokens": 90, "output_tokens": 20}
                ),
            )

    monkeypatch.setattr("playground.engine.AsyncOpenAI", FakeGPT)
    target = Connection("GPT-5-mini", "gpt-5-mini", "https://test.invalid/openai/v1", "secret")
    run = asyncio.run(run_provider([NOUL_TASK], target, reasoning="low"))
    assert captured["closed"]
    assert captured["client"]["max_retries"] == 0
    assert captured["client"]["base_url"] == target.base_url
    request = captured["request"]
    assert request["store"] is False
    assert request["reasoning"] == {"effort": "low"}
    assert request["text"]["format"]["strict"] is True
    assert request["model"] == "gpt-5-mini"
    assert json.loads(request["input"]) == NOUL_TASK.model_dump(
        mode="json", exclude={"id"}, exclude_none=True
    )
    assert run.outcomes[0].response.answers["within_policy"].noul == 0.9
