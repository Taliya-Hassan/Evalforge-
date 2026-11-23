CREDS = {"email": "Ada@Example.com", "password": "correct-horse-battery"}


def signup(client):
    return client.post("/auth/signup", json=CREDS)


def login(client, password=CREDS["password"]):
    return client.post("/auth/login", json={"email": CREDS["email"], "password": password})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_signup_creates_user_and_hides_hash(client):
    r = signup(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ada@example.com"
    assert "password" not in body and "password_hash" not in body


def test_duplicate_signup_conflicts(client):
    signup(client)
    assert signup(client).status_code == 409


def test_short_password_rejected(client):
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "short"})
    assert r.status_code == 422


def test_login_success_and_me(client):
    signup(client)
    token = login(client).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ada@example.com"


def test_login_wrong_password(client):
    signup(client)
    assert login(client, "wrong-password-123").status_code == 401


def test_me_requires_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    r = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401
