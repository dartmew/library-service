import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from tests.utils import PASS, get_token, register, make_book

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден — проверьте .env")

TEST_DB_NAME = "library_test"
TEST_URL = make_url(DATABASE_URL).set(database=TEST_DB_NAME)

# создаём тестовую базу, если её ещё нет
_admin = create_engine(TEST_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
with _admin.connect() as conn:
    exists = conn.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB_NAME}
    ).scalar()
    if not exists:
        conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

engine = create_engine(TEST_URL)
TestSession = sessionmaker(bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def user_token(client):
    register(client, "user@test.com")
    return get_token(client, "user@test.com")


@pytest.fixture()
def other_token(client):
    register(client, "other@test.com")
    return get_token(client, "other@test.com")


@pytest.fixture()
def admin_token(client, db_session):
    register(client, "admin@test.com")
    user = db_session.scalar(select(User).where(User.email == "admin@test.com"))
    user.is_admin = True
    db_session.commit()
    return get_token(client, "admin@test.com")


@pytest.fixture()
def book(client, user_token):
    return make_book(client, user_token)