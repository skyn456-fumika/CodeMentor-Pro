# 동시성 테스트
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User
from backend.app.services.refresh_token_service import (
    InvalidRefreshTokenError,
    get_valid_refresh_token,
    issue_refresh_token,
    rotate_refresh_token,
)


def test_concurrent_refresh_token_rotation():
    database_url = os.environ["TEST_DATABASE_URL"]

    # 개발 DB를 실수로 사용하는 상황 방지
    assert make_url(database_url).database == "codementor_test"

    engine = create_engine(
        database_url,
        connect_args={
            "options": "-c lock_timeout=5000", # 테스트가 DB 잠금 때문에 무한정 대기하지 않도록 설정한 값
        },
    )

    session_factory = sessionmaker(bind=engine)
    user_id = None

    try:
        # 1. 테스트 데이터 생성 및 커밋
        with session_factory.begin() as session:
            user = User(
                email=f"concurrent-{uuid.uuid4().hex}@example.com",
                password_hash="test-hash",
            )
            session.add(user)
            session.flush()

            user_id = user.id
            old_token = issue_refresh_token(session, user_id)

        # 2. 독립적인 DB 세션에서 동시 갱신
        # 이것만으로 실제 DB 잠금 경합이 반드시 발생한다고 보장하지는 않음
        barrier = Barrier(2)

        def worker():
            with session_factory() as session:
                barrier.wait(timeout=10)

                try:
                    result = rotate_refresh_token(session, old_token)
                    session.commit()
                    return ("success", result[1])

                except InvalidRefreshTokenError:
                    session.rollback()
                    return ("rejected", None)

                except Exception:
                    session.rollback()
                    raise

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(worker)
                for _ in range(2)
            ]

            results = [
                future.result(timeout=15)
                for future in futures
            ]

        # 3. 결과 검증
        successes = [
            token for status, token in results
            if status == "success"
        ]
        rejected = sum(
            1 for status, _ in results
            if status == "rejected"
        )

        assert len(successes) == 1
        assert rejected == 1

        # 4. 최종 DB 상태 검증
        with session_factory() as session:
            assert get_valid_refresh_token(
                session, old_token
            ) is None

            assert get_valid_refresh_token(
                session, successes[0]
            ) is not None

            tokens = session.scalars(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id
                )
            ).all()

            active_tokens = [
                token for token in tokens
                if token.revoked_at is None
            ]

            assert len(tokens) == 2
            assert len(active_tokens) == 1

    finally:
        # 테스트 데이터 정리
        if user_id is not None:
            with session_factory.begin() as session:
                session.execute(
                    delete(RefreshToken).where(
                        RefreshToken.user_id == user_id
                    )
                )
                session.execute(
                    delete(User).where(User.id == user_id)
                )

        engine.dispose()