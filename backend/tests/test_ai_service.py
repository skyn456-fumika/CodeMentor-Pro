
from types import SimpleNamespace

import pytest

from backend.app.services import ai_service


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return self.response


class FakeClient:
    def __init__(self, models):
        self.models = models

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_ai_review_success(monkeypatch):
    models = FakeModels(
        response=SimpleNamespace(
            text="코드에 개선할 부분이 있습니다."
        )
    )

    monkeypatch.setattr(
        ai_service,
        "create_gemini_client",
        lambda: FakeClient(models),
    )

    result = ai_service.review_code("print('hello')")

    assert result == "코드에 개선할 부분이 있습니다."
    assert models.calls[0]["model"]


def test_ai_review_empty_code():
    with pytest.raises(ValueError):
        ai_service.review_code("   ")


def test_ai_review_api_failure(monkeypatch):
    models = FakeModels(
        error=RuntimeError("API failed")
    )

    monkeypatch.setattr(
        ai_service,
        "create_gemini_client",
        lambda: FakeClient(models),
    )

    with pytest.raises(
        ai_service.AIServiceError,
        match="Gemini API 요청에 실패",
    ):
        ai_service.review_code("print('hello')")


def test_ai_review_empty_response(monkeypatch):
    models = FakeModels(
        response=SimpleNamespace(text="   ")
    )

    monkeypatch.setattr(
        ai_service,
        "create_gemini_client",
        lambda: FakeClient(models),
    )

    with pytest.raises(
        ai_service.AIServiceError,
        match="빈 응답",
    ):
        ai_service.review_code("print('hello')")


def test_ai_review_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(
        ai_service.AIServiceError,
        match="API 키가 설정되지 않았습니다",
    ):
        ai_service.create_gemini_client()
