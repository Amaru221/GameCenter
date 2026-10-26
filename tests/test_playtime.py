"""Playtime files for non-Steam games."""

import pytest

from gamecenter.core import playtime
from gamecenter.core.models import Game


@pytest.fixture(autouse=True)
def isolated_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(playtime, "_fallback_path", lambda: tmp_path / "fallback.json")
    monkeypatch.setattr(playtime, "history_path", lambda: tmp_path / "history.json")


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


def test_fallback_when_the_game_has_no_folder(tmp_path) -> None:
    game = Game(id="battlenet:1", title="Test", source="battlenet")

    playtime.add_seconds(game, 60)

    assert playtime.seconds_for(game) == 60
    assert playtime.minutes_for(game) == 1
    assert (tmp_path / "fallback.json").is_file()


def test_fallback_recovers_after_losing_the_root_file(tmp_path) -> None:
    folder = tmp_path / "Game"
    folder.mkdir()
    game = _game(folder)

    playtime.add_seconds(game, 120)
    (folder / playtime.FILENAME).unlink()  # simulate an uninstall

    assert playtime.seconds_for(game) == 120  # read from the mirror
    assert playtime.restore_to_root(game) is True
    assert (folder / playtime.FILENAME).is_file()
    assert playtime.seconds_for(game) == 120


def test_manual_game_moved_to_another_folder_matches_by_title(tmp_path) -> None:
    old = Game(id="local:old-123", title="My Game", source="local")
    playtime._fallback_write(
        old.id,
        {
            "seconds": 3600,
            "sessions": 2,
            "last_played": 123,
            "title": "My Game",
            "source": "local",
        },
    )

    folder = tmp_path / "NewFolder"
    folder.mkdir()
    moved = Game(id="local:new-456", title="My Game", source="local", install_dir=folder)

    assert playtime.seconds_for(moved) == 3600
    assert playtime.restore_to_root(moved) is True
    assert (folder / playtime.FILENAME).is_file()


def test_fallback_records_the_title(tmp_path) -> None:
    folder = tmp_path / "Game"
    folder.mkdir()
    game = _game(folder)

    playtime.add_seconds(game, 60)

    entry = playtime._fallback_read(game.id)
    assert entry["title"] == "Test"
    assert entry["source"] == "epic"


def test_restore_does_not_overwrite_root_data(tmp_path) -> None:
    folder = tmp_path / "Game"
    folder.mkdir()
    game = _game(folder)

    playtime.add_seconds(game, 60)
    (folder / playtime.FILENAME).write_text('{"seconds": 999}', encoding="utf-8")

    assert playtime.restore_to_root(game) is False
    assert playtime.seconds_for(game) == 999


def test_missing_folder_does_not_create_it(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(playtime, "_fallback_path", lambda: tmp_path / "playtime.json")
    folder = tmp_path / "Missing"
    game = _game(folder)

    playtime.add_seconds(game, 60)

    assert not folder.exists()
    assert playtime.seconds_for(game) == 60


def test_history_is_newest_first(tmp_path) -> None:
    game = _game(tmp_path)

    playtime.record_session(game, 1_700_000_000, 60)
    playtime.record_session(game, 1_700_000_100, 120)
    playtime.record_session(game, 1_700_000_200, 30)

    history = playtime.history_for(game)
    assert [item["start"] for item in history] == [
        1_700_000_200,
        1_700_000_100,
        1_700_000_000,
    ]
    assert [item["seconds"] for item in history] == [30, 120, 60]


def test_history_is_trimmed(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(playtime, "MAX_HISTORY", 2)
    game = _game(tmp_path)

    for second in range(4):
        playtime.record_session(game, 1_700_000_000 + second, 60)

    history = playtime.history_for(game)
    assert len(history) == 2
    assert [item["start"] for item in history] == [
        1_700_000_003,
        1_700_000_002,
    ]


def test_steam_sessions_still_get_history(tmp_path) -> None:
    game = _game(tmp_path, source="steam")

    playtime.record_session(game, 1_700_000_000, 300)

    assert playtime.seconds_for(game) == 0
    assert len(playtime.history_for(game)) == 1


def test_history_ignores_empty_or_invalid_sessions(tmp_path) -> None:
    game = _game(tmp_path)

    playtime.record_session(game, 1_700_000_000, 0)
    playtime.record_session(game, 1_700_000_000, 1)

    history = playtime.history_for(game)
    assert len(history) == 1
    assert history[0]["seconds"] == 1
