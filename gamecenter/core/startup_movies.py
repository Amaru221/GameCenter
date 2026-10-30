"""Startup movies for Big Picture.

Two short WebM intros ship with the app in ``startup-movies/``. The user can
pick one of those or import a video of their own; imported files are copied to
``%APPDATA%/GameCenter/startup_movies`` so moving the original does not break
the intro.

The manager only resolves paths and persists the choice. Playback lives in QML
(``StartupMovie.qml``), which keeps the core testable without a media backend.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from .i18n import tr
from .preferences import Preferences, config_dir

VIDEO_SUFFIXES = frozenset({".webm", ".mp4", ".m4v", ".mov", ".mkv"})
BUNDLE_DIRNAME = "startup-movies"
CUSTOM_DIRNAME = "startup_movies"

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


def bundle_dir() -> Path:
    """Where the videos shipped with the app live (source tree or PyInstaller)."""
    frozen = getattr(sys, "_MEIPASS", None)
    if frozen:
        return Path(frozen) / BUNDLE_DIRNAME
    return Path(__file__).resolve().parents[2] / BUNDLE_DIRNAME


def custom_dir() -> Path:
    """Where user-imported videos are copied."""
    return config_dir() / CUSTOM_DIRNAME


def _pretty_name(path: Path) -> str:
    words = re.split(r"[_\-\s]+", path.stem.strip())
    return " ".join(word.capitalize() for word in words if word) or path.stem


def _entry(path: Path, custom: bool) -> dict:
    return {
        "id": f"{'custom' if custom else 'default'}:{path.name}",
        "name": _pretty_name(path),
        "url": QUrl.fromLocalFile(str(path)).toString(),
        "path": str(path),
        "custom": custom,
    }


def _videos(folder: Path) -> list[Path]:
    try:
        items = list(folder.iterdir())
    except OSError:
        return []
    return [
        path
        for path in items
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    ]


def list_movies() -> list[dict]:
    """Bundled movies first, then the ones imported by the user."""
    movies: list[dict] = []
    movies.extend(
        _entry(path, False)
        for path in sorted(_videos(bundle_dir()), key=lambda item: item.name.casefold())
    )
    movies.extend(
        _entry(path, True)
        for path in sorted(_videos(custom_dir()), key=lambda item: item.name.casefold())
    )
    return movies


def resolve(movie_id: str, movies: list[dict] | None = None) -> dict | None:
    for movie in movies if movies is not None else list_movies():
        if movie["id"] == movie_id:
            return movie
    return None


def first_movie(movies: list[dict] | None = None) -> dict | None:
    available = movies if movies is not None else list_movies()
    return available[0] if available else None


def _safe_target(folder: Path, source: Path) -> Path:
    stem = _SAFE_NAME.sub("_", source.stem).strip("._ ") or "startup"
    suffix = source.suffix.lower()
    target = folder / f"{stem}{suffix}"
    if not target.exists():
        return target
    stamp = time.time_ns() // 1000
    return folder / f"{stem}-{stamp}{suffix}"


def import_movie(source: Path) -> dict:
    """Copy a user video into the app data and return its entry."""
    source = Path(source)
    if not source.is_file():
        raise ValueError(tr("Couldn't read that movie."))
    if source.suffix.lower() not in VIDEO_SUFFIXES:
        raise ValueError(tr("That movie format is not supported."))

    folder = custom_dir()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        target = _safe_target(folder, source)
        shutil.copy2(source, target)
    except OSError as exc:
        raise ValueError(tr("Couldn't copy that movie.")) from exc
    return _entry(target, True)


def remove_movie(movie_id: str, movies: list[dict] | None = None) -> bool:
    """Delete a user-imported movie. Bundled movies are never removed."""
    movie = resolve(movie_id, movies)
    if movie is None or not movie.get("custom"):
        return False
    try:
        Path(str(movie["path"])).unlink(missing_ok=True)
        return True
    except OSError:
        return False


class StartupMovieManager(QObject):
    """QML-facing choice of startup movie."""

    changed = Signal()
    failed = Signal(str)

    def __init__(self, prefs: Preferences, parent=None) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._movies = list_movies()
        self._error = ""
        self._ensure_selection()

    # -- helpers ----------------------------------------------------------

    def _ensure_selection(self) -> None:
        ids = {movie["id"] for movie in self._movies}
        if self._prefs.startup_movie not in ids:
            first = self._movies[0]["id"] if self._movies else ""
            self._prefs.startup_movie = first

    def _current(self) -> dict | None:
        movie = resolve(self._prefs.startup_movie, self._movies)
        return movie or first_movie(self._movies)

    def _reload(self) -> None:
        self._movies = list_movies()
        self._ensure_selection()
        self.changed.emit()

    # -- properties -------------------------------------------------------

    @Property(bool, notify=changed)
    def suppressed(self) -> bool:
        platform = os.environ.get("QT_QPA_PLATFORM", "").lower()
        return bool(os.environ.get("GC_NO_STARTUP_MOVIE")) or platform in {
            "offscreen",
            "minimal",
        }

    @Property(bool, notify=changed)
    def enabled(self) -> bool:
        return bool(self._prefs.startup_movie_enabled)

    @Property("QVariantList", notify=changed)
    def movies(self) -> list[dict]:
        return self._movies

    @Property("QVariantList", notify=changed)
    def options(self) -> list[dict]:
        return [
            {"text": movie["name"], "value": movie["id"]}
            for movie in self._movies
        ]

    @Property(str, notify=changed)
    def selected(self) -> str:
        movie = self._current()
        return str(movie["id"]) if movie else ""

    @Property(str, notify=changed)
    def currentUrl(self) -> str:
        movie = self._current()
        return str(movie["url"]) if movie else ""

    @Property(str, notify=changed)
    def currentName(self) -> str:
        movie = self._current()
        return str(movie["name"]) if movie else ""

    @Property(bool, notify=changed)
    def selectedIsCustom(self) -> bool:
        movie = self._current()
        return bool(movie and movie.get("custom"))

    @Property(bool, notify=changed)
    def ready(self) -> bool:
        return bool(
            not self.suppressed
            and self.enabled
            and self.currentUrl
        )

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    # -- slots ------------------------------------------------------------

    @Slot(bool)
    def setEnabled(self, value: bool) -> None:
        value = bool(value)
        if value != self._prefs.startup_movie_enabled:
            self._prefs.startup_movie_enabled = value
            self.changed.emit()

    @Slot(str)
    def setSelected(self, movie_id: str) -> None:
        if resolve(movie_id, self._movies) is None:
            return
        if movie_id != self._prefs.startup_movie:
            self._prefs.startup_movie = movie_id
            self.changed.emit()

    @Slot(str, result=bool)
    def importMovie(self, file_url: str) -> bool:
        raw = str(file_url or "")
        path = QUrl(raw).toLocalFile() if raw.startswith("file:") else raw
        try:
            movie = import_movie(Path(path))
        except ValueError as exc:
            self._error = str(exc)
            self.failed.emit(self._error)
            self.changed.emit()
            return False
        self._error = ""
        self._prefs.startup_movie = movie["id"]
        self._prefs.startup_movie_enabled = True
        self._reload()
        return True

    @Slot()
    def removeSelected(self) -> None:
        movie = self._current()
        if movie is None or not movie.get("custom"):
            return
        if not remove_movie(str(movie["id"]), self._movies):
            self._error = tr("Couldn't remove that movie.")
            self.failed.emit(self._error)
            self.changed.emit()
            return
        self._error = ""
        self._prefs.startup_movie = ""
        self._reload()

    @Slot()
    def refresh(self) -> None:
        self._reload()
