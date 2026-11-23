"""Scorers turn (test case, model output) into a score in [0, 1]."""

import re
from collections.abc import Callable
from typing import Any

Judge = Callable[[str], str]


def _parse_judge_score(text: str) -> float:
    m = re.search(r"\d+(?:\.\d+)?", text)
    if not m:
        return 0.0
    return max(0.0, min(1.0, float(m.group()) / 10.0))


def score_case(case: Any, output: str, judge: Judge | None = None) -> float:
    cfg = case.scorer_config or {}
    expected = case.expected_output or ""

    if case.scorer in ("exact_match", "contains"):
        a, b = output.strip(), expected.strip()
        if not cfg.get("case_sensitive", False):
            a, b = a.lower(), b.lower()
        hit = (a == b) if case.scorer == "exact_match" else (b in a)
        return 1.0 if hit else 0.0

    if case.scorer == "regex":
        pattern = cfg.get("pattern", expected)
        flags = 0 if cfg.get("case_sensitive", False) else re.IGNORECASE
        return 1.0 if re.search(pattern, output, flags) else 0.0

    if case.scorer == "llm_judge":
        if judge is None:
            raise ValueError("llm_judge needs a judge model")
        prompt = (
            "You are grading an AI answer.\n"
            f"Criteria: {cfg.get('criteria', 'The answer is correct and helpful.')}\n"
            f"Question: {case.prompt}\n"
            f"Reference answer (may be empty): {expected}\n"
            f"Answer to grade: {output}\n"
            "Reply with only a number from 0 to 10."
        )
        return _parse_judge_score(judge(prompt))

    raise ValueError(f"Unknown scorer: {case.scorer}")