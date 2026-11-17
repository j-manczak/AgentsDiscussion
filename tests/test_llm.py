from types import SimpleNamespace
import json
import urllib.error

import pytest
from openai import RateLimitError

from llm.client import ModelRequestError, ModelResponseError, OllamaJsonClient, OpenAIJsonClient


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.content


def should_translate_rate_limit_errors_when_provider_rejects_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OpenAIJsonClient(api_key="test-key", model="test-model")
    response = SimpleNamespace(
        status_code=429,
        headers={},
        request=SimpleNamespace(),
    )

    def raise_rate_limit(*args: object, **kwargs: object) -> None:
        raise RateLimitError("Rate limited", response=response, body=None)

    monkeypatch.setattr(client.client.chat.completions, "create", raise_rate_limit)

    with pytest.raises(ModelRequestError, match="rate limit"):
        client.complete_json("system", "user")


def should_send_json_mode_and_parse_ollama_output_when_local_model_responds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(
            b'{"message":{"content":"{\\"main_claim\\":\\"A\\",\\"conclusion\\":\\"B\\"}"}}'
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OllamaJsonClient("qwen2.5:7b")

    result = client.complete_json("system prompt", "user prompt")

    assert result == {"main_claim": "A", "conclusion": "B"}
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["body"]["model"] == "qwen2.5:7b"
    assert captured["body"]["format"] == "json"
    assert captured["body"]["stream"] is False


def should_explain_local_server_startup_when_ollama_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_connection_error(*args: object, **kwargs: object) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", raise_connection_error)
    client = OllamaJsonClient("qwen2.5:7b")

    with pytest.raises(ModelRequestError, match="Start Ollama"):
        client.complete_json("system prompt", "user prompt")


def should_explain_missing_ollama_model_when_local_model_is_not_pulled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_not_found(*args: object, **kwargs: object) -> None:
        raise urllib.error.HTTPError(
            "http://127.0.0.1:11434/api/chat",
            404,
            "Not Found",
            {},
            None,
        )

    monkeypatch.setattr("urllib.request.urlopen", raise_not_found)
    client = OllamaJsonClient("qwen2.5:7b")

    with pytest.raises(ModelRequestError, match="ollama pull qwen2.5:7b"):
        client.complete_json("system prompt", "user prompt")


def should_reject_invalid_ollama_payload_when_response_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: FakeResponse(b"not json"),
    )
    client = OllamaJsonClient("qwen2.5:7b")

    with pytest.raises(ModelResponseError, match="invalid response"):
        client.complete_json("system prompt", "user prompt")
