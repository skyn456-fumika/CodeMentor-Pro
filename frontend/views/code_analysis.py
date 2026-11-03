# 코드 분석 화면
import requests
import streamlit as st

from frontend.api_client import (
    analyze_code,
    review_code_with_ai,
)


def render_code_analysis():
    st.subheader("🔍 Python 코드 분석")

    source_code = st.text_area(
        "분석할 Python 코드를 입력하세요.",
        value="""def divide(a, b):
    return a / b
""",
        height=250,
        key="source_code",
    )

    ruff_tab, ai_tab = st.tabs([
        "🔍 Ruff 정적 분석",
        "🤖 Gemini AI 코드 리뷰",
    ])

    with ruff_tab:
        st.markdown("#### Ruff 정적 분석")

        if st.button(
            "Ruff 분석 실행",
            use_container_width=True,
            key="ruff_button",
        ):
            if not source_code.strip():
                st.warning("분석할 코드를 입력해 주세요.")
            else:
                with st.spinner("Ruff 분석 중..."):
                    try:
                        result = analyze_code(
                            code=source_code,
                            token=st.session_state.access_token,
                        )

                        st.session_state.ruff_result = result

                    except requests.exceptions.HTTPError as exc:
                        st.error(
                            f"Ruff 분석 요청 실패: "
                            f"HTTP {exc.response.status_code}"
                        )

                    except requests.exceptions.RequestException:
                        st.error("FastAPI 서버에 연결할 수 없습니다.")

        result = st.session_state.get("ruff_result")

        if result is not None:
            total = result.get("total", 0)
            issues = result.get("issues", [])

            st.metric("발견된 문제", total)

            if total == 0:
                st.success("Ruff에서 발견한 문제가 없습니다.")
            else:
                for issue in issues:
                    with st.container(border=True):
                        st.markdown(
                            f"**{issue.get('code', 'UNKNOWN')}** — "
                            f"{issue.get('message', '')}"
                        )
                        st.caption(
                            f"위치: {issue.get('line', '?')}행, "
                            f"{issue.get('column', '?')}열"
                        )

    with ai_tab:
        st.markdown("#### Gemini AI 코드 리뷰")

        if st.button(
            "AI 코드 리뷰 실행",
            use_container_width=True,
            key="ai_button",
        ):
            if not source_code.strip():
                st.warning("분석할 코드를 입력해 주세요.")
            else:
                with st.spinner("Gemini가 코드를 분석하고 있습니다..."):
                    try:
                        result = review_code_with_ai(
                            code=source_code,
                            token=st.session_state.access_token,
                        )

                        st.session_state.ai_review_result = result

                    except requests.exceptions.HTTPError as exc:
                        status_code = exc.response.status_code

                        if status_code == 503:
                            st.error(
                                "AI 서비스를 일시적으로 사용할 수 없습니다. "
                                "다시 시도해 주세요."
                            )
                        else:
                            st.error(
                                f"AI 리뷰 요청 실패: HTTP {status_code}"
                            )

                    except requests.exceptions.Timeout:
                        st.error("Gemini 응답 시간이 초과됐습니다.")

                    except requests.exceptions.RequestException:
                        st.error("FastAPI 서버에 연결할 수 없습니다.")

        result = st.session_state.get("ai_review_result")

        if result is not None:
            st.markdown("#### AI 리뷰 결과")
            st.markdown(
                result.get("review", "리뷰 결과가 없습니다.")
            )