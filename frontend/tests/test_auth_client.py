from unittest.mock import Mock

from frontend import api_client


# 실제 토큰이나 DB를 사용하지 않고, Streamlit API Client가 올바른 엔드포인트와 요청 본문을 사용하는지 검증
def test_refresh_access_token(monkeypatch):
    response = Mock()
    response.json.return_value = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "token_type": "bearer",
    }

    def fake_post(url, **kwargs):
        assert url.endswith("/api/v1/auth/refresh")
        assert kwargs["json"] == {
            "refresh_token": "old-refresh"
        }
        return response

    monkeypatch.setattr(
        api_client.requests,
        "post",
        fake_post,
    )

    result = api_client.refresh_access_token("old-refresh")

    response.raise_for_status.assert_called_once()
    assert result["access_token"] == "new-access"
    assert result["refresh_token"] == "new-refresh"


def test_logout_from_server(monkeypatch):
    response = Mock()

    def fake_post(url, **kwargs):
        assert url.endswith("/api/v1/auth/logout")
        assert kwargs["json"] == {
            "refresh_token": "test-refresh"
        }
        return response

    monkeypatch.setattr(
        api_client.requests,
        "post",
        fake_post,
    )

    result = api_client.logout_from_server("test-refresh")

    response.raise_for_status.assert_called_once()
    assert result is None