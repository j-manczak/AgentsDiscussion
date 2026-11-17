from pydantic import BaseModel, ConfigDict, Field


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_name: str = Field(min_length=1)
    weight: float = Field(ge=0, le=1)
    player_a_score: float = Field(ge=0, le=10)
    player_b_score: float = Field(ge=0, le=10)
    explanation: str = Field(min_length=1)


class JudgeAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria_scores: list[CriterionScore]
    strongest_arguments_a: list[str] = Field(default_factory=list)
    strongest_arguments_b: list[str] = Field(default_factory=list)
    final_explanation: str = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    winner: str | None
    player_a_score: float = Field(ge=0, le=10)
    player_b_score: float = Field(ge=0, le=10)
    criteria_scores: list[CriterionScore]
    strongest_arguments_a: list[str]
    strongest_arguments_b: list[str]
    final_explanation: str
    limitations: list[str]
