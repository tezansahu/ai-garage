import pytest

from playground.metrics import percentile, summary, wall_ratio
from playground.models import Answer, DecisionResponse, Outcome, Run


def make_run(provider="Decision-1", wall=1000):
    return Run(
        provider=provider,
        model="test",
        concurrency=5,
        wall_ms=wall,
        outcomes=[
            Outcome(
                task_id=str(i),
                latency_ms=latency,
                response=DecisionResponse(
                    model="test", answers={"q": Answer(type="noul", noul=0.9)}
                ),
            )
            for i, latency in enumerate([100, 200, 300, 400])
        ],
    )


def test_metrics_exact_values():
    run = make_run()
    result = summary(run)
    assert result["p50 (ms)"] == 250
    assert result["p95 (ms)"] == 385
    assert result["Tasks/s"] == 4
    assert percentile([], 0.95) is None
    assert percentile([123], 0.95) == 123
    assert wall_ratio(make_run("GPT-5-mini", 5000), run) == 5


def test_failed_requests_are_not_success_metrics_or_speedups():
    run = make_run()
    run.outcomes[0].response = None
    run.outcomes[0].error = "failed"
    result = summary(run)
    assert result["Succeeded"] == 3
    assert result["Failed"] == 1
    assert result["p50 (ms)"] == 300
    assert result["p95 (ms)"] == 390
    assert result["Tasks/s"] == 3
    assert wall_ratio(make_run("GPT-5-mini", 5000), run) is None
    for item in run.outcomes:
        item.response = None
        item.error = "failed"
    assert summary(run)["p50 (ms)"] is None
    assert summary(run)["p95 (ms)"] is None


@pytest.mark.parametrize(
    "update",
    [
        {"concurrency": 1},
        {"wall_ms": 0},
        {"outcomes": []},
    ],
)
def test_ratios_require_comparable_complete_runs(update):
    assert wall_ratio(make_run(), make_run().model_copy(update=update)) is None
