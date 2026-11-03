# Router와 Service 호출 관계를 검증하는 Mock 기반 API 테스트
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import chats
from backend.app.core.dependencies import get_current_user
from backend.app.main import app
from backend.app.services.chat_message_service import ChatNotFoundError

client = TestClient(app)


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1)
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)


def fake_message(message_id, content):
    return SimpleNamespace(
        id=message_id,
        session_id=1,
        role="user",
        content=content,
        created_at=datetime.now(UTC),
    )


def test_create_message_success(monkeypatch, authenticated_user):
    saved_data = {}

    def fake_create(session, chat_id, user_id, content):
        saved_data.update({
            "chat_id": chat_id,
            "user_id": user_id,
            "content": content,
        })

        return fake_message(1, content)

    monkeypatch.setattr(chats, "create_user_message", fake_create)

    response = client.post(
        "/api/v1/chats/1/messages",
        json={"content": "Python 리스트와 튜플의 차이는?"},
    )

    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert saved_data["chat_id"] == 1
    assert saved_data["user_id"] == 1


def test_create_message_blank_content(authenticated_user):
    response = client.post(
        "/api/v1/chats/1/messages",
        json={"content": "   "},
    )

    assert response.status_code == 422


def test_create_message_without_authentication():
    response = client.post(
        "/api/v1/chats/1/messages",
        json={"content": "인증 없는 메시지"},
    )

    assert response.status_code == 401


def test_create_message_other_users_chat(
    monkeypatch,
    authenticated_user,
):
    def fake_create(session, chat_id, user_id, content):
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    monkeypatch.setattr(chats, "create_user_message", fake_create)

    response = client.post(
        "/api/v1/chats/999/messages",
        json={"content": "다른 사람의 대화"},
    )

    assert response.status_code == 404


def test_get_messages_success(monkeypatch, authenticated_user):
    monkeypatch.setattr(
        chats,
        "get_chat_messages",
        lambda session, chat_id, user_id: [
            fake_message(1, "첫 번째 질문"),
            fake_message(2, "두 번째 질문"),
        ],
    )

    response = client.get("/api/v1/chats/1/messages")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["content"] == "첫 번째 질문"
    assert response.json()[1]["content"] == "두 번째 질문"


def test_get_messages_other_users_chat(
    monkeypatch,
    authenticated_user,
):
    def fake_get(session, chat_id, user_id):
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    monkeypatch.setattr(chats, "get_chat_messages", fake_get)

    response = client.get("/api/v1/chats/999/messages")

    assert response.status_code == 404