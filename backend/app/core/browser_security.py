# 브라우저 인증 요청 출처 검증
import os
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "BROWSER_ALLOWED_ORIGINS",
        "http://localhost:8000,http://localhost:8501",
    ).split(",")
    if origin.strip()
}

# 요청의 Origin을 먼저 확인하고, 없으면 Referer를 확인
# 둘 다 없거나 허용되지 않은 주소라면 요청을 거부
# OWASP에서 설명하는 CSRF 방어 수단 중 요청 출처 검증 방식에 해당
def validate_browser_origin(request: Request) -> None:
    origin = request.headers.get("origin")

    if not origin:
        referer = request.headers.get("referer")

        if referer:
            parsed = urlsplit(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}"

    if origin not in ALLOWED_ORIGINS:
        raise HTTPException(
            status_code=403,
            detail="허용되지 않은 브라우저 요청입니다.",
        )