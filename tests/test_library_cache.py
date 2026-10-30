"""The bootstrap cache that lets the window paint before the scan finishes."""

from __future__ import annotations

import json

from gamecenter.core import library_cache
from gamecenter.core.models import Game


def _sample(tmp_path) -> list[Game]:
    return [
        Game(
            id="steam:1",
            title="Alpha Quest",
            source="steam",
            app_id="123",
            install_dir=tmp_path / "Alpha",
            launch_uri="steam://rungameid/123",
            size_bytes=10 * 1024 ** 3,
            last_played=1_700_000_000,
            playtime_minutes=42,
        ),
        Game(
            id="epic:2",
            title="Beta Racer",
            source="epic",
            executable=tmp_path / "Beta" / "beta.exe",
            launch_args=("-dx11", "--fullscreen"),
            installed=False,
        ),
    ]


def test_round_trip_keeps_every_field(tmp_path) -> None:
    path = tmp_path / "library_cache.json"

    assert library_cache.save(_sample(tmp_path), path)
    assert library_cache.load(path) == _sample(tmp_path)


def test_missing_or_corrupt_cache_is_empty(tmp_path) -> None:
    assert library_cache.load(tmp_path / "missing.json") == []

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert library_cache.load(broken) == []

    array = tmp_path / "array.json"
    array.write_text("[]", encoding="utf-8")
    assert library_cache.load(array) == []


def test_unknown_future_version_is_ignored(tmp_path) -> None:
    path = tmp_path / "future.json"
    path.write_text(
        json.dumps({"version": library_cache.VERSION + 1, "games": []}),
        encoding="utf-8",
    )

    assert library_cache.load(path) == []


def test_invalid_entries_are_skipped(tmp_path) -> None:
    path = tmp_path / "partial.json"
    path.write_text(
        json.dumps(
            {
                "version": library_cache.VERSION,
                "games": [
                    {"id": "steam:1", "title": "Good", "source": "steam"},
                    {"id": "", "title": "No id", "source": "steam"},
                    {"id": "steam:3", "title": "", "source": "steam"},
                    {"id": "steam:4", "title": "No source"},
                    "not a dict",
                ],
            }
        ),
        encoding="utf-8",
    )

    games = library_cache.load(path)

    assert [game.id for game in games] == ["steam:1"]
    assert games[0].installed is True


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path) -> None:
    path = tmp_path / "library_cache.json"

    assert library_cache.save(_sample(tmp_path), path)

    assert path.is_file()
    assert not (tmp_path / "library_cache.json.tmp").exists()


def test_default_path_uses_config_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(library_cache, "config_dir", lambda: tmp_path)

    assert library_cache.cache_path() == tmp_path / library_cache.FILENAME
