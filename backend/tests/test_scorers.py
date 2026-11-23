from types import SimpleNamespace

import pytest

from app.services.scorers import score_case


def case(scorer, expected=None, cfg=None):
    return SimpleNamespace(
        scorer=scorer, expected_output=expected, scorer_config=cfg or {}, prompt="q"
    )


def test_exact_match_is_case_insensitive_by_default():
    assert score_case(case("exact_match", "Paris"), " paris ") == 1.0
    assert score_case(case("exact_match", "Paris"), "Paris, France") == 0.0


def test_exact_match_case_sensitive_option():
    c = case("exact_match", "Paris", {"case_sensitive": True})
    assert score_case(c, "paris") == 0.0


def test_contains():
    assert score_case(case("contains", "jupiter"), "It is Jupiter.") == 1.0
    assert score_case(case("contains", "jupiter"), "Saturn") == 0.0


def test_regex():
    assert score_case(case("regex", r"^\d{4}$"), "2024") == 1.0
    assert score_case(case("regex", r"^\d{4}$"), "abc") == 0.0


def test_llm_judge_parses_number():
    c = case("llm_judge", None, {"criteria": "polite"})
    assert score_case(c, "hi", judge=lambda p: "8") == pytest.approx(0.8)
    assert score_case(c, "hi", judge=lambda p: "no idea") == 0.0


def test_unknown_scorer_raises():
    with pytest.raises(ValueError):
        score_case(case("nope"), "x")
