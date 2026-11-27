PW = "password-123"


def auth(client, email):
    client.post("/auth/signup", json={"email": email, "password": PW})
    r = client.post("/auth/login", json={"email": email, "password": PW})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_project_suite(client, h):
    pid = client.post("/projects", json={"name": "P1"}, headers=h).json()["id"]
    sid = client.post(f"/projects/{pid}/suites", json={"name": "S1"}, headers=h).json()["id"]
    return pid, sid


def test_project_crud(client):
    h = auth(client, "a@example.com")
    pid = client.post("/projects", json={"name": "P1"}, headers=h).json()["id"]
    assert [p["name"] for p in client.get("/projects", headers=h).json()] == ["P1"]
    r = client.put(f"/projects/{pid}", json={"name": "Renamed", "description": "d"}, headers=h)
    assert r.status_code == 200 and r.json()["name"] == "Renamed"
    assert client.delete(f"/projects/{pid}", headers=h).status_code == 204
    assert client.get(f"/projects/{pid}", headers=h).status_code == 404
    assert client.get("/projects", headers=h).json() == []


def test_suite_and_case_crud(client):
    h = auth(client, "a@example.com")
    _, sid = make_project_suite(client, h)
    body = {"name": "c1", "prompt": "2+2?", "expected_output": "4", "scorer": "exact_match"}
    created = client.post(f"/suites/{sid}/cases", json=body, headers=h)
    assert created.status_code == 201
    cid = created.json()["id"]
    assert len(client.get(f"/suites/{sid}/cases", headers=h).json()) == 1

    r = client.put(f"/cases/{cid}", json={**body, "expected_output": "four"}, headers=h)
    assert r.status_code == 200 and r.json()["expected_output"] == "four"

    assert client.delete(f"/cases/{cid}", headers=h).status_code == 204
    assert client.get(f"/suites/{sid}/cases", headers=h).json() == []
    assert client.delete(f"/suites/{sid}", headers=h).status_code == 204
    assert client.get(f"/suites/{sid}", headers=h).status_code == 404


def test_cannot_edit_or_delete_someone_elses_case(client):
    h1 = auth(client, "one@example.com")
    h2 = auth(client, "two@example.com")
    _, sid = make_project_suite(client, h1)
    body = {"name": "c1", "prompt": "q", "scorer": "contains"}
    cid = client.post(f"/suites/{sid}/cases", json=body, headers=h1).json()["id"]

    assert client.put(f"/cases/{cid}", json=body, headers=h2).status_code == 404
    assert client.delete(f"/cases/{cid}", headers=h2).status_code == 404
    assert client.get(f"/suites/{sid}/cases", headers=h2).status_code == 404
    assert len(client.get(f"/suites/{sid}/cases", headers=h1).json()) == 1