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


def test_csrf_token_generation():
    token1 = create_csrf_token()
    token2 = create_csrf_token()

    assert token1
    assert token2
    assert token1 != token2


def test_csrf_token_valid():
    token = create_csrf_token()

    validate_csrf_token(token, token)


@pytest.mark.parametrize(
    ("cookie_token", "form_token"),
    [
        (None, None),
        ("token", None),
        (None, "token"),
        ("", "token"),
        ("token", ""),
    ],
)
def test_csrf_token_missing(cookie_token, form_token):
    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(cookie_token, form_token)

    assert exc_info.value.status_code == 403


def test_csrf_token_mismatch():
    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token("cookie-token", "different-form-token")

    assert exc_info.value.status_code == 403

# 위조 토큰 차단 테스트
def test_csrf_rejects_forged_matching_token():
    forged_token = "attacker-controlled-token"

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(
            forged_token,
            forged_token,
        )

    assert exc_info.value.status_code == 403


def test_csrf_rejects_tampered_signature():
    token = create_csrf_token()

    nonce, _ = token.rsplit(".", 1)
    tampered_token = f"{nonce}.invalid-signature"

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(
            tampered_token,
            tampered_token,
        )

    assert exc_info.value.status_code == 403


def test_csrf_token_bound_to_refresh_token():
    refresh_token = "session-refresh-token-A"

    token = create_csrf_token(binding=refresh_token)

    validate_csrf_token(
        token,
        token,
        binding=refresh_token,
    )


def test_csrf_token_rejects_different_session():
    token = create_csrf_token(
        binding="session-refresh-token-A"
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(
            token,
            token,
            binding="session-refresh-token-B",
        )

    assert exc_info.value.status_code == 403


def test_csrf_token_rejects_missing_session_binding():
    token = create_csrf_token(
        binding="session-refresh-token-A"
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(
            token,
            token,
        )

    assert exc_info.value.status_code == 403
