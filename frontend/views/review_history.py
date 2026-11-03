# 분석 기록 화면
import json

import requests
import streamlit as st

from frontend.api_client import (
    get_review_detail,
    get_review_list,
)


def render_review_history():
    st.subheader("📚 내 코드 분석 기록")

    token = st.session_state.access_token

    try:
        review_data = get_review_list(
            token=token,
            page=st.session_state.review_page,
            size=5,
        )

        total = review_data["total"]
        items = review_data["items"]

        st.caption(f"전체 분석 기록: {total}개")

        if not items:
            st.info("이 페이지에 표시할 분석 기록이 없습니다.")

        for item in items:
            review_type = (
                "🔍 Ruff"
                if item["analysis_type"] == "RUFF"
                else "🤖 Gemini"
            )

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(
                        f"**{review_type} — 기록 #{item['id']}**"
                    )
                    st.caption(
                        f"분석 일시: {item['created_at']}"
                    )

                with col2:
                    if st.button(
                        "상세 보기",
                        key=f"review_detail_{item['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_review_id = item["id"]
                        st.rerun()

        total_pages = max(1, (total + 4) // 5)

        prev_col, page_col, next_col = st.columns([1, 2, 1])

        with prev_col:
            if st.button(
                "이전",
                disabled=st.session_state.review_page <= 1,
                use_container_width=True,
            ):
                st.session_state.review_page -= 1
                st.session_state.selected_review_id = None
                st.rerun()

        with page_col:
            st.write(
                f"{st.session_state.review_page} / {total_pages}"
            )

        with next_col:
            if st.button(
                "다음",
                disabled=st.session_state.review_page >= total_pages,
                use_container_width=True,
            ):
                st.session_state.review_page += 1
                st.session_state.selected_review_id = None
                st.rerun()

    except requests.exceptions.RequestException:
        st.error("분석 기록을 불러오지 못했습니다.")

    # 상세 조회
    if st.session_state.selected_review_id is not None:
        st.divider()
        st.subheader("📄 분석 기록 상세")

        try:
            detail = get_review_detail(
                token=token,
                review_id=st.session_state.selected_review_id,
            )

            st.write(f"**기록 ID:** {detail['id']}")
            st.write(f"**분석 유형:** {detail['analysis_type']}")

            st.markdown("#### 원본 코드")
            st.code(detail["source_code"], language="python")

            st.markdown("#### 분석 결과")

            if detail["analysis_type"] == "AI":
                st.markdown(detail["result"])

            else:
                try:
                    issues = json.loads(detail["result"])

                    if isinstance(issues, list):
                        if not issues:
                            st.success("발견된 문제가 없습니다.")

                        for issue in issues:
                            with st.container(border=True):
                                st.markdown(
                                    f"**{issue['code']}** — {issue['message']}"
                                )
                                st.caption(
                                    f"{issue['line']}행, {issue['column']}열"
                                )
                    else:
                        st.write(detail["result"])

                except (json.JSONDecodeError, TypeError, KeyError):
                    st.write(detail["result"])

        except requests.exceptions.RequestException:
            st.error("상세 기록을 불러오지 못했습니다.")

        if st.button("상세 보기 닫기"):
            st.session_state.selected_review_id = None
            st.rerun()