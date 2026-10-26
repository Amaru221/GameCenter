"""Track the games launched from GameCenter while they run.

A session knows the game, when it started and (when the store gave us one) the
process id and install folder. A poll every second drops sessions whose
processes are gone; the dock shows the rest with a live timer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from .models import SOURCE_LABELS, Game

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is a declared dependency
    psutil = None

# A store URI has no pid; give the launcher time to spawn the real game before
# the first poll decides the session is gone.
LAUNCH_GRACE = 30.0


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


def _process_running(session: "Session") -> bool:
    if psutil is None:
        return session.started_at + 60 > time.time()

    if session.pid is not None:
        try:
            if psutil.pid_exists(session.pid):
                return True
        except psutil.Error:
            pass

    if session.install_dir is not None:
        try:
            for process in psutil.process_iter(["exe"]):
                exe = process.info.get("exe")
                if exe and _under(exe, session.install_dir):
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


class SessionTracker(QObject):
    changed = Signal()

    def __init__(
        self,
        running: Callable[[Session], bool] | None = None,
        clock: Callable[[], float] | None = None,
        on_end: Callable[[Session, float], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._sessions: list[Session] = []
        self._running = running or _process_running
        self._clock = clock or time.time
        self._on_end = on_end
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
            }
            for session in self._sessions
        ]

    def start(self, game: Game, pid: int | None, cover: str) -> Session:
        """Add a session, or return the one already tracking this game."""
        for session in self._sessions:
            if session.game_id == game.id:
                return session

        self._seq += 1
        session = Session(
            id=f"s{self._seq}",
            game_id=game.id,
            title=game.title,
            source=game.source,
            cover=cover,
            started_at=self._clock(),
            pid=pid,
            install_dir=game.install_dir,
        )
        self._sessions.append(session)
        self.changed.emit()
        return session

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
