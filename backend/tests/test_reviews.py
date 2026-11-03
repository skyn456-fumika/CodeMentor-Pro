from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import reviews
from backend.app.core.dependencies import get_current_user
from backend.app.main import app


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

# 실제 DB에 의존하게 만들지 않도록 create_review()를 Mock 처리
def test_analyze_with_issues(monkeypatch):
    monkeypatch.setattr(
        reviews,
        "create_review",
        lambda **kwargs: None,
    )
        
    response = client.post(
        "/api/v1/reviews/analyze",
        json={"code": "import os\n\nprint(message)\n"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == len(data["issues"])
    assert {issue["code"] for issue in data["issues"]} >= {
        "F401",
        "F821",
    }


def test_analyze_valid_code(monkeypatch):
    monkeypatch.setattr(
        reviews,
        "create_review",
        lambda **kwargs: None,
    )

    response = client.post(
        "/api/v1/reviews/analyze",
        json={"code": "print('Hello World')\n"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "issues": [],
    }


def test_analyze_empty_code():
    response = client.post(
        "/api/v1/reviews/analyze",
        json={"code": "   "},
    )

    assert response.status_code == 422


def test_analyze_missing_code():
    response = client.post(
        "/api/v1/reviews/analyze",
        json={},
    )

    assert response.status_code == 422
