"""Canonical keyboard shortcuts.

One place for validating, normalising and converting shortcuts, shared by the
preferences file (what gets stored), the QML ``Shortcut`` items (what gets
matched while the app has focus) and the Windows global hotkey (what gets
registered with ``RegisterHotKey``).

The canonical text is Qt's portable form (``"Ctrl+PgDown"``, ``"F12"``), so the
same string can be handed to a QML ``Shortcut`` without extra conversion.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

# Modifier flags used by RegisterHotKey (winuser.h).
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

MODIFIER_FLAGS = {
    "Ctrl": MOD_CONTROL,
    "Alt": MOD_ALT,
    "Shift": MOD_SHIFT,
    "Meta": MOD_WIN,
}

# Keys that make sense on their own (no modifier): function keys and Print.
_ALONE_PREFIXES = ("F",)

# Keys that are only modifiers: pressing them alone is not a shortcut yet.
IGNORED_KEYS = frozenset(
    {
        Qt.Key_Control,
        Qt.Key_Shift,
        Qt.Key_Alt,
        Qt.Key_AltGr,
        Qt.Key_Meta,
        Qt.Key_Super_L,
        Qt.Key_Super_R,
        Qt.Key_CapsLock,
        Qt.Key_NumLock,
        Qt.Key_ScrollLock,
    }
)

# Canonical Qt key name -> Windows virtual-key code.
_VK = {
    "PgDown": 0x22,
    "PgUp": 0x21,
    "Print": 0x2C,
    "Pause": 0x13,
    "Esc": 0x1B,
    "Ins": 0x2D,
    "Del": 0x2E,
    "Home": 0x24,
    "End": 0x23,
    "Space": 0x20,
    "Tab": 0x09,
    "Backspace": 0x08,
    "Return": 0x0D,
    "Enter": 0x0D,
    "Up": 0x26,
    "Down": 0x28,
    "Left": 0x25,
    "Right": 0x27,
}

# What the user reads in Settings.
_DISPLAY = {
    "PgDown": "Page Down",
    "PgUp": "Page Up",
    "Ins": "Insert",
    "Del": "Delete",
    "Esc": "Escape",
    "Backspace": "Backspace",
    "Return": "Enter",
    "Enter": "Enter",
    "Print": "Print Screen",
    "Space": "Space",
    "Up": "Up",
    "Down": "Down",
    "Left": "Left",
    "Right": "Right",
}


def allowed_alone(name: str) -> bool:
    """True for keys that are valid without any modifier."""
    if name == "Print":
        return True
    if name.startswith(_ALONE_PREFIXES) and name[1:].isdigit():
        return 1 <= int(name[1:]) <= 24
    return False


def normalize(value: str | None) -> str | None:
    """Canonical shortcut text, ``""`` for "none" and ``None`` when invalid."""
    text = str(value or "").strip()
    if not text or text.lower() in ("none", "disabled", "off"):
        return ""

    sequence = QKeySequence.fromString(text, QKeySequence.PortableText)
    if sequence.isEmpty() or sequence.count() != 1:
        return None
    canonical = sequence.toString(QKeySequence.PortableText)
    if not canonical:
        return None

    tokens = canonical.split("+")
    if len(tokens) == 1 and not allowed_alone(tokens[0]):
        return None
    return canonical


def _as_int(value) -> int:
    """PySide6 enums expose ``.value``; plain ints pass through."""
    return int(getattr(value, "value", value))


def from_key(key: int, modifiers: int) -> str | None:
    """Canonical shortcut for a ``Qt.Key`` plus ``Qt.KeyboardModifiers``."""
    key_code = _as_int(key)
    if not key_code or key_code in IGNORED_KEYS:
        return None
    sequence = QKeySequence(key_code | _as_int(modifiers))
    if sequence.isEmpty():
        return None
    return normalize(sequence.toString(QKeySequence.PortableText))


def raw_from_key(key: int, modifiers: int) -> str:
    """The combination exactly as pressed, even if it is not a valid shortcut."""
    key_code = _as_int(key)
    if not key_code:
        return ""
    sequence = QKeySequence(key_code | _as_int(modifiers))
    return sequence.toString(QKeySequence.PortableText)


def to_vk(sequence: str | None) -> tuple[int, int] | None:
    """``(modifiers, virtual-key)`` for ``RegisterHotKey``."""
    canonical = normalize(sequence)
    if not canonical:
        return None

    tokens = canonical.split("+")
    name = tokens[-1]
    modifiers = 0
    for token in tokens[:-1]:
        flag = MODIFIER_FLAGS.get(token)
        if flag is None:
            return None
        modifiers |= flag

    vk = _VK.get(name)
    if vk is None and len(name) == 1 and name.isalnum():
        vk = ord(name.upper())
    if vk is None and name.startswith("F") and name[1:].isdigit():
        number = int(name[1:])
        if 1 <= number <= 24:
            vk = 0x70 + number - 1
    if vk is None:
        return None
    return modifiers, vk


def prettify(text: str | None) -> str:
    """Human label for any combination, without validating it."""
    return "+".join(
        _DISPLAY.get(token, token)
        for token in str(text or "").split("+")
        if token
    )


def display(sequence: str | None) -> str:
    """Human label for the UI (``Ctrl+Page Down``)."""
    canonical = normalize(sequence)
    if not canonical:
        return ""
    return prettify(canonical)
