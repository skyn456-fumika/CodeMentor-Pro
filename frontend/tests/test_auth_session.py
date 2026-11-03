# Access Token 자동 갱신 테스트
import requests

from frontend import auth_session


def test_renew_login_success(monkeypatch):
    state = {
        "access_token": "old-access",
        "refresh_token": "old-refresh",
    }

    monkeypatch.setattr(
        auth_session,
        "refresh_access_token",
        lambda token: {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
        },
    )

    assert auth_session.renew_login(state) is True
    assert state["access_token"] == "new-access"
    assert state["refresh_token"] == "new-refresh"


def test_renew_login_without_refresh_token():
    state = {"access_token": "old-access"}

    assert auth_session.renew_login(state) is False

# 갱신 실패 시 토큰을 임의로 변경하지 않는지 확인
def test_renew_login_invalid_refresh_token(monkeypatch):
    state = {
        "access_token": "old-access",
        "refresh_token": "invalid-refresh",
    }

    def fake_refresh(token):
        raise requests.exceptions.HTTPError("401 Unauthorized")

    monkeypatch.setattr(
        auth_session,
        "refresh_access_token",
        fake_refresh,
    )

    assert auth_session.renew_login(state) is False
    assert state["access_token"] == "old-access"
    assert state["refresh_token"] == "invalid-refresh"