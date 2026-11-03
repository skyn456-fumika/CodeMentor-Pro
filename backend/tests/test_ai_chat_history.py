# 제한 동작 확인용 테스트
from types import SimpleNamespace

from backend.app.services import ai_chat_service


# 실제 Gemini API를 호출하지 않고, 전달되는 contents를 직접 확인하는 방식
# 현재 문자 수 제한은 이전 대화 이력에만 적용
# 새 질문 자체의 크기는 기존 Pydantic 스키마에서 최대 20,000자로 검증
def test_chat_history_limit(monkeypatch):
    captured = {}

    class FakeModels:
        def generate_content(self, model, contents, config):
            captured["contents"] = contents
            return SimpleNamespace(text="테스트 답변")

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(
        ai_chat_service,
        "create_gemini_client",
        lambda: FakeClient(),
    )

    history = [
        ("user" if i % 2 == 0 else "assistant", f"메시지 {i}")
        for i in range(30)
    ]

    result = ai_chat_service.generate_chat_response(
        history=history,
        question="새로운 질문",
    )

    assert result == "테스트 답변"

    contents = captured["contents"]

    # 최근 이력 20개 + 현재 질문 1개
    assert len(contents) == 21

    # 이전 메시지 10개는 제외
    assert contents[0].parts[0].text == "메시지 10"
    assert contents[-2].parts[0].text == "메시지 29"
    assert contents[-1].parts[0].text == "새로운 질문"