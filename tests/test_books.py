from tests.utils import auth, make_book


def test_create_and_get(client, user_token):
    created = make_book(client, user_token)
    got = client.get(f"/books/{created['id']}", headers=auth(user_token))
    assert got.status_code == 200
    assert got.json()["available_copies"] == 1


def test_list_with_filter(client, user_token):
    make_book(client, user_token, author="Пушкин", title="Евгений Онегин", genre="поэзия")
    make_book(client, user_token, title="Космос", author="Саган", genre="наука")
    resp = client.get("/books?author=пуш", headers=auth(user_token))
    assert resp.status_code == 200
    titles = [b["title"] for b in resp.json()]
    assert titles == ["Евгений Онегин"]


def test_filter_by_title_and_genre(client, user_token):
    make_book(client, user_token, title="Тени", genre="детектив")
    make_book(client, user_token, title="Свет", genre="драма")

    assert client.get("/books?title=тени", headers=auth(user_token)).json()[0]["title"] == "Тени"
    assert client.get("/books?genre=драма", headers=auth(user_token)).json()[0]["genre"] == "драма"


def test_patch_partial(client, user_token, book):
    resp = client.patch(f"/books/{book['id']}", json={"genre": "классика"}, headers=auth(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["genre"] == "классика"
    assert data["title"] == book["title"]


def test_get_missing(client, user_token):
    assert client.get("/books/999999", headers=auth(user_token)).status_code == 404


def test_delete(client, user_token, book):
    assert client.delete(f"/books/{book['id']}", headers=auth(user_token)).status_code == 204
    assert client.get(f"/books/{book['id']}", headers=auth(user_token)).status_code == 404


def test_delete_book_with_active_rental_409(client, user_token, book):
    client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    assert client.delete(f"/books/{book['id']}", headers=auth(user_token)).status_code == 409


def test_requires_token(client):
    assert client.get("/books").status_code == 401


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
