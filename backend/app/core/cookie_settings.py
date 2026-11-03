# 쿠키 설정
import os

REFRESH_COOKIE_NAME = "codementor_refresh"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60

# 로컬 HTTP 개발 환경에서는 false
# 실제 HTTPS 배포 환경에서는 true
COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)


def set_refresh_cookie(response, refresh_token: str):
    # httponly, secure, samesite 등의 옵션을 지원
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )