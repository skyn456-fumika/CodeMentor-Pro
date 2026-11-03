import pytest

from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.services.review_service import (
    create_review,
    get_review,
)


def test_create_review(db_session):
    review = create_review(
        session=db_session,
        source_code="print('hello')",
        analysis_type="RUFF",
        result="문제 없음",
    )

    assert review.id is not None
    assert review.analysis_type == "RUFF"


def test_get_review(db_session):
    user = User(
        email="review-test@example.com",
        password_hash=hash_password("TestPassword123!"),
    )

    db_session.add(user)
    db_session.flush()

    saved = create_review(
        session=db_session,
        source_code="print('test')",
        analysis_type="AI",
        result="정상 코드입니다.",
        user_id=user.id,
    )

    review = get_review(
        session=db_session,
        review_id=saved.id,
        user_id=user.id,
    )

    assert review is not None
    assert review.id == saved.id
    assert review.result == "정상 코드입니다."


def test_invalid_analysis_type(db_session):
    with pytest.raises(ValueError):
        create_review(
            session=db_session,
            source_code="print('test')",
            analysis_type="INVALID",
            result="오류",
        )


def test_rollback_on_db_error(db_session, monkeypatch):
    from backend.app.services import review_service

    def fake_save(session, review):
        session.add(review)
        session.flush()
        raise RuntimeError("DB 저장 실패 가정")

    monkeypatch.setattr(
        review_service,
        "save_review",
        fake_save,
    )

    with pytest.raises(RuntimeError):
        create_review(
            session=db_session,
            source_code="print('rollback-test')",
            analysis_type="RUFF",
            result="테스트",
        )

    from sqlalchemy import select

    from backend.app.models.review import Review

    saved = db_session.scalars(
        select(Review).where(
            Review.source_code == "print('rollback-test')"
        )
    ).all()

    assert saved == []