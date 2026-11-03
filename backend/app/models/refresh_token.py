# Refresh Token
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


# Refresh Token 원본을 DB에 저장하지 않는다
# secrets.token_urlsafe()로 충분히 긴 무작위 토큰을 생성하고, SHA-256 해시만 저장
# 토큰 원본을 획득하지 못하면 DB에 있는 해시만으로 인증할 수 없도록 설계
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # 토큰 레코드 식별자
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 토큰 소유자
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Refresh Token의 SHA-256 해시값
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    # 만료 시각
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # 폐기 시각, 사용 가능한 토큰은 NULL
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 발급 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )