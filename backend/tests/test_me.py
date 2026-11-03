# /me API 자동 테스트
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.core import dependencies
from backend.app.core.security import create_access_token
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "local-test-secret-key-for-pytest-2026-only",
    )


def test_me_success(monkeypatch):
    fake_user = SimpleNamespace(
        id=1,
        email="test@example.com",
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        dependencies,
        "find_user_by_id",
        lambda session, user_id: fake_user,
    )

    token = create_access_token(1)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["email"] == "test@example.com"
    assert "password_hash" not in response.json()


def test_me_without_token():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_invalid_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token"},
    )

    assert response.status_code == 401


def test_me_user_not_found(monkeypatch):
    monkeypatch.setattr(
        dependencies,
        "find_user_by_id",
        lambda session, user_id: None,
    )

    token = create_access_token(999999)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401