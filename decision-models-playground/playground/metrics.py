from __future__ import annotations

import math
from statistics import median

from playground.models import Run


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    low, high = math.floor(index), math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def summary(run: Run) -> dict[str, str | int | float | None]:
    latencies = [item.latency_ms for item in run.outcomes if item.response is not None]
    return {
        "Provider": run.provider,
        "Requested model": run.model,
        "Concurrency": run.concurrency,
        "Succeeded": len(latencies),
        "Failed": len(run.outcomes) - len(latencies),
        "Wall time (s)": round(run.wall_ms / 1000, 3),
        "p50 (ms)": round(median(latencies), 1) if latencies else None,
        "p95 (ms)": round(percentile(latencies, 0.95) or 0, 1) if latencies else None,
        "Tasks/s": round(len(latencies) * 1000 / run.wall_ms, 2) if run.wall_ms > 0 else None,
    }


def wall_ratio(baseline: Run, candidate: Run) -> float | None:
    baseline_ids = [item.task_id for item in baseline.outcomes]
    candidate_ids = [item.task_id for item in candidate.outcomes]
    if (
        baseline_ids != candidate_ids
        or not baseline_ids
        or baseline.concurrency != candidate.concurrency
        or any(
            item.error or item.response is None for item in baseline.outcomes + candidate.outcomes
        )
        or candidate.wall_ms <= 0
    ):
        return None
    return baseline.wall_ms / candidate.wall_ms
