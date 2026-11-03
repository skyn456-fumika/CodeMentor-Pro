from sqlalchemy.orm import Session

from backend.app.models.review import Review
from backend.app.repositories.review_repository import (
    find_review_by_id,
    find_reviews,
    get_review_stats,
    save_review,
)


def create_review(
    session: Session,
    source_code: str,
    analysis_type: str,
    result: str,
    user_id: int | None = None,
) -> Review:
    if not source_code.strip():
        raise ValueError("코드가 비어 있습니다.")

    if analysis_type not in {"RUFF", "AI"}:
        raise ValueError("지원하지 않는 분석 유형입니다.")

    review = Review(
        source_code=source_code,
        analysis_type=analysis_type,
        result=result,
        user_id=user_id,
    )

    try:
        save_review(session, review)
        session.commit()
        session.refresh(review)
        return review

    except Exception:
        session.rollback()
        raise

def get_review(
    session: Session,
    review_id: int,
    user_id: int,
) -> Review | None:
    return find_review_by_id(
        session=session,
        review_id=review_id,
        user_id=user_id,
    )

# 목록 조회
def get_reviews(
    session: Session,
    page: int,
    size: int,
    user_id: int,
) -> tuple[list[Review], int]:
    offset = (page - 1) * size

    return find_reviews(
        session=session,
        offset=offset,
        limit=size,
        user_id=user_id,
    )

def get_user_review_stats(session: Session, user_id: int) -> dict:
    return get_review_stats(session, user_id)