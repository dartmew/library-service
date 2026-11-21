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


def test_get_own_profile(client, user_token):
    me_id = client.get("/auth/me", headers=auth(user_token)).json()["id"]
    resp = client.get(f"/users/{me_id}", headers=auth(user_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == me_id


def test_get_missing_404(client, user_token):
    assert client.get("/users/999999", headers=auth(user_token)).status_code == 404


def test_patch_own_name(client, user_token):
    me_id = client.get("/auth/me", headers=auth(user_token)).json()["id"]
    resp = client.patch(f"/users/{me_id}", json={"name": "Новое имя"}, headers=auth(user_token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Новое имя"
    # и перечитываем — имя действительно сохранилось
    assert client.get(f"/users/{me_id}", headers=auth(user_token)).json()["name"] == "Новое имя"


def test_patch_missing_404(client, user_token):
    resp = client.patch("/users/999999", json={"name": "x"}, headers=auth(user_token))
    assert resp.status_code == 404


def test_delete_missing_404(client, admin_token):
    assert client.delete("/users/999999", headers=auth(admin_token)).status_code == 404
