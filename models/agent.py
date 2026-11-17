from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    claim: str = Field(min_length=1)
    source_name: str | None = None
    source_url: str | None = None
    confidence: Literal["high", "medium", "low", "unknown"] = "unknown"
    is_verified: bool = False


class AgentArgument(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    main_claim: str = Field(min_length=1)
    supporting_arguments: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    rebuttals: list[str] = Field(default_factory=list)
    concessions: list[str] = Field(default_factory=list)
    conclusion: str = Field(min_length=1)


class DebateTurn(BaseModel):
    round_number: int = Field(ge=1, le=3)
    agent_name: Literal["Proponent", "Opponent"]
    player_name: str = Field(min_length=1)
    argument: AgentArgument
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
