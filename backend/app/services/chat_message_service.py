from sqlalchemy.orm import Session

from backend.app.models.chat_message import ChatMessage
from backend.app.repositories.chat_message_repository import (
    find_chat_messages,
    save_chat_message,
)
from backend.app.repositories.chat_repository import (
    find_chat_session_by_id,
)


class ChatNotFoundError(Exception):
    pass


def create_user_message(
    session: Session,
    chat_id: int,
    user_id: int,
    content: str,
) -> ChatMessage:
    # chat_id와 user_id를 함께 조건으로 조회하도록 만들었기 때문에, 
    # 다른 사용자의 대화방은 존재하지 않는 것처럼 처리할 수 있음.
    chat = find_chat_session_by_id(
        session=session,
        chat_id=chat_id,
        user_id=user_id,
    )

    if chat is None:
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    content = content.strip()

    if not content:
        raise ValueError("메시지 내용은 비워둘 수 없습니다.")

    message = ChatMessage(
        session_id=chat_id,
        role="user",
        content=content,
    )

    try:
        save_chat_message(session, message)
        session.commit()
        session.refresh(message)

        return message

    except Exception:
        session.rollback()
        raise


def get_chat_messages(
    session: Session,
    chat_id: int,
    user_id: int,
) -> list[ChatMessage]:
    chat = find_chat_session_by_id(
        session=session,
        chat_id=chat_id,
        user_id=user_id,
    )

    if chat is None:
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    return find_chat_messages(
        session=session,
        chat_id=chat_id,
    )

# 사용자 질문과 AI 답변을 함께 저장하는 Service
from backend.app.services.ai_chat_service import generate_chat_response


# 두 메시지를 하나의 트랜잭션으로 저장
# 두 번째 메시지 저장에 실패하면 첫 번째 사용자 질문도 함께 롤백되도록 구성
# Gemini 호출에 실패하면 현재 구현에서는 질문과 답변 모두 저장되지 않음
# 일관된 대화 기록을 유지하기 위한 초기 설계
def ask_chat(
    session: Session,
    chat_id: int,
    user_id: int,
    question: str,
) -> ChatMessage:
    question = question.strip()

    if not question:
        raise ValueError("질문을 입력해 주세요.")

    # 본인 대화방인지 확인
    chat = find_chat_session_by_id(
        session=session,
        chat_id=chat_id,
        user_id=user_id,
    )

    if chat is None:
        raise ChatNotFoundError("대화 세션을 찾을 수 없습니다.")

    # 이전 대화 불러오기
    previous_messages = find_chat_messages(
        session=session,
        chat_id=chat_id,
    )

    history = [
        (message.role, message.content)
        for message in previous_messages
    ]

    # Gemini 호출
    answer = generate_chat_response(
        history=history,
        question=question,
    )

    # Gemini가 성공했을 때 질문과 답변을 함께 저장
    user_message = ChatMessage(
        session_id=chat_id,
        role="user",
        content=question,
    )

    assistant_message = ChatMessage(
        session_id=chat_id,
        role="assistant",
        content=answer,
    )

    try:
        save_chat_message(session, user_message)
        save_chat_message(session, assistant_message)

        session.commit()
        session.refresh(assistant_message)

        return assistant_message

    except Exception:
        session.rollback()
        raise