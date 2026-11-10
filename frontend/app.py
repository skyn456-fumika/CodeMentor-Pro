# Streamlit 메인 화면
import os

import requests
import streamlit as st

from frontend.api_client import (
    AuthenticationExpiredError,
    register_user,
)
from frontend.views.ai_chat import render_ai_chat
from frontend.views.code_analysis import render_code_analysis
from frontend.views.dashboard import render_dashboard
from frontend.views.review_history import render_review_history

st.set_page_config(
    page_title="CodeMentor Pro",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.auth_session import (
    renew_authentication,
    restore_login_from_cookie,
)

PUBLIC_API_BASE_URL = os.getenv(
    "PUBLIC_API_BASE_URL",
    "http://localhost:8000",
).rstrip("/")

def browser_auth_url(endpoint: str) -> str:
    return f"{PUBLIC_API_BASE_URL}/api/v1/auth/{endpoint}"

# 로그인 정보 초기화
if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "user" not in st.session_state:
    st.session_state.user = None

# 분석 결과 상태 초기화
if "ruff_result" not in st.session_state:
    st.session_state.ruff_result = None

if "ai_review_result" not in st.session_state:
    st.session_state.ai_review_result = None

if "review_page" not in st.session_state:
    st.session_state.review_page = 1

if "selected_review_id" not in st.session_state:
    st.session_state.selected_review_id = None

if "selected_chat_id" not in st.session_state:
    st.session_state.selected_chat_id = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None


def logout():
    keys = [
        "access_token",
        "user",
        "ruff_result",
        "ai_review_result",
        "review_page",
        "selected_review_id",
        "selected_chat_id",
        "chat_selector",
        "source_code",
        "selected_menu",
        "refresh_token",
        "auth_mode",
    ]

    for key in keys:
        st.session_state.pop(key, None)

def handle_auth_expired():
    logout()
    st.session_state.auth_expired_message = (
        "로그인이 만료되었습니다. 다시 로그인해 주세요."
    )
    st.rerun()

st.title("💻 CodeMentor Pro")
st.caption("FastAPI + Ruff + Gemini 기반 AI 코드 멘토")

# F5 새로고침 등으로 Streamlit 세션이 초기화된 경우
# 브라우저 쿠키를 이용해 로그인 상태 복원
if not st.session_state.get("access_token") and restore_login_from_cookie():
    st.rerun()

# 로그인하지 않은 사용자
if not st.session_state.access_token:
    st.subheader("시작하기")

    # 로그인 화면에 만료 메시지 표시
    message = st.session_state.pop(
        "auth_expired_message",
        None,
    )

    if message:
        st.warning(message)

    login_tab, register_tab = st.tabs(["로그인", "회원가입"])

    # 로그인·회원가입을 st.form()으로 구현
    with login_tab:
        st.info(
            "로그인하면 브라우저 인증 쿠키를 통해 "
            "새로고침 후에도 로그인 상태가 유지됩니다."
        )

        st.link_button(
            "🔐 로그인하기",
            browser_auth_url("browser-signin"),
            use_container_width=True,
        )

    with register_tab:
        with st.form("register_form"):
            new_email = st.text_input(
                "이메일",
                key="register_email",
            )
            new_password = st.text_input(
                "비밀번호 (8자 이상)",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "비밀번호 확인",
                type="password",
            )

            register_submitted = st.form_submit_button(
                "회원가입",
                use_container_width=True,
            )

        if register_submitted:
            if new_password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                try:
                    register_user(new_email, new_password)
                    st.success("회원가입 완료! 로그인해 주세요.")

                except requests.exceptions.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 409:
                        st.error("이미 사용 중인 이메일입니다.")
                    elif exc.response is not None and exc.response.status_code == 422:
                        st.error("이메일 형식이나 비밀번호 길이를 확인해 주세요.")
                    else:
                        st.error("회원가입에 실패했습니다.")

                except requests.exceptions.RequestException:
                    st.error("백엔드 서버에 연결할 수 없습니다.")

# 로그인한 사용자
else:
    with st.sidebar:

        st.header("💻 CodeMentor Pro")

        user = st.session_state.user
        st.caption(user["email"] if user else "사용자")

        st.divider()

        selected_menu = st.radio(
            "메뉴", 
            [
                "🏠 대시보드",
                "🔍 코드 분석",
                "📚 분석 기록",
                "💬 AI 채팅",
            ],
            label_visibility="collapsed",
            key="selected_menu",
        )

        st.divider()

        st.link_button(
            "로그아웃",
            browser_auth_url("browser-signout"),
            use_container_width=True,
        )


    try:
        if selected_menu == "🏠 대시보드":
            render_dashboard()

        elif selected_menu == "🔍 코드 분석":
            render_code_analysis()

        elif selected_menu == "📚 분석 기록":
            render_review_history()

        elif selected_menu == "💬 AI 채팅":
            render_ai_chat()

    # 401을 반환했을 때 Refresh Token으로 재발급을 시도
    except AuthenticationExpiredError:
        # 성공하면 갱신된 Access Token으로 화면을 다시 실행
        if renew_authentication():
            st.rerun()
        else:
            handle_auth_expired()