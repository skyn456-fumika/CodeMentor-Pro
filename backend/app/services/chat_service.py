from sqlalchemy.orm import Session

from backend.app.models.chat_session import ChatSession
from backend.app.repositories.chat_repository import save_chat_session


def create_chat_session(
    session: Session,
    user_id: int,
    title: str,
) -> ChatSession:
    title = title.strip()

    if not title:
        raise ValueError("대화 제목은 비워둘 수 없습니다.")

    chat_session = ChatSession(
        user_id=user_id,
        title=title,
    )

    try:
        save_chat_session(session, chat_session)

        session.commit()
        session.refresh(chat_session)

        return chat_session

    except Exception:
        session.rollback()
        raise

from backend.app.repositories.chat_repository import (
    find_chat_session_by_id,
    find_chat_sessions,
)


def get_chat_session(
    session: Session,
    chat_id: int,
    user_id: int,
) -> ChatSession | None:
    return find_chat_session_by_id(
        session=session,
        chat_id=chat_id,
        user_id=user_id,
    )


def get_chat_sessions(
    session: Session,
    user_id: int,
    page: int,
    size: int,
) -> tuple[list[ChatSession], int]:
    offset = (page - 1) * size

    return find_chat_sessions(
        session=session,
        user_id=user_id,
        offset=offset,
        limit=size,
    )