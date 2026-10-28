"""Screenshots of the running game.

The keyboard shortcut is registered as a system-wide hotkey on Windows so it
keeps working while the game owns the foreground. On other platforms (or when
the system rejects the combination) QML installs a local ``Shortcut`` instead.
Screenshots are plain PNG files under ``%APPDATA%/GameCenter/screenshots``.

Shortcuts can be customised: ``startRecording()`` puts the manager in listen
mode, ``recordKey()`` turns the next key press into a canonical sequence and
``setShortcut()`` accepts any valid combination directly.
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

from . import screenshot_store, shortcuts
from .i18n import tr
from .preferences import config_dir

# RegisterHotKey flags (winuser.h).
_MOD_NOREPEAT = 0x4000
_WM_HOTKEY = 0x0312
HOTKEY_ID = 0x4743  # "GC"


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
        self._recording = False
        self._last_key_press = ""
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

    @Property(str, notify=changed)
    def shortcutLabel(self) -> str:
        return shortcuts.display(self._prefs.screenshot_shortcut)

    @Slot(str)
    def setShortcut(self, value: str) -> None:
        canonical = shortcuts.normalize(value)
        if canonical is None:
            self._error = tr("That combination can't be used.")
            self.changed.emit()
            return
        if canonical != self._prefs.screenshot_shortcut:
            self._prefs.screenshot_shortcut = canonical
        self._error = ""
        self._apply_hotkey()
        self.changed.emit()

    @Slot()
    def clearShortcut(self) -> None:
        self.setShortcut("")

    @Property(bool, notify=changed)
    def recording(self) -> bool:
        return self._recording

    @Property(str, notify=changed)
    def lastKeyPress(self) -> str:
        """Raw combination of the last key press while recording.

        Useful when a controller/macro sends keys the app cannot register: the
        chip shows exactly what arrived.
        """
        return self._last_key_press

    @Slot()
    def startRecording(self) -> None:
        if self._recording:
            return
        self._recording = True
        self._error = ""
        self._last_key_press = ""
        # Let the OS see the combination the user wants to capture.
        self._unregister()
        self.changed.emit()

    @Slot()
    def cancelRecording(self) -> None:
        if not self._recording:
            return
        self._recording = False
        self._apply_hotkey()
        self.changed.emit()

    @Slot(int, int, result=str)
    def recordKey(self, key: int, modifiers: int) -> str:
        """Store the pressed combination; returns the canonical sequence."""
        if not self._recording:
            return ""
        if int(key) in shortcuts.IGNORED_KEYS:
            return ""
        canonical = shortcuts.from_key(key, modifiers)
        self._last_key_press = shortcuts.prettify(
            shortcuts.raw_from_key(key, modifiers)
        )
        if canonical is None:
            self._error = tr("Add a modifier (Ctrl, Alt or Shift) or use an F-key.")
            self.changed.emit()
            return ""
        self._recording = False
        self._last_key_press = shortcuts.display(canonical)
        self._prefs.screenshot_shortcut = canonical
        self._error = ""
        self._apply_hotkey()
        self.changed.emit()
        return canonical

    @Property(str, notify=changed)
    def shortcutSequence(self) -> str:
        return shortcuts.normalize(self._prefs.screenshot_shortcut) or ""

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
            or self._recording
            or not self._has_session()
        ):
            self._registered = False
            return
        sequence = shortcuts.normalize(self._prefs.screenshot_shortcut)
        if not sequence:
            self._registered = False
            return
        combo = shortcuts.to_vk(sequence)
        if combo is None:
            self._registered = False
            self._error = tr("This combination can only be used while GameCenter has focus.")
            return
        mods, vk = combo
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
