from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.api.v1 import auth
from backend.app.main import app
from backend.app.services.auth_service import DuplicateEmailError

client = TestClient(app)

# 실제 DB에 회원을 생성하지 않음. 
# monkeypatch로 회원가입 Service를 대신 호출하도록 설정했기 때문
def test_register_success(monkeypatch):
    def fake_register(session, email, password):
        return SimpleNamespace(
            id=1,
            email=email,
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(auth, "register_user", fake_register)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_duplicate_email(monkeypatch):
    def fake_register(session, email, password):
        raise DuplicateEmailError("이미 사용 중인 이메일입니다.")

    monkeypatch.setattr(auth, "register_user", fake_register)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 409


def test_register_invalid_email():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "1234",
        },
    )

    assert response.status_code == 422