import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models.refresh_token import RefreshToken
from backend.app.repositories.refresh_token_repository import (
    find_refresh_token_by_hash,
    find_refresh_token_by_hash_for_update,
    save_refresh_token,
)

REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_refresh_token(
    session: Session,
    user_id: int,
) -> str:
    # 충분한 무작위성을 가진 토큰을 생성
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_token)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        # PostgreSQL에서는 일반적으로 시간대 정보를 가진 TIMESTAMP WITH TIME ZONE으로 저장
        expires_at=(
            datetime.now(UTC)
            + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        ),
    )

    save_refresh_token(session, refresh_token)

    return raw_token


def get_valid_refresh_token(
    session: Session,
    raw_token: str,
) -> RefreshToken | None:
    token_hash = hash_refresh_token(raw_token)

    refresh_token = find_refresh_token_by_hash(
        session=session,
        token_hash=token_hash,
    )

    if refresh_token is None:
        return None

    if refresh_token.revoked_at is not None:
        return None

    if refresh_token.expires_at <= datetime.now(UTC):
        return None

    return refresh_token

class InvalidRefreshTokenError(Exception):
    pass

# commit()을 하지 않음
# 기존 토큰 폐기와 새 토큰 발급을 호출하는 쪽에서 하나의 트랜잭션으로 커밋하도록 설계
def rotate_refresh_token(
    session: Session,
    raw_token: str,
) -> tuple[int, str]:
    token_hash = hash_refresh_token(raw_token)

    # 동일 토큰에 대한 동시 갱신을 직렬화
    refresh_token = find_refresh_token_by_hash_for_update(
        session=session,
        token_hash=token_hash,
    )

    if refresh_token is None:
        raise InvalidRefreshTokenError(
            "Refresh Token을 찾을 수 없습니다."
        )

    now = datetime.now(UTC)

    # 락을 획득한 후 유효성 검사
    if (
        refresh_token.revoked_at is not None
        or refresh_token.expires_at <= now
    ):
        raise InvalidRefreshTokenError(
            "유효하지 않거나 만료된 Refresh Token입니다."
        )

    user_id = refresh_token.user_id

    # 기존 토큰 폐기
    refresh_token.revoked_at = now
    session.flush()

    # 새 토큰 발급
    new_raw_token = issue_refresh_token(
        session=session,
        user_id=user_id,
    )

    return user_id, new_raw_token

# 토큰 폐기
# 존재하지 않거나 이미 폐기된 토큰을 전달해도 오류를 발생시키지 않음.
# 멱등성(Idempotency) : 같은 로그아웃 요청을 여러 번 보내도 최종 상태가 같다는 의미
def revoke_refresh_token(
    session: Session,
    raw_token: str,
) -> None:
    token_hash = hash_refresh_token(raw_token)

    refresh_token = find_refresh_token_by_hash_for_update(
        session=session,
        token_hash=token_hash,
    )

    if refresh_token is None:
        return

    if refresh_token.revoked_at is not None:
        return

    refresh_token.revoked_at = datetime.now(UTC)
    session.flush()