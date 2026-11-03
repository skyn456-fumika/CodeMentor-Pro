from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


import os
from datetime import UTC, datetime, timedelta

import jwt
from dotenv import load_dotenv

load_dotenv()


def create_access_token(user_id: int) -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY가 설정되지 않았습니다.")

    expire_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    expire = datetime.now(UTC) + timedelta(
        minutes=expire_minutes
    )

    # sub에는 사용자 ID를 문자열로 저장하고, exp에는 토큰 만료 시각을 넣었음.
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
    )

class InvalidTokenError(Exception):
    pass

# JWT 검증 함수
def decode_access_token(token: str) -> int:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY가 설정되지 않았습니다.")

    try:
        # jwt.decode()는 서명과 만료 시간을 확인하고, 
        # require 옵션으로 필수 클레임 존재 여부도 검증
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat"]},
        )

        user_id = int(payload["sub"])

        if user_id < 1:
            raise InvalidTokenError("잘못된 사용자 ID입니다.")

        return user_id

    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise InvalidTokenError("유효하지 않은 토큰입니다.") from exc