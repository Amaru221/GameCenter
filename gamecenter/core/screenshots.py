"""Screenshots of the running game.

The keyboard shortcut is registered as a system-wide hotkey on Windows so it
keeps working while the game owns the foreground. On other platforms (or when
the system rejects the combination) QML installs a local ``Shortcut`` instead.
Screenshots are plain PNG files under ``%APPDATA%/GameCenter/screenshots``.
"""

from __future__ import annotations

import ctypes
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QAbstractNativeEventFilter,
    QCoreApplication,
    QObject,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication

from .i18n import tr
from .preferences import SCREENSHOT_SHORTCUTS, config_dir
from . import screenshot_store

# Qt key sequences for the local Shortcut fallback.
QT_SEQUENCES = {
    "ctrl+pagedown": "Ctrl+PageDown",
    "ctrl+f12": "Ctrl+F12",
    "f12": "F12",
    "printscreen": "Print",
    "ctrl+shift+s": "Ctrl+Shift+S",
    "none": "",
}

# Win32 virtual-key codes and modifiers for RegisterHotKey.
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_NOREPEAT = 0x4000
_VK_PAGEDOWN = 0x22
_VK_SNAPSHOT = 0x2C
_VK_F12 = 0x7B
_VK_S = 0x53
_WM_HOTKEY = 0x0312
HOTKEY_ID = 0x4743  # "GC"

_WIN_HOTKEYS = {
    "ctrl+pagedown": (_MOD_CONTROL, _VK_PAGEDOWN),
    "ctrl+f12": (_MOD_CONTROL, _VK_F12),
    "f12": (0, _VK_F12),
    "printscreen": (0, _VK_SNAPSHOT),
    "ctrl+shift+s": (_MOD_CONTROL | _MOD_SHIFT, _VK_S),
}


class _HotkeyFilter(QAbstractNativeEventFilter):
    """Turns the native ``WM_HOTKEY`` message into a Python callback."""

    def __init__(self, callback) -> None:
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, eventType, message):  # noqa: N802 (Qt API)
        try:
            kind = bytes(eventType)
        except (TypeError, ValueError):
            kind = b""
        if kind not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0
        if sys.platform != "win32":
            return False, 0
        try:
            from ctypes import wintypes

            address = int(message)
            msg = ctypes.cast(address, ctypes.POINTER(wintypes.MSG)).contents
        except (TypeError, ValueError, OSError):
            return False, 0
        if msg.message == _WM_HOTKEY and int(msg.wParam) == HOTKEY_ID:
            self._callback()
            return True, 0
        return False, 0


def _user32():
    if sys.platform != "win32":
        return None
    try:
        from ctypes import wintypes

        library = ctypes.WinDLL("user32", use_last_error=True)
        library.RegisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            wintypes.UINT,
            wintypes.UINT,
        ]
        library.RegisterHotKey.restype = wintypes.BOOL
        library.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        library.UnregisterHotKey.restype = wintypes.BOOL
        return library
    except (OSError, AttributeError):
        return None


def _safe_name(title: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", title or "").strip("-._")
    return (value[:60] or "GameCenter")


class ScreenshotManager(QObject):
    changed = Signal()
    saved = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        prefs,
        sessions,
        parent=None,
        directory: Path | str | None = None,
        register_hotkey: bool = True,
    ) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._sessions = sessions
        self._directory = (
            Path(directory) if directory is not None else config_dir() / "screenshots"
        )
        self._last_path = ""
        self._last_capture: dict = {}
        self._registered = False
        self._error = ""
        self._user32 = None
        self._filter = None
        self._last_has_session = False
        self._hotkeys_enabled = (
            register_hotkey
            and sys.platform == "win32"
            and not os.environ.get("GC_NO_HOTKEYS")
        )
        if self._hotkeys_enabled:
            self._user32 = _user32()
            self._install_filter()
            self._apply_hotkey()
        changed = getattr(self._sessions, "changed", None)
        if changed is not None:
            changed.connect(self._on_sessions_changed)
        self._last_has_session = self._has_session()

    # -- QML API ----------------------------------------------------------

    @Property(str, notify=changed)
    def shortcut(self) -> str:
        return self._prefs.screenshot_shortcut

    @Slot(str)
    def setShortcut(self, value: str) -> None:
        value = str(value or "").lower()
        if value not in SCREENSHOT_SHORTCUTS:
            return
        if value != self._prefs.screenshot_shortcut:
            self._prefs.screenshot_shortcut = value
        self._apply_hotkey()
        self.changed.emit()

    @Property(str, notify=changed)
    def shortcutSequence(self) -> str:
        return QT_SEQUENCES.get(self._prefs.screenshot_shortcut, "")

    @Property(bool, notify=changed)
    def localShortcutEnabled(self) -> bool:
        return bool(self.shortcutSequence) and not self._registered

    @Property(bool, notify=changed)
    def registered(self) -> bool:
        return self._registered

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    @Property(str, constant=True)
    def directory(self) -> str:
        return str(self._directory)

    @Property(str, notify=changed)
    def lastPath(self) -> str:
        return self._last_path

    @Property("QVariantMap", notify=changed)
    def lastCapture(self) -> dict:
        return dict(self._last_capture)

    @Slot(result=str)
    def captureIfPlaying(self) -> str:
        session = self._active_session()
        title = str(session.get("title") or "")
        if not title:
            return ""
        return self._capture(title, session)

    @Slot(result=str)
    def capture(self) -> str:
        session = self._active_session()
        return self._capture(str(session.get("title") or "GameCenter"), session)

    @Slot()
    def openFolder(self) -> None:
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._directory)))

    # -- capture ----------------------------------------------------------

    def _active_session(self) -> dict:
        try:
            entries = list(self._sessions.list)
        except (AttributeError, TypeError):
            return {}
        if not entries:
            return {}
        return dict(entries[-1])

    def _has_session(self) -> bool:
        try:
            return bool(list(self._sessions.list))
        except (AttributeError, TypeError):
            return False

    def _screen(self):
        app = QGuiApplication.instance()
        if app is None:
            return None
        screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen

    def _grab(self):
        screen = self._screen()
        if screen is None:
            return None
        return screen.grabWindow(0)

    def _capture(self, title: str, session: dict | None = None) -> str:
        session = session or {}
        pixmap = self._grab()
        if pixmap is None or pixmap.isNull():
            self.failed.emit(tr("Couldn't capture the screen."))
            return ""
        try:
            path = self._destination(title)
            if not pixmap.save(str(path), "PNG"):
                raise OSError(path)
        except OSError:
            self.failed.emit(tr("Couldn't capture the screen."))
            return ""
        taken_at = int(time.time())
        try:
            screenshot_store.record(
                path,
                game_id=str(session.get("gameId") or ""),
                session_id=str(session.get("id") or ""),
                session_started_at=session.get("startedAt") or 0,
                title=title,
                taken_at=taken_at,
            )
        except Exception:  # noqa: BLE001 - the PNG is already safe on disk
            pass

        screen = self._screen()
        geometry = screen.geometry() if screen is not None else None
        self._last_path = str(path)
        self._last_capture = {
            "path": str(path),
            "url": path.as_uri(),
            "gameId": str(session.get("gameId") or ""),
            "sessionId": str(session.get("id") or ""),
            "title": title,
            "takenAt": taken_at,
            "screenX": geometry.x() if geometry is not None else 0,
            "screenY": geometry.y() if geometry is not None else 0,
            "screenWidth": geometry.width() if geometry is not None else 0,
            "screenHeight": geometry.height() if geometry is not None else 0,
        }
        self.changed.emit()
        self.saved.emit(str(path))
        return str(path)

    def _destination(self, title: str) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        name = f"{_safe_name(title)}-{stamp}"
        path = self._directory / f"{name}.png"
        index = 2
        while path.exists():
            path = self._directory / f"{name}-{index}.png"
            index += 1
        return path

    # -- global hotkey ----------------------------------------------------

    def _install_filter(self) -> None:
        app = QCoreApplication.instance()
        if app is None:
            return
        self._filter = _HotkeyFilter(self._on_hotkey)
        app.installNativeEventFilter(self._filter)
        app.aboutToQuit.connect(self._unregister)

    def _on_hotkey(self) -> None:
        self.captureIfPlaying()

    def _on_sessions_changed(self) -> None:
        has_session = self._has_session()
        if has_session == self._last_has_session:
            return
        self._last_has_session = has_session
        self._apply_hotkey()
        self.changed.emit()

    def _apply_hotkey(self) -> None:
        self._unregister()
        self._error = ""
        if (
            not self._hotkeys_enabled
            or self._user32 is None
            or not self._has_session()
        ):
            self._registered = False
            return
        key = self._prefs.screenshot_shortcut
        if key == "none":
            self._registered = False
            return
        mods, vk = _WIN_HOTKEYS.get(key, (0, 0))
        if not vk:
            self._registered = False
            return
        try:
            registered = bool(
                self._user32.RegisterHotKey(
                    None, HOTKEY_ID, mods | _MOD_NOREPEAT, vk
                )
            )
        except OSError:
            registered = False
        self._registered = registered
        if not registered:
            self._error = tr("This shortcut is already in use.")

    @Slot()
    def _unregister(self) -> None:
        if self._registered and self._user32 is not None:
            try:
                self._user32.UnregisterHotKey(None, HOTKEY_ID)
            except OSError:
                pass
        self._registered = False

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        try:
            self._unregister()
        except Exception:  # noqa: BLE001 - never fail during destruction
            pass
