# FastAPI 호출 코드
import os

import requests
from dotenv import load_dotenv


class AuthenticationExpiredError(Exception):
    pass

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
)

STREAMLIT_APP_URL = os.getenv(
    "STREAMLIT_APP_URL",
    "http://localhost:8501",
).rstrip("/")

# requests.get()으로 백엔드를 호출하고, 
# HTTP 오류가 발생하면 raise_for_status()로 처리
# 요청에 timeout을 지정해서 서버가 응답하지 않을 때 무한정 대기하지 않도록 함
def check_backend_health() -> dict:
    response = requests.get(
        f"{API_BASE_URL}/health",
        timeout=5,
    )

    response.raise_for_status()
    return response.json()

# 인증 함수
def register_user(email: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def login_user(email: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_my_profile(token: str) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    return check_api_response(response)

# Ruff 정적 분석
def analyze_code(code: str, token: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/reviews/analyze",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    return check_api_response(response)

# Gemini 코드 리뷰
def review_code_with_ai(code: str, token: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/reviews/ai",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
        timeout=90,
    )
    return check_api_response(response)

# 조회 함수
def get_review_list(
    token: str,
    page: int = 1,
    size: int = 10,
) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/reviews",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": page, "size": size},
        timeout=10,
    )

    return check_api_response(response)


def get_review_detail(
    token: str,
    review_id: int,
) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/reviews/{review_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )

    return check_api_response(response)

# 채팅 함수
def create_chat(token: str, title: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": title},
        timeout=10,
    )
    return check_api_response(response)


def get_chat_list(token: str) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/chats",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "size": 100},
        timeout=10,
    )
    return check_api_response(response)


def get_chat_messages(token: str, chat_id: int) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    return check_api_response(response)


def ask_chat_ai(token: str, chat_id: int, question: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": question},
        timeout=90,
    )
    return check_api_response(response)

# 통계 조회
def get_review_stats(token: str) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/api/v1/reviews/stats",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )

    return check_api_response(response)

# 공통 응답 검증
def check_api_response(response: requests.Response) -> dict:
    if response.status_code == 401:
        raise AuthenticationExpiredError(
            "로그인이 만료되었거나 인증이 유효하지 않습니다."
        )

    response.raise_for_status()
    return response.json()

def refresh_access_token(refresh_token: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def logout_from_server(refresh_token: str) -> None:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        timeout=10,
    )

    response.raise_for_status()

# F5 로그인 복원
# Streamlit 서버에서 FastAPI로 쿠키를 전달하고, 새로운 Access Token을 받아오는 역할
def restore_browser_login(refresh_token: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/browser-restore",
        headers={
            "Origin": STREAMLIT_APP_URL,
        },
        cookies={
            "codementor_refresh": refresh_token,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

# 서버 측 쿠키 토큰 폐기 함수
def revoke_browser_login(refresh_token: str) -> None:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/browser-logout",
        headers={
            "Origin": STREAMLIT_APP_URL,
        },
        cookies={
            "codementor_refresh": refresh_token,
        },
        timeout=10,
    )
    response.raise_for_status()