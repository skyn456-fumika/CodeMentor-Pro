from uuid import uuid4

from backend.app.models.user import User
from backend.app.services.review_service import (
    create_review,
    get_review,
    get_reviews,
)


def make_user(db_session):
    user = User(
        # uuid4() : 여러 번 테스트를 실행해도 
        # 이메일 UNIQUE 제약조건에 걸리지 않도록 하기 위해서
        email=f"{uuid4().hex}@example.com",
        # password_hash에 넣은 문자열은 실제 로그인에 사용하지 않는 테스트 전용 값
        password_hash="test-only-password-hash",
    )

    db_session.add(user)
    db_session.flush()

    return user


def make_review(db_session, user_id):
    return create_review(
        session=db_session,
        source_code="print('hello')",
        analysis_type="RUFF",
        result="[]",
        user_id=user_id,
    )


def test_user_cannot_read_another_users_review(db_session):
    user_a = make_user(db_session)
    user_b = make_user(db_session)

    review_a = make_review(db_session, user_a.id)

    # 본인의 기록은 조회 가능
    own_review = get_review(
        session=db_session,
        review_id=review_a.id,
        user_id=user_a.id,
    )

    assert own_review is not None
    assert own_review.id == review_a.id

    # 다른 사용자의 기록은 조회 불가
    other_review = get_review(
        session=db_session,
        review_id=review_a.id,
        user_id=user_b.id,
    )

    assert other_review is None


def test_user_can_only_list_own_reviews(db_session):
    user_a = make_user(db_session)
    user_b = make_user(db_session)

    review_a1 = make_review(db_session, user_a.id)
    review_a2 = make_review(db_session, user_a.id)
    review_b = make_review(db_session, user_b.id)

    reviews, total = get_reviews(
        session=db_session,
        page=1,
        size=10,
        user_id=user_a.id,
    )

    review_ids = [review.id for review in reviews]

    assert total == 2
    assert review_ids == [review_a2.id, review_a1.id]
    assert review_b.id not in review_ids


def test_legacy_review_is_not_accessible(db_session):
    user = make_user(db_session)

    # 인증 도입 이전의 소유자 없는 기록
    legacy_review = make_review(db_session, None)

    result = get_review(
        session=db_session,
        review_id=legacy_review.id,
        user_id=user.id,
    )

    reviews, total = get_reviews(
        session=db_session,
        page=1,
        size=10,
        user_id=user.id,
    )

    assert result is None
    assert total == 0
    assert reviews == []