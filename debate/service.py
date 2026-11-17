from agents.judge_agent import JudgeAgent
from agents.player_agent import PlayerAgent
from config.settings import get_settings
from debate.orchestrator import DebateOrchestrator, DebateOutcome
from llm.client import JsonModelClient, OllamaJsonClient, OpenAIJsonClient
from models.debate import DebateConfig
from players.lookup import resolve_player_pair


def run_debate(config: DebateConfig) -> DebateOutcome:
    player_a, player_b = resolve_player_pair(config.player_a, config.player_b)
    config = config.model_copy(update={"player_a": player_a, "player_b": player_b})
    settings = get_settings()
    client: JsonModelClient
    if settings.provider == "ollama":
        client = OllamaJsonClient(
            model=settings.model,
            base_url=settings.ollama_url,
        )
    else:
        client = OpenAIJsonClient(api_key=settings.openai_api_key, model=settings.model)
    orchestrator = DebateOrchestrator(
        proponent=PlayerAgent(client, "Proponent", config.player_a, config.player_b),
        opponent=PlayerAgent(client, "Opponent", config.player_b, config.player_a),
        judge=JudgeAgent(client),
    )
    return orchestrator.run(config)
