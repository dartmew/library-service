PASS = "password123"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client, email: str, name: str = "Тест") -> None:
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": PASS, "name": name},
    )
    assert resp.status_code == 201, resp.text


def get_token(client, email: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": PASS})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def make_book(client, token: str, title="Мастер и Маргарита", author="Булгаков",
              genre="роман", total_copies=1) -> dict:
    resp = client.post(
        "/books",
        json={"title": title, "author": author, "genre": genre, "total_copies": total_copies},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
