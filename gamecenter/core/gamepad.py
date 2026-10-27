"""XInput gamepad support for the Big Picture mode.

No extra dependency is needed on Windows: the XInput DLL is loaded with
``ctypes`` and polled from a QTimer. The rest of the app listens to the
semantic signals (navigate/accept/back/menu/...), so the UI never deals with
raw button masks.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time

from PySide6.QtCore import Property, QObject, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication

# XInput button masks.
DPAD_UP = 0x0001
DPAD_DOWN = 0x0002
DPAD_LEFT = 0x0004
DPAD_RIGHT = 0x0008
BUTTON_START = 0x0010
BUTTON_BACK = 0x0020
LEFT_SHOULDER = 0x0100
RIGHT_SHOULDER = 0x0200
BUTTON_A = 0x1000
BUTTON_B = 0x2000
BUTTON_X = 0x4000
BUTTON_Y = 0x8000

DEADZONE = 0.55
REPEAT_FIRST = 0.35
REPEAT_NEXT = 0.13
POLL_MS = 33
SCREENSHOT_HOLD_SECONDS = 5.0


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


def _load_xinput():
    if sys.platform != "win32":
        return None
    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            library = ctypes.WinDLL(name)
        except OSError:
            continue
        try:
            library.XInputGetState.argtypes = [
                ctypes.c_uint,
                ctypes.POINTER(XINPUT_STATE),
            ]
            library.XInputGetState.restype = ctypes.c_uint
        except AttributeError:
            continue
        return library
    return None


def _axis_navigation(pad) -> tuple[int, int]:
    """Map a D-pad/stick state to one cardinal direction."""
    buttons = int(getattr(pad, "wButtons", 0))
    if buttons & DPAD_LEFT:
        return -1, 0
    if buttons & DPAD_RIGHT:
        return 1, 0
    if buttons & DPAD_UP:
        return 0, -1
    if buttons & DPAD_DOWN:
        return 0, 1

    lx = float(getattr(pad, "sThumbLX", 0)) / 32767.0
    ly = float(getattr(pad, "sThumbLY", 0)) / 32767.0
    if abs(lx) >= DEADZONE:
        return (1 if lx > 0 else -1), 0
    if abs(ly) >= DEADZONE:
        return 0, (-1 if ly > 0 else 1)
    return 0, 0


class GamepadManager(QObject):
    connectedChanged = Signal()
    navigate = Signal(int, int)
    accept = Signal()
    back = Signal()
    menu = Signal()
    pageLeft = Signal()
    pageRight = Signal()
    favorite = Signal()
    details = Signal()
    screenshot = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._library = None if os.environ.get("GC_NO_GAMEPAD") else _load_xinput()
        self._connected = False
        self._index = 0
        self._last_buttons = 0
        self._nav_dx = 0
        self._nav_dy = 0
        self._nav_next = 0.0
        self._back_down_at = 0.0
        self._back_screenshot = False
        self._cursor_hidden = False
        self._cursor_pos = QCursor.pos()
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._poll)
        if self._library is not None:
            self._timer.start()
        app = QGuiApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.showCursor)

    @Property(bool, notify=connectedChanged)
    def connected(self) -> bool:
        return self._connected

    @Property(float, constant=True)
    def screenshotHoldSeconds(self) -> float:
        return SCREENSHOT_HOLD_SECONDS

    def _hide_cursor(self) -> None:
        if self._cursor_hidden:
            return
        app = QGuiApplication.instance()
        if app is None:
            return
        app.setOverrideCursor(QCursor(Qt.BlankCursor))
        self._cursor_hidden = True
        self._cursor_pos = QCursor.pos()

    @Slot()
    def showCursor(self) -> None:
        if not self._cursor_hidden:
            return
        app = QGuiApplication.instance()
        if app is not None:
            app.restoreOverrideCursor()
        self._cursor_hidden = False

    def _poll_cursor(self) -> None:
        if not self._cursor_hidden:
            return
        position = QCursor.pos()
        if position != self._cursor_pos:
            self._cursor_pos = position
            self.showCursor()

    def _read(self):
        if self._library is None:
            return None
        for offset in range(4):
            index = (self._index + offset) % 4
            state = XINPUT_STATE()
            try:
                result = self._library.XInputGetState(
                    index, ctypes.byref(state)
                )
            except Exception:  # noqa: BLE001 - a broken driver must not crash
                return None
            if result == 0:
                self._index = index
                return state
        return None

    def _poll(self) -> None:
        self._poll_cursor()
        state = self._read()
        if state is None:
            if self._connected:
                self._connected = False
                self.connectedChanged.emit()
            self._last_buttons = 0
            self._nav_dx = 0
            self._nav_dy = 0
            self._back_down_at = 0.0
            self._back_screenshot = False
            return

        if not self._connected:
            self._connected = True
            self.connectedChanged.emit()

        pad = state.Gamepad
        buttons = int(pad.wButtons)
        fresh = buttons & ~self._last_buttons
        self._update_back_hold(buttons, time.monotonic())
        self._last_buttons = buttons
        if fresh:
            self._hide_cursor()

        if fresh & BUTTON_A:
            self.accept.emit()
        if fresh & BUTTON_B:
            self.back.emit()
        if fresh & BUTTON_X:
            self.favorite.emit()
        if fresh & BUTTON_Y:
            self.details.emit()
        if fresh & BUTTON_START:
            self.menu.emit()
        if fresh & BUTTON_BACK:
            self.back.emit()
        if fresh & LEFT_SHOULDER:
            self.pageLeft.emit()
        if fresh & RIGHT_SHOULDER:
            self.pageRight.emit()

        self._update_navigation(pad)

    def _update_back_hold(self, buttons: int, now: float) -> None:
        """Select/View held for five seconds asks for a screenshot."""
        if buttons & BUTTON_BACK:
            if not self._last_buttons & BUTTON_BACK:
                self._back_down_at = now
                self._back_screenshot = False
            elif (
                not self._back_screenshot
                and self._back_down_at > 0.0
                and now - self._back_down_at >= SCREENSHOT_HOLD_SECONDS
            ):
                self._back_screenshot = True
                self.screenshot.emit()
            return
        self._back_down_at = 0.0
        self._back_screenshot = False

    def _update_navigation(self, pad) -> None:
        now = time.monotonic()
        dx, dy = _axis_navigation(pad)
        if dx == 0 and dy == 0:
            self._nav_dx = 0
            self._nav_dy = 0
            return
        if (dx, dy) != (self._nav_dx, self._nav_dy):
            self._nav_dx = dx
            self._nav_dy = dy
            self._nav_next = now + REPEAT_FIRST
            self._hide_cursor()
            self.navigate.emit(dx, dy)
        elif now >= self._nav_next:
            self._nav_next = now + REPEAT_NEXT
            self._hide_cursor()
            self.navigate.emit(dx, dy)
