"""Playtime files for non-Steam games."""

from gamecenter.core import playtime
from gamecenter.core.models import Game


def _game(folder, source="epic") -> Game:
    return Game(id=f"{source}:1", title="Test", source=source, install_dir=folder)


def test_writes_in_the_game_root(tmp_path) -> None:
    folder = tmp_path / "Game"
    folder.mkdir()
    game = _game(folder)

    playtime.add_seconds(game, 90)
    playtime.add_seconds(game, 30)

    assert playtime.seconds_for(game) == 120
    assert playtime.minutes_for(game) == 2
    stored = folder / playtime.FILENAME
    assert stored.is_file()
    assert '"seconds": 120' in stored.read_text(encoding="utf-8")
    assert playtime.summary_for(game)["sessions"] == 2


def test_steam_is_never_written(tmp_path) -> None:
    game = _game(tmp_path, source="steam")

    playtime.add_seconds(game, 300)

    assert playtime.seconds_for(game) == 0
    assert not (tmp_path / playtime.FILENAME).exists()


def test_fallback_when_the_game_has_no_folder(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(playtime, "_fallback_path", lambda: tmp_path / "playtime.json")
    game = Game(id="battlenet:1", title="Test", source="battlenet")

    playtime.add_seconds(game, 60)

    assert playtime.seconds_for(game) == 60
    assert playtime.minutes_for(game) == 1
    assert (tmp_path / "playtime.json").is_file()


def test_missing_folder_does_not_create_it(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(playtime, "_fallback_path", lambda: tmp_path / "playtime.json")
    folder = tmp_path / "Missing"
    game = _game(folder)

    playtime.add_seconds(game, 60)

    assert not folder.exists()
    assert playtime.seconds_for(game) == 60
