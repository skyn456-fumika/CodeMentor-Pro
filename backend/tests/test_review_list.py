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


def fake_review(review_id):
    return SimpleNamespace(
        id=review_id,
        source_code="print('hello')",
        analysis_type="RUFF",
        result="[]",
        created_at=datetime.now(UTC),
    )


def test_get_review_list(monkeypatch):
    def fake_get_reviews(session, page, size, user_id):
        assert user_id == 1

        return [
            fake_review(5),
            fake_review(4),
        ], 2

    monkeypatch.setattr(
        reviews,
        "get_reviews",
        fake_get_reviews,
    )

    response = client.get(
        "/api/v1/reviews?page=1&size=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 5
    assert data["items"][1]["id"] == 4


def test_get_review_list_invalid_page():
    response = client.get("/api/v1/reviews?page=0")

    assert response.status_code == 422


def test_get_review_list_invalid_size():
    response = client.get("/api/v1/reviews?size=101")

    assert response.status_code == 422