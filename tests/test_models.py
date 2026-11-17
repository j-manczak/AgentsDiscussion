import pytest
from pydantic import ValidationError

from config.evaluation_criteria import EVALUATION_CRITERIA
from debate.orchestrator import DebateOrchestrator
from llm.client import ModelResponseError
from models.debate import DebateConfig
from models.evaluation import CriterionScore, JudgeAssessment


def should_reject_same_player_names_ignoring_case_when_configured() -> None:
    with pytest.raises(ValidationError, match="Choose two different players"):
        DebateConfig(player_a="Messi", player_b="  messi  ")


@pytest.mark.parametrize("rounds", [0, 4])
def should_reject_unsupported_round_counts_when_configured(rounds: int) -> None:
    with pytest.raises(ValidationError):
        DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=rounds)


def should_trim_names_and_blank_context_when_configured() -> None:
    config = DebateConfig(
        player_a=" Messi ",
        player_b=" Ronaldo ",
        additional_context="  ",
    )
    assert config.player_a == "Messi"
    assert config.player_b == "Ronaldo"
    assert config.additional_context is None


def should_calculate_weighted_scores_and_a_tie_when_assessment_is_close() -> None:
    config = DebateConfig(player_a="A", player_b="B", rounds=1)
    scores = [
        CriterionScore(
            criterion_name=name,
            weight=weight,
            player_a_score=8,
            player_b_score=7.9,
            explanation="Comparable performance.",
        )
        for name, weight in EVALUATION_CRITERIA
    ]
    assessment = JudgeAssessment(
        criteria_scores=scores,
        final_explanation="The case is effectively tied.",
    )
    result = DebateOrchestrator._build_verdict(config, assessment)
    assert result.player_a_score == 8
    assert result.player_b_score == 7.9
    assert result.winner is None


def should_reject_missing_criteria_when_assessment_is_incomplete() -> None:
    config = DebateConfig(player_a="A", player_b="B", rounds=1)
    assessment = JudgeAssessment(
        criteria_scores=[],
        final_explanation="Incomplete.",
    )
    with pytest.raises(ModelResponseError, match="every evaluation criterion"):
        DebateOrchestrator._build_verdict(config, assessment)
