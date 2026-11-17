import json
import urllib.error
import urllib.request
from typing import Protocol

from openai import APIError, APITimeoutError, OpenAI, RateLimitError


class ModelRequestError(RuntimeError):
    pass


class ModelResponseError(RuntimeError):
    pass


class JsonModelClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        ...


class OpenAIJsonClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            timeout=60.0,
            max_retries=2,
        )

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
        except RateLimitError as exc:
            raise ModelRequestError(
                "The model provider rate limit was reached after retries. Try again later."
            ) from exc
        except APITimeoutError as exc:
            raise ModelRequestError(
                "The model request timed out. Try again."
            ) from exc
        except APIError as exc:
            raise ModelRequestError(
                f"The model provider request failed ({type(exc).__name__})."
            ) from exc

        if not response.choices:
            raise ModelResponseError("The model returned no response choices.")
        content = response.choices[0].message.content
        if not content:
            raise ModelResponseError("The model returned an empty response.")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelResponseError(
                "The model response was not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ModelResponseError("The model response must be a JSON object.")
        return payload


class OllamaJsonClient:
    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.url = f"{base_url.rstrip('/')}/api/chat"
        self.timeout = timeout

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        request_body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                message = (
                    f"Ollama could not find model '{self.model}'. "
                    f"Run 'ollama pull {self.model}' and try again."
                )
            else:
                message = f"Ollama request failed with HTTP {exc.code}."
            raise ModelRequestError(message) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ModelRequestError(
                "Could not connect to Ollama. Start Ollama and try again."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelResponseError(
                "Ollama returned an invalid response."
            ) from exc

        if not isinstance(body, dict):
            raise ModelResponseError("Ollama response must be a JSON object.")
        message = body.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content:
            raise ModelResponseError("Ollama returned an empty response.")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelResponseError(
                "Ollama did not return valid JSON for the debate."
            ) from exc
        if not isinstance(payload, dict):
            raise ModelResponseError("Ollama response must contain a JSON object.")
        return payload
