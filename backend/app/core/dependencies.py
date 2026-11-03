# 인증 의존성
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.security import (
    InvalidTokenError,
    decode_access_token,
)
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repository import find_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


# FastAPI의 Depends로 재사용할 수 있는 인증 의존성
def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않거나 만료된 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = find_user_by_id(session, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user