import uuid
from types import SimpleNamespace as NS

from app.services.diff import build_diff, classify
from app.services.stats import percentile, summarize


def res(case_id, passed, score):
    return NS(test_case_id=case_id, passed=passed, score=score, output="o", error=None,
              latency_ms=10)


def test_classify():
    assert classify(res(1, True, 1.0), res(1, False, 0.0)) == "regressed"
    assert classify(res(1, False, 0.0), res(1, True, 1.0)) == "improved"
    assert classify(res(1, True, 1.0), res(1, True, 1.0)) == "unchanged"
    assert classify(res(1, True, 0.9), res(1, True, 0.5)) == "regressed"  # score drop > epsilon
    assert classify(None, res(1, True, 1.0)) == "new"
    assert classify(res(1, True, 1.0), None) == "missing"


def test_build_diff_orders_regressions_first():
    ids = [uuid.uuid4() for _ in range(3)]
    cases = [NS(id=i, name=n, prompt="p") for i, n in zip(ids, ["a", "b", "c"], strict=True)]
    base = [res(ids[0], True, 1), res(ids[1], False, 0), res(ids[2], True, 1)]
    cand = [res(ids[0], True, 1), res(ids[1], True, 1), res(ids[2], False, 0)]
    out = build_diff(cases, base, cand)
    assert [i["status"] for i in out["items"]] == ["regressed", "improved", "unchanged"]
    assert out["counts"]["regressed"] == 1
    assert out["pass_rate_delta"] == 0.0


def test_percentile_and_summary():
    assert percentile([10, 20, 30, 40], 50) == 20
    assert percentile([], 50) is None
    s = summarize([res(1, True, 1.0), res(2, False, 0.0)])
    assert s["pass_rate"] == 0.5 and s["total"] == 2
