"""Screenshot preferences, capture and filename handling."""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from gamecenter.core import screenshot_store, shortcuts
from gamecenter.core.preferences import Preferences
from gamecenter.core.screenshots import ScreenshotManager


class FakeSessions:
    def __init__(self, titles: list[str]) -> None:
        self._titles = titles

    @property
    def list(self) -> list[dict]:
        return [
            {
                "id": f"s{index + 1}",
                "gameId": "steam:1",
                "title": title,
                "startedAt": 1000 + index,
            }
            for index, title in enumerate(self._titles)
        ]


@pytest.fixture(autouse=True)
def isolate_index(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        screenshot_store, "index_path", lambda: tmp_path / "screenshots.json"
    )


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_shortcut_preference_defaults_and_validates(tmp_path: Path) -> None:
    prefs = Preferences(tmp_path / "settings.json")

    assert prefs.screenshot_shortcut == "Ctrl+PgDown"
    assert shortcuts.normalize(prefs.screenshot_shortcut) == "Ctrl+PgDown"
    assert shortcuts.display(prefs.screenshot_shortcut) == "Ctrl+Page Down"

    prefs.screenshot_shortcut = "F12"
    assert prefs.screenshot_shortcut == "F12"

    prefs.screenshot_shortcut = "not-a-shortcut"
    assert prefs.screenshot_shortcut == "F12"

    prefs.screenshot_shortcut = "Ctrl+Alt+P"
    assert prefs.screenshot_shortcut == "Ctrl+Alt+P"

    prefs.screenshot_shortcut = "none"
    assert prefs.screenshot_shortcut == ""
    assert shortcuts.normalize("") == ""


def test_legacy_shortcut_values_are_migrated(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"screenshotShortcut": "ctrl+pagedown"}', encoding="utf-8")
    assert Preferences(path).screenshot_shortcut == "Ctrl+PgDown"

    path.write_text('{"screenshotShortcut": "printscreen"}', encoding="utf-8")
    assert Preferences(path).screenshot_shortcut == "Print"


def test_shortcuts_only_allows_safe_combinations() -> None:
    assert shortcuts.normalize("Ctrl+Shift+S") == "Ctrl+Shift+S"
    assert shortcuts.normalize("shift+ctrl+s") == "Ctrl+Shift+S"
    assert shortcuts.normalize("Alt+F4") == "Alt+F4"
    assert shortcuts.normalize("F8") == "F8"
    assert shortcuts.normalize("Print") == "Print"
    # Plain letters would hijack the whole desktop.
    assert shortcuts.normalize("A") is None
    assert shortcuts.normalize("Ctrl") is None
    assert shortcuts.normalize("nonsense") is None

    assert shortcuts.to_vk("Ctrl+PgDown") == (2, 0x22)
    assert shortcuts.to_vk("F12") == (0, 0x7B)
    assert shortcuts.to_vk("Ctrl+Alt+P") == (3, 0x50)
    assert shortcuts.to_vk("A") is None


def test_keyboard_recording_captures_the_combination(app, tmp_path: Path) -> None:
    from PySide6.QtCore import Qt

    prefs = Preferences(tmp_path / "settings.json")
    manager = ScreenshotManager(
        prefs,
        FakeSessions(["Alpha Quest"]),
        directory=tmp_path / "screenshots",
        register_hotkey=False,
    )

    manager.startRecording()
    assert manager.recording is True

    # A modifier on its own is not a shortcut yet.
    assert manager.recordKey(Qt.Key_Control, Qt.ControlModifier) == ""
    assert manager.recording is True

    # Neither is a plain letter.
    assert manager.recordKey(Qt.Key_A, Qt.NoModifier) == ""
    assert manager.recording is True
    assert manager.error

    captured = manager.recordKey(
        Qt.Key_A, Qt.ControlModifier | Qt.ShiftModifier
    )
    assert captured == "Ctrl+Shift+A"
    assert manager.recording is False
    assert prefs.screenshot_shortcut == "Ctrl+Shift+A"
    assert manager.shortcutLabel == "Ctrl+Shift+A"


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
    assert manager.lastCapture["gameId"] == "steam:1"
    assert manager.lastCapture["sessionId"] == "s1"
    indexed = screenshot_store.for_game("steam:1")
    assert len(indexed) == 1
    assert indexed[0]["url"].startswith("file:")
    assert indexed[0]["path"] == path


def test_screenshot_store_records_and_drops_missing_files(tmp_path: Path) -> None:
    existing = tmp_path / "shot.png"
    existing.write_bytes(b"png")
    screenshot_store.record(
        existing,
        game_id="steam:1",
        session_id="s1",
        session_started_at=1000,
        title="Alpha Quest",
        taken_at=1100,
    )
    missing = tmp_path / "gone.png"
    screenshot_store.record(
        missing,
        game_id="steam:1",
        session_id="s1",
        session_started_at=1000,
        title="Alpha Quest",
        taken_at=1200,
    )

    entries = screenshot_store.for_game("steam:1")

    assert len(entries) == 1
    assert entries[0]["takenAt"] == 1100
    assert entries[0]["sessionStartedAt"] == 1000
    assert entries[0]["url"].startswith("file:")
    assert screenshot_store.for_game("epic:2") == []


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


def test_screenshot_store_recovers_legacy_files_by_title(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(screenshot_store, "config_dir", lambda: tmp_path)
    folder = tmp_path / "screenshots"
    folder.mkdir()
    legacy = folder / "Alpha-Quest-20261027-204937.png"
    legacy.write_bytes(b"png")

    entries = screenshot_store.for_game("steam:1", title="Alpha Quest")

    assert len(entries) == 1
    assert entries[0]["path"] == str(legacy.resolve())
    assert entries[0]["takenAt"] == int(
        datetime(2026, 10, 27, 20, 49, 37).timestamp()
    )
    assert entries[0]["url"].startswith("file:")


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
