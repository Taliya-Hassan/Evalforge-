import math
from collections.abc import Iterable
from typing import Any


def percentile(values: list[int], p: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p / 100 * len(ordered)) - 1)]


def summarize(results: Iterable[Any]) -> dict[str, Any]:
    rows = list(results)
    total = len(rows)
    passed = sum(1 for r in rows if r.passed)
    errors = sum(1 for r in rows if r.error)
    latencies = [r.latency_ms for r in rows if r.latency_ms is not None]
    scores = [r.score or 0.0 for r in rows]
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed - errors,
        "errors": errors,
        "pass_rate": passed / total if total else 0.0,
        "mean_score": sum(scores) / total if total else 0.0,
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
    }
