"""SteamGridDB request building and portrait filtering (no network)."""

from gamecenter.core import steamgriddb
from gamecenter.core.models import Game


def test_steam_game_uses_the_app_id(monkeypatch) -> None:
    calls = []

    def fake_get(path, key, params=None):
        calls.append(path)
        return [
            {"id": 1, "url": "u1", "thumb": "t1", "width": 600, "height": 900},
            {"id": 2, "url": "u2", "thumb": "t2", "width": 900, "height": 600},
        ]

    monkeypatch.setattr(steamgriddb, "_get", fake_get)
    game = Game(id="steam:730", title="Counter-Strike 2", source="steam", app_id="730")

    options = steamgriddb.grids_for(game, "key")

    assert calls == ["/grids/steam/730"]
    assert len(options) == 1
    assert options[0]["url"] == "u1"


def test_other_stores_search_by_title(monkeypatch) -> None:
    calls = []

    def fake_get(path, key, params=None):
        calls.append(path)
        if path.startswith("/search/autocomplete/"):
            return [{"id": 42, "name": "Cobalt Frontier"}]
        return [{"id": 7, "url": "u", "thumb": "t", "width": 600, "height": 900}]

    monkeypatch.setattr(steamgriddb, "_get", fake_get)
    game = Game(id="epic:Cobalt", title="Cobalt Frontier", source="epic", app_id="Cobalt")

    options = steamgriddb.grids_for(game, "key")

    assert calls[0].startswith("/search/autocomplete/")
    assert calls[1] == "/grids/game/42"
    assert len(options) == 1


def test_no_portrait_grids(monkeypatch) -> None:
    monkeypatch.setattr(steamgriddb, "_get", lambda *args, **kwargs: [])
    game = Game(id="steam:1", title="Test", source="steam", app_id="1")

    assert steamgriddb.grids_for(game, "key") == []
