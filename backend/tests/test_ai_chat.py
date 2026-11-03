# AI 대화 이력 및 저장 자동 테스트
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.app.models.chat_message import ChatMessage
from backend.app.models.user import User
from backend.app.services import chat_message_service
from backend.app.services.ai_service import AIServiceError
from backend.app.services.chat_message_service import (
    ChatNotFoundError,
    ask_chat,
)
from backend.app.services.chat_service import create_chat_session


def make_user(db_session):
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-only-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    return user


def make_chat(db_session, user_id):
    return create_chat_session(
        session=db_session,
        user_id=user_id,
        title="AI 대화 테스트",
    )


def get_saved_messages(db_session, chat_id):
    return list(
        db_session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_id)
            .order_by(ChatMessage.id.asc())
        ).all()
    )

# 질문과 AI 답변이 함께 저장되는지
def test_ask_chat_saves_question_and_answer(db_session, monkeypatch):
    user = make_user(db_session)
    chat = make_chat(db_session, user.id)

    monkeypatch.setattr(
        chat_message_service,
        "generate_chat_response",
        lambda history, question: "튜플은 변경할 수 없습니다.",
    )

    answer = ask_chat(
        session=db_session,
        chat_id=chat.id,
        user_id=user.id,
        question="튜플의 특징은?",
    )

    messages = get_saved_messages(db_session, chat.id)

    assert answer.role == "assistant"
    assert len(messages) == 2
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[0].content == "튜플의 특징은?"
    assert messages[1].content == "튜플은 변경할 수 없습니다."

# 후속 질문에서 이전 대화가 전달되는지
def test_ask_chat_passes_previous_history(db_session, monkeypatch):
    user = make_user(db_session)
    chat = make_chat(db_session, user.id)

    received = []

    def fake_generate(history, question):
        received.append({
            "history": list(history),
            "question": question,
        })

        return f"{question}에 대한 답변"

    monkeypatch.setattr(
        chat_message_service,
        "generate_chat_response",
        fake_generate,
    )

    ask_chat(db_session, chat.id, user.id, "첫 번째 질문")
    ask_chat(db_session, chat.id, user.id, "두 번째 질문")

    assert received[0]["history"] == []
    assert received[0]["question"] == "첫 번째 질문"

    assert received[1]["history"] == [
        ("user", "첫 번째 질문"),
        ("assistant", "첫 번째 질문에 대한 답변"),
    ]
    assert received[1]["question"] == "두 번째 질문"

    assert len(get_saved_messages(db_session, chat.id)) == 4

# 다른 사용자의 대화방에 질문할 수 없는지
def test_ask_chat_blocks_other_user(db_session, monkeypatch):
    owner = make_user(db_session)
    other = make_user(db_session)
    chat = make_chat(db_session, owner.id)

    def should_not_call(history, question):
        pytest.fail("다른 사용자 대화방에서 Gemini가 호출됨")

    monkeypatch.setattr(
        chat_message_service,
        "generate_chat_response",
        should_not_call,
    )

    with pytest.raises(ChatNotFoundError):
        ask_chat(
            session=db_session,
            chat_id=chat.id,
            user_id=other.id,
            question="접근 시도",
        )

    assert get_saved_messages(db_session, chat.id) == []

# Gemini 호출 실패 시 메시지가 저장되지 않는지
def test_ask_chat_ai_failure_does_not_save(db_session, monkeypatch):
    user = make_user(db_session)
    chat = make_chat(db_session, user.id)

    def fake_generate(history, question):
        raise AIServiceError("Gemini 요청 실패")

    monkeypatch.setattr(
        chat_message_service,
        "generate_chat_response",
        fake_generate,
    )

    with pytest.raises(AIServiceError):
        ask_chat(
            session=db_session,
            chat_id=chat.id,
            user_id=user.id,
            question="실패 테스트",
        )

    assert get_saved_messages(db_session, chat.id) == []