import os

from google.genai import types

from backend.app.services.ai_service import (
    AIServiceError,
    create_gemini_client,
)

# Gemini 대화 이력 제한 구현
MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_CHARS = 30000

# Gemini 대화 함수
def generate_chat_response(
    history: list[tuple[str, str]],
    question: str,
) -> str:
    question = question.strip()

    if not question:
        raise ValueError("질문을 입력해 주세요.")

    # 가장 최근 대화부터 최대 20개만 사용
    history = history[-MAX_HISTORY_MESSAGES:]

    # 추가로 전체 문자 수 제한
    selected_history = []
    total_chars = 0

    for role, content in reversed(history):
        if role not in ("user", "assistant"):
            continue

        if total_chars + len(content) > MAX_HISTORY_CHARS:
            break

        selected_history.append((role, content))
        total_chars += len(content)

    # 시간순으로 다시 정렬
    history = list(reversed(selected_history))

    contents = []

    # 기존 대화 이력을 Gemini 형식으로 변환
    for role, content in history:
        if role not in ("user", "assistant"):
            continue

        contents.append(
            types.Content(
                role="model" if role == "assistant" else "user",
                parts=[types.Part.from_text(text=content)],
            )
        )

    # 현재 질문 추가
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)],
        )
    )

    try:
        client = create_gemini_client()

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "당신은 Python 개발자를 돕는 AI 코드 멘토입니다. "
                    "이전 대화 맥락을 참고하여 한국어로 답변하세요. "
                    "코드 예제를 제시할 때는 이유도 함께 설명하세요."
                ),
            ),
        )

        answer = response.text

        if not answer or not answer.strip():
            raise AIServiceError("Gemini가 빈 응답을 반환했습니다.")

        return answer.strip()

    except AIServiceError:
        raise

    except Exception as exc:
        raise AIServiceError(
            "Gemini 대화 요청에 실패했습니다."
        ) from exc