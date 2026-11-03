# 질문·답변 저장 실패 시 롤백 테스트
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.app.models.chat_message import ChatMessage
from backend.app.models.user import User
from backend.app.services import chat_message_service
from backend.app.services.chat_message_service import ask_chat
from backend.app.services.chat_service import create_chat_session


# AI 답변 저장 중 오류가 발생해도 사용자 질문만 남는 상황을 막는 것
# db_session fixture가 기존처럼 테스트 데이터를 외부 트랜잭션으로 격리하고, 
# join_transaction_mode="create_savepoint"를 사용하는 구성을 전제로 함
def test_ask_chat_rollback_when_second_save_fails(
    db_session,
    monkeypatch,
):
    # 테스트 사용자 생성
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-only-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    # 테스트 대화방 생성
    chat = create_chat_session(
        session=db_session,
        user_id=user.id,
        title="트랜잭션 롤백 테스트",
    )

    # Gemini는 실제 호출하지 않음
    monkeypatch.setattr(
        chat_message_service,
        "generate_chat_response",
        lambda history, question: "AI 테스트 답변",
    )

    original_save = chat_message_service.save_chat_message
    save_count = 0

    def fake_save(session, message):
        nonlocal save_count

        save_count += 1

        # 실제 INSERT를 실행
        result = original_save(session, message)

        # 두 번째 INSERT까지 성공한 후 장애 발생
        if save_count == 2:
            raise RuntimeError("AI 답변 저장 후 오류 발생")

        return result

    monkeypatch.setattr(
        chat_message_service,
        "save_chat_message",
        fake_save,
    )

    # 저장 과정에서 예외가 발생해야 함
    with pytest.raises(
        RuntimeError,
        match="AI 답변 저장 후 오류 발생",
    ):
        ask_chat(
            session=db_session,
            chat_id=chat.id,
            user_id=user.id,
            question="트랜잭션 테스트 질문",
        )

    assert save_count == 2

    # 예외 이후 DB 조회
    messages = list(
        db_session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat.id)
        ).all()
    )

    # 질문과 답변이 모두 롤백됐는지 검증
    assert messages == []