# JWT 자동 테스트
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from backend.app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-local-pytest-only")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")


def test_create_and_decode_access_token():
    token = create_access_token(user_id=1)

    assert decode_access_token(token) == 1


def test_invalid_token():
    with pytest.raises(InvalidTokenError):
        decode_access_token("invalid.token.value")


def test_expired_token():
    payload = {
        "sub": "1",
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        "test-secret-key-for-local-pytest-only",
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_with_invalid_user_id():
    token = create_access_token(user_id=0)

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)