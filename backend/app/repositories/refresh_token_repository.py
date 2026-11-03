from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.refresh_token import RefreshToken


# commit()을 하지 않고 flush()만 수행
# 토큰 발급과 다른 DB 작업을 하나의 트랜잭션으로 관리할 수 있음.
def save_refresh_token(
    session: Session,
    refresh_token: RefreshToken,
) -> RefreshToken:
    session.add(refresh_token)
    session.flush()
    return refresh_token


def find_refresh_token_by_hash(
    session: Session,
    token_hash: str,
) -> RefreshToken | None:
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash
    )
    return session.scalar(stmt)

# 잠금 조회
# 조회한 행에 배타적 잠금
# 동일한 토큰을 다른 트랜잭션에서 갱신하려 하면 앞선 트랜잭션이 끝날 때까지 기다리게 됨.
def find_refresh_token_by_hash_for_update(
    session: Session,
    token_hash: str,
) -> RefreshToken | None:
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    return session.scalar(stmt)