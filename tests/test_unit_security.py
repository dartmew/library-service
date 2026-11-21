import pytest
from jose import jwt

from app.security import ALGORITHM, SECRET_KEY, create_access_token, hash_password, verify_password


def test_hash_is_not_plaintext():
    hashed = hash_password("password123")
    assert hashed != "password123"
    assert hashed.startswith("$2")


def test_verify_roundtrip():
    hashed = hash_password("password123")
    assert verify_password("password123", hashed) is True
    assert verify_password("не_тот_пароль", hashed) is False


def test_token_contains_email_and_expiry():
    token = create_access_token("user@test.com")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user@test.com"
    assert "exp" in payload


def test_wrong_key_cannot_decode():
    token = create_access_token("user@test.com")
    with pytest.raises(Exception):
        jwt.decode(token, "не_тот_ключ", algorithms=[ALGORITHM])
