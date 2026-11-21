from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.models import Rental
from tests.utils import auth, make_book


def test_rent_and_return(client, user_token, book):
    resp = client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    assert resp.status_code == 201
    rental = resp.json()
    assert rental["returned_at"] is None
    assert rental["due_at"] is not None

    back = client.post(f"/rentals/{rental['id']}/return", headers=auth(user_token))
    assert back.status_code == 200
    assert back.json()["returned_at"] is not None


def test_double_rent_409(client, user_token, book):
    assert client.post(f"/rentals/book/{book['id']}", headers=auth(user_token)).status_code == 201
    assert client.post(f"/rentals/book/{book['id']}", headers=auth(user_token)).status_code == 409


def test_no_free_copies(client, user_token, other_token):
    bk = make_book(client, user_token, total_copies=1)
    assert client.post(f"/rentals/book/{bk['id']}", headers=auth(user_token)).status_code == 201
    assert client.post(f"/rentals/book/{bk['id']}", headers=auth(other_token)).status_code == 409

    client.patch(f"/books/{bk['id']}", json={"total_copies": 2}, headers=auth(user_token))
    assert client.post(f"/rentals/book/{bk['id']}", headers=auth(other_token)).status_code == 201


def test_cannot_return_someone_elses(client, user_token, other_token, book):
    r = client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    rental_id = r.json()["id"]
    assert client.post(f"/rentals/{rental_id}/return", headers=auth(other_token)).status_code == 403


def test_double_return_409(client, user_token, book):
    r = client.post(f"/rentals/book/{book['id']}", headers=auth(user_token))
    rental_id = r.json()["id"]
    client.post(f"/rentals/{rental_id}/return", headers=auth(user_token))
    assert client.post(f"/rentals/{rental_id}/return", headers=auth(user_token)).status_code == 409


def test_active_filter(client, user_token):
    bk1 = make_book(client, user_token, title="Книга раз")
    bk2 = make_book(client, user_token, title="Книга два")
    client.post(f"/rentals/book/{bk1['id']}", headers=auth(user_token))
    r2 = client.post(f"/rentals/book/{bk2['id']}", headers=auth(user_token))
    client.post(f"/rentals/{r2.json()['id']}/return", headers=auth(user_token))

    resp = client.get("/rentals/my?active=true", headers=auth(user_token))
    assert [r["book_id"] for r in resp.json()] == [bk1["id"]]


def test_overdue_filter(client, db_session, user_token, admin_token):
    bk = make_book(client, user_token)
    r = client.post(f"/rentals/book/{bk['id']}", headers=auth(user_token))
    rental_id = r.json()["id"]

    db_session.execute(
        update(Rental)
        .where(Rental.id == rental_id)
        .values(due_at=datetime.now(timezone.utc) - timedelta(days=3))
    )
    db_session.commit()

    overdue = client.get("/rentals?overdue=true", headers=auth(admin_token))
    assert [x["id"] for x in overdue.json()] == [rental_id]

    client.post(f"/rentals/{rental_id}/return", headers=auth(admin_token))
    assert client.get("/rentals?overdue=true", headers=auth(admin_token)).json() == []
