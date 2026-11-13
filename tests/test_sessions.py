"""Sessions: start, tick, eject and automatic removal when the game exits."""

import pytest

from gamecenter.core.models import Game
from gamecenter.core.sessions import (
    ADOPT_WINDOW,
    SCAN_ACTIVE,
    SCAN_IDLE,
    ProcessScanner,
    SessionTracker,
    _format_elapsed,
    _under,
)


class FakeProcess:
    def __init__(self, pid: int, name: str, exe: str, create_time: float) -> None:
        self.pid = pid
        self.info = {"name": name, "exe": exe, "create_time": create_time}


def fake_iter(processes):
    def _iter(attrs=None):
        return iter(list(processes))

    return _iter


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


def test_uri_launch_gets_a_startup_grace(app) -> None:
    tracker = SessionTracker()
    game = Game(id="steam:1", title="Alpha", source="steam")

    session = tracker.start(game, None, "")
    assert tracker.count == 1

    # The launcher has not spawned the game yet: keep the session alive.
    tracker.poll()
    assert tracker.count == 1

    # After the grace window, a session with no detectable process is dropped.
    session.started_at -= 31
    tracker.poll()
    assert tracker.count == 0


def test_session_end_reports_the_elapsed_time(app) -> None:
    now = [100.0]
    alive = [True]
    ended = []

    tracker = SessionTracker(
        running=lambda session: alive[0],
        clock=lambda: now[0],
        on_end=lambda session, seconds: ended.append((session.id, seconds)),
    )
    session = tracker.start(Game(id="epic:1", title="Alpha", source="epic"), None, "")

    now[0] = 165.0
    alive[0] = False
    tracker.poll()

    assert ended == [(session.id, 65.0)]
    assert tracker.count == 0


def test_eject_reports_the_elapsed_time(app) -> None:
    now = [100.0]
    ended = []
    tracker = SessionTracker(
        running=lambda session: True,
        clock=lambda: now[0],
        on_end=lambda session, seconds: ended.append(seconds),
    )
    session = tracker.start(Game(id="epic:1", title="Alpha", source="epic"), None, "")

    now[0] = 110.0
    tracker.eject(session.id)

    assert ended == [10.0]


def test_finish_all_reports_running_sessions(app) -> None:
    now = [100.0]
    ended = []
    tracker = SessionTracker(
        running=lambda session: True,
        clock=lambda: now[0],
        on_end=lambda session, seconds: ended.append(seconds),
    )
    tracker.start(Game(id="epic:1", title="Alpha", source="epic"), None, "")

    now[0] = 130.0
    tracker.finish_all()

    assert ended == [30.0]
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

# -- external detection -----------------------------------------------------


def test_scanner_matches_the_install_folder(app, tmp_path) -> None:
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [
                FakeProcess(1, "explorer.exe", "C:/Windows/explorer.exe", 10.0),
                FakeProcess(
                    42, "alpha.exe", str(folder / "bin" / "alpha.exe"), 20.0
                ),
            ]
        )
    )
    scanner.rebuild([game])

    found = scanner.scan()

    assert len(found) == 1
    assert found[0][0].id == "steam:1"
    assert found[0][1] == 42
    assert found[0][2] == 20.0


def test_scanner_matches_a_known_executable_without_a_folder(app, tmp_path) -> None:
    executable = tmp_path / "portable" / "alpha.exe"
    game = Game(id="local:alpha", title="Alpha", source="local", executable=executable)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [
                FakeProcess(7, "alpha.exe", r"D:\Portable\alpha.exe", 30.0),
                FakeProcess(8, "other.exe", r"D:\Portable\other.exe", 31.0),
            ]
        )
    )
    scanner.rebuild([game])

    found = scanner.scan()

    assert [item[1] for item in found] == [7]


def test_scanner_never_trusts_a_name_without_a_path(app) -> None:
    game = Game(id="local:ghost", title="Ghost", source="local", executable=None)
    scanner = ProcessScanner(
        process_iter=fake_iter([FakeProcess(9, "ghost.exe", "", 40.0)])
    )
    scanner.rebuild([game])

    assert scanner.scan() == []


def test_scanner_keeps_the_earliest_process_of_a_folder(app, tmp_path) -> None:
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [
                FakeProcess(2, "crash.exe", str(folder / "crash.exe"), 50.5),
                FakeProcess(1, "alpha.exe", str(folder / "alpha.exe"), 50.0),
            ]
        )
    )
    scanner.rebuild([game])

    found = scanner.scan()

    assert found[0][1] == 1
    assert found[0][2] == 50.0


def test_detect_starts_a_session_with_the_real_start_time(app, tmp_path) -> None:
    now = [1000.0]
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [FakeProcess(42, "alpha.exe", str(folder / "alpha.exe"), 996.0)]
        )
    )
    tracker = SessionTracker(
        scanner=scanner,
        games=lambda: [game],
        cover=lambda _game: "image://cover/alpha",
        detect_external=True,
        clock=lambda: now[0],
    )

    assert tracker.detect() == 1
    session = tracker._sessions[0]
    assert session.pid == 42
    assert session.pid_started == 996.0
    assert session.started_at == 996.0
    assert session.cover == "image://cover/alpha"


def test_detect_clamps_a_game_that_was_already_running(app, tmp_path) -> None:
    now = [5000.0]
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [FakeProcess(42, "alpha.exe", str(folder / "alpha.exe"), 5000.0 - 600)]
        )
    )
    tracker = SessionTracker(
        scanner=scanner,
        games=lambda: [game],
        detect_external=True,
        clock=lambda: now[0],
    )

    tracker.detect()

    assert tracker._sessions[0].started_at == now[0]
    assert ADOPT_WINDOW < 600


def test_detect_adopts_the_pid_of_a_uri_launch(app, tmp_path) -> None:
    now = [200.0]
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [FakeProcess(77, "alpha.exe", str(folder / "alpha.exe"), 190.0)]
        )
    )
    tracker = SessionTracker(
        scanner=scanner,
        games=lambda: [game],
        cover=lambda _game: "",
        detect_external=True,
        clock=lambda: now[0],
    )
    session = tracker.start(game, None, "")
    assert session.pid is None

    tracker.detect()

    assert tracker.count == 1
    assert session.pid == 77
    assert session.pid_started == 190.0
    assert session.started_at == 200.0


def test_detect_is_off_by_default(app, tmp_path) -> None:
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    scanner = ProcessScanner(
        process_iter=fake_iter(
            [FakeProcess(42, "alpha.exe", str(folder / "alpha.exe"), 90.0)]
        )
    )
    tracker = SessionTracker(scanner=scanner, games=lambda: [game])

    assert tracker.detect() == 0
    assert tracker.count == 0


def test_tick_scans_only_when_due(app, tmp_path) -> None:
    now = [1000.0]
    folder = tmp_path / "Alpha"
    game = Game(id="steam:1", title="Alpha", source="steam", install_dir=folder)
    processes = [FakeProcess(42, "alpha.exe", str(folder / "alpha.exe"), 995.0)]
    scanner = ProcessScanner(process_iter=fake_iter(processes))
    tracker = SessionTracker(
        running=lambda _session: True,
        scanner=scanner,
        games=lambda: [game],
        detect_external=True,
        clock=lambda: now[0],
    )

    tracker.tick()
    assert tracker.count == 1
    assert tracker._scan_at == 1000.0

    # With a game in the dock the scan becomes lazy (SCAN_ACTIVE, not idle).
    processes.append(FakeProcess(43, "beta.exe", str(folder / "beta.exe"), 1001.0))
    now[0] = 1000.0 + SCAN_ACTIVE - 1
    tracker.tick()
    assert tracker.count == 1
    assert tracker._scan_at == 1000.0

    now[0] = 1000.0 + SCAN_ACTIVE
    tracker.tick()
    assert tracker.count == 1  # same game, no duplicate
    assert tracker._scan_at == now[0]

    # A second game from the same folder is not a new session either.
    assert SCAN_IDLE < SCAN_ACTIVE

