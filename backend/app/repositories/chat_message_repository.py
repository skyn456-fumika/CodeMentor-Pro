from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.chat_message import ChatMessage


def save_chat_message(
    session: Session,
    message: ChatMessage,
) -> ChatMessage:
    session.add(message)
    session.flush()

    return message


def find_chat_messages(
    session: Session,
    chat_id: int,
) -> list[ChatMessage]:
    return list(
        session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_id)
            .order_by(ChatMessage.id.asc())
        ).all()
    )