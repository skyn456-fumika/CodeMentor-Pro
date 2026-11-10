# Gemini 재시도 설정 단위 테스트
from unittest.mock import patch

from backend.app.services.ai_service import create_gemini_client


def test_gemini_client_retry_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

    with patch(
        "backend.app.services.ai_service.genai.Client"
    ) as mock_client:
        create_gemini_client()

    mock_client.assert_called_once()

    options = mock_client.call_args.kwargs["http_options"]
    retry = options.retry_options

    assert options.timeout == 30_000
    assert retry.attempts == 3
    assert retry.initial_delay == 1.0
    assert retry.max_delay == 4.0
    assert retry.exp_base == 2.0
    assert retry.http_status_codes == [503]