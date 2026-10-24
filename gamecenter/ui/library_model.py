"""The library as a Qt list model, with filtering, sorting and launching."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QCoreApplication,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices, QGuiApplication

from .. import __version__
from ..core import credentials, manual, playtime, steamgriddb, updater
from ..core.launch import LaunchError, launch as launch_game, open_folder
from ..core.models import SOURCE_LABELS, Game
from ..core.preferences import (
    CARTRIDGES,
    CARTRIDGE_STYLES,
    PALETTE,
    SURFACES,
    Preferences,
)
from ..core.sessions import SessionTracker
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
    appearanceChanged = Signal()
    artOptionsChanged = Signal()
    artChanged = Signal()
    credentialsChanged = Signal()
    updatesChanged = Signal()
    playtimeChanged = Signal()
    _artOptionsReady = Signal(object)
    _artDownloaded = Signal(str, str)
    _artFailed = Signal(str)
    _updateChecked = Signal(object, str)

    def __init__(
        self, download_art: bool = True, settings_path: Path | None = None
    ) -> None:
        super().__init__()
        self._all: list[Game] = scan_all()
        self._visible: list[Game] = []
        self._query = ""
        self._source = ""
        self._sort = "recent"
        self._prefs = Preferences(settings_path)
        self._favorites_only = False
        self._art_options: list[dict] = []
        self._art_loading = False
        self._art_error = ""
        self._credentials_message = ""
        self._has_key = bool(credentials.get_key())
        self._artOptionsReady.connect(self._on_art_options, Qt.QueuedConnection)
        self._artDownloaded.connect(self._on_art_downloaded, Qt.QueuedConnection)
        self._artFailed.connect(self._on_art_failed, Qt.QueuedConnection)
        self._sessions = SessionTracker(on_end=self._session_ended)
        self._session_timer = QTimer(self)
        self._session_timer.setInterval(1000)
        self._session_timer.timeout.connect(self._sessions.poll)
        self._session_timer.start()
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._sessions.finish_all)

        self._update_available: updater.UpdateInfo | None = None
        self._update_checking = False
        self._update_error = ""
        self._update_dismissed = False
        self._updateChecked.connect(self._on_update_checked, Qt.QueuedConnection)
        if self._prefs.check_updates and time.time() - self._prefs.last_update_check > 86400:
            QTimer.singleShot(6000, self.checkForUpdates)
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
            return self._cover_url(game)
        if role == ROLE_INSTALLED:
            return game.installed
        if role == ROLE_SIZE:
            return f"{game.size_gb:.1f} GB" if game.size_gb else ""
        if role == ROLE_HAS_FOLDER:
            return bool(game.install_dir and game.install_dir.is_dir())
        if role == ROLE_FAVORITE:
            return self._prefs.is_favorite(game.id)
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

    @Property(str, notify=appearanceChanged)
    def accent(self) -> str:
        return self._prefs.accent

    @Slot(str)
    def setAccent(self, value: str) -> None:
        self._prefs.accent = value
        self.appearanceChanged.emit()

    @Property("QVariantList", constant=True)
    def palette(self) -> list[str]:
        return list(PALETTE)

    @Property("QVariantList", constant=True)
    def surfacePalette(self) -> list[str]:
        return list(SURFACES)

    @Property("QVariantList", constant=True)
    def cartridgePalette(self) -> list[str]:
        return list(CARTRIDGES)

    @Property(str, notify=appearanceChanged)
    def surfaceColor(self) -> str:
        return self._prefs.surface_color

    @Slot(str)
    def setSurfaceColor(self, value: str) -> None:
        self._prefs.surface_color = value
        self.appearanceChanged.emit()

    @Property(str, notify=appearanceChanged)
    def cartridgeColor(self) -> str:
        return self._prefs.cartridge_color

    @Slot(str)
    def setCartridgeColor(self, value: str) -> None:
        self._prefs.cartridge_color = value
        self.appearanceChanged.emit()

    @Property(str, notify=appearanceChanged)
    def accentText(self) -> str:
        value = self._prefs.accent.lstrip("#")
        try:
            red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return "#08131a"
        luminance = 0.299 * red + 0.587 * green + 0.114 * blue
        return "#08131a" if luminance > 150 else "#ffffff"

    @Property(str, constant=True)
    def version(self) -> str:
        return __version__

    @Property("QVariantList", notify=artOptionsChanged)
    def artOptions(self) -> list[dict]:
        return self._art_options

    @Property(bool, notify=artOptionsChanged)
    def artLoading(self) -> bool:
        return self._art_loading

    @Property(str, notify=artOptionsChanged)
    def artError(self) -> str:
        return self._art_error

    @Property(bool, notify=updatesChanged)
    def updateAvailable(self) -> bool:
        return self._update_available is not None

    @Property(str, notify=updatesChanged)
    def updateVersion(self) -> str:
        return self._update_available.version if self._update_available else ""

    @Property(str, notify=updatesChanged)
    def updateUrl(self) -> str:
        return self._update_available.url if self._update_available else ""

    @Property(str, notify=updatesChanged)
    def updateNotes(self) -> str:
        return self._update_available.notes if self._update_available else ""

    @Property(bool, notify=updatesChanged)
    def updateChecking(self) -> bool:
        return self._update_checking

    @Property(str, notify=updatesChanged)
    def updateError(self) -> str:
        return self._update_error

    @Property(bool, notify=updatesChanged)
    def updateDismissed(self) -> bool:
        return self._update_dismissed

    @Property(bool, notify=updatesChanged)
    def checkUpdatesEnabled(self) -> bool:
        return self._prefs.check_updates

    @Property(str, notify=updatesChanged)
    def lastUpdateCheckText(self) -> str:
        stamp = self._prefs.last_update_check
        if not stamp:
            return "Never"
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(stamp))

    @Property(bool, notify=credentialsChanged)
    def hasSteamGridKey(self) -> bool:
        return self._has_key

    @Property(str, notify=credentialsChanged)
    def credentialsMessage(self) -> str:
        return self._credentials_message

    @Property(str, notify=appearanceChanged)
    def cartridgeStyle(self) -> str:
        return self._prefs.cartridge_style

    @Slot(str)
    def setCartridgeStyle(self, value: str) -> None:
        if value in CARTRIDGE_STYLES:
            self._prefs.cartridge_style = value
            self.appearanceChanged.emit()

    @Slot()
    def checkForUpdates(self) -> None:
        if self._update_checking:
            return
        self._update_checking = True
        self._update_error = ""
        self.updatesChanged.emit()

        def work():
            try:
                info = updater.check(__version__)
            except Exception as exc:  # noqa: BLE001 - reported to the UI
                self._updateChecked.emit(None, str(exc))
                return
            self._updateChecked.emit(info, "")

        threading.Thread(target=work, daemon=True).start()

    @Slot(bool)
    def setCheckUpdates(self, value: bool) -> None:
        value = bool(value)
        self._prefs.check_updates = value
        self.updatesChanged.emit()
        if value and self._update_available is None:
            self.checkForUpdates()

    @Slot()
    def openUpdate(self) -> None:
        if self._update_available is not None:
            QDesktopServices.openUrl(QUrl(self._update_available.url))

    @Slot()
    def dismissUpdate(self) -> None:
        self._update_dismissed = True
        self.updatesChanged.emit()

    @Slot(object, str)
    def _on_update_checked(self, info, error: str) -> None:
        self._update_checking = False
        if error:
            self._update_error = error
        else:
            self._update_available = info
            self._update_error = ""
            self._update_dismissed = False
            self._prefs.last_update_check = time.time()
        self.updatesChanged.emit()

    @Slot(str)
    def saveSteamGridKey(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            return
        saved = credentials.set_key(value)
        self._has_key = saved
        self._credentials_message = (
            "Saved to the system credential store."
            if saved
            else "Couldn't save to the credential store."
        )
        self.credentialsChanged.emit()

    @Slot()
    def clearSteamGridKey(self) -> None:
        credentials.clear_key()
        self._has_key = False
        self._credentials_message = "Key removed."
        self.credentialsChanged.emit()

    @Slot(int)
    def loadArtOptions(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        if not self._has_key:
            self._art_error = "Add a SteamGridDB API key in Settings first."
            self._art_loading = False
            self._art_options = []
            self.artOptionsChanged.emit()
            return

        key = credentials.get_key()
        self._art_loading = True
        self._art_error = ""
        self._art_options = []
        self.artOptionsChanged.emit()

        def work():
            try:
                options = steamgriddb.grids_for(game, key)
            except Exception as exc:  # noqa: BLE001 - reported to the UI
                self._artFailed.emit(str(exc))
                return
            self._artOptionsReady.emit(options)

        threading.Thread(target=work, daemon=True).start()

    @Slot(int, str)
    def chooseArt(self, row: int, url: str) -> None:
        game = self._at(row)
        if game is None or not url:
            return

        self._art_loading = True
        self._art_error = ""
        self.artOptionsChanged.emit()

        def work():
            try:
                path = steamgriddb.download(url, artwork.CACHE / "sgdb")
            except Exception as exc:  # noqa: BLE001
                self._artFailed.emit(str(exc))
                return
            self._artDownloaded.emit(game.id, str(path))

        threading.Thread(target=work, daemon=True).start()

    @Slot(int)
    def resetArt(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._prefs.set_cover(game.id, None)
        self._art_options = []
        self._art_error = ""
        self.artOptionsChanged.emit()
        self._notify_cover(game.id)
        self.artChanged.emit()

    def _notify_cover(self, game_id: str) -> None:
        for row, game in enumerate(self._visible):
            if game.id == game_id:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [ROLE_COVER])
                break

    @Slot(object)
    def _on_art_options(self, options) -> None:
        self._art_loading = False
        self._art_error = ""
        self._art_options = list(options) if isinstance(options, list) else []
        if not self._art_options:
            self._art_error = "No portrait artwork found for this game."
        self.artOptionsChanged.emit()

    @Slot(str, str)
    def _on_art_downloaded(self, game_id: str, path: str) -> None:
        self._prefs.set_cover(game_id, path)
        self._art_loading = False
        self._art_options = []
        self.artOptionsChanged.emit()
        self._notify_cover(game_id)
        self.artChanged.emit()

    @Slot(str)
    def _on_art_failed(self, message: str) -> None:
        self._art_loading = False
        self._art_error = message
        self.artOptionsChanged.emit()

    @Property(QObject, constant=True)
    def sessions(self) -> SessionTracker:
        return self._sessions

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
            and (not self._favorites_only or self._prefs.is_favorite(game.id))
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

    def _session_ended(self, session, seconds: float) -> None:
        """Persist a finished session for a non-Steam game."""
        if session.source == "steam":
            return
        game = next((entry for entry in self._all if entry.id == session.game_id), None)
        if game is None:
            return

        playtime.add_seconds(game, seconds)
        summary = playtime.summary_for(game)
        try:
            total = int(summary.get("seconds") or 0)
        except (TypeError, ValueError):
            total = 0
        try:
            last_played = int(summary.get("last_played") or 0)
        except (TypeError, ValueError):
            last_played = 0

        minutes = total // 60
        if minutes == game.playtime_minutes and (
            not last_played or last_played == game.last_played
        ):
            return

        updated = replace(
            game,
            playtime_minutes=minutes,
            last_played=last_played or game.last_played,
        )
        self._all = [updated if entry.id == game.id else entry for entry in self._all]
        self._visible = [
            updated if entry.id == game.id else entry for entry in self._visible
        ]
        self.playtimeChanged.emit()

    def _cover_url(self, game: Game) -> str:
        override = self._prefs.cover_for(game.id)
        if override and Path(override).is_file():
            return "image://art/" + covers.art_key(override)
        return "image://cover/" + covers.cover_key(
            game.title, game.app_id, self._art_revision
        )

    @Slot(int)
    def launch(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        try:
            pid = launch_game(game)
        except (LaunchError, OSError) as exc:
            self.failed.emit(str(exc))
            return

        self._sessions.start(game, pid, self._cover_url(game))

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

    @Slot(str, result=str)
    def localPath(self, url: str) -> str:
        return QUrl(url).toLocalFile() if url.startswith("file:") else url

    @Slot(str, result="QStringList")
    def executablesIn(self, folder_url: str) -> list[str]:
        folder = QUrl(folder_url).toLocalFile() if folder_url.startswith("file:") else folder_url
        return [str(path) for path in manual.find_executables(Path(folder))]

    @Slot(str, str, str, result=bool)
    def addManualGame(self, title: str, folder_url: str, executable: str) -> bool:
        folder = QUrl(folder_url).toLocalFile() if folder_url.startswith("file:") else folder_url
        try:
            manual.ManualLibrary().add(title, folder, executable)
        except Exception as exc:  # noqa: BLE001 - reported as a toast
            self.failed.emit(str(exc))
            return False
        self._source = "local"
        self.refresh()
        return True

    @Slot(int, result=bool)
    def isManual(self, row: int) -> bool:
        game = self._at(row)
        return game is not None and game.source == "local"

    @Slot(int)
    def removeManualGame(self, row: int) -> None:
        game = self._at(row)
        if game is None or game.source != "local":
            return
        manual.ManualLibrary().remove(game.id)
        self.refresh()

    @Slot(int)
    def toggleFavorite(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._prefs.toggle_favorite(game.id)
        if self._favorites_only and not self._prefs.is_favorite(game.id):
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
        return {
            "title": game.title,
            "source": game.source_label,
            "appId": game.app_id,
            "meta": f"{game.source_label.upper()} · {game.app_id or '—'} · {_tag(game.title)}",
            "cover": self._cover_url(game),
            "installed": game.installed,
            "favorite": self._prefs.is_favorite(game.id),
            "sizeText": f"{game.size_gb:.1f} GB" if game.size_gb else "",
            "playtimeText": _playtime_text(game.playtime_minutes),
            "lastPlayed": _played_text(game.last_played),
            "installDir": str(game.install_dir) if game.install_dir else "",
            "hasFolder": bool(game.install_dir and game.install_dir.is_dir()),
        }
