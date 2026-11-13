"""Track the games running while GameCenter is open.

A session knows the game, when it started and (when known) the process id and
install folder. A poll every second drops sessions whose processes are gone;
the dock shows the rest with a live timer.

Sessions can start two ways: when the user launches a game from the app (the
store may return a pid) or when the user starts it elsewhere (Steam, Epic, the
desktop...). The second case uses a cheap process scan whose frequency adapts
to whether a game is already running.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from PySide6.QtCore import Property, QObject, Signal, Slot

from .models import SOURCE_LABELS, Game

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is a declared dependency
    psutil = None

# A store URI has no pid; give the launcher time to spawn the real game before
# the first poll decides the session is gone.
LAUNCH_GRACE = 30.0

# How often the process list is inspected for games started outside the app.
# With no session the scan looks for a new launch; with one running it only
# looks for a second game, so it can afford to be much lazier.
SCAN_IDLE = 5.0
SCAN_ACTIVE = 30.0

# A game that was already running before it was noticed should not credit the
# app with the whole time since it started: clamp the start to the detection.
ADOPT_WINDOW = 120.0

# Attributes needed to match a process to a library entry. Fetching them is the
# expensive part of the first pass, so the warm-up requests exactly these and
# every later scan reuses psutil's per-process cache.
_SCAN_ATTRS = ["name", "exe", "create_time"]


def _format_elapsed(seconds: int) -> str:
    minutes, secs = divmod(max(0, seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _under(path: str, folder: Path) -> bool:
    try:
        return Path(path).resolve().is_relative_to(folder.resolve())
    except (OSError, ValueError):
        return False


def _under_fast(path: str, folder: Path) -> bool:
    """Prefix check without touching the filesystem (hot path of the scanner)."""
    try:
        candidate = os.path.normcase(os.path.abspath(path))
        root = os.path.normcase(os.path.abspath(str(folder)))
    except (OSError, ValueError):
        return False
    return candidate == root or candidate.startswith(root + os.sep)


def _exe_key(value) -> str:
    return Path(str(value)).name.lower()


def _pid_matches(pid: int, started: float | None) -> bool:
    """``True`` when *pid* is alive and still the same process we saw."""
    if not psutil.pid_exists(pid):
        return False
    if started is None:
        return True
    try:
        return abs(psutil.Process(pid).create_time() - started) < 1.0
    except psutil.Error:
        # A protected process we cannot inspect: trust the pid itself.
        return True


def _process_running(session: "Session") -> bool:
    if psutil is None:
        return session.started_at + 60 > time.time()

    if session.pid is not None:
        try:
            if _pid_matches(session.pid, session.pid_started):
                return True
        except psutil.Error:
            pass

    if session.install_dir is not None:
        try:
            for process in psutil.process_iter(["exe"]):
                exe = process.info.get("exe")
                if exe and _under_fast(exe, session.install_dir):
                    return True
        except (psutil.Error, OSError):
            pass

    # Store launchers (Steam, Epic, …) are opened via URI, so there is no pid
    # and the real game process may take a while to appear. Keep the session
    # alive during a short startup window instead of dropping it on the first
    # poll.
    if session.started_at + LAUNCH_GRACE > time.time():
        return True

    return False


class ProcessScanner:
    """Match the running processes against the installed games.

    ``psutil`` caches each process' attributes: after the first pass a scan only
    enumerates the pids and reads cached values, so it costs a couple of
    milliseconds even on a busy desktop. The first pass is expensive (~0.8 s for
    a few hundred processes), which is why :meth:`warm` runs it in a background
    thread at startup.
    """

    def __init__(self, process_iter=None) -> None:
        if process_iter is not None:
            self._process_iter = process_iter
        elif psutil is not None:
            self._process_iter = psutil.process_iter
        else:  # pragma: no cover - psutil is a declared dependency
            self._process_iter = None
        self._by_name: dict[str, list[Game]] = {}
        self._folders: list[tuple[Path, Game]] = []

    def rebuild(self, games: Iterable[Game]) -> None:
        by_name: dict[str, list[Game]] = {}
        folders: list[tuple[Path, Game]] = []
        for game in games:
            executable = getattr(game, "executable", None)
            if executable is not None:
                by_name.setdefault(_exe_key(executable), []).append(game)
            install_dir = getattr(game, "install_dir", None)
            if install_dir is not None:
                folders.append((install_dir, game))
        self._by_name = by_name
        self._folders = folders

    def warm(self) -> None:
        """First full pass: fills the psutil cache so later scans stay cheap."""
        if self._process_iter is None:
            return
        try:
            for _process in self._process_iter(_SCAN_ATTRS):
                pass
        except Exception:  # noqa: BLE001 - warming must never break startup
            pass

    def scan(self) -> list[tuple[Game, int, float]]:
        """``(game, pid, started_at)`` for every process that belongs to a game."""
        if self._process_iter is None:
            return []
        try:
            processes = list(self._process_iter(_SCAN_ATTRS))
        except Exception:  # noqa: BLE001 - the process list is best effort
            return []

        found: dict[str, tuple[Game, int, float]] = {}
        for process in processes:
            info = getattr(process, "info", None)
            if not isinstance(info, dict):
                continue
            exe = info.get("exe") or ""
            name = str(info.get("name") or "").lower()
            if not exe and not name:
                continue
            game = self._match(name, exe)
            pid = getattr(process, "pid", None)
            if game is None or pid is None:
                continue
            try:
                started = float(info.get("create_time") or 0.0)
            except (TypeError, ValueError):
                started = 0.0
            current = found.get(game.id)
            # A folder can hold several processes (launcher, crash handler...).
            # The main one starts first, so the earliest becomes the session.
            if current is None or (started and started < current[2]):
                found[game.id] = (game, int(pid), started)
        return list(found.values())

    def _match(self, name: str, exe: str) -> Game | None:
        if exe:
            for folder, game in self._folders:
                if _under_fast(exe, folder):
                    return game
            candidates = self._by_name.get(name) or self._by_name.get(_exe_key(exe))
            if not candidates:
                return None
            for game in candidates:
                folder = getattr(game, "install_dir", None)
                if folder is None or _under_fast(exe, folder):
                    return game
        # Without a path there is no way to confirm ownership: never guess.
        return None


@dataclass
class Session:
    id: str
    game_id: str
    title: str
    source: str
    cover: str
    started_at: float
    pid: int | None
    install_dir: Path | None
    pid_started: float | None = None


class SessionTracker(QObject):
    changed = Signal()

    def __init__(
        self,
        running: Callable[[Session], bool] | None = None,
        clock: Callable[[], float] | None = None,
        on_end: Callable[[Session, float], None] | None = None,
        games: Callable[[], Iterable[Game]] | None = None,
        cover: Callable[[Game], str] | None = None,
        scanner: ProcessScanner | None = None,
        detect_external: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._sessions: list[Session] = []
        self._running = running or _process_running
        self._clock = clock or time.time
        self._on_end = on_end
        self._games = games
        self._cover = cover or (lambda _game: "")
        self._scanner = scanner if scanner is not None else ProcessScanner()
        self.detect_external = bool(detect_external)
        # An injected scanner (tests) is ready to use; the real one needs the
        # background warm-up before it can scan cheaply.
        self._warmed = scanner is not None or psutil is None
        self._scan_at = 0.0
        self._seq = 0

    @Property(int, notify=changed)
    def count(self) -> int:
        return len(self._sessions)

    @Property("QVariantList", notify=changed)
    def list(self) -> list[dict]:
        now = self._clock()
        return [
            {
                "id": session.id,
                "gameId": session.game_id,
                "title": session.title,
                "source": SOURCE_LABELS.get(session.source, session.source),
                "cover": session.cover,
                "elapsed": _format_elapsed(int(now - session.started_at)),
                "startedAt": int(session.started_at),
            }
            for session in self._sessions
        ]

    def start(self, game: Game, pid: int | None, cover: str) -> Session:
        """Add a session, or return the one already tracking this game."""
        return self._start(game, pid, cover, self._clock())

    def _start(
        self,
        game: Game,
        pid: int | None,
        cover: str,
        started_at: float,
        pid_started: float | None = None,
    ) -> Session:
        for session in self._sessions:
            if session.game_id == game.id:
                return session

        if pid_started is None and pid is not None and psutil is not None:
            try:
                pid_started = psutil.Process(pid).create_time()
            except psutil.Error:
                pid_started = None

        self._seq += 1
        session = Session(
            id=f"s{self._seq}",
            game_id=game.id,
            title=game.title,
            source=game.source,
            cover=cover,
            started_at=started_at,
            pid=pid,
            install_dir=game.install_dir,
            pid_started=pid_started,
        )
        self._sessions.append(session)
        self.changed.emit()
        return session

    def warm(self) -> None:
        """Fill the psutil cache off the UI thread (one expensive pass)."""
        if self._warmed:
            return
        try:
            self._scanner.warm()
        finally:
            self._warmed = True

    def due(self, now: float | None = None) -> bool:
        """Whether the process scan is due at the adaptive interval."""
        if not self.detect_external or not self._warmed:
            return False
        now = self._clock() if now is None else now
        interval = SCAN_ACTIVE if self._sessions else SCAN_IDLE
        return now - self._scan_at >= interval

    def detect(self, games: Iterable[Game] | None = None) -> int:
        """Discover games started outside the app; returns how many are new."""
        if not self.detect_external or not self._warmed:
            return 0
        if games is None and self._games is not None:
            games = self._games()
        source = list(games or ())
        self._scan_at = self._clock()
        self._scanner.rebuild(source)
        found = self._scanner.scan()
        now = self._clock()
        added = 0
        for game, pid, create_time in found:
            session = next(
                (item for item in self._sessions if item.game_id == game.id), None
            )
            if session is not None:
                # A URI launch had no pid; the real process gives us one.
                if session.pid is None and pid:
                    session.pid = pid
                    session.pid_started = create_time or None
                    self.changed.emit()
                continue
            started_at = now
            if create_time and now - create_time <= ADOPT_WINDOW:
                started_at = create_time
            self._start(game, pid, self._cover(game), started_at, create_time or None)
            added += 1
        return added

    @Slot()
    def tick(self) -> None:
        """Model entry point: poll every second, scan only when due."""
        if self.due():
            self.detect()
        self.poll()

    @Slot()
    def poll(self) -> None:
        if not self._sessions:
            return
        now = self._clock()
        alive: list[Session] = []
        for session in self._sessions:
            if self._running(session):
                alive.append(session)
            elif self._on_end is not None:
                self._on_end(session, max(0.0, now - session.started_at))
        if len(alive) != len(self._sessions):
            self._sessions = alive
        self.changed.emit()

    @Slot(str)
    def eject(self, session_id: str) -> None:
        now = self._clock()
        for session in self._sessions:
            if session.id == session_id and self._on_end is not None:
                self._on_end(session, max(0.0, now - session.started_at))
        before = len(self._sessions)
        self._sessions = [s for s in self._sessions if s.id != session_id]
        if len(self._sessions) != before:
            self.changed.emit()

    @Slot()
    def clear(self) -> None:
        if self._sessions:
            now = self._clock()
            if self._on_end is not None:
                for session in self._sessions:
                    self._on_end(session, max(0.0, now - session.started_at))
            self._sessions.clear()
            self.changed.emit()

    @Slot()
    def finish_all(self) -> None:
        """Record everything still running (used when the app quits)."""
        if not self._sessions:
            return
        now = self._clock()
        if self._on_end is not None:
            for session in self._sessions:
                self._on_end(session, max(0.0, now - session.started_at))
        self._sessions.clear()
        self.changed.emit()
