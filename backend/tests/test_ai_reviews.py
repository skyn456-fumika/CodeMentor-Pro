from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import reviews
from backend.app.core.dependencies import get_current_user
from backend.app.main import app
from backend.app.services.ai_service import AIServiceError


# Fixture는 테스트마다 다음과 같이 동작
# 1. 테스트 시작 전 로그인한 사용자 ID를 1로 설정
# 2 .테스트 요청에서 실제 JWT 검증 대신 가짜 사용자 반환
# 3. 테스트 종료 후 인증 설정 제거
# 주의 : Fixture를 conftest.py에 전역으로 추가하면 안 됨. 
# 기존 /me 미인증 테스트도 인증된 상태로 실행될 수 있기 때문
@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1)
    )

    yield

    # 기존 테스트에서 사용하는 backend.app.main의 FastAPI 애플리케이션
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)

# Mock 처리
def test_ai_review_success(monkeypatch):
    def fake_review(code):
        return "0으로 나누면 ZeroDivisionError가 발생합니다."

    def fake_save(**kwargs):
        return None

    monkeypatch.setattr(reviews, "review_code", fake_review)
    monkeypatch.setattr(reviews, "create_review", fake_save)

    response = client.post(
        "/api/v1/reviews/ai",
        json={"code": "print(10 / 0)"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "review": "0으로 나누면 ZeroDivisionError가 발생합니다."
    }


def test_ai_review_empty_code():
    response = client.post(
        "/api/v1/reviews/ai",
        json={"code": "   "},
    )

    assert response.status_code == 422


def test_ai_review_service_error(monkeypatch):
    def fake_review(code):
        raise AIServiceError("Gemini API failed")

    monkeypatch.setattr(reviews, "review_code", fake_review)

    response = client.post(
        "/api/v1/reviews/ai",
        json={"code": "print('hello')"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI 리뷰 서비스를 사용할 수 없습니다."
    }

# DB 저장 호출 검증 테스트
def test_ai_review_calls_save(monkeypatch):
    saved_data = {}

    def fake_review(code):
        return "AI 분석 결과입니다."

    def fake_save(**kwargs):
        saved_data.update(kwargs)

    monkeypatch.setattr(reviews, "review_code", fake_review)
    monkeypatch.setattr(reviews, "create_review", fake_save)

    response = client.post(
        "/api/v1/reviews/ai",
        json={"code": "print('hello')"},
    )

    assert response.status_code == 200
    
    assert saved_data["user_id"] == 1
    assert saved_data["analysis_type"] == "AI"
    assert saved_data["source_code"] == "print('hello')"
    assert saved_data["result"] == "AI 분석 결과입니다."

from sqlalchemy.exc import SQLAlchemyError


# DB 저장 실패 테스트
def test_ai_review_db_failure(monkeypatch):
    def fake_review(code):
        return "AI 분석 결과입니다."

    def fake_save(**kwargs):
        raise SQLAlchemyError("DB 연결 실패")

    monkeypatch.setattr(reviews, "review_code", fake_review)
    monkeypatch.setattr(reviews, "create_review", fake_save)

    response = client.post(
        "/api/v1/reviews/ai",
        json={"code": "print('hello')"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "분석 기록 저장에 실패했습니다."
    }
