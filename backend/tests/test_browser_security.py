# 쿠키 인증 보안 자동 테스트
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.core.browser_security import validate_browser_origin


def make_request(headers: dict) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/browser-refresh",
        "headers": [
            (key.lower().encode(), value.encode())
            for key, value in headers.items()
        ],
    }
    return Request(scope)


def test_allowed_origin():
    request = make_request({
        "origin": "http://localhost:8000",
    })

    validate_browser_origin(request)


def test_allowed_streamlit_origin():
    request = make_request({
        "origin": "http://localhost:8501",
    })

    validate_browser_origin(request)


def test_blocked_origin():
    request = make_request({
        "origin": "https://evil.example.com",
    })

    with pytest.raises(HTTPException) as exc:
        validate_browser_origin(request)

    assert exc.value.status_code == 403


def test_missing_origin_and_referer():
    request = make_request({})

    with pytest.raises(HTTPException) as exc:
        validate_browser_origin(request)

    assert exc.value.status_code == 403


def test_allowed_referer():
    request = make_request({
        "referer": "http://localhost:8000/docs",
    })

    validate_browser_origin(request)