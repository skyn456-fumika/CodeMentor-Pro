import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    database_url = os.environ.get("TEST_DATABASE_URL")

    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL 환경변수가 필요합니다.")

    # 개발 DB에 테스트 데이터가 기록되는 것을 방지
    if make_url(database_url).database != "codementor_test":
        raise RuntimeError("테스트 전용 DB만 사용할 수 있습니다.")

    engine = create_engine(database_url, pool_pre_ping=True)

    with engine.connect() as connection:
        transaction = connection.begin()

        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as session:
            try:
                yield session
            finally:
                transaction.rollback()

    engine.dispose()
