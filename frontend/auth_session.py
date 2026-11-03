import requests

from frontend.api_client import refresh_access_token


def renew_login(session_state) -> bool:
    refresh_token = session_state.get("refresh_token")

    if not refresh_token:
        return False

    try:
        result = refresh_access_token(refresh_token)

        session_state["access_token"] = result["access_token"]
        session_state["refresh_token"] = result["refresh_token"]

        return True

    except (requests.exceptions.RequestException, KeyError, TypeError):
        return False


import streamlit as st

from backend.app.core.cookie_settings import REFRESH_COOKIE_NAME
from frontend.api_client import (
    get_my_profile,
    restore_browser_login,
    revoke_browser_login,
)


# Streamlit 인증 복원 함수
def restore_login_from_cookie() -> bool:
    """브라우저 쿠키를 이용해 Access Token을 복원한다."""

    if st.session_state.get("access_token"):
        return True

    refresh_token = st.context.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        return False

    try:
        result = restore_browser_login(refresh_token)

        access_token = result["access_token"]

        # 기존 api_client.py에 구현한
        # /auth/me 호출 함수를 사용
        user = get_my_profile(access_token)

        st.session_state["access_token"] = access_token
        st.session_state["user"] = user
        # browser_cookie : 브라우저 쿠키에서 인증 복원, 
        # 미설정 : 기존 Streamlit 로그인 방식
        st.session_state["auth_mode"] = "browser_cookie"

        return True

    except (requests.exceptions.RequestException, KeyError, TypeError):
        return False

# 로그아웃
def revoke_browser_session() -> bool:
    refresh_token = st.context.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        return True

    try:
        revoke_browser_login(refresh_token)
        return True
    except requests.exceptions.RequestException:
        return False

# 통합 갱신 함수
def renew_authentication() -> bool:
    # 만료된 Access Token을 제거한 뒤 쿠키를 이용해 새로운 Access Token을 발급
    if st.session_state.get("auth_mode") == "browser_cookie":
        st.session_state.pop("access_token", None)
        return restore_login_from_cookie()

    return renew_login(st.session_state)