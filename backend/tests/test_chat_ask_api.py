# /ask API 안정성 테스트
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import chats
from backend.app.core.dependencies import get_current_user
from backend.app.main import app
from backend.app.services.ai_service import AIServiceError
from backend.app.services.chat_message_service import ChatNotFoundError

client = TestClient(app)


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1)
    )

    yield

    app.dependency_overrides.pop(get_current_user, None)

# 정상 질문 및 AI 응답(201)
def test_ask_success(monkeypatch, authenticated_user):
    received = {}

    def fake_ask(session, chat_id, user_id, question):
        received.update({
            "chat_id": chat_id,
            "user_id": user_id,
            "question": question,
        })

        return SimpleNamespace(
            id=10,
            session_id=chat_id,
            role="assistant",
            content="리스트는 변경 가능하고 튜플은 변경할 수 없습니다.",
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(chats, "ask_chat", fake_ask)

    response = client.post(
        "/api/v1/chats/1/ask",
        json={"content": "리스트와 튜플의 차이는?"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["role"] == "assistant"
    assert data["session_id"] == 1
    assert received["user_id"] == 1
    assert received["question"] == "리스트와 튜플의 차이는?"

# JWT 없이 요청(401)
def test_ask_without_authentication():
    response = client.post(
        "/api/v1/chats/1/ask",
        json={"content": "인증 없는 질문"},
    )

    assert response.status_code == 401

# 다른 사용자의 대화방(404)
def test_ask_other_users_chat(monkeypatch, authenticated_user):
    def fake_ask(session, chat_id, user_id, question):
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    monkeypatch.setattr(chats, "ask_chat", fake_ask)

    response = client.post(
        "/api/v1/chats/999/ask",
        json={"content": "다른 사람의 대화방"},
    )

    assert response.status_code == 404

# 공백 질문(422)
def test_ask_blank_question(authenticated_user):
    response = client.post(
        "/api/v1/chats/1/ask",
        json={"content": "   "},
    )

    assert response.status_code == 422

# Gemini 서비스 장애(503)
def test_ask_ai_service_error(monkeypatch, authenticated_user):
    def fake_ask(session, chat_id, user_id, question):
        raise AIServiceError("Gemini 요청 실패")

    monkeypatch.setattr(chats, "ask_chat", fake_ask)

    response = client.post(
        "/api/v1/chats/1/ask",
        json={"content": "Python 예외 처리를 설명해 줘."},
    )

    assert response.status_code == 503