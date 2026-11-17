import json

import pytest

from agents.judge_agent import JudgeAgent
from agents.player_agent import PlayerAgent
from config.evaluation_criteria import EVALUATION_CRITERIA
from debate.orchestrator import DebateOrchestrator
from llm.client import ModelRequestError, ModelResponseError
from models.debate import DebateConfig


class FakeModelClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.player_call_count = 0

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        self.calls.append((system_prompt, user_prompt))
        if "neutral, independent judge" in system_prompt:
            return {
                "criteria_scores": [
                    {
                        "criterion_name": name,
                        "weight": weight,
                        "player_a_score": 8,
                        "player_b_score": 7,
                        "explanation": f"Assessment for {name}.",
                    }
                    for name, weight in EVALUATION_CRITERIA
                ],
                "strongest_arguments_a": ["A's strongest case."],
                "strongest_arguments_b": ["B's strongest case."],
                "final_explanation": "A made the stronger case.",
                "limitations": ["Historical comparisons are uncertain."],
            }
        self.player_call_count += 1
        side = "A" if '"defended_player": "Messi"' in user_prompt else "B"
        return {
            "main_claim": f"{side}-argument-{self.player_call_count}",
            "supporting_arguments": [f"Support for {side}."],
            "evidence": [],
            "rebuttals": [],
            "concessions": [],
            "conclusion": f"{side} conclusion.",
        }


def make_orchestrator(client: FakeModelClient) -> DebateOrchestrator:
    return DebateOrchestrator(
        proponent=PlayerAgent(client, "Proponent", "Messi", "Ronaldo"),
        opponent=PlayerAgent(client, "Opponent", "Ronaldo", "Messi"),
        judge=JudgeAgent(client),
    )


def should_keep_agent_order_and_round_limit_when_debate_runs() -> None:
    client = FakeModelClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=2)

    outcome = make_orchestrator(client).run(config)

    assert [(turn.round_number, turn.agent_name) for turn in outcome.turns] == [
        (1, "Proponent"),
        (1, "Opponent"),
        (2, "Proponent"),
        (2, "Opponent"),
    ]
    assert len(outcome.turns) == 2 * config.rounds
    assert "neutral, independent judge" in client.calls[-1][0]
    assert outcome.verdict.winner == "Messi"


def should_pass_opponent_arguments_to_later_turns_when_debate_runs() -> None:
    client = FakeModelClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=2)

    make_orchestrator(client).run(config)

    round_two_proponent_payload = json.loads(client.calls[2][1])
    assert round_two_proponent_payload["previous_round_transcript"][1]["player_name"] == "Ronaldo"
    assert (
        round_two_proponent_payload["previous_round_transcript"][1]["argument"][
            "main_claim"
        ]
        == "B-argument-2"
    )


def should_send_complete_transcript_to_judge_when_debate_finishes() -> None:
    client = FakeModelClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=3)

    make_orchestrator(client).run(config)

    judge_payload = json.loads(client.calls[-1][1])
    assert len(judge_payload["transcript"]) == 6
    assert {turn["round_number"] for turn in judge_payload["transcript"]} == {1, 2, 3}


class InvalidPlayerClient(FakeModelClient):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        if "neutral, independent judge" not in system_prompt:
            return {"main_claim": ""}
        return super().complete_json(system_prompt, user_prompt)


def should_report_invalid_agent_output_when_model_response_is_malformed() -> None:
    client = InvalidPlayerClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=1)

    with pytest.raises(ModelResponseError, match="did not match the required format"):
        make_orchestrator(client).run(config)


class InvalidJudgeOnceClient(FakeModelClient):
    def __init__(self) -> None:
        super().__init__()
        self.judge_call_count = 0

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        if "neutral, independent judge" in system_prompt:
            self.judge_call_count += 1
            if self.judge_call_count == 1:
                return {"criteria_scores": []}
        return super().complete_json(system_prompt, user_prompt)


def should_retry_judge_once_when_its_response_does_not_match_the_schema() -> None:
    client = InvalidJudgeOnceClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=1)

    outcome = make_orchestrator(client).run(config)

    assert client.judge_call_count == 2
    assert outcome.verdict.winner == "Messi"
    assert "did not match the required format" in client.calls[-1][1]


class FailingClient(FakeModelClient):
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        raise ModelRequestError("Provider request failed.")


def should_surface_provider_failures_when_model_request_fails() -> None:
    client = FailingClient()
    config = DebateConfig(player_a="Messi", player_b="Ronaldo", rounds=1)

    with pytest.raises(ModelRequestError, match="Provider request failed"):
        make_orchestrator(client).run(config)
