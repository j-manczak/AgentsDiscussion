import math
from typing import Sequence

from agents.judge_agent import JudgeAgent
from agents.player_agent import PlayerAgent
from config.evaluation_criteria import EVALUATION_CRITERIA, TIE_THRESHOLD
from llm.client import ModelResponseError
from models.agent import DebateTurn
from models.debate import DebateConfig
from models.evaluation import CriterionScore, JudgeAssessment, JudgeResult


class DebateOutcome:
    def __init__(
        self,
        config: DebateConfig,
        turns: Sequence[DebateTurn],
        verdict: JudgeResult,
    ) -> None:
        self.config = config
        self.turns = list(turns)
        self.verdict = verdict


class DebateOrchestrator:
    def __init__(
        self,
        proponent: PlayerAgent,
        opponent: PlayerAgent,
        judge: JudgeAgent,
    ) -> None:
        self.proponent = proponent
        self.opponent = opponent
        self.judge = judge

    def run(self, config: DebateConfig) -> DebateOutcome:
        turns: list[DebateTurn] = []
        for round_number in range(1, config.rounds + 1):
            prior_rounds = tuple(turns)
            proponent_argument = self.proponent.generate(
                config, round_number, prior_rounds
            )
            opponent_argument = self.opponent.generate(
                config, round_number, prior_rounds
            )
            turns.extend(
                (
                    DebateTurn(
                        round_number=round_number,
                        agent_name="Proponent",
                        player_name=config.player_a,
                        argument=proponent_argument,
                    ),
                    DebateTurn(
                        round_number=round_number,
                        agent_name="Opponent",
                        player_name=config.player_b,
                        argument=opponent_argument,
                    ),
                )
            )

        assessment = self.judge.evaluate(config, turns)
        verdict = self._build_verdict(config, assessment)
        return DebateOutcome(config=config, turns=turns, verdict=verdict)

    @staticmethod
    def _build_verdict(
        config: DebateConfig, assessment: JudgeAssessment
    ) -> JudgeResult:
        expected = dict(EVALUATION_CRITERIA)
        actual_names = [score.criterion_name for score in assessment.criteria_scores]
        if len(actual_names) != len(set(actual_names)) or set(actual_names) != set(
            expected
        ):
            raise ModelResponseError(
                "Judge did not score every evaluation criterion exactly once."
            )

        scores_by_name = {
            score.criterion_name: score for score in assessment.criteria_scores
        }
        normalized_scores: list[CriterionScore] = []
        for name, weight in EVALUATION_CRITERIA:
            score = scores_by_name[name]
            if not math.isclose(score.weight, weight, abs_tol=1e-6):
                raise ModelResponseError(
                    f"Judge returned an invalid weight for '{name}'."
                )
            normalized_scores.append(score)

        player_a_score = sum(
            score.player_a_score * score.weight for score in normalized_scores
        )
        player_b_score = sum(
            score.player_b_score * score.weight for score in normalized_scores
        )
        score_difference = player_a_score - player_b_score
        winner = None
        if abs(score_difference) > TIE_THRESHOLD:
            winner = config.player_a if score_difference > 0 else config.player_b

        return JudgeResult(
            winner=winner,
            player_a_score=round(player_a_score, 2),
            player_b_score=round(player_b_score, 2),
            criteria_scores=normalized_scores,
            strongest_arguments_a=assessment.strongest_arguments_a,
            strongest_arguments_b=assessment.strongest_arguments_b,
            final_explanation=assessment.final_explanation,
            limitations=assessment.limitations,
        )
