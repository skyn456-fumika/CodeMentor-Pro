from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.user import User


def find_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(
        select(User).where(User.email == email)
    )


def save_user(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user

# 사용자 ID 조회
def find_user_by_id(
    session: Session,
    user_id: int,
) -> User | None:
    return session.get(User, user_id)