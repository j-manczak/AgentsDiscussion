import json
import urllib.error
import urllib.parse
import urllib.request
from typing import TypedDict


WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
FOOTBALL_PLAYER_OCCUPATION = "Q937857"


class PlayerLookupError(RuntimeError):
    pass


class PlayerNotFoundError(ValueError):
    pass


class SearchResult(TypedDict, total=False):
    id: str
    label: str
    description: str
    aliases: list[str]


def _request(parameters: dict[str, str]) -> dict[str, object]:
    url = f"{WIKIDATA_API_URL}?{urllib.parse.urlencode(parameters)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FootballDebateDemo/1.0 (player validation)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PlayerLookupError(
            f"The player lookup service returned HTTP {exc.code}."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PlayerLookupError(
            "Could not reach Wikidata to verify player names. Check your internet "
            "connection and try again."
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlayerLookupError("Wikidata returned an invalid response.") from exc

    if not isinstance(payload, dict):
        raise PlayerLookupError("Wikidata returned an invalid response.")
    return payload


def _search_players(name: str) -> list[SearchResult]:
    payload = _request(
        {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "type": "item",
            "limit": "10",
        }
    )
    results = payload.get("search")
    if not isinstance(results, list):
        raise PlayerLookupError("Wikidata returned an invalid search response.")
    return [result for result in results if isinstance(result, dict)]


def _association_football_player_ids(entity_ids: list[str]) -> set[str]:
    if not entity_ids:
        return set()
    payload = _request(
        {
            "action": "wbgetentities",
            "ids": "|".join(entity_ids),
            "props": "claims",
            "format": "json",
        }
    )
    entities = payload.get("entities")
    if not isinstance(entities, dict):
        raise PlayerLookupError("Wikidata returned an invalid entity response.")
    player_ids: set[str] = set()
    for entity_id, entity in entities.items():
        claims = entity.get("claims") if isinstance(entity, dict) else None
        occupations = claims.get("P106") if isinstance(claims, dict) else None
        if not isinstance(occupations, list):
            continue
        if any(
            isinstance(statement, dict)
            and isinstance(statement.get("mainsnak"), dict)
            and isinstance(statement["mainsnak"].get("datavalue"), dict)
            and isinstance(statement["mainsnak"]["datavalue"].get("value"), dict)
            and statement["mainsnak"]["datavalue"]["value"].get("id")
            == FOOTBALL_PLAYER_OCCUPATION
            for statement in occupations
        ):
            player_ids.add(entity_id)
    return player_ids


def _matches_input(result: SearchResult, name: str) -> bool:
    normalized_name = name.casefold()
    label = result.get("label")
    if isinstance(label, str) and label.casefold() == normalized_name:
        return True
    aliases = result.get("aliases", [])
    return any(
        isinstance(alias, str) and alias.casefold() == normalized_name
        for alias in aliases
    )


def _resolve_name(name: str) -> tuple[str | None, list[str]]:
    results = _search_players(name)
    identified_results = [
        result
        for result in results
        if isinstance(result.get("id"), str)
    ]
    player_ids = _association_football_player_ids(
        [result["id"] for result in identified_results]
    )

    valid_results: list[SearchResult] = []
    for result in identified_results:
        if result["id"] in player_ids:
            valid_results.append(result)

    exact_matches = [result for result in valid_results if _matches_input(result, name)]
    if exact_matches:
        canonical_name = exact_matches[0].get("label")
        if isinstance(canonical_name, str) and canonical_name.strip():
            return canonical_name, []
        return name, []

    suggestions = list(
        dict.fromkeys(
            result["label"]
            for result in valid_results
            if isinstance(result.get("label"), str)
        )
    )
    return None, suggestions[:3]


def resolve_player_pair(player_a: str, player_b: str) -> tuple[str, str]:
    resolved_a, suggestions_a = _resolve_name(player_a)
    resolved_b, suggestions_b = _resolve_name(player_b)
    invalid: list[str] = []
    if resolved_a is None:
        invalid.append(_format_invalid_player(player_a, suggestions_a))
    if resolved_b is None:
        invalid.append(_format_invalid_player(player_b, suggestions_b))
    if invalid:
        raise PlayerNotFoundError(" ".join(invalid))
    if resolved_a is None or resolved_b is None:
        raise PlayerNotFoundError("Both players must be recognized football players.")
    if resolved_a.casefold() == resolved_b.casefold():
        raise PlayerNotFoundError(
            "Both names resolve to the same football player. Choose two different players."
        )
    return resolved_a, resolved_b


def _format_invalid_player(name: str, suggestions: list[str]) -> str:
    message = f"'{name}' was not recognized as an association football player."
    if suggestions:
        message += " Possible matches: " + ", ".join(suggestions) + "."
    return message
