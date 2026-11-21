from tests.utils import auth


def test_list_requires_admin(client, user_token):
    assert client.get("/users", headers=auth(user_token)).status_code == 403


def test_admin_sees_users(client, admin_token, user_token):
    resp = client.get("/users", headers=auth(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_cannot_read_other_profile(client, user_token, other_token):
    resp = client.get("/users/1", headers=auth(other_token))
    assert resp.status_code == 403


def test_cannot_edit_other(client, user_token, other_token):
    resp = client.patch("/users/1", json={"name": "хакер"}, headers=auth(other_token))
    assert resp.status_code == 403


def test_admin_cannot_delete_self(client, admin_token):
    resp = client.get("/auth/me", headers=auth(admin_token))
    my_id = resp.json()["id"]
    assert client.delete(f"/users/{my_id}", headers=auth(admin_token)).status_code == 409


def test_admin_can_delete_other(client, admin_token, other_token):
    resp = client.get("/auth/me", headers=auth(other_token))
    other_id = resp.json()["id"]
    assert client.delete(f"/users/{other_id}", headers=auth(admin_token)).status_code == 204
