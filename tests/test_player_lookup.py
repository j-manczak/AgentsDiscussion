import pytest

from players.lookup import PlayerNotFoundError, resolve_player_pair


def _football_player_claim() -> dict[str, object]:
    return {
        "P106": [
            {
                "mainsnak": {
                    "datavalue": {
                        "value": {"id": "Q937857"},
                    }
                }
            }
        ]
    }


def should_resolve_exact_player_names_and_use_canonical_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(parameters: dict[str, str]) -> dict[str, object]:
        if parameters["action"] == "wbsearchentities":
            name = parameters["search"]
            player_id, label = (
                ("Q615", "Lionel Messi")
                if name == "Messi"
                else ("Q11571", "Cristiano Ronaldo")
            )
            return {
                "search": [
                    {
                        "id": player_id,
                        "label": label,
                        "aliases": [name],
                    }
                ]
            }
        return {
            "entities": {
                entity_id: {"claims": _football_player_claim()}
                for entity_id in parameters["ids"].split("|")
            }
        }

    monkeypatch.setattr("players.lookup._request", fake_request)

    assert resolve_player_pair("Messi", "Ronaldo") == (
        "Lionel Messi",
        "Cristiano Ronaldo",
    )


def should_reject_unknown_players_and_suggest_verified_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(parameters: dict[str, str]) -> dict[str, object]:
        if parameters["action"] == "wbsearchentities":
            if parameters["search"] == "X":
                return {
                    "search": [
                        {
                            "id": "QXavi",
                            "label": "Xavi",
                            "description": "Spanish footballer",
                        }
                    ]
                }
            return {"search": []}
        return {
            "entities": {
                entity_id: {"claims": _football_player_claim()}
                for entity_id in parameters["ids"].split("|")
            }
        }

    monkeypatch.setattr("players.lookup._request", fake_request)

    with pytest.raises(PlayerNotFoundError, match="Possible matches: Xavi"):
        resolve_player_pair("X", "Y")


def should_reject_two_inputs_that_resolve_to_the_same_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request(parameters: dict[str, str]) -> dict[str, object]:
        if parameters["action"] == "wbsearchentities":
            return {
                "search": [
                    {
                        "id": "Q615",
                        "label": "Lionel Messi",
                        "aliases": [parameters["search"]],
                    }
                ]
            }
        return {
            "entities": {
                entity_id: {"claims": _football_player_claim()}
                for entity_id in parameters["ids"].split("|")
            }
        }

    monkeypatch.setattr("players.lookup._request", fake_request)

    with pytest.raises(PlayerNotFoundError, match="same football player"):
        resolve_player_pair("Messi", "Leo")
