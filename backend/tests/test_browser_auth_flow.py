# 브라우저 인증 정상 흐름 통합 테스트
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.db.database import get_db
from backend.app.main import app

ORIGIN = "http://localhost:8501"
AUTH_URL = "/api/v1/auth"


def test_browser_login_refresh_logout_flow(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            email = f"browser-{uuid4().hex}@example.com"
            password = "TestPassword123!"

            register_response = client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": email,
                    "password": password,
                },
            )
            assert register_response.status_code in (200, 201)

            # 1. 브라우저 로그인
            login_response = client.post(
                f"{AUTH_URL}/browser-login",
                headers={"Origin": ORIGIN},
                json={
                    "email": email,
                    "password": password,
                },
            )

            assert login_response.status_code == 200
            assert "access_token" not in login_response.json()
            assert "refresh_token" not in login_response.json()

            assert "codementor_refresh" in client.cookies

            old_token = client.cookies.get("codementor_refresh")

            # 2. 브라우저 토큰 갱신
            refresh_response = client.post(
                f"{AUTH_URL}/browser-refresh",
                headers={"Origin": ORIGIN},
            )

            assert refresh_response.status_code == 200
            assert refresh_response.json()["access_token"]
            assert "refresh_token" not in refresh_response.json()

            new_token = client.cookies.get("codementor_refresh")

            assert new_token
            assert old_token != new_token

            # 3. 기존 Refresh Token 재사용 방지
            with TestClient(app) as old_client:
                old_client.cookies.set(
                    "codementor_refresh",
                    old_token,
                )

                reused_response = old_client.post(
                    f"{AUTH_URL}/browser-refresh",
                    headers={"Origin": ORIGIN},
                )

                assert reused_response.status_code == 401

            # 4. 로그아웃
            logout_response = client.post(
                f"{AUTH_URL}/browser-logout",
                headers={"Origin": ORIGIN},
            )

            assert logout_response.status_code == 204
            assert "codementor_refresh" not in client.cookies

            # 5. 로그아웃 후 재갱신 차단
            rejected_response = client.post(
                f"{AUTH_URL}/browser-refresh",
                headers={"Origin": ORIGIN},
            )

            assert rejected_response.status_code == 401

    finally:
        app.dependency_overrides.clear()