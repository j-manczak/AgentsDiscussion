import pytest

from config.settings import ConfigurationError, get_settings


def should_use_local_ollama_without_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)

    settings = get_settings()

    assert settings.provider == "ollama"
    assert settings.model == "qwen2.5:7b"
    assert settings.ollama_url == "http://127.0.0.1:11434"


def should_require_openai_credentials_only_when_openai_is_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "")

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY, OPENAI_MODEL"):
        get_settings()


def should_reject_unknown_model_providers_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    with pytest.raises(ConfigurationError, match="LLM_PROVIDER"):
        get_settings()
