import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


# 기존 DB 트랜잭션 격리 Fixture 재사용
@pytest.fixture
def db_session():
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://codementor:devpassword"
        "@127.0.0.1:5433/codementor_test",
    )

    # 개발 DB에 테스트가 기록되는 사고 방지
    if not url.split("?")[0].endswith("/codementor_test"):
        raise RuntimeError("테스트 전용 DB만 사용할 수 있습니다.")

    engine = create_engine(url, pool_pre_ping=True)

    # 테스트마다 별도 트랜잭션 시작
    with engine.connect() as connection:
        transaction = connection.begin()

        with Session(
            bind=connection,
            # 서비스 내부에서 session.commit()을 호출하더라도 
            # 테스트의 바깥 트랜잭션은 유지하기 위해서
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

        # 테스트 종료 후 모든 변경 취소
        transaction.rollback()

    engine.dispose()