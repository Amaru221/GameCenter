"""Description lookup and its local cache."""

import pytest

from gamecenter.core import metadata
from gamecenter.core.models import Game


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(
        metadata, "cache_path", lambda: tmp_path / "metadata.json"
    )


def _steam_game() -> Game:
    return Game(id="steam:570", title="Dota 2", source="steam", app_id="570")


def _app_payload(**data) -> dict:
    return {"570": {"success": True, "data": data}}


def test_steam_description_is_fetched_and_cached(monkeypatch) -> None:
    calls = []

    def fake_get(url, params, timeout=8):
        calls.append((url, params))
        return _app_payload(
            short_description="A competitive game.",
            developers=["Valve"],
            genres=[{"description": "Action"}, {"description": "Strategy"}],
            release_date={"date": "2013"},
        )

    monkeypatch.setattr(metadata, "_get_json", fake_get)

    data = metadata.fetch(_steam_game(), "es")

    assert data["description"] == "A competitive game."
    assert data["developers"] == "Valve"
    assert data["genres"] == "Action, Strategy"
    assert data["releaseDate"] == "2013"
    assert calls[0][1]["l"] == "spanish"

    cached = metadata.cached(_steam_game(), "es")
    assert cached == data
    # The cached read does not touch the network.
    assert metadata.cached(_steam_game(), "en") is None


def test_non_steam_game_uses_exact_title_search(monkeypatch) -> None:
    searched = []

    def fake_get(url, params, timeout=8):
        if url == metadata._STORE_SEARCH:
            searched.append(params["term"])
            return {"items": [{"type": "app", "name": "Hades", "id": 1145360}]}
        return {
            "1145360": {
                "success": True,
                "data": {
                    "short_description": "Escape the underworld.",
                    "developers": ["Supergiant Games"],
                    "genres": [{"description": "Action"}],
                    "release_date": {"date": "2020"},
                },
            }
        }

    monkeypatch.setattr(metadata, "_get_json", fake_get)
    game = Game(id="epic:hades", title="Hades", source="epic")

    data = metadata.fetch(game, "en")

    assert searched == ["Hades"]
    assert data["description"] == "Escape the underworld."
    assert data["releaseDate"] == "2020"


def test_weak_title_match_is_rejected(monkeypatch) -> None:
    calls = []

    def fake_get(url, params, timeout=8):
        calls.append(url)
        return {"items": [{"type": "app", "name": "Hades II", "id": 1}]}

    monkeypatch.setattr(metadata, "_get_json", fake_get)
    game = Game(id="gog:other", title="Hades", source="gog")

    data = metadata.fetch(game, "en")
    assert data["description"] == ""
    assert len(calls) == 1


def test_missing_description_is_cached(monkeypatch) -> None:
    monkeypatch.setattr(
        metadata, "_get_json", lambda url, params, timeout=8: {"items": []}
    )
    game = Game(id="riot:unknown", title="Unknown Game", source="riot")

    data = metadata.fetch(game, "en")
    assert data["description"] == ""
    assert metadata.cached(game, "en") == {
        "description": "",
        "developers": "",
        "genres": "",
        "releaseDate": "",
    }


def test_html_is_cleaned_and_long_text_is_trimmed(monkeypatch) -> None:
    long_text = "<p>" + ("word " * 300) + "</p>"

    monkeypatch.setattr(
        metadata,
        "_get_json",
        lambda url, params, timeout=8: _app_payload(
            short_description="", detailed_description=long_text
        ),
    )

    data = metadata.fetch(_steam_game(), "en")
    assert "<" not in data["description"]
    assert len(data["description"]) <= metadata.MAX_DESCRIPTION + 1
