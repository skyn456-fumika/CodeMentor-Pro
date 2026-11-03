from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    # 분석 기록 식별자 (PK)
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 사용자가 입력한 Python 코드
    source_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # RUFF 또는 AI
    analysis_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # 분석 결과(학습용으로 result를 문자열로 저장)
    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 분석 기록 생성 시각 
    # default는 Python에서 INSERT할 때 적용되는 기본값
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # relationship()는 SQLAlchemy 객체 간의 관계를 나타내고, 
    # ForeignKey()는 실제 DB의 외래 키 제약조건을 정의함.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    user = relationship("User", back_populates="reviews")