"""The library as a Qt list model, with filtering, sorting and launching."""

from __future__ import annotations

import hashlib
import re
import threading
import time
from dataclasses import replace
from datetime import datetime
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
from PySide6.QtGui import QGuiApplication, QImage

from .. import __version__
from ..core import (
    credentials,
    i18n,
    manual,
    metadata,
    playtime,
    profiles,
    screenshot_store,
    stats as stats_module,
    steamgriddb,
    updater,
)
from ..core.i18n import Translator, tr
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
from ..core.sources import scan_all, scan_source
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
ROLE_CARTRIDGE_COLOR = Qt.UserRole + 10

ART_BATCH = 5

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
        return tr("{minutes} min played", minutes=minutes)
    hours = minutes // 60
    if hours == 1:
        return tr("1 hour played")
    return tr("{hours} hours played", hours=f"{hours:,}")


def _played_text(timestamp: int) -> str:
    if not timestamp:
        return tr("Never played")
    days = (time.time() - timestamp) / 86400
    if days < 1:
        return tr("Played today")
    if days < 2:
        return tr("Played yesterday")
    if days < 30:
        return tr("Played {days} days ago", days=int(days))
    if days < 365:
        months = int(days // 30)
        if months == 1:
            return tr("Played {months} month ago", months=months)
        return tr("Played {months} months ago", months=months)
    years = int(days // 365)
    if years == 1:
        return tr("Played {years} year ago", years=years)
    return tr("Played {years} years ago", years=years)


def _duration_text(seconds: int) -> str:
    minutes = max(1, int(round(max(0, seconds) / 60)))
    if minutes < 60:
        return tr("{minutes} min", minutes=minutes)
    hours, rest = divmod(minutes, 60)
    if rest:
        return tr("{hours} h {minutes} min", hours=hours, minutes=rest)
    return tr("{hours} h", hours=hours)


class LibraryModel(QAbstractListModel):
    changed = Signal()
    failed = Signal(str)
    notice = Signal(str)
    artReady = Signal(str)
    appearanceChanged = Signal()
    artOptionsChanged = Signal()
    artChanged = Signal()
    credentialsChanged = Signal()
    updatesChanged = Signal()
    playtimeChanged = Signal()
    detailsChanged = Signal()
    _artOptionsReady = Signal(object, int, str, bool)
    _artDownloaded = Signal(str, str)
    _artFailed = Signal(str, str)
    _detailsReady = Signal(str, str, object)
    _updateChecked = Signal(object, str)
    _updateProgress = Signal(int, int)
    _updateDownloaded = Signal(str)
    _updateFailed = Signal(str)

    def __init__(
        self, download_art: bool = True, settings_path: Path | None = None
    ) -> None:
        super().__init__()
        self._all: list[Game] = []
        self._visible: list[Game] = []
        self._query = ""
        self._source = ""
        self._sort = "recent"
        self._prefs = Preferences(settings_path)
        self._i18n = Translator(self._prefs)
        i18n.set_active(self._i18n)
        self._i18n.languageChanged.connect(self._on_language_changed)
        self._all = [
            game for game in scan_all() if not self._prefs.is_hidden(game.id)
        ]
        self._favorites_only = False
        self._art_options_all: list[dict] = []
        self._art_visible = 0
        self._art_page = 0
        self._art_page_full = False
        self._art_has_more = False
        self._art_loading = False
        self._art_loading_more = False
        self._art_game: Game | None = None
        self._art_error = ""
        self._credentials_message = ""
        self._has_key = bool(credentials.get_key())
        self._artOptionsReady.connect(self._on_art_options, Qt.QueuedConnection)
        self._artDownloaded.connect(self._on_art_downloaded, Qt.QueuedConnection)
        self._artFailed.connect(self._on_art_failed, Qt.QueuedConnection)
        self._details: dict[tuple[str, str], dict] = {}
        self._details_loaded: set[tuple[str, str]] = set()
        self._details_loading: set[tuple[str, str]] = set()
        self._detailsReady.connect(self._on_details_ready, Qt.QueuedConnection)
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
        self._update_downloading = False
        self._update_installing = False
        self._update_progress = 0.0
        self._update_downloaded_bytes = 0
        self._update_total_bytes = 0
        self._update_installer = ""
        self._update_status = ""
        self._updateChecked.connect(self._on_update_checked, Qt.QueuedConnection)
        self._updateProgress.connect(self._on_update_progress, Qt.QueuedConnection)
        self._updateDownloaded.connect(self._on_update_downloaded, Qt.QueuedConnection)
        self._updateFailed.connect(self._on_update_failed, Qt.QueuedConnection)
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
            return self._source_label(game)
        if role == ROLE_APP_ID:
            return game.app_id
        if role == ROLE_META:
            return self._meta_line(game)
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
        if role == ROLE_CARTRIDGE_COLOR:
            return self._cartridge_color(game)
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
            ROLE_CARTRIDGE_COLOR: QByteArray(b"cartridgeColor"),
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

    @Property(int, notify=changed)
    def hiddenCount(self) -> int:
        return len(self._prefs.hidden_games)

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
        self._refresh_cartridge_colors()

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
        return self._art_options_all[: self._art_visible]

    @Property(bool, notify=artOptionsChanged)
    def artLoading(self) -> bool:
        return self._art_loading

    @Property(bool, notify=artOptionsChanged)
    def artLoadingMore(self) -> bool:
        return self._art_loading_more

    @Property(bool, notify=artOptionsChanged)
    def artHasMore(self) -> bool:
        return self._art_has_more

    @Property(int, notify=artOptionsChanged)
    def artTotal(self) -> int:
        return len(self._art_options_all)

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
    def updateDownloading(self) -> bool:
        return self._update_downloading

    @Property(bool, notify=updatesChanged)
    def updateInstalling(self) -> bool:
        return self._update_installing

    @Property(bool, notify=updatesChanged)
    def updateReady(self) -> bool:
        return (
            bool(self._update_installer)
            and not self._update_downloading
            and not self._update_installing
        )

    @Property(float, notify=updatesChanged)
    def updateProgress(self) -> float:
        return self._update_progress

    @Property(str, notify=updatesChanged)
    def updateStatus(self) -> str:
        return self._update_status

    @Property(str, notify=updatesChanged)
    def updateBytesText(self) -> str:
        if self._update_installing:
            return tr("Installing...")
        if self._update_downloading:
            done = self._update_downloaded_bytes / (1024 * 1024)
            if self._update_total_bytes:
                total = self._update_total_bytes / (1024 * 1024)
                return f"{done:.1f} / {total:.1f} MB"
            return f"{done:.1f} MB"
        return ""

    @Property(str, notify=updatesChanged)
    def updateSizeText(self) -> str:
        info = self._update_available
        if info is None or not info.installer_size:
            return ""
        return f"{info.installer_size / (1024 * 1024):.1f} MB"

    @Property(bool, notify=updatesChanged)
    def checkUpdatesEnabled(self) -> bool:
        return self._prefs.check_updates

    @Property(str, notify=updatesChanged)
    def lastUpdateCheckText(self) -> str:
        stamp = self._prefs.last_update_check
        if not stamp:
            return tr("Never")
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
    def downloadUpdate(self) -> None:
        info = self._update_available
        if info is None:
            self._update_error = tr("No update available.")
            self.updatesChanged.emit()
            return
        if self._update_downloading or self._update_installing:
            return
        if not info.installer_url:
            self._update_error = tr("This release doesn't include a Windows installer.")
            self.updatesChanged.emit()
            return

        self._update_downloading = True
        self._update_installing = False
        self._update_progress = 0.0
        self._update_downloaded_bytes = 0
        self._update_total_bytes = int(info.installer_size or 0)
        self._update_installer = ""
        self._update_status = tr("Downloading update...")
        self._update_error = ""
        self.updatesChanged.emit()

        def work():
            try:
                path = updater.download_installer(
                    info,
                    progress=lambda done, total: self._updateProgress.emit(
                        done, total
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - reported to the UI
                self._updateFailed.emit(str(exc))
                return
            self._updateDownloaded.emit(str(path))

        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def installUpdate(self) -> None:
        if self._update_installing:
            return
        installer = Path(self._update_installer) if self._update_installer else None
        if installer is None or not installer.is_file():
            self._on_update_failed(tr("The update file is missing."))
            return

        self._update_downloading = False
        self._update_installing = True
        self._update_progress = 1.0
        self._update_status = tr("Installing update. GameCenter will restart...")
        self._update_error = ""
        self.updatesChanged.emit()

        try:
            updater.launch_installer(installer)
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            self._on_update_failed(str(exc))
            return
        QTimer.singleShot(900, QCoreApplication.quit)

    @Slot()
    def dismissUpdate(self) -> None:
        if self._update_downloading or self._update_installing:
            return
        self._update_dismissed = True
        self.updatesChanged.emit()

    @Slot(int, int)
    def _on_update_progress(self, downloaded: int, total: int) -> None:
        if not self._update_downloading:
            return
        self._update_downloaded_bytes = max(0, int(downloaded))
        if total:
            self._update_total_bytes = int(total)
        if self._update_total_bytes:
            self._update_progress = min(
                1.0, self._update_downloaded_bytes / self._update_total_bytes
            )
        else:
            self._update_progress = 0.0
        self.updatesChanged.emit()

    @Slot(str)
    def _on_update_downloaded(self, path: str) -> None:
        self._update_downloading = False
        self._update_installer = path
        self._update_progress = 1.0
        self._update_status = tr("Update downloaded. Installing...")
        self.updatesChanged.emit()
        QTimer.singleShot(600, self.installUpdate)

    @Slot(str)
    def _on_update_failed(self, message: str) -> None:
        self._update_downloading = False
        self._update_installing = False
        self._update_progress = 0.0
        self._update_status = ""
        self._update_error = message
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
            self._update_downloading = False
            self._update_installing = False
            self._update_progress = 0.0
            self._update_downloaded_bytes = 0
            self._update_total_bytes = int(info.installer_size or 0) if info else 0
            self._update_installer = ""
            self._update_status = ""
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
            tr("Saved to the system credential store.")
            if saved
            else tr("Couldn't save to the credential store.")
        )
        self.credentialsChanged.emit()

    @Slot()
    def clearSteamGridKey(self) -> None:
        credentials.clear_key()
        self._has_key = False
        self._credentials_message = tr("Key removed.")
        self.credentialsChanged.emit()

    @Slot(int)
    def loadDetails(self, row: int) -> None:
        """Fetch (or load from cache) the description for one row."""
        game = self._at(row)
        if game is not None:
            self._load_details(game)

    @Slot(str)
    def loadDetailsById(self, game_id: str) -> None:
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is not None:
            self._load_details(game)

    def _load_details(self, game: Game) -> None:
        language = self._i18n.language
        key = (game.id, language)
        if key in self._details_loaded or key in self._details_loading:
            return

        cached = metadata.cached(game, language)
        if cached is not None:
            self._details[key] = cached
            self._details_loaded.add(key)
            self.detailsChanged.emit()
            return

        self._details_loading.add(key)

        def work():
            try:
                data = metadata.fetch(game, language)
            except Exception:  # noqa: BLE001 - metadata is optional
                data = {}
            self._detailsReady.emit(game.id, language, data)

        threading.Thread(target=work, daemon=True).start()

    @Slot(str, str, object)
    def _on_details_ready(self, game_id: str, language: str, data) -> None:
        key = (game_id, language)
        self._details_loading.discard(key)
        self._details[key] = data if isinstance(data, dict) else {}
        self._details_loaded.add(key)
        self.detailsChanged.emit()

    @Slot(int)
    def loadArtOptions(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._reset_art_state()
        self._art_game = game
        if not self._has_key:
            self._art_error = tr("Add a SteamGridDB API key in Settings first.")
            self._art_loading = False
            self.artOptionsChanged.emit()
            return

        key = credentials.get_key()
        self._art_loading = True
        self._art_error = ""
        self.artOptionsChanged.emit()

        def work():
            try:
                options, page_full = steamgriddb.grids_page(game, key, 0)
            except Exception as exc:  # noqa: BLE001 - reported to the UI
                self._artFailed.emit(str(exc), game.id)
                return
            self._artOptionsReady.emit(options, 0, game.id, page_full)

        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def loadMoreArtOptions(self) -> None:
        if self._art_loading or self._art_loading_more or not self._art_has_more:
            return

        if self._art_visible < len(self._art_options_all):
            self._art_visible = min(
                self._art_visible + ART_BATCH, len(self._art_options_all)
            )
            self._art_has_more = (
                self._art_page_full or self._art_visible < len(self._art_options_all)
            )
            self.artOptionsChanged.emit()
            return

        game = self._art_game
        key = credentials.get_key()
        if game is None or not key:
            self._art_has_more = False
            self.artOptionsChanged.emit()
            return

        page = self._art_page + 1
        self._art_loading_more = True
        self.artOptionsChanged.emit()

        def work():
            try:
                options, page_full = steamgriddb.grids_page(game, key, page)
            except Exception as exc:  # noqa: BLE001 - reported as a toast
                self._artFailed.emit(str(exc), game.id)
                return
            self._artOptionsReady.emit(options, page, game.id, page_full)

        threading.Thread(target=work, daemon=True).start()

    def _reset_art_state(self) -> None:
        self._art_options_all = []
        self._art_visible = 0
        self._art_page = 0
        self._art_page_full = False
        self._art_has_more = False
        self._art_loading = False
        self._art_loading_more = False
        self._art_game = None
        self._art_error = ""

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
                self._artFailed.emit(str(exc), game.id)
                return
            self._artDownloaded.emit(game.id, str(path))

        threading.Thread(target=work, daemon=True).start()

    @Slot(int)
    def resetArt(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._prefs.set_cover(game.id, None)
        self._reset_art_state()
        self.artOptionsChanged.emit()
        self._notify_cover(game.id)
        self.artChanged.emit()
        self.changed.emit()

    def _notify_cover(self, game_id: str) -> None:
        for row, game in enumerate(self._visible):
            if game.id == game_id:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [ROLE_COVER])
                break

    @Slot(object, int, str, bool)
    def _on_art_options(
        self, options, page: int, game_id: str, page_full: bool
    ) -> None:
        if self._art_game is None or game_id != self._art_game.id:
            return

        if page == 0:
            self._art_options_all = []
            self._art_visible = 0

        known = {str(option.get("id")) for option in self._art_options_all}
        for option in options or []:
            key = str(option.get("id"))
            if key not in known:
                self._art_options_all.append(option)
                known.add(key)

        self._art_page = page
        self._art_page_full = page_full
        self._art_loading = False
        self._art_loading_more = False
        if page == 0:
            self._art_visible = min(ART_BATCH, len(self._art_options_all))
        else:
            self._art_visible = min(
                self._art_visible + ART_BATCH, len(self._art_options_all)
            )
        self._art_has_more = (
            self._art_page_full or self._art_visible < len(self._art_options_all)
        )
        self._art_error = ""
        if not self._art_options_all and not self._art_page_full:
            self._art_error = tr("No portrait artwork found for this game.")
        self.artOptionsChanged.emit()

    @Slot(str, str)
    def _on_art_downloaded(self, game_id: str, path: str) -> None:
        self._prefs.set_cover(game_id, path)
        self._reset_art_state()
        self.artOptionsChanged.emit()
        self._notify_cover(game_id)
        self.artChanged.emit()
        self.changed.emit()

    @Slot(str, str)
    def _on_art_failed(self, message: str, game_id: str) -> None:
        if self._art_game is not None and game_id != self._art_game.id:
            return
        loading_more = self._art_loading_more
        self._art_loading = False
        self._art_loading_more = False
        if loading_more and self._art_options_all:
            self.failed.emit(message)
        else:
            self._art_error = message
        self.artOptionsChanged.emit()

    @Property(QObject, constant=True)
    def sessions(self) -> SessionTracker:
        return self._sessions

    @Property(QObject, constant=True)
    def translator(self) -> Translator:
        return self._i18n

    @Property("QVariantList", notify=changed)
    def sourceOptions(self) -> list[dict]:
        known = [key for key in SOURCE_LABELS if key != "local"]
        known += sorted({game.source for game in self._all} - set(SOURCE_LABELS))
        return [
            {
                "text": SOURCE_LABELS.get(key, key.capitalize()),
                "value": key,
            }
            for key in known
        ]

    @Property("QVariantList", notify=changed)
    def bigPictureGames(self) -> list[dict]:
        rows = sorted(self._all, key=lambda game: game.title.casefold())
        return [
            {
                "id": game.id,
                "title": game.title,
                "source": self._source_label(game),
                "appId": game.app_id,
                "meta": self._meta_line(game),
                "cover": self._cover_url(game),
                "cartridgeColor": self._cartridge_color(game),
                "installed": game.installed,
                "favorite": self._prefs.is_favorite(game.id),
                "sizeText": f"{game.size_gb:.1f} GB" if game.size_gb else "",
                "playtimeText": _playtime_text(game.playtime_minutes),
                "lastPlayed": _played_text(game.last_played),
                "lastPlayedTimestamp": game.last_played,
                "playtimeMinutes": game.playtime_minutes,
            }
            for game in rows
        ]

    def _source_label(self, game: Game) -> str:
        if game.source == "local":
            return tr("Local")
        return SOURCE_LABELS.get(game.source, game.source.capitalize())

    def _meta_line(self, game: Game) -> str:
        return (
            f"{self._source_label(game).upper()} · "
            f"{game.app_id or '—'} · {_tag(game.title)}"
        )

    def _on_language_changed(self) -> None:
        if self._visible:
            top = self.index(0, 0)
            bottom = self.index(len(self._visible) - 1, 0)
            self.dataChanged.emit(top, bottom)
        self.changed.emit()

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
        elif self._sort == "most":
            rows.sort(key=lambda g: (-g.playtime_minutes, g.title.casefold()))
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
        self._all = [
            game for game in scan_all() if not self._prefs.is_hidden(game.id)
        ]
        self._refresh_rows()
        self._start_art()

    @Slot(str)
    def scanStore(self, source: str) -> None:
        if not source:
            self.refresh()
            self.notice.emit(
                tr("Library rescanned: {count} game(s).", count=len(self._all))
            )
            return

        label = SOURCE_LABELS.get(source, source.title())
        try:
            games = scan_source(source)
        except Exception as exc:  # noqa: BLE001 - reported as a toast
            self.failed.emit(
                tr("Couldn't scan {label}: {error}", label=label, error=exc)
            )
            return

        games = [game for game in games if not self._prefs.is_hidden(game.id)]
        self._all = [game for game in self._all if game.source != source] + games
        self._all.sort(key=lambda game: (not game.installed, game.title.casefold()))
        self._refresh_rows()
        self._start_art()
        self.notice.emit(
            tr("{label}: {count} game(s) found.", label=label, count=len(games))
        )

    @Slot()
    def restoreHiddenGames(self) -> None:
        count = self._prefs.clear_hidden_games()
        self.refresh()
        if count:
            self.notice.emit(tr("Restored {count} removed game(s).", count=count))
        else:
            self.notice.emit(tr("No removed games to restore."))

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
        self.changed.emit()

    # -- actions ----------------------------------------------------------

    def _at(self, row: int) -> Game | None:
        if 0 <= row < len(self._visible):
            return self._visible[row]
        return None

    def _session_ended(self, session, seconds: float) -> None:
        """Persist the finished session and its timeline entry."""
        game = next((entry for entry in self._all if entry.id == session.game_id), None)
        if game is None:
            return

        # Every store gets a timeline entry, including Steam (whose total time
        # is still owned by localconfig.vdf).
        playtime.record_session(game, session.started_at, seconds)
        last_played = max(game.last_played, int(session.started_at or 0))

        if session.source != "steam":
            playtime.add_seconds(game, seconds)
            summary = playtime.summary_for(game)
            try:
                total = int(summary.get("seconds") or 0)
            except (TypeError, ValueError):
                total = 0
            try:
                last_played = int(summary.get("last_played") or last_played)
            except (TypeError, ValueError):
                pass
            updated = replace(
                game,
                playtime_minutes=total // 60,
                last_played=last_played or game.last_played,
            )
        else:
            updated = replace(game, last_played=last_played or game.last_played)

        if updated != game:
            self._all = [
                updated if entry.id == game.id else entry for entry in self._all
            ]
            self._visible = [
                updated if entry.id == game.id else entry
                for entry in self._visible
            ]
        self.playtimeChanged.emit()
        self.changed.emit()

    def _find_game(self, game_id: str) -> Game | None:
        return next((entry for entry in self._all if entry.id == game_id), None)

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _catalog_game(
        self,
        game_id: str,
        title,
        source,
        seconds: int = 0,
        last_played: int = 0,
    ) -> Game:
        source_key = str(source or game_id.split(":", 1)[0] or "")
        app_id = game_id.split(":", 1)[1] if ":" in game_id else ""
        return Game(
            id=game_id,
            title=str(title or game_id),
            source=source_key,
            app_id=app_id,
            installed=False,
            playtime_minutes=max(0, int(seconds)) // 60,
            last_played=max(0, int(last_played or 0)),
        )

    def _known_catalog(self) -> dict[str, Game]:
        """Current library plus entries that still have data after being removed."""
        known = {game.id: game for game in self._all}
        history = playtime.all_history()
        meta = {}
        totals = {}
        for game_id, entries in history.items():
            if entries:
                meta[game_id] = entries[-1]
                totals[game_id] = sum(
                    self._safe_int(item.get("seconds")) for item in entries
                )

        for game_id, summary in playtime.all_summaries().items():
            if game_id in known:
                continue
            entry = meta.get(game_id, {})
            known[game_id] = self._catalog_game(
                game_id,
                summary.get("title") or entry.get("title"),
                summary.get("source") or entry.get("source"),
                max(
                    self._safe_int(summary.get("seconds")),
                    totals.get(game_id, 0),
                ),
                self._safe_int(summary.get("last_played")),
            )

        for game_id, entries in history.items():
            if game_id in known or not entries:
                continue
            entry = entries[-1]
            known[game_id] = self._catalog_game(
                game_id,
                entry.get("title"),
                entry.get("source"),
                totals.get(game_id, 0),
                max(self._safe_int(item.get("start")) for item in entries),
            )
        return known

    def _source_game(self, game_id: str) -> Game | None:
        return self._find_game(game_id) or self._known_catalog().get(game_id)

    def _history_seconds(self, game: Game) -> int:
        return sum(
            int(item.get("seconds") or 0) for item in playtime.history_for(game)
        )

    def _summary_seconds(self, game: Game) -> int:
        history = self._history_seconds(game)
        if game.source == "steam":
            native = max(0, int(game.playtime_minutes)) * 60
            return max(native, history)
        return max(playtime.seconds_for(game), history)

    def _sessions_for(self, game: Game) -> int:
        summary = playtime.summary_for(game)
        try:
            count = int(summary.get("sessions") or 0)
        except (TypeError, ValueError):
            count = 0
        return max(count, len(playtime.history_for(game)))

    def _importable_sessions(self, game: Game) -> int:
        """Sessions that will exist after importing, including Steam-only time."""
        covered = self._history_seconds(game)
        missing = max(0, self._summary_seconds(game) - covered)
        return self._sessions_for(game) + (1 if missing else 0)

    def _has_real_cover(self, game: Game) -> bool:
        override = self._prefs.cover_for(game.id)
        if override and Path(override).is_file():
            return True
        if game.source == "steam" and game.app_id.isdigit():
            return artwork.cached_path(game.app_id) is not None
        return False

    def _save_recap_cover(self, game: Game) -> str:
        """Snapshot the visible cover so it survives an uninstall or removal."""
        image = self._art_image(game)
        if image.isNull():
            return ""
        try:
            profiles.cover_dir().mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha1(game.id.encode("utf-8")).hexdigest()[:10]
            target = profiles.cover_dir() / f"{digest}-{time.time_ns()}.png"
            if not image.save(str(target), "PNG"):
                return ""
            return str(target)
        except OSError:
            return ""

    def _cover_url_from_path(self, path: str) -> str:
        if not path:
            return ""
        file = Path(path)
        if not file.is_file():
            return ""
        return "image://art/" + covers.art_key(str(file))

    def _cover_url(self, game: Game) -> str:
        override = self._prefs.cover_for(game.id)
        if override and Path(override).is_file():
            return "image://art/" + covers.art_key(override)
        return "image://cover/" + covers.cover_key(
            game.title, game.app_id, self._art_revision
        )

    def _art_image(self, game: Game) -> QImage:
        override = self._prefs.cover_for(game.id)
        if override and Path(override).is_file():
            image = QImage(override)
            if not image.isNull():
                return image
        if game.source == "steam" and game.app_id.isdigit():
            path = artwork.cached_path(game.app_id)
            if path is not None:
                image = QImage(str(path))
                if not image.isNull():
                    return image
        return covers.render_cover(game.title)

    def _texture_url(self, game: Game) -> str:
        """A PNG label for the 3D cartridge, cached by art + metadata."""
        if self._prefs.cartridge_style != "ds":
            return ""
        override = self._prefs.cover_for(game.id)
        meta = self._meta_line(game)
        key = hashlib.sha1(
            f"{game.id}|{game.title}|{game.app_id}|{self._art_revision}|{override}|{meta}".encode(
                "utf-8"
            )
        ).hexdigest()[:16]
        path = artwork.CACHE / "labels" / f"{key}.png"
        if not path.is_file():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                covers.render_label(
                    self._art_image(game), game.source_label, meta
                ).save(str(path), "PNG")
            except OSError:
                return ""
        return path.as_uri()

    @Slot(int, result=str)
    def launch(self, row: int) -> str:
        game = self._at(row)
        if game is None:
            return ""
        return self._launch(game)

    @Slot(str, result=str)
    def launchById(self, game_id: str) -> str:
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is None:
            return ""
        return self._launch(game)

    def _launch(self, game: Game) -> str:
        try:
            pid = launch_game(game)
        except (LaunchError, OSError) as exc:
            self.failed.emit(str(exc))
            return ""

        session = self._sessions.start(game, pid, self._cover_url(game))
        return session.id

    @Slot(int)
    def openFolder(self, row: int) -> None:
        game = self._at(row)
        if game is not None:
            self._open_folder(game)

    @Slot(str)
    def openFolderById(self, game_id: str) -> None:
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is not None:
            self._open_folder(game)

    def _open_folder(self, game: Game) -> None:
        if not game.install_dir or not game.install_dir.is_dir():
            self.failed.emit(tr("This game has no install folder."))
            return
        try:
            open_folder(game.install_dir)
        except OSError as exc:
            self.failed.emit(str(exc))

    @Slot(int)
    def copyAppId(self, row: int) -> None:
        game = self._at(row)
        if game is not None:
            QGuiApplication.clipboard().setText(game.app_id)

    @Slot(str)
    def copyAppIdById(self, game_id: str) -> None:
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is not None:
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
    def removeGame(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        if game.source == "local":
            manual.ManualLibrary().remove(game.id)
        else:
            self._prefs.hide_game(game.id)
        self._all = [item for item in self._all if item.id != game.id]
        self._refresh_rows()
        self.notice.emit(tr("Removed {title} from the library.", title=game.title))

    @Slot(int)
    def removeManualGame(self, row: int) -> None:
        game = self._at(row)
        if game is not None and game.source == "local":
            self.removeGame(row)

    def _cartridge_color(self, game: Game) -> str:
        return self._prefs.cartridge_color_for(game.id) or self._prefs.cartridge_color

    def _refresh_cartridge_colors(self) -> None:
        if not self._visible:
            return
        top = self.index(0, 0)
        bottom = self.index(len(self._visible) - 1, 0)
        self.dataChanged.emit(top, bottom, [ROLE_CARTRIDGE_COLOR])

    @Slot(int, result=str)
    def cartridgeColorAt(self, row: int) -> str:
        game = self._at(row)
        return self._cartridge_color(game) if game is not None else self._prefs.cartridge_color

    @Slot(int, str)
    def setGameCartridgeColor(self, row: int, value: str) -> None:
        game = self._at(row)
        if game is None:
            return
        self._prefs.set_cartridge_color(game.id, value)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [ROLE_CARTRIDGE_COLOR])

    @Slot(int)
    def resetGameCartridgeColor(self, row: int) -> None:
        game = self._at(row)
        if game is None:
            return
        self._prefs.set_cartridge_color(game.id, None)
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [ROLE_CARTRIDGE_COLOR])

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
        self.changed.emit()

    @Slot(str, result=bool)
    def toggleFavoriteById(self, game_id: str) -> bool:
        value = self._prefs.toggle_favorite(game_id)
        self.changed.emit()
        return value

    @Slot(int, result="QVariantMap")
    def gameAt(self, row: int) -> dict:
        """Everything the detail panel needs about one row."""
        game = self._at(row)
        if game is None:
            return {}
        return self._detail_payload(game)

    @Slot(str, result="QVariantMap")
    def gameDetailById(self, game_id: str) -> dict:
        """The same detail payload, looked up by game id."""
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is None:
            return {}
        return self._detail_payload(game)

    @Slot(str, result=int)
    def rowForId(self, game_id: str) -> int:
        """Current visible row for a game id, or -1 when it is filtered out."""
        for row, game in enumerate(self._visible):
            if game.id == game_id:
                return row
        return -1

    @Slot(str, result="QVariantList")
    def mergeCandidates(self, game_id: str) -> list[dict]:
        """Other known entries that can donate their data to this game."""
        target = self._find_game(game_id)
        if target is None:
            return []
        current_ids = {game.id for game in self._all}
        items = []
        for game in self._known_catalog().values():
            if game.id == game_id:
                continue
            if profiles.get(game.id).get("merged_into"):
                continue
            seconds = self._summary_seconds(game)
            items.append(
                {
                    "id": game.id,
                    "title": game.title,
                    "source": self._source_label(game),
                    "sourceKey": game.source,
                    "cover": self._cover_url(game),
                    "playtimeText": _playtime_text(seconds // 60),
                    "seconds": seconds,
                    "sessions": self._importable_sessions(game),
                    "installed": game.installed,
                    "orphan": game.id not in current_ids,
                    "sameTitle": game.title.casefold() == target.title.casefold(),
                }
            )
        items.sort(
            key=lambda item: (
                not item["sameTitle"],
                item["orphan"],
                -item["seconds"],
                item["title"].casefold(),
                item["source"],
            )
        )
        return items

    @Slot(str, int, result=bool)
    def setGameRating(self, game_id: str, rating: int) -> bool:
        if self._find_game(game_id) is None:
            return False
        profiles.set_rating(game_id, rating)
        self.changed.emit()
        return True

    @Slot(str, str, result=bool)
    def setGameStatus(self, game_id: str, status: str) -> bool:
        if self._find_game(game_id) is None:
            return False
        value = str(status or "").strip().lower()
        if value and value not in profiles.STATUS_SET:
            return False
        profiles.set_status(game_id, value)
        self.changed.emit()
        return True

    @Slot(str, str, bool, result="QVariantMap")
    def mergeGameData(
        self, source_id: str, target_id: str, hide_source: bool = True
    ) -> dict:
        """Move one entry's playtime, sessions and cover into another entry."""
        source = self._source_game(source_id)
        target = self._find_game(target_id)
        if source is None or target is None:
            message = tr("Couldn't unify the data.")
            self.failed.emit(message)
            return {"ok": False, "message": message}
        if source.id == target.id:
            message = tr("Choose a different game to import.")
            self.failed.emit(message)
            return {"ok": False, "message": message}
        source_profile = profiles.get(source.id)
        source_merged = source_profile.get("merged_into")
        if source_merged:
            merged_title = source_profile.get("merged_into_title") or source_merged
            message = tr(
                "This game was already unified into {title}.",
                title=merged_title,
            )
            self.failed.emit(message)
            return {"ok": False, "message": message}
        try:
            message = self._merge_game_data(source, target, hide_source)
        except Exception as exc:  # noqa: BLE001 - reported as a toast
            self.failed.emit(str(exc))
            return {"ok": False, "message": tr("Couldn't unify the data.")}
        self.refresh()
        self.playtimeChanged.emit()
        self.changed.emit()
        self.notice.emit(message)
        return {"ok": True, "message": message, "targetId": target.id}

    def _merge_game_data(
        self, source: Game, target: Game, hide_source: bool
    ) -> str:
        now = int(time.time())
        source_summary = playtime.summary_for(source)
        source_history = playtime.history_for(source)
        source_seconds = self._summary_seconds(source)
        source_sessions = self._sessions_for(source)
        covered = sum(int(item.get("seconds") or 0) for item in source_history)
        missing = max(0, source_seconds - covered)
        effective_sessions = source_sessions + (1 if missing else 0)
        try:
            source_last = int(
                source_summary.get("last_played") or source.last_played or 0
            )
        except (TypeError, ValueError):
            source_last = int(source.last_played or 0)

        target_summary = playtime.summary_for(target)
        try:
            target_seconds = int(target_summary.get("seconds") or 0)
        except (TypeError, ValueError):
            target_seconds = 0
        try:
            target_sessions = int(target_summary.get("sessions") or 0)
        except (TypeError, ValueError):
            target_sessions = 0
        try:
            target_last = int(
                target_summary.get("last_played") or target.last_played or 0
            )
        except (TypeError, ValueError):
            target_last = int(target.last_played or 0)

        source_profile = profiles.get(source.id)
        target_profile = profiles.get(target.id)
        source_rating = source_profile.get("rating")
        if target_profile.get("rating") is None and isinstance(source_rating, int):
            profiles.set_rating(target.id, source_rating)
        source_status = str(source_profile.get("status") or "")
        if not target_profile.get("status") and source_status in profiles.STATUS_SET:
            profiles.set_status(target.id, source_status)

        cover_path = self._save_recap_cover(source)

        if target.source == "steam":
            profiles.add_extra(
                target.id, source_seconds, effective_sessions, source_last
            )
        else:
            playtime.write_summary(
                target,
                target_seconds + source_seconds,
                target_sessions + effective_sessions,
                max(target_last, source_last),
            )

        playtime.move_history(source.id, target.id)
        playtime.clear_summary(source)

        if missing:
            synthetic = replace(target, title=source.title, source=source.source)
            playtime.add_history_entry(
                synthetic, source_last or now, missing, imported=True
            )

        profiles.mark_merged(
            source.id,
            target.id,
            target.title,
            source_seconds,
            effective_sessions,
            cover_path,
            now,
        )
        profiles.add_merged_source(
            target.id,
            {
                "id": source.id,
                "title": source.title,
                "source": self._source_label(source),
                "sourceKey": source.source,
                "at": now,
                "seconds": source_seconds,
                "sessions": effective_sessions,
                "cover_path": cover_path,
                "orphan": self._find_game(source.id) is None,
            },
        )

        if cover_path and not self._has_real_cover(target):
            self._prefs.set_cover(target.id, cover_path)
            self._notify_cover(target.id)
            self.artChanged.emit()

        if hide_source and self._find_game(source.id) is not None:
            self._prefs.hide_game(source.id)

        return tr(
            "{title} data imported into {target}.",
            title=source.title,
            target=target.title,
        )

    def _detail_payload(self, game: Game) -> dict:
        language = self._i18n.language
        key = (game.id, language)
        details = self._details.get(key, {})

        def shot_payload(item: dict) -> dict:
            taken = int(item.get("takenAt") or 0)
            return {
                **item,
                "timeText": (
                    datetime.fromtimestamp(taken).strftime("%H:%M") if taken else ""
                ),
                "dateText": (
                    datetime.fromtimestamp(taken).strftime("%d/%m %H:%M")
                    if taken
                    else ""
                ),
            }

        gallery = [
            shot_payload(item)
            for item in screenshot_store.for_game(game.id, title=game.title)
        ]
        gallery.reverse()  # newest first
        used_shots: set[str] = set()
        history = []
        for item in playtime.history_for(game):
            start = int(item["start"])
            seconds = int(item["seconds"])
            end = start + seconds
            session_shots = []
            for shot in gallery:
                if shot["path"] in used_shots:
                    continue
                started = int(shot.get("sessionStartedAt") or 0)
                matched = abs(started - start) <= 2
                if not matched:
                    matched = start - 2 <= int(shot["takenAt"]) <= end + 2
                if matched:
                    session_shots.append(shot)
                    used_shots.add(shot["path"])
            session_shots.sort(key=lambda shot: (shot["takenAt"], shot["path"]))
            history.append(
                {
                    "timestamp": start,
                    "seconds": seconds,
                    "duration": _duration_text(seconds),
                    "imported": bool(item.get("imported")),
                    "screenshots": session_shots,
                    "previewScreenshots": session_shots[:2],
                    "overflowScreenshot": (
                        session_shots[2] if len(session_shots) > 2 else {}
                    ),
                    "overflowCount": max(0, len(session_shots) - 2),
                }
            )
        history_seconds = sum(item["seconds"] for item in history)

        profile = profiles.get(game.id)
        raw_rating = profile.get("rating")
        try:
            rating = int(raw_rating) if raw_rating is not None else -1
        except (TypeError, ValueError):
            rating = -1

        merged_sources = []
        for item in profile.get("merged_sources") or []:
            if not isinstance(item, dict):
                continue
            try:
                seconds = int(item.get("seconds") or 0)
            except (TypeError, ValueError):
                seconds = 0
            try:
                sessions = int(item.get("sessions") or 0)
            except (TypeError, ValueError):
                sessions = 0
            merged_sources.append(
                {
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("title") or ""),
                    "source": str(item.get("source") or ""),
                    "sourceKey": str(item.get("sourceKey") or ""),
                    "at": int(item.get("at") or 0),
                    "seconds": seconds,
                    "secondsText": _duration_text(seconds) if seconds else "",
                    "sessions": sessions,
                    "orphan": bool(item.get("orphan")),
                    "cover": self._cover_url_from_path(
                        str(item.get("cover_path") or "")
                    ),
                }
            )

        return {
            "id": game.id,
            "title": game.title,
            "source": self._source_label(game),
            "appId": game.app_id,
            "meta": self._meta_line(game),
            "cover": self._cover_url(game),
            "cartridgeColor": self._cartridge_color(game),
            "texture": self._texture_url(game),
            "installed": game.installed,
            "favorite": self._prefs.is_favorite(game.id),
            "sizeText": f"{game.size_gb:.1f} GB" if game.size_gb else "",
            "playtimeText": _playtime_text(game.playtime_minutes),
            "lastPlayed": _played_text(game.last_played),
            "installDir": str(game.install_dir) if game.install_dir else "",
            "hasFolder": bool(game.install_dir and game.install_dir.is_dir()),
            "description": str(details.get("description") or ""),
            "developers": str(details.get("developers") or ""),
            "genres": str(details.get("genres") or ""),
            "releaseDate": str(details.get("releaseDate") or ""),
            "detailsLoaded": key in self._details_loaded,
            "rating": rating,
            "hasRating": rating >= 0,
            "status": str(profile.get("status") or ""),
            "mergedSources": merged_sources,
            "mergedInto": str(profile.get("merged_into") or ""),
            "mergedIntoTitle": str(profile.get("merged_into_title") or ""),
            "history": history,
            "sessionCount": len(history),
            "historyTotalText": _duration_text(history_seconds) if history_seconds else "",
            "screenshots": gallery,
            "screenshotCount": len(gallery),
        }

    @Slot(str, result="QVariantMap")
    def sessionCard(self, game_id: str) -> dict:
        """Cartridge data for a running session, looked up by game id."""
        game = next((entry for entry in self._all if entry.id == game_id), None)
        if game is None:
            return {}
        return {
            "title": game.title,
            "source": self._source_label(game),
            "appId": game.app_id,
            "meta": self._meta_line(game),
            "cover": self._cover_url(game),
            "cartridgeColor": self._cartridge_color(game),
            "installed": game.installed,
        }

    @Slot(str, int, int, result="QVariantMap")
    def stats(self, period: str, year: int, month: int = -1) -> dict:
        """Aggregated playtime data for the Statistics view."""
        covers = {game.id: self._cover_url(game) for game in self._all}
        return stats_module.build(
            self._all,
            period=period,
            year=year,
            language=self._i18n.language,
            month=month,
            covers=covers,
        )

    @Slot(int, result="QVariantMap")
    def yearReview(self, year: int) -> dict:
        """The story-style recap for one year of playtime."""
        covers = {game.id: self._cover_url(game) for game in self._all}
        return stats_module.year_review(
            self._all,
            year,
            language=self._i18n.language,
            covers=covers,
        )
