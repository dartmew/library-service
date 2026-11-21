from tests.utils import PASS, auth, get_token, register


def test_register_and_me(client, user_token):
    resp = client.get("/auth/me", headers=auth(user_token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"
    assert "hashed_password" not in resp.json()


def test_register_duplicate_email(client):
    register(client, "dup@test.com")
    resp = client.post(
        "/auth/register",
        json={"email": "dup@test.com", "password": PASS, "name": "Второй"},
    )
    assert resp.status_code == 409


def test_login_wrong_password(client):
    register(client, "wrong@test.com")
    resp = client.post(
        "/auth/token", data={"username": "wrong@test.com", "password": "неправильный"}
    )
    assert resp.status_code == 401


def test_me_without_token(client):
    assert client.get("/auth/me").status_code == 401


def test_register_short_password(client):
    resp = client.post(
        "/auth/register",
        json={"email": "short@test.com", "password": "123", "name": "Краткий"},
    )
    assert resp.status_code == 422


def test_me_invalid_token(client):
    resp = client.get("/auth/me", headers=auth("fake.token.value"))
    assert resp.status_code == 401
