# 대시보드 화면
import requests
import streamlit as st

from frontend.api_client import (
    check_backend_health,
    get_review_list,
    get_review_stats,
)


def move_to_review_detail(review_id: int):
    st.session_state.selected_review_id = review_id
    st.session_state.review_page = 1
    st.session_state.selected_menu = "📚 분석 기록"

def move_to_menu(menu: str):
    st.session_state.selected_menu = menu


def render_dashboard():
    st.title("🏠 대시보드")

    user = st.session_state.get("user")
    token = st.session_state.get("access_token")

    if user:
        st.caption(f"{user['email']}님의 개발 활동 현황")

    st.divider()

    st.subheader("📊 코드 분석 현황")

    try:
        stats = get_review_stats(token)

        total = stats["total"]
        ruff_count = stats["ruff_count"]
        ai_count = stats["ai_count"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("전체 분석", total)

        with col2:
            st.metric("Ruff 분석", ruff_count)

        with col3:
            st.metric("AI 리뷰", ai_count)

    except requests.exceptions.RequestException:
        st.error("분석 통계를 불러오지 못했습니다.")

    # 최근 분석 기록 조회
    st.divider()
    st.subheader("🕒 최근 분석 기록")

    try:
        recent_data = get_review_list(
            token=token,
            page=1,
            size=5,
        )

        recent_items = recent_data["items"]

        if not recent_items:
            st.info("아직 분석 기록이 없습니다.")
        else:
            for item in recent_items:
                analysis_type = item["analysis_type"]

                if analysis_type == "RUFF":
                    type_label = "🔍 Ruff 정적 분석"
                else:
                    type_label = "🤖 Gemini AI 리뷰"

                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(
                            f"**{type_label}** — 기록 #{item['id']}"
                        )
                        st.caption(
                            f"분석 일시: {item['created_at']}"
                        )

                    with col2:
                        st.button(
                            "상세 보기",
                            key=f"dashboard_review_{item['id']}",
                            use_container_width=True,
                            on_click=move_to_review_detail,
                            args=(item["id"],),
                        )

    except requests.exceptions.RequestException:
        st.error("최근 분석 기록을 불러오지 못했습니다.")

    st.divider()

    st.subheader("🛠 주요 기능")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button(
            "🔍 Ruff 코드 분석",
            use_container_width=True,
            on_click=move_to_menu,
            args=("🔍 코드 분석",),
        )

    with col2:
        st.button(
            "🤖 Gemini 코드 리뷰",
            use_container_width=True,
            on_click=move_to_menu,
            args=("🔍 코드 분석",),
        )

    with col3:
        st.button(
            "💬 AI 코드 멘토",
            use_container_width=True,
            on_click=move_to_menu,
            args=("💬 AI 채팅",),
        )

    st.divider()

    st.subheader("🔌 서버 상태")

    if st.button("FastAPI 연결 확인"):
        try:
            result = check_backend_health()
            st.success("FastAPI 서버 연결 성공!")
            st.json(result)

        except requests.exceptions.RequestException:
            st.error("FastAPI 서버에 연결할 수 없습니다.")