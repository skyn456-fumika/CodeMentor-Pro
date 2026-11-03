from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.repositories.user_repository import (
    find_user_by_email,
    save_user,
)


class DuplicateEmailError(Exception):
    pass


def register_user(
    session: Session,
    email: str,
    password: str,
) -> User:
    email = email.strip().lower()

    if find_user_by_email(session, email) is not None:
        raise DuplicateEmailError("이미 사용 중인 이메일입니다.")

    user = User(
        email=email,
        password_hash=hash_password(password),
    )

    try:
        save_user(session, user)
        session.commit()
        session.refresh(user)
        return user

    except IntegrityError as exc:
        session.rollback()
        raise DuplicateEmailError(
            "이미 사용 중인 이메일입니다."
        ) from exc

    except Exception:
        session.rollback()
        raise


from backend.app.core.security import (
    create_access_token,
    verify_password,
)


class InvalidCredentialsError(Exception):
    pass

# 로그인 실패 시 사용자 존재 여부를 구분하지 않고 동일한 오류 메시지를 반환
def login_user(
    session: Session,
    email: str,
    password: str,
) -> str:
    email = email.strip().lower()

    user = find_user_by_email(session, email)

    if user is None or not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsError(
            "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    return create_access_token(user.id)
