# 대화 세션 생성 자동 테스트
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import chats
from backend.app.core.dependencies import get_current_user
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1)
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)

# 로그인 사용자 ID가 Service로 전달되는지 검증
def test_create_chat_success(monkeypatch, authenticated_user):
    saved_data = {}

    def fake_create_chat_session(session, user_id, title):
        saved_data["user_id"] = user_id
        saved_data["title"] = title

        return SimpleNamespace(
            id=1,
            user_id=user_id,
            title=title,
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(
        chats,
        "create_chat_session",
        fake_create_chat_session,
    )

    response = client.post(
        "/api/v1/chats",
        json={"title": "Python 예외 처리 공부"},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["user_id"] == 1
    assert data["title"] == "Python 예외 처리 공부"

    assert saved_data["user_id"] == 1

# 인증 없이 대화방을 생성할 수 없는지 확인
def test_create_chat_without_authentication():
    response = client.post(
        "/api/v1/chats",
        json={"title": "인증 없는 대화"},
    )

    assert response.status_code == 401


def test_create_chat_blank_title(monkeypatch, authenticated_user):
    def fake_create_chat_session(session, user_id, title):
        raise ValueError("대화 제목은 비워둘 수 없습니다.")

    monkeypatch.setattr(
        chats,
        "create_chat_session",
        fake_create_chat_session,
    )

    response = client.post(
        "/api/v1/chats",
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_create_chat_missing_title(monkeypatch, authenticated_user):
    def fake_create_chat_session(session, user_id, title):
        return SimpleNamespace(
            id=2,
            user_id=user_id,
            title=title,
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(
        chats,
        "create_chat_session",
        fake_create_chat_session,
    )

    response = client.post(
        "/api/v1/chats",
        json={},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "새 대화"