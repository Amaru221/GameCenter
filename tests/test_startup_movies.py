"""Bundled and user-imported startup movies for Big Picture."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QUrl

from gamecenter.core import startup_movies
from gamecenter.core.preferences import Preferences


def _video(folder: Path, name: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(b"video")
    return path


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    bundled = tmp_path / "startup-movies"
    custom = tmp_path / "custom-movies"
    monkeypatch.setattr(startup_movies, "bundle_dir", lambda: bundled)
    monkeypatch.setattr(startup_movies, "custom_dir", lambda: custom)
    _video(bundled, "cyberpunk.webm")
    _video(bundled, "star_wars.webm")
    _video(custom, "my_intro.mp4")
    return bundled, custom


def test_list_movies_puts_bundled_first_and_pretty_prints_names(dirs) -> None:
    movies = startup_movies.list_movies()

    assert [movie["id"] for movie in movies] == [
        "default:cyberpunk.webm",
        "default:star_wars.webm",
        "custom:my_intro.mp4",
    ]
    assert movies[0]["name"] == "Cyberpunk"
    assert movies[1]["name"] == "Star Wars"
    assert movies[2]["custom"] is True
    assert movies[0]["url"].startswith("file:")


def test_import_movie_copies_into_the_custom_folder(dirs) -> None:
    _bundled, custom = dirs
    source = _video(dirs[0].parent, "new_intro.webm")

    movie = startup_movies.import_movie(source)

    assert movie["custom"] is True
    assert movie["name"] == "New Intro"
    copied = custom / "new_intro.webm"
    assert copied.is_file()
    assert copied.read_bytes() == source.read_bytes()


def test_import_movie_rejects_missing_and_unsupported_files(dirs) -> None:
    with pytest.raises(ValueError):
        startup_movies.import_movie(dirs[0] / "missing.webm")

    text = dirs[0].parent / "notes.txt"
    text.write_text("not a video", encoding="utf-8")
    with pytest.raises(ValueError):
        startup_movies.import_movie(text)


def test_remove_movie_only_removes_custom_entries(dirs) -> None:
    assert startup_movies.remove_movie("default:cyberpunk.webm") is False

    assert startup_movies.remove_movie("custom:my_intro.mp4") is True
    assert not (dirs[1] / "my_intro.mp4").exists()


def test_manager_persists_selection_and_enabled_switch(dirs, tmp_path, monkeypatch) -> None:
    prefs = Preferences(tmp_path / "settings.json")
    manager = startup_movies.StartupMovieManager(prefs)

    assert manager.selected == "default:cyberpunk.webm"
    assert len(manager.options) == 3
    assert manager.currentName == "Cyberpunk"
    assert manager.currentUrl.startswith("file:")

    manager.setSelected("default:star_wars.webm")
    manager.setEnabled(False)
    assert manager.selected == "default:star_wars.webm"
    assert manager.enabled is False

    again = Preferences(tmp_path / "settings.json")
    assert again.startup_movie == "default:star_wars.webm"
    assert again.startup_movie_enabled is False


def test_manager_ready_respects_enabled_and_suppression(dirs, tmp_path, monkeypatch) -> None:
    prefs = Preferences(tmp_path / "settings.json")
    manager = startup_movies.StartupMovieManager(prefs)

    monkeypatch.setenv("QT_QPA_PLATFORM", "win32")
    monkeypatch.delenv("GC_NO_STARTUP_MOVIE", raising=False)
    assert manager.ready is True

    manager.setEnabled(False)
    assert manager.ready is False

    manager.setEnabled(True)
    monkeypatch.setenv("GC_NO_STARTUP_MOVIE", "1")
    assert manager.ready is False


def test_manager_imports_and_removes_a_custom_movie(dirs, tmp_path, monkeypatch) -> None:
    prefs = Preferences(tmp_path / "settings.json")
    manager = startup_movies.StartupMovieManager(prefs)
    source = _video(dirs[0].parent, "holiday.webm")

    assert manager.importMovie(QUrl.fromLocalFile(str(source)).toString()) is True
    assert manager.selectedIsCustom is True
    assert manager.selected == "custom:holiday.webm"
    assert manager.enabled is True

    manager.removeSelected()
    assert manager.selectedIsCustom is False
    assert manager.selected == "default:cyberpunk.webm"


def test_manager_reports_an_unsupported_import(dirs, tmp_path) -> None:
    prefs = Preferences(tmp_path / "settings.json")
    manager = startup_movies.StartupMovieManager(prefs)
    text = dirs[0].parent / "notes.txt"
    text.write_text("not a video", encoding="utf-8")
    errors = []
    manager.failed.connect(errors.append)

    assert manager.importMovie(str(text)) is False
    assert errors
    assert manager.error
