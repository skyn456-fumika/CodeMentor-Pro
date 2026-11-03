from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.models.review import Review


def save_review(session: Session, review: Review) -> Review:
    session.add(review)
    # DB에 INSERT를 실행해 생성된 ID를 확인할 수 있게 하지만, 
    # 아직 트랜잭션을 확정하는 commit()은 아니야
    session.flush()
    return review

# 사용자별 분석 기록 조회 제한
def find_review_by_id(
    session: Session,
    review_id: int,
    user_id: int,
) -> Review | None:
    return session.scalar(
        # 사용자 ID를 필터링하는 SQLAlchemy 방식
        select(Review).where(
            Review.id == review_id,
            Review.user_id == user_id,
        )
    )

# 목록 조회
# id 내림차순으로 정렬하므로 최근 생성된 기록부터 조회
def find_reviews(
    session: Session,
    offset: int,
    limit: int,
    user_id: int,
) -> tuple[list[Review], int]:
    condition = Review.user_id == user_id

    total = session.scalar(
        select(func.count())
        .select_from(Review)
        .where(condition)
    ) or 0

    reviews = session.scalars(
        select(Review)
        .where(condition)
        .order_by(Review.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return list(reviews), total

# 통계 조회
# Review는 기존에 사용하던 SQLAlchemy 모델을 그대로 활용
def get_review_stats(session: Session, user_id: int) -> dict:
    stmt = (
        select(
            # SQLAlchemy 집계 방식
            func.count(Review.id).label("total"),
            func.count(
                case(
                    (Review.analysis_type == "RUFF", 1)
                )
            ).label("ruff_count"),
            func.count(
                case(
                    (Review.analysis_type == "AI", 1)
                )
            ).label("ai_count"),
        )
        .where(Review.user_id == user_id)
    )

    result = session.execute(stmt).one()

    return {
        "total": result.total,
        "ruff_count": result.ruff_count,
        "ai_count": result.ai_count,
    }