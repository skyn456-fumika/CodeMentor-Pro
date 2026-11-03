from sqlalchemy.orm import Session

from backend.app.models.chat_session import ChatSession


def save_chat_session(
    session: Session,
    chat_session: ChatSession,
) -> ChatSession:
    session.add(chat_session)
    session.flush()

    return chat_session

from sqlalchemy import func, select


def find_chat_session_by_id(
    session: Session,
    chat_id: int,
    user_id: int,
) -> ChatSession | None:
    return session.scalar(
        select(ChatSession).where(
            ChatSession.id == chat_id,
            ChatSession.user_id == user_id,
        )
    )


def find_chat_sessions(
    session: Session,
    user_id: int,
    offset: int,
    limit: int,
) -> tuple[list[ChatSession], int]:
    condition = ChatSession.user_id == user_id

    total = session.scalar(
        select(func.count())
        .select_from(ChatSession)
        .where(condition)
    ) or 0

    chats = session.scalars(
        select(ChatSession)
        .where(condition)
        .order_by(ChatSession.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return list(chats), total