# CSRF 차단 자동 테스트
import re

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.core.browser_csrf import (
    CSRF_COOKIE_NAME,
    validate_csrf_token,
)
from backend.app.main import app

AUTH_URL = "/api/v1/auth"
ORIGIN = "http://localhost:8000"


def make_form_data(endpoint: str, csrf_token: str) -> dict:
    data = {"csrf_token": csrf_token}

    if endpoint == "/browser-signin":
        data.update({
            "email": "test@example.com",
            "password": "TestPassword123!",
        })

    return data


@pytest.mark.parametrize(
    "endpoint",
    [
        "/browser-signin",
        "/browser-signout",
    ],
)
def test_browser_form_rejects_missing_csrf(endpoint):
    with TestClient(app) as client:
        response = client.post(
            f"{AUTH_URL}{endpoint}",
            headers={"Origin": ORIGIN},
            data=make_form_data(endpoint, ""),
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF 토큰이 없습니다."


@pytest.mark.parametrize(
    "endpoint",
    [
        "/browser-signin",
        "/browser-signout",
    ],
)
def test_browser_form_rejects_invalid_csrf(endpoint):
    with TestClient(app) as client:
        client.cookies.set(
            "codementor_csrf",
            "valid-cookie-token",
        )

        response = client.post(
            f"{AUTH_URL}{endpoint}",
            headers={"Origin": ORIGIN},
            data=make_form_data(endpoint, "invalid-form-token"),
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF 토큰이 일치하지 않습니다."


def test_signout_csrf_bound_to_refresh_token():
    with TestClient(app) as client:
        client.cookies.set(
            "codementor_refresh",
            "test-refresh-session-A",
        )

        response = client.get(
            f"{AUTH_URL}/browser-signout"
        )

    assert response.status_code == 200

    csrf_cookie = response.cookies.get(CSRF_COOKIE_NAME)

    match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        response.text,
    )

    assert match is not None

    form_token = match.group(1)

    # 동일한 인증 세션에서는 정상
    validate_csrf_token(
        csrf_cookie,
        form_token,
        binding="test-refresh-session-A",
    )


def test_signout_csrf_rejects_other_session():
    with TestClient(app) as client:
        client.cookies.set(
            "codementor_refresh",
            "test-refresh-session-A",
        )

        response = client.get(
            f"{AUTH_URL}/browser-signout"
        )

    csrf_token = response.cookies.get(CSRF_COOKIE_NAME)

    with pytest.raises(HTTPException) as exc_info:
        validate_csrf_token(
            csrf_token,
            csrf_token,
            binding="test-refresh-session-B",
        )

    assert exc_info.value.status_code == 403


# 다른 인증 세션의 CSRF 토큰 차단 테스트
def test_browser_signout_rejects_other_session_csrf():
    with TestClient(app) as client:
        # 세션 A의 Refresh Token 설정
        client.cookies.set(
            "codementor_refresh",
            "refresh-token-session-A",
        )

        # 세션 A의 CSRF 토큰 발급
        response = client.get(
            f"{AUTH_URL}/browser-signout"
        )

        assert response.status_code == 200

        match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )

        assert match is not None
        csrf_token = match.group(1)

        # Refresh Token만 세션 B로 교체
        client.cookies.set(
            "codementor_refresh",
            "refresh-token-session-B",
        )

        # 세션 A의 CSRF 토큰으로 로그아웃 시도
        response = client.post(
            f"{AUTH_URL}/browser-signout",
            headers={"Origin": ORIGIN},
            data={"csrf_token": csrf_token},
        )

        # 다른 세션의 토큰이므로 차단
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "유효하지 않은 CSRF 토큰입니다."
        )

# 로컬 주소가 아닌 운영용 주소를 설정했을 때도 취소 버튼이 올바르게 생성되는지 검증
def test_signout_cancel_link_uses_configured_url(monkeypatch):
    monkeypatch.setenv(
        "STREAMLIT_APP_URL",
        "https://app.example.com",
    )

    with TestClient(app) as client:
        response = client.get(
            f"{AUTH_URL}/browser-signout"
        )

    assert response.status_code == 200
    assert 'href="https://app.example.com"' in response.text