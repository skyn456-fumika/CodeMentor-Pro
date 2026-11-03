# Refresh Token 통합 테스트
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.repositories.refresh_token_repository import (
    find_refresh_token_by_hash,
)
from backend.app.services.refresh_token_service import (
    InvalidRefreshTokenError,
    get_valid_refresh_token,
    hash_refresh_token,
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)


def create_test_user(db_session: Session) -> User:
    user = User(
        email="refresh-test@example.com",
        password_hash="test-hash",
    )

    db_session.add(user)
    db_session.flush()

    return user

# 토큰 발급 및 해시 저장
def test_issue_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(
        session=db_session,
        user_id=user.id,
    )

    assert isinstance(raw_token, str)
    assert len(raw_token) > 40

    token_hash = hash_refresh_token(raw_token)

    saved_token = find_refresh_token_by_hash(
        session=db_session,
        token_hash=token_hash,
    )

    assert saved_token is not None
    assert saved_token.user_id == user.id
    assert saved_token.token_hash != raw_token
    assert saved_token.revoked_at is None

# 정상 토큰 조회
def test_valid_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(db_session, user.id)

    result = get_valid_refresh_token(
        session=db_session,
        raw_token=raw_token,
    )

    assert result is not None
    assert result.user_id == user.id

# 만료된 토큰 거부
def test_expired_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(db_session, user.id)

    saved_token = find_refresh_token_by_hash(
        db_session,
        hash_refresh_token(raw_token),
    )

    saved_token.expires_at = datetime.now(UTC) - timedelta(days=1)
    db_session.flush()

    result = get_valid_refresh_token(db_session, raw_token)

    assert result is None

# 폐기된 토큰 거부
def test_revoked_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(db_session, user.id)

    saved_token = find_refresh_token_by_hash(
        db_session,
        hash_refresh_token(raw_token),
    )

    saved_token.revoked_at = datetime.now(UTC)
    db_session.flush()

    result = get_valid_refresh_token(db_session, raw_token)

    assert result is None

# 존재하지 않는 토큰 거부
def test_unknown_refresh_token(db_session: Session):
    result = get_valid_refresh_token(
        session=db_session,
        raw_token="invalid-refresh-token",
    )

    assert result is None

# 정상 Rotation
def test_rotate_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    old_token = issue_refresh_token(
        db_session,
        user.id,
    )

    user_id, new_token = rotate_refresh_token(
        db_session,
        old_token,
    )

    assert user_id == user.id
    assert new_token != old_token

    # 기존 토큰은 더 이상 유효하지 않아야 함
    assert get_valid_refresh_token(
        db_session,
        old_token,
    ) is None

    # 새 토큰은 유효해야 함
    assert get_valid_refresh_token(
        db_session,
        new_token,
    ) is not None

# 기존 토큰의 재사용이 거부되는지
def test_reuse_rotated_token_is_rejected(db_session: Session):
    user = create_test_user(db_session)

    old_token = issue_refresh_token(
        db_session,
        user.id,
    )

    rotate_refresh_token(db_session, old_token)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(db_session, old_token)

# 실제 DB 토큰 폐기 검증
def test_revoke_refresh_token(db_session: Session):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(
        session=db_session,
        user_id=user.id,
    )

    # 발급 직후에는 유효
    assert get_valid_refresh_token(
        db_session,
        raw_token,
    ) is not None

    # 로그아웃 처리
    revoke_refresh_token(
        session=db_session,
        raw_token=raw_token,
    )

    # 폐기 후에는 사용 불가능
    assert get_valid_refresh_token(
        db_session,
        raw_token,
    ) is None

    saved_token = find_refresh_token_by_hash(
        db_session,
        hash_refresh_token(raw_token),
    )

    assert saved_token is not None
    assert saved_token.revoked_at is not None

# 멱등성을 검증
def test_revoke_refresh_token_is_idempotent(
    db_session: Session,
):
    user = create_test_user(db_session)

    raw_token = issue_refresh_token(
        db_session,
        user.id,
    )

    # 같은 토큰으로 두 번 로그아웃
    revoke_refresh_token(db_session, raw_token)

    saved_token = find_refresh_token_by_hash(
        db_session,
        hash_refresh_token(raw_token),
    )

    first_revoked_at = saved_token.revoked_at

    revoke_refresh_token(db_session, raw_token)

    # 폐기 시간이 변경되지 않아야 함
    assert saved_token.revoked_at == first_revoked_at

    # 존재하지 않는 토큰도 오류 없이 처리
    revoke_refresh_token(
        db_session,
        "unknown-refresh-token",
    )

    assert get_valid_refresh_token(
        db_session,
        raw_token,
    ) is None