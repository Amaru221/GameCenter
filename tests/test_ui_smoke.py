"""Smoke test for the window, rendered headlessly.

It doesn't try to be a UI test suite: it proves that the window builds, that it
fills the shelf from a library, and that filtering hides the right items.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from gamecenter.core.models import Game  # noqa: E402
from gamecenter.ui import main_window  # noqa: E402


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _visible(window) -> int:
    return sum(not window.grid.item(i).isHidden() for i in range(window.grid.count()))


def test_window_lists_and_filters_games(app, monkeypatch) -> None:
    games = [
        Game(id="steam:1", title="Alpha Quest", source="steam"),
        Game(id="steam:2", title="Beta Racer", source="steam", installed=False),
    ]
    monkeypatch.setattr(main_window.steam, "scan", lambda: games)

    window = main_window.MainWindow()
    try:
        assert window.grid.count() == 2
        assert _visible(window) == 2

        window.search.setText("alpha")
        assert _visible(window) == 1

        window.search.clear()
        window.source.setCurrentIndex(window.source.findData("steam"))
        assert _visible(window) == 2
    finally:
        window.close()


def test_empty_library_shows_the_hint(app, monkeypatch) -> None:
    monkeypatch.setattr(main_window.steam, "scan", lambda: [])

    window = main_window.MainWindow()
    try:
        assert window.stack.currentWidget() is window.empty
        assert "No Steam library" in window.empty.text()
    finally:
        window.close()
