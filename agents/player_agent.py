import json
from typing import Sequence

from agents.base_agent import load_prompt, validate_response
from config.evaluation_criteria import EVALUATION_CRITERIA
from debate.rounds import ROUND_NAMES
from llm.client import JsonModelClient, ModelResponseError
from models.agent import AgentArgument, DebateTurn
from models.debate import DebateConfig


class PlayerAgent:
    def __init__(
        self,
        client: JsonModelClient,
        agent_name: str,
        defended_player: str,
        opposing_player: str,
    ) -> None:
        self.client = client
        self.agent_name = agent_name
        self.defended_player = defended_player
        self.opposing_player = opposing_player
        self.system_prompt = load_prompt("player_agent.txt").replace(
            "{role}", agent_name
        )

    def generate(
        self,
        config: DebateConfig,
        round_number: int,
        previous_turns: Sequence[DebateTurn],
    ) -> AgentArgument:
        transcript = [turn.model_dump(mode="json") for turn in previous_turns]
        user_payload = {
            "agent_name": self.agent_name,
            "defended_player": self.defended_player,
            "opposing_player": self.opposing_player,
            "round_number": round_number,
            "round_name": ROUND_NAMES[round_number],
            "total_rounds": config.rounds,
            "evaluation_criteria": [
                {"name": name, "weight": weight}
                for name, weight in EVALUATION_CRITERIA
            ],
            "additional_context": config.additional_context,
            "previous_round_transcript": transcript,
        }
        payload = self.client.complete_json(
            self.system_prompt,
            json.dumps(user_payload, ensure_ascii=False, indent=2),
        )
        return validate_response(AgentArgument, payload, self.agent_name)
