# CSRF 보안 모듈
import hashlib
import hmac
import os
import secrets

from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

CSRF_COOKIE_NAME = "codementor_csrf"


def get_csrf_secret() -> bytes:
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError("JWT_SECRET_KEY가 설정되지 않았습니다.")

    return secret.encode()


def sign_csrf_nonce(
    nonce: str,
    binding: str | None = None,
) -> str:
    if binding is None:
        # 로그인 전 CSRF 토큰
        message = f"codementor-csrf-v1:unbound:{nonce}"
    else:
        # 로그인한 인증 세션과 CSRF 토큰을 연결
        binding_hash = hashlib.sha256(
            binding.encode()
        ).hexdigest()

        message = (
            f"codementor-csrf-v1:bound:"
            f"{binding_hash}:{nonce}"
        )

    return hmac.new(
        get_csrf_secret(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

# create_csrf_token()	                                    로그인 전 CSRF 토큰
# create_csrf_token(binding=refresh_token)	                로그인 후 세션 결합 CSRF 토큰
# validate_csrf_token(token, token)	                        로그인 폼 검증
# validate_csrf_token(token, token, binding=refresh_token)	인증 세션 결합 검증
def create_csrf_token(
    binding: str | None = None,
) -> str:
    nonce = secrets.token_urlsafe(32)
    signature = sign_csrf_nonce(nonce, binding)

    return f"{nonce}.{signature}"


def validate_csrf_token(
    cookie_token: str | None,
    form_token: str | None,
    binding: str | None = None,
) -> None:
    if not cookie_token or not form_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 없습니다.",
        )

    if not hmac.compare_digest(cookie_token, form_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 일치하지 않습니다.",
        )

    try:
        nonce, signature = cookie_token.rsplit(".", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 CSRF 토큰입니다.",
        ) from None

    expected_signature = sign_csrf_nonce(
        nonce,
        binding,
    )

    if not nonce or not hmac.compare_digest(
        signature,
        expected_signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 CSRF 토큰입니다.",
        )
