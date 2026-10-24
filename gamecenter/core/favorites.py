"""Favorites, kept in a small JSON file next to the user's other settings."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "GameCenter"


class Favorites:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_dir() / "settings.json"
        self._ids: set[str] = self._load()

    def _load(self) -> set[str]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return set()
        ids = data.get("favorites") if isinstance(data, dict) else None
        if not isinstance(ids, list):
            return set()
        return {str(item) for item in ids}

    def __contains__(self, game_id: str) -> bool:
        return game_id in self._ids

    def toggle(self, game_id: str) -> bool:
        if game_id in self._ids:
            self._ids.discard(game_id)
            value = False
        else:
            self._ids.add(game_id)
            value = True
        self._save()
        return value

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps({"favorites": sorted(self._ids)}, indent=2),
                encoding="utf-8",
            )
            os.replace(tmp, self.path)
        except OSError:
            pass
