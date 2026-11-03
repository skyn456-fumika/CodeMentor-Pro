from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.v1 import reviews
from backend.app.core.dependencies import get_current_user
from backend.app.main import app


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = (
        lambda: SimpleNamespace(id=1)
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)

# 상세 조회 테스트
def test_get_review_success(monkeypatch):
    fake_review = SimpleNamespace(
        id=3,
        source_code="print('hello')",
        analysis_type="AI",
        result="AI 리뷰 결과",
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        reviews,
        "get_review",
        lambda session, review_id, user_id: fake_review
    )

    response = client.get("/api/v1/reviews/3")

    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["analysis_type"] == "AI"
    assert response.json()["result"] == "AI 리뷰 결과"


def test_get_review_not_found(monkeypatch):
    monkeypatch.setattr(
        reviews,
        "get_review",
        lambda session, review_id, user_id: None,
    )

    response = client.get("/api/v1/reviews/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "분석 기록을 찾을 수 없습니다."
    )


def test_get_review_invalid_id():
    response = client.get("/api/v1/reviews/0")

    assert response.status_code == 422