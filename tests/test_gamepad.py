"""Gamepad mapping helpers (hardware-independent)."""

from types import SimpleNamespace

from gamecenter.core import gamepad


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
