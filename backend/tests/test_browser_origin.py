# Origin 검증 테스트 보강
# 허용 주소를 테스트 내부에서 고정했기 때문에, 로컬 환경변수나 Docker 설정에 영향을 받지 않음.
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.core import browser_security


def make_request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/auth/browser-signin",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in headers.items()
        ],
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def allowed_origins(monkeypatch):
    monkeypatch.setattr(
        browser_security,
        "ALLOWED_ORIGINS",
        {
            "http://localhost:8000",
            "http://localhost:8501",
        },
    )


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:8000",
        "http://localhost:8501",
    ],
)
def test_allowed_origin(origin):
    request = make_request({"origin": origin})

    browser_security.validate_browser_origin(request)


def test_allowed_referer():
    request = make_request({
        "referer": "http://localhost:8000/browser-signin",
    })

    browser_security.validate_browser_origin(request)


def test_blocked_origin():
    request = make_request({
        "origin": "https://untrusted.example",
    })

    with pytest.raises(HTTPException) as exc_info:
        browser_security.validate_browser_origin(request)

    assert exc_info.value.status_code == 403


def test_missing_origin_and_referer():
    request = make_request({})

    with pytest.raises(HTTPException) as exc_info:
        browser_security.validate_browser_origin(request)

    assert exc_info.value.status_code == 403


def test_origin_takes_priority_over_referer():
    request = make_request({
        "origin": "https://untrusted.example",
        "referer": "http://localhost:8000/browser-signin",
    })

    with pytest.raises(HTTPException) as exc_info:
        browser_security.validate_browser_origin(request)

    assert exc_info.value.status_code == 403
