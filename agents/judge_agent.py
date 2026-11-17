import json
from typing import Sequence

from agents.base_agent import load_prompt, validate_response
from config.evaluation_criteria import EVALUATION_CRITERIA
from llm.client import JsonModelClient, ModelResponseError
from models.agent import DebateTurn
from models.debate import DebateConfig
from models.evaluation import JudgeAssessment


class JudgeAgent:
    def __init__(self, client: JsonModelClient) -> None:
        self.client = client
        self.system_prompt = load_prompt("judge_agent.txt")

    def evaluate(
        self, config: DebateConfig, turns: Sequence[DebateTurn]
    ) -> JudgeAssessment:
        transcript = [turn.model_dump(mode="json") for turn in turns]
        user_payload = {
            "player_a": config.player_a,
            "player_b": config.player_b,
            "evaluation_criteria": [
                {"name": name, "weight": weight}
                for name, weight in EVALUATION_CRITERIA
            ],
            "transcript": transcript,
        }
        payload = self.client.complete_json(
            self.system_prompt,
            json.dumps(user_payload, ensure_ascii=False, indent=2),
        )
        try:
            return validate_response(JudgeAssessment, payload, "Judge")
        except ModelResponseError:
            repair_prompt = (
                json.dumps(user_payload, ensure_ascii=False, indent=2)
                + "\n\nYour previous response did not match the required format. "
                "Correct it and return only one JSON object that satisfies the "
                "required schema. Include every evaluation criterion exactly once."
            )
            repaired_payload = self.client.complete_json(
                self.system_prompt,
                repair_prompt,
            )
            return validate_response(JudgeAssessment, repaired_payload, "Judge")
