def _register(client, username="alice", password="password123"):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def _login(client, username="alice", password="password123"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_register_login_flow(client):
    r = _register(client)
    assert r.status_code == 201
    assert r.json()["username"] == "alice"

    r2 = _login(client)
    assert r2.status_code == 200
    body = r2.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_create_bot_unique_per_user(client):
    _register(client, "alice", "password123")
    token = _login(client, "alice", "password123").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "mybot", "description": "x", "code": "def act(observation, state):\n    return 'C', state\n"}
    r1 = client.post("/api/bots", json=payload, headers=headers)
    assert r1.status_code == 201

    r2 = client.post("/api/bots", json=payload, headers=headers)
    assert r2.status_code == 409
    assert r2.json()["detail"] == "bot_name_taken"

