"""Playtime for games whose store does not track it.

A small JSON file in the game's root folder:

    .gamecenter_playtime.json
    {"seconds": 1234, "sessions": 3, "last_played": 1700000000}

If the folder is missing or not writable (for example a game under Program
Files), the time is kept in %APPDATA%/GameCenter/playtime.json keyed by game id,
so nothing is lost. Steam games are never written here: Steam already owns that
data in localconfig.vdf.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .models import Game
from .preferences import config_dir

FILENAME = ".gamecenter_playtime.json"


def _fallback_path() -> Path:
    return config_dir() / "playtime.json"


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(path: Path, data: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def file_for(game: Game) -> Path | None:
    """The per-game file, or None when there is no writable game folder."""
    if (
        game.source == "steam"
        or game.install_dir is None
        or not game.install_dir.is_dir()
    ):
        return None
    return game.install_dir / FILENAME


def _fallback_read(game_id: str) -> dict:
    data = _read(_fallback_path())
    entry = data.get(game_id)
    return entry if isinstance(entry, dict) else {}


def _fallback_write(game_id: str, entry: dict) -> None:
    data = _read(_fallback_path())
    data[game_id] = entry
    _write(_fallback_path(), data)


def summary_for(game: Game) -> dict:
    """The stored summary for this game (root file first, then fallback)."""
    if game.source == "steam":
        return {}
    path = file_for(game)
    entry = _read(path) if path is not None else {}
    if not entry:
        entry = _fallback_read(game.id)
    return entry


def seconds_for(game: Game) -> int:
    try:
        return int(summary_for(game).get("seconds") or 0)
    except (TypeError, ValueError):
        return 0


def minutes_for(game: Game) -> int:
    return seconds_for(game) // 60


def add_seconds(game: Game, seconds: float) -> None:
    """Add one finished session to the game's playtime."""
    if game.source == "steam" or seconds < 1:
        return

    path = file_for(game)
    root_entry = _read(path) if path is not None else {}
    fallback_entry = _fallback_read(game.id)
    base = root_entry or fallback_entry

    entry = {
        "seconds": int(base.get("seconds") or 0) + int(seconds),
        "sessions": int(base.get("sessions") or 0) + 1,
        "last_played": int(time.time()),
    }

    if path is not None and _write(path, entry):
        return
    _fallback_write(game.id, entry)
