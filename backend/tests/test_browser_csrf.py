# CSRF 토큰 검증
import pytest
from fastapi import HTTPException

from backend.app.core.browser_csrf import (
    create_csrf_token,
    validate_csrf_token,
)


def test_create_csrf_token():
    token = create_csrf_token()

    assert token
    assert isinstance(token, str)


def test_csrf_tokens_are_random():
    token1 = create_csrf_token()
    token2 = create_csrf_token()

    assert token1 != token2


def test_valid_csrf_token():
    token = create_csrf_token()

    validate_csrf_token(token, token)


def test_missing_csrf_cookie():
    with pytest.raises(HTTPException) as exc:
        validate_csrf_token(None, "some-token")

    assert exc.value.status_code == 403


def test_missing_csrf_form_token():
    with pytest.raises(HTTPException) as exc:
        validate_csrf_token("some-token", None)

    assert exc.value.status_code == 403


def test_invalid_csrf_token():
    with pytest.raises(HTTPException) as exc:
        validate_csrf_token("token-a", "token-b")

    assert exc.value.status_code == 403