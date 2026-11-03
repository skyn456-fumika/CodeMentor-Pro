# Refresh API 자동 테스트
from fastapi.testclient import TestClient

from backend.app.api.v1 import auth
from backend.app.main import app

client = TestClient(app)


def test_refresh_success(monkeypatch):
    monkeypatch.setattr(
        auth,
        "rotate_refresh_token",
        lambda session, raw_token: (1, "new-refresh-token"),
    )
    monkeypatch.setattr(
        auth,
        "create_access_token",
        lambda user_id: "new-access-token",
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }


def test_refresh_invalid_token(monkeypatch):
    def fake_rotate(session, raw_token):
        raise auth.InvalidRefreshTokenError("유효하지 않은 토큰")

    monkeypatch.setattr(
        auth,
        "rotate_refresh_token",
        fake_rotate,
    )

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401


def test_refresh_empty_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ""},
    )

    assert response.status_code == 422