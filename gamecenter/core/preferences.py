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
DEFAULT_SURFACE = "#12151b"
DEFAULT_CARTRIDGE = "#3c414a"
CARTRIDGE_STYLES = ("classic", "ds", "ps2")

# A wide but curated set; all have enough contrast on the dark background.
PALETTE = (
    "#4cc9f0", "#38bdf8", "#3b82f6", "#6366f1", "#8b5cf6", "#a855f7",
    "#d946ef", "#ec4899", "#f43f5e", "#ef4444", "#f97316", "#f59e0b",
    "#eab308", "#84cc16", "#22c55e", "#10b981", "#14b8a6", "#06b6d4",
    "#0ea5e9", "#64748b", "#94a3b8", "#e2e8f0", "#f8fafc", "#facc15",
)

# Dark tones for the navbar, the dock and the cartridge shelf.
SURFACES = (
    "#0b0d10", "#12151b", "#1a1f29", "#20242e", "#101418", "#181818",
    "#1f2a33", "#1f2a24", "#2a1f2e", "#2a2418", "#2a1c1c", "#1c1c2a",
)

# Plastic tones for the cartridge shells.
CARTRIDGES = (
    "#3c414a", "#23262d", "#5b616b", "#8a8f98", "#c9ced6", "#2f3e46",
    "#3a2f46", "#463a2f", "#3f2b2b", "#2b3f3a", "#1f2f4a", "#4a3b1f",
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

        surface = str(data.get("surfaceColor") or DEFAULT_SURFACE)
        data["surfaceColor"] = surface if _HEX.match(surface) else DEFAULT_SURFACE

        cartridge = str(data.get("cartridgeColor") or DEFAULT_CARTRIDGE)
        data["cartridgeColor"] = cartridge if _HEX.match(cartridge) else DEFAULT_CARTRIDGE

        covers = data.get("covers")
        data["covers"] = covers if isinstance(covers, dict) else {}

        colors = data.get("cartridgeColors")
        if isinstance(colors, dict):
            data["cartridgeColors"] = {
                str(key): str(value)
                for key, value in colors.items()
                if _HEX.match(str(value))
            }
        else:
            data["cartridgeColors"] = {}

        hidden = data.get("hiddenGames")
        data["hiddenGames"] = (
            [str(item) for item in hidden] if isinstance(hidden, list) else []
        )

        data["checkUpdates"] = bool(data.get("checkUpdates", True))
        try:
            data["lastUpdateCheck"] = float(data.get("lastUpdateCheck") or 0)
        except (TypeError, ValueError):
            data["lastUpdateCheck"] = 0.0
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

    @property
    def surface_color(self) -> str:
        return self._data["surfaceColor"]

    @surface_color.setter
    def surface_color(self, value: str) -> None:
        if _HEX.match(value or ""):
            self._data["surfaceColor"] = value
            self._save()

    @property
    def cartridge_color(self) -> str:
        return self._data["cartridgeColor"]

    @cartridge_color.setter
    def cartridge_color(self, value: str) -> None:
        if _HEX.match(value or ""):
            self._data["cartridgeColor"] = value
            self._save()

    # -- updates ----------------------------------------------------------

    @property
    def check_updates(self) -> bool:
        return bool(self._data["checkUpdates"])

    @check_updates.setter
    def check_updates(self, value: bool) -> None:
        self._data["checkUpdates"] = bool(value)
        self._save()

    @property
    def last_update_check(self) -> float:
        return float(self._data["lastUpdateCheck"])

    @last_update_check.setter
    def last_update_check(self, value: float) -> None:
        self._data["lastUpdateCheck"] = float(value)
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

    # -- per-game cartridge colour ---------------------------------------

    def cartridge_color_for(self, game_id: str) -> str:
        return str(self._data["cartridgeColors"].get(game_id, ""))

    def set_cartridge_color(self, game_id: str, value: str | None) -> None:
        if value and _HEX.match(value):
            self._data["cartridgeColors"][game_id] = value
        else:
            self._data["cartridgeColors"].pop(game_id, None)
        self._save()

    # -- removed games ----------------------------------------------------

    @property
    def hidden_games(self) -> list[str]:
        return list(self._data["hiddenGames"])

    def is_hidden(self, game_id: str) -> bool:
        return game_id in self._data["hiddenGames"]

    def hide_game(self, game_id: str) -> None:
        if game_id not in self._data["hiddenGames"]:
            self._data["hiddenGames"].append(game_id)
            self._save()

    def clear_hidden_games(self) -> int:
        count = len(self._data["hiddenGames"])
        if count:
            self._data["hiddenGames"] = []
            self._save()
        return count
