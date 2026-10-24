"""Sessions: start, tick, eject and automatic removal when the game exits."""

import pytest

from gamecenter.core.models import Game
from gamecenter.core.sessions import SessionTracker, _format_elapsed, _under


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_elapsed_format() -> None:
    assert _format_elapsed(0) == "0:00"
    assert _format_elapsed(65) == "1:05"
    assert _format_elapsed(3661) == "1:01:01"


def test_under() -> None:
    from pathlib import Path

    folder = Path("C:/Games/Example")
    assert _under("C:/Games/Example/bin/game.exe", folder)
    assert not _under("C:/Games/Other/game.exe", folder)


def test_session_lifecycle(app) -> None:
    now = [1000.0]
    alive = [True]
    tracker = SessionTracker(running=lambda session: alive[0], clock=lambda: now[0])
    game = Game(id="steam:1", title="Alpha", source="steam")

    session = tracker.start(game, None, "image://cover/x")
    assert tracker.count == 1
    assert tracker.list[0]["title"] == "Alpha"

    now[0] += 65
    assert tracker.list[0]["elapsed"] == "1:05"

    alive[0] = False
    tracker.poll()
    assert tracker.count == 0

    tracker.eject(session.id)  # no-op, already gone
    assert tracker.count == 0


def test_duplicate_launch_reuses_the_session(app) -> None:
    tracker = SessionTracker(running=lambda session: True, clock=lambda: 0.0)
    game = Game(id="steam:1", title="Alpha", source="steam")

    first = tracker.start(game, None, "")
    second = tracker.start(game, None, "")

    assert tracker.count == 1
    assert first.id == second.id


def test_eject_removes_only_that_session(app) -> None:
    tracker = SessionTracker(running=lambda session: True, clock=lambda: 0.0)
    alpha = tracker.start(Game(id="steam:1", title="Alpha", source="steam"), None, "")
    beta = tracker.start(Game(id="steam:2", title="Beta", source="steam"), None, "")

    tracker.eject(alpha.id)

    assert tracker.count == 1
    assert tracker.list[0]["id"] == beta.id
