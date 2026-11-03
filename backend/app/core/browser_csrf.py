# CSRF 보안 모듈
import hmac
import secrets

from fastapi import HTTPException, status

CSRF_COOKIE_NAME = "codementor_csrf"


def create_csrf_token() -> str:
    # 예측하기 어려운 난수를 생성
    return secrets.token_urlsafe(32)

# 쿠키와 HTML 폼에 같은 임의 토큰을 발급하고 비교하는 Double Submit Cookie 방식의 기초
def validate_csrf_token(
    cookie_token: str | None,
    form_token: str | None,
) -> None:
    if not cookie_token or not form_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 없습니다.",
        )

    # 토큰을 비교할 때 타이밍 공격의 위험을 줄여줌
    if not hmac.compare_digest(cookie_token, form_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 일치하지 않습니다.",
        )