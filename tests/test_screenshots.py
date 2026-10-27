"""Screenshot preferences, capture and filename handling."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from gamecenter.core.preferences import Preferences
from gamecenter.core.screenshots import QT_SEQUENCES, ScreenshotManager


class FakeSessions:
    def __init__(self, titles: list[str]) -> None:
        self._titles = titles

    @property
    def list(self) -> list[dict]:
        return [{"title": title} for title in self._titles]


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_shortcut_preference_defaults_and_validates(tmp_path: Path) -> None:
    prefs = Preferences(tmp_path / "settings.json")

    assert prefs.screenshot_shortcut == "ctrl+pagedown"
    assert QT_SEQUENCES[prefs.screenshot_shortcut] == "Ctrl+PageDown"

    prefs.screenshot_shortcut = "f12"
    assert prefs.screenshot_shortcut == "f12"

    prefs.screenshot_shortcut = "not-a-shortcut"
    assert prefs.screenshot_shortcut == "f12"

    prefs.screenshot_shortcut = "none"
    assert prefs.screenshot_shortcut == "none"


def test_capture_saves_a_png_for_the_running_game(app, tmp_path: Path, monkeypatch) -> None:
    from PySide6.QtGui import QColor, QPixmap

    prefs = Preferences(tmp_path / "settings.json")
    manager = ScreenshotManager(
        prefs,
        FakeSessions(["Alpha Quest"]),
        directory=tmp_path / "screenshots",
        register_hotkey=False,
    )
    pixmap = QPixmap(32, 24)
    pixmap.fill(QColor("#123456"))
    monkeypatch.setattr(manager, "_grab", lambda: pixmap)

    saved: list[str] = []
    manager.saved.connect(saved.append)

    path = manager.captureIfPlaying()

    assert path
    assert Path(path).is_file()
    assert Path(path).name.startswith("Alpha-Quest-")
    assert Path(path).suffix == ".png"
    assert saved == [path]


def test_capture_is_ignored_without_a_game(app, tmp_path: Path, monkeypatch) -> None:
    prefs = Preferences(tmp_path / "settings.json")
    manager = ScreenshotManager(
        prefs,
        FakeSessions([]),
        directory=tmp_path / "screenshots",
        register_hotkey=False,
    )
    monkeypatch.setattr(
        manager, "_grab", lambda: pytest.fail("no screenshot expected")
    )

    assert manager.captureIfPlaying() == ""


def test_capture_always_works_when_requested(app, tmp_path: Path, monkeypatch) -> None:
    from PySide6.QtGui import QColor, QPixmap

    prefs = Preferences(tmp_path / "settings.json")
    manager = ScreenshotManager(
        prefs,
        FakeSessions([]),
        directory=tmp_path / "screenshots",
        register_hotkey=False,
    )
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor("#abcdef"))
    monkeypatch.setattr(manager, "_grab", lambda: pixmap)

    path = manager.capture()

    assert path
    assert Path(path).name.startswith("GameCenter-")
