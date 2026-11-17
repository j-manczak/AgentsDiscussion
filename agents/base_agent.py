from pathlib import Path
from typing import TypeVar

from llm.client import ModelResponseError
from pydantic import BaseModel, ValidationError


PROMPTS_DIRECTORY = Path(__file__).parent / "prompts"
ModelT = TypeVar("ModelT", bound=BaseModel)


def load_prompt(name: str) -> str:
    return (PROMPTS_DIRECTORY / name).read_text(encoding="utf-8")


def validate_response(
    model: type[ModelT],
    payload: dict[str, object],
    agent_label: str,
) -> ModelT:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise ModelResponseError(
            f"{agent_label} returned a response that did not match the required format."
        ) from exc
