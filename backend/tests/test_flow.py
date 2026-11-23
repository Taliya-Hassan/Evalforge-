import pytest

from app.config import settings

PW = "password-123"


def headers(client, email="a@example.com"):
    client.post("/auth/signup", json={"email": email, "password": PW})
    token = client.post("/auth/login", json={"email": email, "password": PW}).json()
    return {"Authorization": f"Bearer {token['access_token']}"}


def setup_suite(client, h):
    pid = client.post("/projects", json={"name": "Bot"}, headers=h).json()["id"]
    sid = client.post(f"/projects/{pid}/suites", json={"name": "Smoke"}, headers=h).json()["id"]
    for name, prompt, expected, scorer in [
        ("q1", "q1", "yes", "exact_match"),
        ("q2", "q2", "Paris", "contains"),
        ("q3", "q3", "4", "exact_match"),
    ]:
        r = client.post(
            f"/suites/{sid}/cases",
            json={"name": name, "prompt": prompt, "expected_output": expected, "scorer": scorer},
            headers=h,
        )
        assert r.status_code == 201
    return pid, sid


def add_model(client, h, pid, name, responses, provider="mock"):
    r = client.post(
        f"/projects/{pid}/models",
        json={"name": name, "provider": provider, "model_identifier": name,
              "params": {"responses": responses}},
        headers=h,
    )
    assert r.status_code == 201
    return r.json()["id"]


def run_suite(client, h, sid, mid):
    r = client.post(f"/suites/{sid}/runs", json={"model_id": mid}, headers=h)
    assert r.status_code == 202
    return r.json()["id"]


def test_full_flow_define_run_diff(client):
    h = headers(client)
    pid, sid = setup_suite(client, h)
    good = add_model(client, h, pid, "v1", {"q1": "yes", "q2": "Paris", "q3": "5"})
    bad = add_model(client, h, pid, "v2", {"q1": "no", "q2": "Paris", "q3": "4"})

    r1 = run_suite(client, h, sid, good)
    r2 = run_suite(client, h, sid, bad)

    detail = client.get(f"/runs/{r1}", headers=h).json()
    assert detail["status"] == "completed"
    assert detail["summary"]["total"] == 3 and detail["summary"]["passed"] == 2

    d = client.get(f"/suites/{sid}/diff?baseline={r1}&candidate={r2}", headers=h).json()
    assert d["counts"] == {"regressed": 1, "improved": 1, "new": 0, "missing": 0, "unchanged": 1}
    assert d["items"][0]["name"] == "q1" and d["items"][0]["status"] == "regressed"

    # default: latest two completed runs
    d2 = client.get(f"/suites/{sid}/diff", headers=h)
    assert d2.status_code == 200


def test_other_users_cannot_see_my_data(client):
    h1 = headers(client, "one@example.com")
    h2 = headers(client, "two@example.com")
    pid, sid = setup_suite(client, h1)
    assert client.get(f"/projects/{pid}", headers=h2).status_code == 404
    assert client.get(f"/suites/{sid}", headers=h2).status_code == 404
    assert client.get("/projects", headers=h2).json() == []
    assert client.get("/projects").status_code == 401


def test_provider_error_is_recorded_not_fatal(client, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    h = headers(client)
    pid, sid = setup_suite(client, h)
    mid = add_model(client, h, pid, "gpt", {}, provider="openai")
    rid = run_suite(client, h, sid, mid)
    detail = client.get(f"/runs/{rid}", headers=h).json()
    assert detail["status"] == "completed"
    assert detail["summary"]["errors"] == 3
    assert "OPENAI_API_KEY" in detail["results"][0]["error"]


def test_empty_suite_cannot_run_and_duplicate_names_conflict(client):
    h = headers(client)
    pid = client.post("/projects", json={"name": "P"}, headers=h).json()["id"]
    assert client.post("/projects", json={"name": "P"}, headers=h).status_code == 409
    sid = client.post(f"/projects/{pid}/suites", json={"name": "S"}, headers=h).json()["id"]
    mid = add_model(client, h, pid, "m", {})
    r = client.post(f"/suites/{sid}/runs", json={"model_id": mid}, headers=h)
    assert r.status_code == 400


def test_case_update_and_validation(client):
    h = headers(client)
    _, sid = setup_suite(client, h)
    case = client.get(f"/suites/{sid}/cases", headers=h).json()[0]
    body = {"name": "renamed", "prompt": case["prompt"], "scorer": "contains",
            "expected_output": "x", "threshold": 0.5}
    r = client.put(f"/cases/{case['id']}", json=body, headers=h)
    assert r.status_code == 200 and r.json()["name"] == "renamed"
    bad = {**body, "threshold": 7}
    assert client.put(f"/cases/{case['id']}", json=bad, headers=h).status_code == 422


@pytest.mark.parametrize("path", ["/projects", "/auth/me"])
def test_requires_auth(client, path):
    assert client.get(path).status_code == 401
