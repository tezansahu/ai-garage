import json

import pytest

from playground.examples import PRESETS, batch_presets
from playground.models import (
    MAX_UPLOAD_BYTES,
    DecisionResponse,
    Task,
    parse_task,
    parse_upload,
    read_json,
    validate_response,
    validate_tasks,
)

ROUTE = Task.model_validate(
    {
        "id": "route",
        "state": "The API returns 500 on every call.",
        "questions": {
            "team": {
                "type": "choice",
                "instructions": "Which team should handle this ticket?",
                "criteria": {"billing": "Charges", "engineering": "Bugs", "support": "How-to"},
            }
        },
    }
)
NOUL_ONLY = Task.model_validate(
    {
        "id": "page",
        "state": {"signal": "5xx 38%"},
        "questions": {"page_now": {"type": "noul", "instructions": "Page on-call now?"}},
    }
)


def test_all_examples_and_batches_validate():
    for task in PRESETS.values():
        assert parse_task(task.model_dump_json()) == task
    for tasks in batch_presets().values():
        assert len(validate_tasks(tasks)) == 10
        for task in tasks:
            assert Task.model_validate(task.model_dump()) == task


@pytest.mark.parametrize(
    "text", ['{"a":1,"a":2}', '{"a":{"b":1,"b":2}}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e309}']
)
def test_invalid_json_is_rejected(text):
    with pytest.raises(ValueError):
        read_json(text)


def test_task_limits_and_unknown_fields():
    task = ROUTE.model_dump()
    for update in [
        {"state": " "},
        {"state": "a" * 50_001},
        {"state": 42},
        {"id": " "},
        {"questions": {}},
        {"extra": "not allowed"},
    ]:
        with pytest.raises(ValueError):
            Task.model_validate({**task, **update})
    with pytest.raises(ValueError):
        Task.model_validate(
            {
                **task,
                "questions": {
                    "bad": {"type": "choice", "instructions": "pick", "criteria": {"a": "only one"}}
                },
            }
        )
    with pytest.raises(ValueError):
        Task.model_validate(
            {
                **task,
                "questions": {
                    "bad": {"type": "score", "instructions": "rate", "criteria": ["one"] * 11}
                },
            }
        )


def test_batch_cardinality_and_unique_ids():
    task = next(iter(PRESETS.values()))
    for tasks in [[], [task] * 2, [task.model_copy(update={"id": str(i)}) for i in range(51)]]:
        with pytest.raises(ValueError):
            validate_tasks(tasks)


def test_upload_json_jsonl_csv_and_bom():
    task = ROUTE
    payload = task.model_dump(mode="json", exclude_none=True)
    assert parse_upload(json.dumps([payload]).encode(), "tasks.json", task) == [task]
    assert parse_upload((json.dumps(payload) + "\n\n").encode(), "tasks.jsonl", task) == [task]
    csv_tasks = parse_upload(b'\xef\xbb\xbfid,state\none,"first ticket"\n', "tasks.csv", task)
    assert csv_tasks[0].state == "first ticket"
    assert csv_tasks[0].questions == task.questions


def test_csv_can_override_questions():
    tasks = parse_upload(
        b'id,state,questions\none,hello,"{""q"":{""type"":""noul"",'
        b'""instructions"":""Is this a greeting?""}}"\n',
        "tasks.csv",
        ROUTE,
    )
    assert list(tasks[0].questions) == ["q"]


@pytest.mark.parametrize(
    "data,name",
    [
        (b"id,content\none,hello", "tasks.csv"),
        (b"id,state,state\none,a,b", "tasks.csv"),
        (b"id,state\none,a,b", "tasks.csv"),
        (b"id,state\none", "tasks.csv"),
        (b"id,state,extra\none,a,b", "tasks.csv"),
        (b"{}", "tasks.json"),
        (b"[]", "tasks.json"),
        (b"\xff", "tasks.json"),
        (b"[]", "tasks.txt"),
    ],
)
def test_bad_uploads(data, name):
    with pytest.raises(ValueError):
        parse_upload(data, name, next(iter(PRESETS.values())))


def test_oversize_upload():
    with pytest.raises(ValueError, match="2 MB"):
        parse_upload(b" " * (MAX_UPLOAD_BYTES + 1), "tasks.json", next(iter(PRESETS.values())))


def test_response_requires_matching_shape_and_probability_distribution():
    task = ROUTE
    good = {
        "model": "test",
        "answers": {
            "team": {
                "type": "choice",
                "choice": "engineering",
                "confidence": 0.7,
                "probabilities": {"billing": 0.1, "engineering": 0.8, "support": 0.1},
            }
        },
    }
    assert validate_response(DecisionResponse.model_validate(good), task)
    for update in [
        {"choice": "unknown"},
        {"probabilities": {"billing": 0.5, "engineering": 0.5}},
        {"probabilities": {"billing": -0.2, "engineering": 1.1, "support": 0.1}},
        {"probabilities": {"billing": 0.2, "engineering": 0.8, "support": 0.2}},
        {"confidence": None},
        {"type": "score"},
    ]:
        bad = {**good, "answers": {"team": {**good["answers"]["team"], **update}}}
        with pytest.raises(ValueError):
            validate_response(DecisionResponse.model_validate(bad), task)
    with pytest.raises(ValueError):
        validate_response(DecisionResponse(model="x", answers={}), task)


def test_response_score_consistency_and_noul_required():
    task = PRESETS["Score / contract clause risk"]
    levels = task.questions["customer_risk"].criteria
    good = {
        "model": "test",
        "answers": {
            "customer_risk": {
                "type": "score",
                "score": 2.8,
                "confidence": 0.8,
                "probabilities": {"0": 0.0, "1": 0.0, "2": 0.2, "3": 0.8},
                "legend": {str(i): level for i, level in enumerate(levels)},
            }
        },
    }
    assert validate_response(DecisionResponse.model_validate(good), task)
    for update in [{"score": 2.0}, {"score": 4}, {"legend": {"0": "wrong"}}]:
        bad = {**good, "answers": {"customer_risk": {**good["answers"]["customer_risk"], **update}}}
        with pytest.raises(ValueError):
            validate_response(DecisionResponse.model_validate(bad), task)
    with pytest.raises(ValueError):
        validate_response(
            DecisionResponse.model_validate(
                {"model": "test", "answers": {"page_now": {"type": "noul"}}}
            ),
            NOUL_ONLY,
        )
