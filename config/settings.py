import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    openai_api_key: str = ""
    ollama_url: str = "http://127.0.0.1:11434"


class ConfigurationError(RuntimeError):
    pass


def get_settings() -> Settings:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip()
        if not model:
            raise ConfigurationError("OLLAMA_MODEL must not be empty.")
        return Settings(
            provider=provider,
            model=model,
            ollama_url=os.getenv(
                "OLLAMA_URL", "http://127.0.0.1:11434"
            ).rstrip("/"),
        )
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = os.getenv("OPENAI_MODEL", "").strip()
        missing = [
            name
            for name, value in (("OPENAI_API_KEY", api_key), ("OPENAI_MODEL", model))
            if not value
        ]
        if missing:
            raise ConfigurationError(
                "OpenAI provider selected. Set: " + ", ".join(missing) + "."
            )
        return Settings(
            provider=provider,
            model=model,
            openai_api_key=api_key,
        )
    raise ConfigurationError(
        "LLM_PROVIDER must be either 'ollama' or 'openai'."
    )
