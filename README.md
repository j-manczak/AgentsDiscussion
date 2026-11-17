# Football Debate

A Streamlit MVP where two independent AI agents argue for different football
players and a third, neutral agent evaluates the complete debate.

## Local setup (free, no API key)

- Python 3.12 or newer
- [Ollama](https://ollama.com/download) installed and running

Download a model once in PowerShell:

```powershell
ollama pull qwen2.5:7b
```

Create the Python environment and install the app:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Ollama is the default provider. No `.env` file or API key is required. The
default model is `qwen2.5:7b`; use `.env` with `OLLAMA_MODEL` to select another
model you've pulled locally, or `OLLAMA_URL` to use a different local Ollama
server. Model downloads use disk space, and generation speed depends on your
computer.

### Optional: OpenAI

To use OpenAI instead, create `.env` and set `LLM_PROVIDER=openai`,
`OPENAI_API_KEY`, and `OPENAI_MODEL`. Never commit `.env` or share your API key.

## Run

```powershell
streamlit run app.py
```

Enter two different association football players and choose one to three rounds.
Before starting, the app verifies the names using Wikidata's free, keyless API.
Unrecognized names are rejected and may include suggestions; a network
connection is required for this check.

1. Opening statements
2. Counterarguments responding to the previous round
3. Final defense

Both player agents receive the same prior-round transcript and criteria. The
orchestrator controls turn order and the round count. After the final round, a
separate judge scores both players against the seven weighted criteria. The app
calculates weighted totals and determines a tie when the difference is at most
0.15 points.

The MVP uses model knowledge and does not independently verify historical
claims. Wikidata is used only to check player identity, not to verify debate
claims. Evidence is therefore not marked verified, and the verdict is an
AI-generated assessment rather than objective truth. Debate history is kept in
the current Streamlit session and is not saved to a database.

## Tests

```powershell
python -m pytest
```

Tests use a fake model client; they do not require an API key or make paid
requests.
