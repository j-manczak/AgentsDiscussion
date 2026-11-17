# PROJECT_SPEC_MULTI_AGENT_FOOTBALL_DEBATE

## 1. Project Goal

Build a Python application in which two independent AI agents debate which of two football players is better or deserves to be considered the greatest player of all time.

The user chooses both players, for example:
- Lionel Messi vs Cristiano Ronaldo
- Pelé vs Diego Maradona
- Zinedine Zidane vs Ronaldinho

The application should present arguments from both sides, responses to the opposing agent's arguments, and a final verdict from a third, independent AI agent acting as a judge.

**This must be a genuine multi-agent debate**, not a single model response pretending to be a conversation between two people. Each agent must have its own role, instructions, debate history, and access to the opponent's arguments.

## 2. Mandatory Instructions for the Coding Agent

Before implementing anything:

1. Inspect the entire repository and existing code.
2. Briefly summarize your understanding of the task.
3. Present the proposed architecture and implementation plan in execution order.
4. Identify the key technical decisions and any unresolved questions.
5. **Stop and wait for the user's explicit approval. Do not write or modify code before the plan is approved.**

After approval:
- implement the project in stages;
- run relevant tests after each major stage;
- do not hide errors or mark unfinished features as complete;
- keep the README and documentation up to date;
- avoid unnecessary complexity and dependencies.

If the repository already contains established conventions or implementation choices, preserve them unless they conflict with the requirements. Do not overwrite existing files without inspecting their contents.

## 3. Proposed Technology Stack

Preferred MVP stack:

- **Python 3.12+**
- **Streamlit** — user interface.
- **OpenAI Python SDK** — communication with language models.
- **Pydantic** — validation of input data and structured agent responses.
- **pytest** — automated tests.
- **python-dotenv** — local configuration through a `.env` file.
- **SQLite** — optional storage of debate history in the MVP.

Design the LLM integration layer so that another model provider can be added later without redesigning the debate logic.

Never hardcode API keys or commit them to the repository. Use environment variables.

Example `.env.example`:

```env
OPENAI_API_KEY=
OPENAI_MODEL=
```

Do not hardcode a specific model name. The model must be configurable.

## 4. Logical Architecture

The application should consist of the following components.

### 4.1. Debate Orchestrator

The central component responsible for controlling the debate.

Responsibilities:
- receive and validate user input;
- create two agents with their respective roles;
- pass arguments between the agents;
- control the order of responses;
- enforce the configured number of rounds;
- store the debate transcript;
- pass the complete debate to the Judge;
- return the final result to the user interface.

The Orchestrator, not the agents, controls the process. Agents must not independently end the debate or change the number of rounds.

### 4.2. Agent A — Proponent

The agent representing the first player.

Example: if the user selects Messi vs Ronaldo, Agent A argues that Messi is the better player.

Responsibilities:
- build logical arguments;
- use statistics, achievements, and historical context;
- respond to specific arguments made by Agent B;
- identify weaknesses in the opponent's reasoning;
- avoid repeating the same arguments;
- acknowledge valid points made by the opponent without abandoning its assigned position.

### 4.3. Agent B — Opponent

The agent representing the second player.

It has responsibilities equivalent to Agent A, but defends the second player.

Both agents must have comparable levels of detail, standards of reasoning, and access to information. Neither agent should receive extra data or instructions that favor its assigned player.

### 4.4. Judge — Neutral Evaluator

A third agent that does not participate in the debate.

The Judge must:
- remain neutral and avoid favoring either player in advance;
- analyze the arguments from both sides;
- distinguish facts from opinions;
- evaluate the quality of reasoning, not just the number of arguments;
- identify the strongest and weakest arguments;
- assign scores using explicit criteria;
- deliver a verdict with an explanation.

The Judge must not automatically select the player whose agent used more persuasive language. It should evaluate the substantive quality of the arguments and the accuracy of the information used.

## 5. Debate Flow

By default, the debate consists of a maximum of 3 rounds. The user can change the number of rounds before starting.

Proposed flow:

### Round 1 — Opening Statements

- Agent A presents its main case for Player A.
- Agent B presents its main case for Player B.
- Each agent should provide several distinct arguments.

### Round 2 — Counterarguments

- Agent A receives Agent B's arguments and responds to them.
- Agent B receives Agent A's arguments and responds to them.
- Each agent should identify which opposing arguments it disagrees with and explain why.

### Round 3 — Final Defense

- Both agents present their closing arguments.
- They should address the most important points of disagreement.
- They should avoid introducing numerous unrelated arguments.

After the final round, the Orchestrator closes the debate and sends the full transcript to the Judge.

In the MVP, the order and number of responses must be deterministic and controlled by the Orchestrator.

## 6. Evaluation Criteria

The Judge should score each player from 0 to 10 for every criterion.

Initial weights:

| Criterion | Weight |
|---|---:|
| Individual skill and technique | 20% |
| Statistics and achievements | 20% |
| Team impact and contribution to team play | 15% |
| Peak performance | 15% |
| Longevity and consistency | 10% |
| Performance in the most important matches | 10% |
| Historical impact on football | 10% |
| **Total** | **100%** |

Store the weights in a single configuration location so they can be changed later.

Weighted score:

`score = sum(criterion_score * criterion_weight)`

The Judge should return:
- each player's score for every criterion;
- the final weighted score for both players;
- the winner;
- a tie result if the score difference is sufficiently small;
- an explanation for every score;
- the strongest arguments from the winning side;
- particularly strong arguments from the losing side;
- a short final summary.

The result must not be presented as objective truth. It is an AI-generated assessment based on the selected criteria and the arguments presented.

## 7. Information Accuracy and Sources

The debate requires historical and statistical information. Agents must not present invented statistics as facts.

Requirements:
- distinguish facts, estimates, and opinions;
- explicitly indicate uncertainty when an agent is unsure about a statistic or record;
- never invent quotations, sources, records, or statistics;
- account for differences between eras, positions, roles, and team contexts;
- do not compare raw statistics from different eras without considering context.

In the MVP, agents may rely on the model's knowledge, but they must communicate uncertainty and must not fabricate citations.

Design the architecture so that the following can be added in a later stage:
- web search;
- a football statistics database;
- a shared package of verified data provided to both agents;
- explicit sources and links for factual claims.

If sources are added, both agents and the Judge must use the same dataset. Never invent URLs or claim that information has been verified when it has not.

## 8. User Interface

The interface should be simple, clear, and modern.

### Debate Configuration Screen

The user should be able to:
- enter the first player's full name;
- enter the second player's full name;
- optionally provide additional context or debate criteria;
- select the number of rounds (3 by default);
- start the debate.

Validation:
- both player names are required;
- the two players must be different;
- the number of rounds must be within the supported range;
- errors must be displayed clearly.

### Debate Screen

Display:
- both players' names;
- the current round number;
- Agent A's and Agent B's statements;
- a clear indication of which player each agent is defending;
- a clear separation between rounds;
- the generation status.

Do not expose raw system prompts or API keys to the user.

### Verdict Screen

Display:
- the debate winner;
- the final scores of both players;
- a score table broken down by criteria;
- the Judge's explanation;
- the strongest arguments from both sides;
- any uncertainty or limitations in the available data.

Ensure the interface continues to behave correctly if a model request fails.

## 9. Data Contracts

Use Pydantic to define and validate data structures.

The following example models may be adjusted during implementation planning.

### DebateConfig

- `player_a: str`
- `player_b: str`
- `rounds: int`
- `additional_context: str | None`

### AgentArgument

- `main_claim: str`
- `supporting_arguments: list[str]`
- `evidence: list[EvidenceItem]`
- `rebuttals: list[str]`
- `concessions: list[str]`
- `conclusion: str`

### EvidenceItem

- `claim: str`
- `source_name: str | None`
- `source_url: str | None`
- `confidence: str`
- `is_verified: bool`

Do not mark information as verified unless the application has actually performed verification.

### DebateTurn

- `round_number: int`
- `agent_name: str`
- `player_name: str`
- `argument: AgentArgument`
- `created_at: datetime`

### JudgeResult

- `winner: str | None`
- `player_a_score: float`
- `player_b_score: float`
- `criteria_scores: list[CriterionScore]`
- `strongest_arguments_a: list[str]`
- `strongest_arguments_b: list[str]`
- `final_explanation: str`
- `limitations: list[str]`

### CriterionScore

- `criterion_name: str`
- `weight: float`
- `player_a_score: float`
- `player_b_score: float`
- `explanation: str`

Validate score ranges, the sum of criterion weights, and model responses against the expected schemas.

## 10. Agent Prompts

Keep prompts in separate files or modules. Do not put all prompt logic inside the Streamlit interface.

### Agent A and Agent B Prompts

Each prompt must clearly specify:
- the player the agent is defending;
- the opposing player;
- the goal of the debate;
- the comparison criteria;
- factual accuracy requirements;
- the need to respond to the opponent's arguments;
- the prohibition against repeating arguments without adding value;
- the required response format, compatible with the Pydantic schema.

An agent should be biased toward its assigned player, but factual claims must remain honest. It must not deliberately misrepresent data.

### Judge Prompt

The Judge must:
- remain neutral;
- evaluate both sides using identical criteria;
- avoid awarding points merely for longer statements;
- distinguish argument quality from rhetorical style;
- identify uncertain or unsupported factual claims;
- justify its scores;
- return a result that conforms to the data schema.

## 11. Suggested Project Structure

Adapt this structure to the existing repository while preserving a clear separation of responsibilities.

```text
football-debate/
├── app.py
├── config/
│   ├── settings.py
│   └── evaluation_criteria.py
├── agents/
│   ├── base_agent.py
│   ├── player_agent.py
│   ├── judge_agent.py
│   └── prompts/
│       ├── player_agent.txt
│       └── judge_agent.txt
├── debate/
│   ├── orchestrator.py
│   ├── debate_service.py
│   └── turn_manager.py
├── models/
│   ├── debate.py
│   ├── agent.py
│   └── evaluation.py
├── llm/
│   ├── client.py
│   └── response_parser.py
├── persistence/
│   └── debate_repository.py
├── tests/
│   ├── test_orchestrator.py
│   ├── test_agents.py
│   ├── test_judge.py
│   └── test_models.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 12. Error Handling and Security

Implement:
- handling of API errors and rate limits;
- reasonable timeouts for model requests;
- a limited number of retries;
- validation of model responses;
- clear error messages for users;
- protection of secrets and `.env` files;
- logging that does not expose API keys or other secrets.

An invalid response from one agent must not silently corrupt the entire debate.

## 13. Testing

Tests should cover at least:

1. Debate configuration validation.
2. Rejection of identical player names.
3. Correct order of agent statements.
4. Enforcement of the round limit by the Orchestrator.
5. Passing the opponent's arguments into the next response.
6. Correct submission of the full debate to the Judge.
7. Validation of scores and criterion weights.
8. Handling of invalid model responses.
9. Handling of API errors.
10. An end-to-end debate flow using mocked model responses.

Unit tests must not require a real API key or trigger paid LLM requests.

Use clear test names following the `should_[expected_behavior]_when_[condition]` convention.

## 14. MVP Acceptance Criteria

The MVP is complete when:

- the user can enter any pair of football players;
- the user can select the number of rounds;
- the application creates two agents with distinct roles;
- agents generate arguments and respond to the opponent's arguments;
- the Orchestrator controls the order and number of rounds;
- the Judge analyzes the complete debate and delivers an explained verdict;
- evaluation results are displayed using the defined criteria;
- the application handles API errors and invalid responses;
- unit and integration tests pass;
- the project can be launched by following the README instructions.

## 15. Out of Scope for the First MVP

Do not implement the following without prior approval:
- user accounts and authentication;
- subscriptions and payment systems;
- advanced RAG;
- automatic ingestion of large football datasets;
- training custom models;
- multiple simultaneous debates;
- extensive administration features.

The architecture may allow future extensions, but the priority is a working, testable MVP.

## 16. Possible Future Enhancements

After the MVP is complete, consider:
- statistical sources and web search;
- a database of players and their achievements;
- user-configurable evaluation weights;
- different models for individual agents;
- different personalities and debate styles;
- debates involving more than two players;
- exporting debates to Markdown or PDF;
- debate history and comparison;
- visualization of score changes after each round;
- the ability for users to provide facts and sources manually.

## 17. First Step After Plan Approval

Once the user approves the plan:

1. Create the minimal project structure.
2. Implement Pydantic models and configuration.
3. Implement the LLM integration layer.
4. Implement the agents and prompts.
5. Implement the Orchestrator and round flow.
6. Implement the Judge and scoring.
7. Build the Streamlit interface.
8. Add tests.
9. Prepare the README with installation and run instructions.

After each stage, provide a short summary of completed work and test results.

**Most important: present the plan first and wait for approval. Do not start implementation autonomously.**
