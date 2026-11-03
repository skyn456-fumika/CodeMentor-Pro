# AI 채팅 화면
import requests
import streamlit as st

from frontend.api_client import (
    ask_chat_ai,
    create_chat,
    get_chat_list,
    get_chat_messages,
)


def render_ai_chat():
    st.subheader("💬 AI 코드 멘토")

    token = st.session_state.access_token

    # 새 대화방 생성
    with st.form("new_chat_form"):
        chat_title = st.text_input(
            "새 대화 제목",
            value="새 대화",
        )

        create_submitted = st.form_submit_button(
            "새 대화 만들기"
        )

    if create_submitted:
        try:
            new_chat = create_chat(token, chat_title)
            st.session_state.selected_chat_id = new_chat["id"]
            st.rerun()

        except requests.exceptions.RequestException:
            st.error("대화방 생성에 실패했습니다.")

    # 대화방 목록
    try:
        chat_data = get_chat_list(token)
        chat_items = chat_data.get("items", [])

        if chat_items:
            chat_options = {
                chat["id"]: f"{chat['title']} (#{chat['id']})"
                for chat in chat_items
            }

            chat_ids = list(chat_options.keys())

            current_chat_id = st.session_state.selected_chat_id

            if current_chat_id not in chat_ids:
                current_chat_id = chat_ids[0]

            selected_chat_id = st.selectbox(
                "대화방 선택",
                options=chat_ids,
                index=chat_ids.index(current_chat_id),
                format_func=lambda chat_id: chat_options[chat_id],
                key="chat_selector",
            )

            st.session_state.selected_chat_id = selected_chat_id

        else:
            st.session_state.selected_chat_id = None
            st.info("대화방이 없습니다. 새 대화를 만들어 주세요.")

    except requests.exceptions.RequestException:
        st.error("대화방 목록을 불러오지 못했습니다.")
        st.session_state.selected_chat_id = None

    # 선택된 대화방의 메시지 출력
    if st.session_state.selected_chat_id is None:
        return

    chat_id = st.session_state.selected_chat_id

    try:
        messages = get_chat_messages(token, chat_id)

        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    except requests.exceptions.RequestException:
        st.error("대화 메시지를 불러오지 못했습니다.")
        return

    # 새로운 질문
    question = st.chat_input(
        "Python 코드나 개발 관련 질문을 입력하세요."
    )

    if not question:
        return

    if not question.strip():
        st.warning("질문을 입력해 주세요.")
        return

    with st.chat_message("user"):
        st.markdown(question)

    with (
            st.chat_message("assistant"),
            st.spinner("Gemini가 답변을 생성하고 있습니다..."),
        ):
            try:
                answer = ask_chat_ai(
                    token=token,
                    chat_id=chat_id,
                    question=question,
                )

                st.markdown(answer["content"])
                st.rerun()

            except requests.exceptions.Timeout:
                st.error("AI 응답 시간이 초과됐습니다.")

            except requests.exceptions.HTTPError as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else None
                )

                if status_code == 503:
                    st.error("AI 서비스를 일시적으로 사용할 수 없습니다.")

                elif status_code == 401:
                    st.error("로그인이 만료되었습니다.")

                elif status_code == 404:
                    st.error("대화방을 찾을 수 없습니다.")

                else:
                    st.error(
                        f"AI 질문 처리 실패: HTTP {status_code}"
                    )

            except requests.exceptions.RequestException:
                st.error("백엔드 서버에 연결할 수 없습니다.")