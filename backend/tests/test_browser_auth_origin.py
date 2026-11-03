# 브라우저 인증 API 통합 테스트
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

BROWSER_ENDPOINTS = (
    "/api/v1/auth/browser-login",
    "/api/v1/auth/browser-refresh",
    "/api/v1/auth/browser-logout",
    "/api/v1/auth/browser-signin",
    "/api/v1/auth/browser-signout",
)


@pytest.mark.parametrize("endpoint", BROWSER_ENDPOINTS)
def test_rejects_untrusted_origin(endpoint):
    response = client.post(
        endpoint,
        headers={
            "Origin": "https://evil.example.com",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "허용되지 않은 브라우저 요청입니다."
    )


@pytest.mark.parametrize("endpoint", BROWSER_ENDPOINTS)
def test_rejects_missing_origin_and_referer(endpoint):
    response = client.post(
        endpoint,
        headers={
            "Origin": "",
            "Referer": "",
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize("endpoint", BROWSER_ENDPOINTS)
def test_rejects_untrusted_referer(endpoint):
    response = client.post(
        endpoint,
        headers={
            "Referer": "https://evil.example.com/attack",
        },
    )

    assert response.status_code == 403