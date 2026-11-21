from tests.utils import auth, make_book


def test_popular(client, user_token, book):
    resp = client.get("/analytics/popular", headers=auth(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == book["title"]
    assert data[0]["total_rentals"] == 0


def test_popular_after_rent(client, user_token, book):
    client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    resp = client.get("/analytics/popular", headers=auth(user_token))
    assert resp.json()[0]["total_rentals"] == 1


def test_genres(client, user_token, book):
    resp = client.get("/analytics/genres", headers=auth(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["genre"] == book["genre"]
    assert data[0]["books"] == 1
    assert data[0]["rentals_active"] == 0


def test_stats(client, user_token, book):
    client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    client.post(f"/rentals/{1}/return", headers=auth(user_token))
    resp = client.get("/analytics/stats", headers=auth(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rentals"] == 1
    assert data["active_rentals"] == 0
    assert data["total_books"] == 1


def test_popular_plot_is_png(client, user_token, book):
    resp = client.get("/analytics/popular-plot", headers=auth(user_token))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_genres_plot_is_png(client, user_token, book):
    resp = client.get("/analytics/genres-plot", headers=auth(user_token))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_analytics_requires_token(client):
    assert client.get("/analytics/popular").status_code == 401
    assert client.get("/analytics/stats").status_code == 401
