"""User preferences: favorites, appearance and per-game cover overrides.

One small JSON file next to the user's other settings. API keys are not stored
here; they go to the operating system's credential store (see credentials.py).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEFAULT_ACCENT = "#4cc9f0"
CARTRIDGE_STYLES = ("classic", "ds", "ps2")

# A wide but curated set; all have enough contrast on the dark background.
PALETTE = (
    "#4cc9f0", "#38bdf8", "#3b82f6", "#6366f1", "#8b5cf6", "#a855f7",
    "#d946ef", "#ec4899", "#f43f5e", "#ef4444", "#f97316", "#f59e0b",
    "#eab308", "#84cc16", "#22c55e", "#10b981", "#14b8a6", "#06b6d4",
    "#0ea5e9", "#64748b", "#94a3b8", "#e2e8f0", "#f8fafc", "#facc15",
)

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "GameCenter"


class Preferences:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_dir() / "settings.json"
        self._data = self._load()

    # -- storage ----------------------------------------------------------

    def _load(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}

        favorites = data.get("favorites")
        data["favorites"] = [str(item) for item in favorites] if isinstance(favorites, list) else []

        accent = str(data.get("accent") or DEFAULT_ACCENT)
        data["accent"] = accent if _HEX.match(accent) else DEFAULT_ACCENT

        style = str(data.get("cartridgeStyle") or "classic")
        data["cartridgeStyle"] = style if style in CARTRIDGE_STYLES else "classic"

        covers = data.get("covers")
        data["covers"] = covers if isinstance(covers, dict) else {}
        return data

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except OSError:
            pass

    # -- favorites --------------------------------------------------------

    def is_favorite(self, game_id: str) -> bool:
        return game_id in self._data["favorites"]

    def toggle_favorite(self, game_id: str) -> bool:
        favorites = self._data["favorites"]
        if game_id in favorites:
            favorites.remove(game_id)
            value = False
        else:
            favorites.append(game_id)
            value = True
        self._save()
        return value

    # -- appearance -------------------------------------------------------

    @property
    def accent(self) -> str:
        return self._data["accent"]

    @accent.setter
    def accent(self, value: str) -> None:
        if _HEX.match(value or ""):
            self._data["accent"] = value
            self._save()

    @property
    def cartridge_style(self) -> str:
        return self._data["cartridgeStyle"]

    @cartridge_style.setter
    def cartridge_style(self, value: str) -> None:
        if value in CARTRIDGE_STYLES:
            self._data["cartridgeStyle"] = value
            self._save()

    # -- per-game cover ---------------------------------------------------

    def cover_for(self, game_id: str) -> str:
        return str(self._data["covers"].get(game_id, ""))

    def set_cover(self, game_id: str, path: str | None) -> None:
        if path:
            self._data["covers"][game_id] = str(path)
        else:
            self._data["covers"].pop(game_id, None)
        self._save()
