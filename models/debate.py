from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DebateConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    player_a: str = Field(min_length=1, max_length=100)
    player_b: str = Field(min_length=1, max_length=100)
    rounds: int = Field(default=3, ge=1, le=3)
    additional_context: str | None = Field(default=None, max_length=2000)

    @field_validator("player_a", "player_b")
    @classmethod
    def player_name_must_not_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("Player names are required.")
        return value

    @field_validator("additional_context")
    @classmethod
    def blank_context_becomes_none(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def players_must_be_different(self) -> "DebateConfig":
        if self.player_a.casefold() == self.player_b.casefold():
            raise ValueError("Choose two different players.")
        return self
