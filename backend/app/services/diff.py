"""Regression diff between two runs of the same suite."""

from collections import Counter
from collections.abc import Iterable
from typing import Any

from app.services.stats import summarize

EPSILON = 0.05
ORDER = ["regressed", "improved", "new", "missing", "unchanged"]


def classify(base: Any | None, cand: Any | None) -> str:
    if base is None:
        return "new"
    if cand is None:
        return "missing"
    if base.passed and not cand.passed:
        return "regressed"
    if cand.passed and not base.passed:
        return "improved"
    delta = (cand.score or 0.0) - (base.score or 0.0)
    if delta < -EPSILON:
        return "regressed"
    if delta > EPSILON:
        return "improved"
    return "unchanged"


def build_diff(
    cases: Iterable[Any], base_results: Iterable[Any], cand_results: Iterable[Any]
) -> dict[str, Any]:
    base_list, cand_list = list(base_results), list(cand_results)
    base = {r.test_case_id: r for r in base_list}
    cand = {r.test_case_id: r for r in cand_list}
    items = []
    for case in cases:
        b, c = base.get(case.id), cand.get(case.id)
        if b is None and c is None:
            continue
        delta = None
        if b is not None and c is not None:
            delta = (c.score or 0.0) - (b.score or 0.0)
        items.append(
            {
                "test_case_id": case.id,
                "name": case.name,
                "prompt": case.prompt,
                "status": classify(b, c),
                "baseline_passed": b.passed if b else None,
                "candidate_passed": c.passed if c else None,
                "baseline_score": b.score if b else None,
                "candidate_score": c.score if c else None,
                "score_delta": delta,
                "baseline_output": b.output if b else None,
                "candidate_output": c.output if c else None,
                "baseline_error": b.error if b else None,
                "candidate_error": c.error if c else None,
            }
        )
    items.sort(key=lambda i: (ORDER.index(i["status"]), i["name"]))
    counts = Counter(i["status"] for i in items)
    base_rate = summarize(base_list)["pass_rate"]
    cand_rate = summarize(cand_list)["pass_rate"]
    return {
        "counts": {k: counts.get(k, 0) for k in ORDER},
        "baseline_pass_rate": base_rate,
        "candidate_pass_rate": cand_rate,
        "pass_rate_delta": cand_rate - base_rate,
        "items": items,
    }


