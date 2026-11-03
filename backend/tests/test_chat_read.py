# 대화 세션 조회 자동 테스트
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


def fake_chat(chat_id):
    return SimpleNamespace(
        id=chat_id,
        user_id=1,
        title=f"테스트 대화 {chat_id}",
        created_at=datetime.now(UTC),
    )


def test_chat_list_success(monkeypatch, authenticated_user):
    def fake_get_chat_sessions(session, user_id, page, size):
        assert user_id == 1
        assert page == 1
        assert size == 2

        return [fake_chat(3), fake_chat(2)], 3

    monkeypatch.setattr(
        chats,
        "get_chat_sessions",
        fake_get_chat_sessions,
    )

    response = client.get("/api/v1/chats?page=1&size=2")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2
    assert [item["id"] for item in data["items"]] == [3, 2]


def test_chat_list_without_authentication():
    response = client.get("/api/v1/chats")

    assert response.status_code == 401


def test_chat_list_invalid_page(authenticated_user):
    response = client.get("/api/v1/chats?page=0")

    assert response.status_code == 422


def test_chat_detail_success(monkeypatch, authenticated_user):
    def fake_get_chat_session(session, chat_id, user_id):
        assert chat_id == 3
        assert user_id == 1

        return fake_chat(3)

    monkeypatch.setattr(
        chats,
        "get_chat_session",
        fake_get_chat_session,
    )

    response = client.get("/api/v1/chats/3")

    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["user_id"] == 1


def test_chat_detail_not_found(monkeypatch, authenticated_user):
    monkeypatch.setattr(
        chats,
        "get_chat_session",
        lambda session, chat_id, user_id: None,
    )

    response = client.get("/api/v1/chats/999999")

    assert response.status_code == 404


def test_chat_detail_without_authentication():
    response = client.get("/api/v1/chats/3")

    assert response.status_code == 401