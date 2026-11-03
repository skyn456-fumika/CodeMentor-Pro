from backend.app.db.database import SessionLocal
from backend.app.services.review_service import (
    create_review,
    get_review,
)


def main():
    with SessionLocal() as session:
        saved = create_review(
            session=session,
            source_code="print('Hello CodeMentor')",
            analysis_type="RUFF",
            result="분석 결과: 문제 없음",
        )

        review_id = saved.id
        print(f"저장 완료! ID: {review_id}")

    # 새로운 Session에서도 조회되는지 확인
    with SessionLocal() as session:
        found = get_review(session, review_id)

        assert found is not None
        assert found.analysis_type == "RUFF"
        assert found.result == "분석 결과: 문제 없음"

        print(f"조회 완료! ID: {found.id}")
        print(f"코드: {found.source_code}")
        print(f"결과: {found.result}")


if __name__ == "__main__":
    main()
