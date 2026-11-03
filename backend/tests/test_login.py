from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.api.v1 import auth
from backend.app.main import app
from backend.app.services.auth_service import InvalidCredentialsError

client = TestClient(app)



def test_login_success(monkeypatch):
    # Access Token 발급 Mock
    monkeypatch.setattr(
        auth,
        "login_user",
        lambda session, email, password: "fake.jwt.token",
    )

    # 인증된 사용자 조회 Mock
    monkeypatch.setattr(
        auth,
        "find_user_by_email",
        # 실제 SQLAlchemy 엔티티를 만들지 않고도 user.id를 제공하는 간단한 가짜 객체
        lambda session, email: SimpleNamespace(id=1),
    )

    # Refresh Token 발급 Mock
    monkeypatch.setattr(
        auth,
        "issue_refresh_token",
        lambda session, user_id: "fake-refresh-token-for-testing",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] == "fake.jwt.token"
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] == "fake-refresh-token-for-testing"

    assert set(data.keys()) == {
        "access_token",
        "refresh_token",
        "token_type",
    }


def test_login_invalid_credentials(monkeypatch):
    def fake_login(session, email, password):
        raise InvalidCredentialsError(
            "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    monkeypatch.setattr(auth, "login_user", fake_login)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


def test_login_invalid_email():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-email",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 422
