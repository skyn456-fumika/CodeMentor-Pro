# CSRF 차단 자동 테스트
import pytest
from fastapi.testclient import TestClient

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
