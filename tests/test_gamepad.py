"""Gamepad mapping helpers (hardware-independent)."""

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from gamecenter.core import gamepad


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _pad(buttons=0, lx=0, ly=0):
    return SimpleNamespace(wButtons=buttons, sThumbLX=lx, sThumbLY=ly)


def test_dpad_maps_to_cardinal_directions() -> None:
    assert gamepad._axis_navigation(_pad(gamepad.DPAD_LEFT)) == (-1, 0)
    assert gamepad._axis_navigation(_pad(gamepad.DPAD_RIGHT)) == (1, 0)
    assert gamepad._axis_navigation(_pad(gamepad.DPAD_UP)) == (0, -1)
    assert gamepad._axis_navigation(_pad(gamepad.DPAD_DOWN)) == (0, 1)


def test_left_stick_uses_deadzone() -> None:
    assert gamepad._axis_navigation(_pad(lx=10000)) == (0, 0)
    assert gamepad._axis_navigation(_pad(lx=26000)) == (1, 0)
    assert gamepad._axis_navigation(_pad(lx=-26000)) == (-1, 0)
    assert gamepad._axis_navigation(_pad(ly=26000)) == (0, -1)
    assert gamepad._axis_navigation(_pad(ly=-26000)) == (0, 1)


def test_dpad_wins_over_stick() -> None:
    pad = _pad(gamepad.DPAD_LEFT, lx=26000, ly=26000)
    assert gamepad._axis_navigation(pad) == (-1, 0)


def test_button_masks_are_distinct() -> None:
    masks = [
        gamepad.BUTTON_A,
        gamepad.BUTTON_B,
        gamepad.BUTTON_X,
        gamepad.BUTTON_Y,
        gamepad.BUTTON_START,
        gamepad.BUTTON_BACK,
        gamepad.LEFT_SHOULDER,
        gamepad.RIGHT_SHOULDER,
        gamepad.DPAD_UP,
        gamepad.DPAD_DOWN,
        gamepad.DPAD_LEFT,
        gamepad.DPAD_RIGHT,
    ]
    assert len(set(masks)) == len(masks)
    assert all(mask & (mask - 1) == 0 for mask in masks)


def test_select_hold_requests_one_screenshot(app, monkeypatch) -> None:
    monkeypatch.setenv("GC_NO_GAMEPAD", "1")
    manager = gamepad.GamepadManager()
    shots: list[bool] = []
    manager.screenshot.connect(lambda: shots.append(True))

    manager._last_buttons = 0
    manager._update_back_hold(gamepad.BUTTON_BACK, 10.0)
    manager._last_buttons = gamepad.BUTTON_BACK

    manager._update_back_hold(gamepad.BUTTON_BACK, 14.9)
    assert shots == []

    manager._update_back_hold(gamepad.BUTTON_BACK, 15.0)
    assert shots == [True]

    # Holding longer must not fire again until the button is released.
    manager._update_back_hold(gamepad.BUTTON_BACK, 16.0)
    assert shots == [True]

    manager._update_back_hold(0, 16.1)
    manager._last_buttons = 0
    manager._update_back_hold(gamepad.BUTTON_BACK, 20.0)
    manager._last_buttons = gamepad.BUTTON_BACK
    manager._update_back_hold(gamepad.BUTTON_BACK, 25.0)
    assert shots == [True, True]
    assert gamepad.SCREENSHOT_HOLD_SECONDS == 5.0


def test_button_order_matches_the_preferences() -> None:
    from gamecenter.core.preferences import GAMEPAD_BUTTONS

    assert tuple(name for name, _mask in gamepad.BUTTON_ORDER) == GAMEPAD_BUTTONS


def test_custom_combo_fires_once_per_press(app, monkeypatch, tmp_path) -> None:
    from gamecenter.core.preferences import Preferences

    monkeypatch.setenv("GC_NO_GAMEPAD", "1")
    prefs = Preferences(tmp_path / "settings.json")
    prefs.screenshot_gamepad = "rb+lb"
    assert prefs.screenshot_gamepad == "LB+RB"

    manager = gamepad.GamepadManager(prefs)
    shots: list[bool] = []
    manager.screenshot.connect(lambda: shots.append(True))

    manager._check_screenshot_combo("LB+RB")
    manager._check_screenshot_combo("LB+RB")  # still held
    manager._check_screenshot_combo("")
    manager._check_screenshot_combo("LB+RB")

    assert shots == [True, True]

    # The custom combo replaces the Select-hold gesture.
    manager._last_buttons = 0
    manager._update_back_hold(gamepad.BUTTON_BACK, 10.0)
    manager._last_buttons = gamepad.BUTTON_BACK
    manager._update_back_hold(gamepad.BUTTON_BACK, 20.0)
    assert shots == [True, True]


def test_combo_capture_waits_for_the_release(app, monkeypatch, tmp_path) -> None:
    from gamecenter.core.preferences import Preferences

    monkeypatch.setenv("GC_NO_GAMEPAD", "1")
    prefs = Preferences(tmp_path / "settings.json")
    manager = gamepad.GamepadManager(prefs)
    captured: list[str] = []
    manager.comboCaptured.connect(captured.append)

    manager.startCapture()
    assert manager.capturing is True

    manager._capture_step(gamepad.LEFT_SHOULDER)
    manager._capture_step(gamepad.LEFT_SHOULDER | gamepad.BUTTON_START)
    assert manager.capturing is True
    assert captured == []

    manager._capture_step(0)
    assert manager.capturing is False
    assert captured == ["LB+Start"]
    assert prefs.screenshot_gamepad == "LB+Start"
    assert manager.screenshotCombo == "LB+Start"
    assert manager.screenshotComboLabel == "LB + Start"

    manager.clearScreenshotCombo()
    assert manager.screenshotCombo == ""
    assert prefs.screenshot_gamepad == ""


def test_capture_can_be_cancelled(app, monkeypatch) -> None:
    monkeypatch.setenv("GC_NO_GAMEPAD", "1")
    manager = gamepad.GamepadManager()
    manager.startCapture()
    manager.cancelCapture()
    assert manager.capturing is False
    assert manager.screenshotCombo == ""
