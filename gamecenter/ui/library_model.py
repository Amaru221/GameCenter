"""The library as a Qt list model, with filtering, sorting and launching."""

from __future__ import annotations

import re
import threading
import time
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    Property,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication

from ..core.favorites import Favorites
from ..core.launch import LaunchError, launch as launch_game, open_folder
from ..core.models import SOURCE_LABELS, Game
from ..core.sources import scan_all
from . import artwork, covers

ROLE_TITLE = Qt.UserRole + 1
ROLE_SOURCE = Qt.UserRole + 2
ROLE_APP_ID = Qt.UserRole + 3
ROLE_META = Qt.UserRole + 4
ROLE_COVER = Qt.UserRole + 5
ROLE_INSTALLED = Qt.UserRole + 6
ROLE_SIZE = Qt.UserRole + 7
ROLE_HAS_FOLDER = Qt.UserRole + 8
ROLE_FAVORITE = Qt.UserRole + 9

_TAG_WORDS = re.compile(r"[A-Z0-9]+")


def _tag(title: str) -> str:
    words = _TAG_WORDS.findall(title.upper())
    if not words:
        return "GAME"
    head = words[0][:4]
    tail = words[-1] if len(words) > 1 and words[-1].isdigit() else ""
    return (head + tail)[:7]


def _playtime_text(minutes: int) -> str:
    if minutes <= 0:
        return ""
    if minutes < 60:
        return f"{minutes} min played"
    hours = minutes // 60
    return "1 hour played" if hours == 1 else f"{hours:,} hours played"


def _played_text(timestamp: int) -> str:
    if not timestamp:
        return "Never played"
    days = (time.time() - timestamp) / 86400
    if days < 1:
        return "Played today"
    if days < 2:
        return "Played yesterday"
    if days < 30:
        return f"Played {int(days)} days ago"
    if days < 365:
        months = int(days // 30)
        return f"Played {months} month{'s' if months != 1 else ''} ago"
    years = int(days // 365)
    return f"Played {years} year{'s' if years != 1 else ''} ago"


class LibraryModel(QAbstractListModel):
    changed = Signal()
    failed = Signal(str)
    artReady = Signal(str)

    def __init__(
        self, download_art: bool = True, favorites_path: Path | None = None
    ) -> None:
        super().__init__()
        self._all: list[Game] = scan_all()
        self._visible: list[Game] = []
        self._query = ""
        self._source = ""
        self._sort = "recent"
        self._favorites = Favorites(favorites_path)
        self._favorites_only = False
        self._art_revision = 0
        self._art_downloads = download_art and artwork.enabled()
        self._art_running = False
        self._art_lock = threading.Lock()
        self.artReady.connect(self._on_art_ready, Qt.QueuedConnection)
        self._refresh_rows()
        self._start_art()

    # -- Qt model ---------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._visible):
            return None
        game = self._visible[index.row()]
        if role == ROLE_TITLE:
            return game.title
        if role == ROLE_SOURCE:
            return game.source_label
        if role == ROLE_APP_ID:
            return game.app_id
        if role == ROLE_META:
            return f"{game.source_label.upper()} · {game.app_id or '—'} · {_tag(game.title)}"
        if role == ROLE_COVER:
            key = covers.cover_key(game.title, game.app_id, self._art_revision)
            return "image://cover/" + key
        if role == ROLE_INSTALLED:
            return game.installed
        if role == ROLE_SIZE:
            return f"{game.size_gb:.1f} GB" if game.size_gb else ""
        if role == ROLE_HAS_FOLDER:
            return bool(game.install_dir and game.install_dir.is_dir())
        if role == ROLE_FAVORITE:
            return game.id in self._favorites
        if role == Qt.DisplayRole:
            return game.title
        return None

    def roleNames(self) -> dict[int, QByteArray]:
        return {
            ROLE_TITLE: QByteArray(b"title"),
            ROLE_SOURCE: QByteArray(b"source"),
            ROLE_APP_ID: QByteArray(b"appId"),
            ROLE_META: QByteArray(b"meta"),
            ROLE_COVER: QByteArray(b"cover"),
            ROLE_INSTALLED: QByteArray(b"installed"),
            ROLE_SIZE: QByteArray(b"sizeText"),
            ROLE_HAS_FOLDER: QByteArray(b"hasFolder"),
            ROLE_FAVORITE: QByteArray(b"favorite"),
        }

    # -- properties -------------------------------------------------------

    @Property(str, notify=changed)
    def query(self) -> str:
        return self._query

    @Property(str, notify=changed)
    def sourceFilter(self) -> str:
        return self._source

    @Property(str, notify=changed)
    def sortMode(self) -> str:
        return self._sort

    @Property(int, notify=changed)
    def count(self) -> int:
        return len(self._visible)

    @Property(int, notify=changed)
    def total(self) -> int:
        return len(self._all)

    @Property(bool, notify=changed)
    def favoritesOnly(self) -> bool:
        return self._favorites_only

    @Property("QVariantList", notify=changed)
    def sourceOptions(self) -> list[dict]:
        keys = sorted({game.source for game in self._all})
        return [
            {"text": SOURCE_LABELS.get(key, key.capitalize()), "value": key}
            for key in keys
        ]

    # -- filtering --------------------------------------------------------

    def _refresh_rows(self) -> None:
        query = self._query.casefold()
        rows = [
            game
            for game in self._all
            if (not query or query in game.title.casefold())
            and (not self._source or game.source == self._source)
            and (not self._favorites_only or game.id in self._favorites)
        ]
        if self._sort == "title":
            rows.sort(key=lambda g: g.title.casefold())
        elif self._sort == "size":
            rows.sort(key=lambda g: -g.size_bytes)
        else:
            rows.sort(key=lambda g: (-g.last_played, g.title.casefold()))

        self.beginResetModel()
        self._visible = rows
        self.endResetModel()
        self.changed.emit()

    @Slot(str)
    def setQuery(self, text: str) -> None:
        text = text or ""
        if text != self._query:
            self._query = text
            self._refresh_rows()

    @Slot(str)
    def setSourceFilter(self, source: str) -> None:
        source = source or ""
        if source != self._source:
            self._source = source
            self._refresh_rows()

    @Slot(str)
    def setSort(self, mode: str) -> None:
        if mode != self._sort:
            self._sort = mode
            self._refresh_rows()

    @Slot(bool)
    def setFavoritesOnly(self, value: bool) -> None:
        value = bool(value)
        if value != self._favorites_only:
            self._favorites_only = value
            self._refresh_rows()

    @Slot()
    def refresh(self) -> None:
        self._all = scan_all()
        self._refresh_rows()
        self._start_art()

    # -- cover art --------------------------------------------------------

    def _start_art(self) -> None:
        if not self._art_downloads:
            return
        with self._art_lock:
            if self._art_running:
                return
            self._art_running = True
        threading.Thread(target=self._warm_art, daemon=True).start()

    def _warm_art(self) -> None:
        """Fetch missing capsules one by one; give up after repeated failures."""
        downloads = 0
        failures = 0
        try:
            for game in list(self._all):
                if downloads >= artwork.MAX_DOWNLOADS or failures >= 3:
                    break
                if (
                    game.source != "steam"
                    or not game.installed
                    or not game.app_id.isdigit()
                    or artwork.cached_path(game.app_id) is not None
                ):
                    continue
                if artwork.fetch(game.app_id):
                    downloads += 1
                    failures = 0
                    self.artReady.emit(game.id)
                else:
                    failures += 1
        finally:
            with self._art_lock:
                self._art_running = False

    @Slot(str)
    def _on_art_ready(self, game_id: str) -> None:
        self._art_revision += 1
        for row, game in enumerate(self._visible):
            if game.id == game_id:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [ROLE_COVER])
                break

    # -- actions ----------------------------------------------------------

    def _at(self, row: int) -> Game | None:
        if 0 <= row < len(self._visible):
            return self._visible[row]
        return None

    @Slot(int)
    def launch(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        try:
            launch_game(game)
        except (LaunchError, OSError) as exc:
            self.failed.emit(str(exc))

    @Slot(int)
    def openFolder(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        if not game.install_dir or not game.install_dir.is_dir():
            self.failed.emit("This game has no install folder.")
            return
        try:
            open_folder(game.install_dir)
        except OSError as exc:
            self.failed.emit(str(exc))

    @Slot(int)
    def copyAppId(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        QGuiApplication.clipboard().setText(game.app_id)

    @Slot(int)
    def toggleFavorite(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._favorites.toggle(game.id)
        if self._favorites_only and game.id not in self._favorites:
            self._refresh_rows()
            return
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [ROLE_FAVORITE])

    @Slot(int, result="QVariantMap")
    def gameAt(self, row: int) -> dict:
        """Everything the detail panel needs about one row."""
        game = self._at(row)
        if game is None:
            return {}
        key = covers.cover_key(game.title, game.app_id, self._art_revision)
        return {
            "title": game.title,
            "source": game.source_label,
            "appId": game.app_id,
            "meta": f"{game.source_label.upper()} · {game.app_id or '—'} · {_tag(game.title)}",
            "cover": "image://cover/" + key,
            "installed": game.installed,
            "favorite": game.id in self._favorites,
            "sizeText": f"{game.size_gb:.1f} GB" if game.size_gb else "",
            "playtimeText": _playtime_text(game.playtime_minutes),
            "lastPlayed": _played_text(game.last_played),
            "installDir": str(game.install_dir) if game.install_dir else "",
            "hasFolder": bool(game.install_dir and game.install_dir.is_dir()),
        }
