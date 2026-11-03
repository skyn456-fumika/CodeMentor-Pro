import subprocess
from types import SimpleNamespace

import pytest

from backend.app.core.dependencies import get_current_user
from backend.app.services import analyzer_service


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
    
# monkeypatch는 실제 subprocess.run() 대신 
# 테스트용 함수를 일시적으로 사용하도록 바꾸는 기능
def test_ruff_timeout(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="ruff",
            timeout=10,
        )

    monkeypatch.setattr(
        analyzer_service.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(analyzer_service.AnalyzerError):
        analyzer_service.analyze_code("print('hello')")


def test_ruff_not_installed(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("Ruff not found")

    monkeypatch.setattr(
        analyzer_service.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(analyzer_service.AnalyzerError):
        analyzer_service.analyze_code("print('hello')")


def test_ruff_invalid_json(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["ruff"],
            returncode=0,
            stdout="invalid json",
            stderr="",
        )

    monkeypatch.setattr(
        analyzer_service.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(analyzer_service.AnalyzerError):
        analyzer_service.analyze_code("print('hello')")


def test_ruff_process_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["ruff"],
            returncode=2,
            stdout="",
            stderr="Ruff process failed",
        )

    monkeypatch.setattr(
        analyzer_service.subprocess,
        "run",
        fake_run,
    )

    with pytest.raises(analyzer_service.AnalyzerError):
        analyzer_service.analyze_code("print('hello')")


from fastapi.testclient import TestClient

from backend.app.api.v1 import reviews
from backend.app.main import app

client = TestClient(app)

# Service에서 AnalyzerError가 발생했을 때 
# Router가 이를 HTTP 503으로 올바르게 변환하는지 확인함.
def test_analyze_api_service_unavailable(monkeypatch):
    def fake_analyze(code):
        raise analyzer_service.AnalyzerError(
            "Ruff process failed"
        )

    monkeypatch.setattr(
        reviews,
        "analyze_code",
        fake_analyze,
    )

    response = client.post(
        "/api/v1/reviews/analyze",
        json={"code": "print('hello')"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "코드 분석 서비스를 사용할 수 없습니다."
    }