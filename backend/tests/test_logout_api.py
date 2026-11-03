# 로그아웃 API 자동 테스트
from fastapi.testclient import TestClient

from backend.app.api.v1 import auth
from backend.app.main import app

client = TestClient(app)


# 정상 로그아웃
def test_logout_success(monkeypatch):
    called = []

    def fake_revoke(session, raw_token):
        called.append(raw_token)

    monkeypatch.setattr(
        auth,
        "revoke_refresh_token",
        fake_revoke,
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "test-refresh-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert called == ["test-refresh-token"]

# 존재하지 않는 토큰
def test_logout_unknown_token(monkeypatch):
    def fake_revoke(session, raw_token):
        # 존재하지 않는 토큰도 조용히 처리
        return None

    monkeypatch.setattr(
        auth,
        "revoke_refresh_token",
        fake_revoke,
    )

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "unknown-token"},
    )

    assert response.status_code == 204

# 빈 Refresh Token
def test_logout_empty_token():
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": ""},
    )

    assert response.status_code == 422