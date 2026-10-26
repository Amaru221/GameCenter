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
HISTORY_FILENAME = "history.json"
MAX_HISTORY = 200


def _fallback_path() -> Path:
    return config_dir() / "playtime.json"


def history_path() -> Path:
    return config_dir() / HISTORY_FILENAME


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


def _fallback_entry(game: Game) -> dict:
    """The fallback for this game id, or by title for a moved manual game."""
    entry = _fallback_read(game.id)
    if entry:
        return entry
    if game.source == "local":
        data = _read(_fallback_path())
        for value in data.values():
            if (
                isinstance(value, dict)
                and value.get("source") == "local"
                and value.get("title") == game.title
            ):
                return value
    return {}


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
        entry = _fallback_entry(game)
    return entry


def restore_to_root(game: Game) -> bool:
    """After a reinstall, copy the fallback back into the game's new folder."""
    if game.source == "steam":
        return False
    path = file_for(game)
    if path is None:
        return False
    if path.is_file() and _read(path):
        return False  # the folder already has its own data
    fallback = _fallback_entry(game)
    if not fallback:
        return False
    return _write(path, fallback)


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
    fallback_entry = _fallback_entry(game)
    base = root_entry or fallback_entry

    entry = {
        "seconds": int(base.get("seconds") or 0) + int(seconds),
        "sessions": int(base.get("sessions") or 0) + 1,
        "last_played": int(time.time()),
        "title": game.title,
        "source": game.source,
    }

    if path is not None and _write(path, entry):
        # Keep a mirror under %APPDATA% so an uninstall/reinstall can recover it.
        _fallback_write(game.id, entry)
        return
    _fallback_write(game.id, entry)


def record_session(game: Game, started_at: float, seconds: float) -> None:
    """Append one session to the global, per-game timeline."""
    if seconds < 1:
        return

    path = history_path()
    data = _read(path)
    entries = data.get(game.id)
    if not isinstance(entries, list):
        entries = []

    entries.append(
        {
            "start": int(started_at or time.time() - int(seconds)),
            "seconds": int(seconds),
        }
    )
    data[game.id] = entries[-MAX_HISTORY:]
    _write(path, data)


def history_for(game: Game) -> list[dict]:
    """Finished sessions for a game, newest first."""
    entries = _read(history_path()).get(game.id)
    if not isinstance(entries, list):
        return []

    out: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            start = int(entry.get("start") or 0)
            seconds = int(entry.get("seconds") or 0)
        except (TypeError, ValueError):
            continue
        if seconds > 0:
            out.append({"start": start, "seconds": seconds})

    out.sort(key=lambda item: item["start"], reverse=True)
    return out
