# 사용자별 통계 격리 테스트
from sqlalchemy.orm import Session

from backend.app.models.review import Review
from backend.app.models.user import User
from backend.app.repositories.review_repository import (
    get_review_stats,
)


def test_review_stats_are_isolated_by_user(
    db_session: Session,
):
    # 테스트 사용자 생성
    user1 = User(
        email="stats-user1@example.com",
        password_hash="test-hash",
    )
    user2 = User(
        email="stats-user2@example.com",
        password_hash="test-hash",
    )

    db_session.add_all([user1, user2])
    db_session.flush()

    # 사용자별 분석 기록 생성
    reviews = [
        Review(
            user_id=user1.id,
            source_code="print(1)",
            analysis_type="RUFF",
            result="[]",
        ),
        Review(
            user_id=user1.id,
            source_code="print(2)",
            analysis_type="RUFF",
            result="[]",
        ),
        Review(
            user_id=user1.id,
            source_code="print(3)",
            analysis_type="AI",
            result="AI review",
        ),
        Review(
            user_id=user2.id,
            source_code="print(4)",
            analysis_type="AI",
            result="Other user review",
        ),
    ]

    db_session.add_all(reviews)
    db_session.flush()

    # 사용자 1 통계
    stats1 = get_review_stats(
        session=db_session,
        user_id=user1.id,
    )

    assert stats1["total"] == 3
    assert stats1["ruff_count"] == 2
    assert stats1["ai_count"] == 1

    # 사용자 2 통계
    stats2 = get_review_stats(
        session=db_session,
        user_id=user2.id,
    )

    assert stats2["total"] == 1
    assert stats2["ruff_count"] == 0
    assert stats2["ai_count"] == 1

# 기록이 없는 사용자도 테스트
def test_review_stats_when_no_reviews(
    db_session: Session,
):
    user = User(
        email="stats-empty@example.com",
        password_hash="test-hash",
    )

    db_session.add(user)
    db_session.flush()

    stats = get_review_stats(
        session=db_session,
        user_id=user.id,
    )

    assert stats == {
        "total": 0,
        "ruff_count": 0,
        "ai_count": 0,
    }