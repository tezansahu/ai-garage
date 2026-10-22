from __future__ import annotations

import csv
import io
import json
import math
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

MAX_TASKS = 50
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
State = str | dict[str, JsonValue] | list[JsonValue]
Content = str | dict[str, JsonValue] | list[JsonValue]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class NoulCriteria(StrictModel):
    true: Content
    false: Content


class NoulQuestion(StrictModel):
    type: Literal["noul"]
    instructions: Content
    criteria: NoulCriteria | None = None


class ChoiceQuestion(StrictModel):
    type: Literal["choice"]
    instructions: Content
    criteria: dict[str, Content | None] = Field(min_length=2, max_length=255)


class ScoreQuestion(StrictModel):
    type: Literal["score"]
    instructions: Content
    criteria: list[Content] = Field(min_length=2, max_length=10)


Question = Annotated[NoulQuestion | ChoiceQuestion | ScoreQuestion, Field(discriminator="type")]


class Task(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    state: State
    questions: dict[str, Question] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if not self.id.strip():
            raise ValueError("Task id must not be blank.")
        if isinstance(self.state, str) and not self.state.strip():
            raise ValueError("State must not be blank.")
        if len(json.dumps(self.state)) > 50_000:
            raise ValueError("State exceeds the 50,000-character playground limit.")
        for name, question in self.questions.items():
            if not name.strip():
                raise ValueError("Question names must not be blank.")
            if not question.instructions or (
                isinstance(question.instructions, str) and not question.instructions.strip()
            ):
                raise ValueError("Instructions must not be blank.")
            if isinstance(question, ChoiceQuestion) and any(
                not key.strip() for key in question.criteria
            ):
                raise ValueError("Choice labels must not be blank.")
        if len(self.model_dump_json()) > 100_000:
            raise ValueError("Task exceeds the 100,000-character playground limit.")
        return self


class Answer(StrictModel):
    type: Literal["noul", "choice", "score"]
    noul: float | None = Field(default=None, ge=0, le=1)
    choice: str | None = None
    score: float | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    probabilities: dict[str, float] | None = None
    legend: dict[str, Content] | None = None


class DecisionResponse(StrictModel):
    model: str
    answers: dict[str, Answer]
    usage: dict[str, JsonValue] = Field(default_factory=dict)


class Outcome(StrictModel):
    task_id: str
    latency_ms: float
    response: DecisionResponse | None = None
    error: str | None = None


class Run(StrictModel):
    provider: str
    model: str
    concurrency: int
    wall_ms: float
    outcomes: list[Outcome]


def unique_object(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON keys are not allowed.")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"{value} is not a valid finite JSON value.")


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON numbers must be finite.")
    return number


def read_json(text: str) -> JsonValue:
    value: JsonValue = json.loads(
        text,
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )
    return value


def parse_task(text: str) -> Task:
    return Task.model_validate(read_json(text))


def validate_tasks(tasks: list[Task]) -> list[Task]:
    if not 1 <= len(tasks) <= MAX_TASKS:
        raise ValueError(f"Supply 1 to {MAX_TASKS} tasks.")
    if len({task.id for task in tasks}) != len(tasks):
        raise ValueError("Each task must have a unique id.")
    return tasks


def parse_upload(data: bytes, filename: str, template: Task) -> list[Task]:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload exceeds the 2 MB limit.")
    text = data.decode("utf-8-sig")
    suffix = filename.lower().rsplit(".", 1)[-1]
    tasks: list[Task] = []
    if suffix == "json":
        rows = read_json(text)
        if not isinstance(rows, list):
            raise ValueError("JSON upload must be an array of tasks.")
        tasks = [Task.model_validate(row) for row in rows]
    elif suffix == "jsonl":
        tasks = [parse_task(line) for line in text.splitlines() if line.strip()]
    elif suffix == "csv":
        reader = csv.DictReader(io.StringIO(text))
        fields = reader.fieldnames
        if fields is None or not {"id", "state"}.issubset(fields):
            raise ValueError("CSV requires id and state columns.")
        if len(fields) != len(set(fields)) or set(fields) - {"id", "state", "questions"}:
            raise ValueError("CSV allows unique id, state, and optional questions columns only.")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("CSV row has missing or extra columns.")
            questions = (
                read_json(row["questions"])
                if row.get("questions", "").strip()
                else template.model_dump(mode="json")["questions"]
            )
            tasks.append(
                Task.model_validate(
                    {"id": row["id"], "state": row["state"], "questions": questions}
                )
            )
    else:
        raise ValueError("Use a .json, .jsonl, or .csv file.")
    return validate_tasks(tasks)


def validate_response(response: DecisionResponse, task: Task) -> DecisionResponse:
    if set(response.answers) != set(task.questions):
        raise ValueError("Response question names do not match the request.")
    for name, question in task.questions.items():
        answer = response.answers[name]
        if answer.type != question.type:
            raise ValueError("Response answer type does not match the question.")
        if isinstance(question, NoulQuestion):
            if answer.noul is None:
                raise ValueError("Noul response is missing its probability.")
            continue
        expected = (
            set(question.criteria)
            if isinstance(question, ChoiceQuestion)
            else {str(i) for i in range(len(question.criteria))}
        )
        probabilities = answer.probabilities
        if probabilities is None or set(probabilities) != expected:
            raise ValueError("Response probability labels do not match the criteria.")
        if any(not 0 <= p <= 1 for p in probabilities.values()) or not math.isclose(
            sum(probabilities.values()), 1, abs_tol=0.01
        ):
            raise ValueError("Response probabilities must be in [0, 1] and sum to 1.")
        if answer.confidence is None:
            raise ValueError("Response is missing confidence.")
        if isinstance(question, ChoiceQuestion):
            if answer.choice not in expected:
                raise ValueError("Response chose a label outside the criteria.")
        else:
            if answer.score is None or not 0 <= answer.score <= len(question.criteria) - 1:
                raise ValueError("Score is outside the requested scale.")
            weighted = sum(int(key) * value for key, value in probabilities.items())
            if not math.isclose(answer.score, weighted, abs_tol=0.02):
                raise ValueError("Score does not match its probability-weighted indices.")
            legend = {str(i): value for i, value in enumerate(question.criteria)}
            if answer.legend != legend:
                raise ValueError("Score legend does not match the requested criteria.")
    return response
