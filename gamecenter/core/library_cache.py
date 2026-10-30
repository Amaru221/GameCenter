"""The last successful library scan, kept for an instant first paint.

The real scan runs in a background thread. While it works, the window shows the
games discovered last time from this cache. It is only a bootstrap: the next
scan always replaces it, so a removed store or an uninstalled game disappears as
soon as the scan finishes.

The cache lives in ``%APPDATA%/GameCenter/library_cache.json`` (or the platform
equivalent) and is written atomically. A corrupt file is ignored instead of
breaking the startup.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Game
from .preferences import config_dir

FILENAME = "library_cache.json"
VERSION = 1


def cache_path() -> Path:
    """Default location of the cache file."""
    return config_dir() / FILENAME


def _as_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _to_dict(game: Game) -> dict:
    return {
        "id": game.id,
        "title": game.title,
        "source": game.source,
        "app_id": game.app_id,
        "install_dir": str(game.install_dir) if game.install_dir else None,
        "launch_uri": game.launch_uri,
        "launch_command": game.launch_command,
        "executable": str(game.executable) if game.executable else None,
        "launch_args": list(game.launch_args),
        "installed": bool(game.installed),
        "size_bytes": _as_int(game.size_bytes),
        "last_played": _as_int(game.last_played),
        "playtime_minutes": _as_int(game.playtime_minutes),
    }


def _from_dict(item: object) -> Game | None:
    if not isinstance(item, dict):
        return None
    game_id = str(item.get("id") or "")
    title = str(item.get("title") or "")
    source = str(item.get("source") or "")
    if not game_id or not title or not source:
        return None

    install_dir = item.get("install_dir")
    executable = item.get("executable")
    args = item.get("launch_args")
    return Game(
        id=game_id,
        title=title,
        source=source,
        app_id=str(item.get("app_id") or ""),
        install_dir=Path(install_dir) if install_dir else None,
        launch_uri=str(item.get("launch_uri") or ""),
        launch_command=str(item.get("launch_command") or ""),
        executable=Path(executable) if executable else None,
        launch_args=tuple(str(arg) for arg in args) if isinstance(args, list) else (),
        installed=bool(item.get("installed", True)),
        size_bytes=_as_int(item.get("size_bytes")),
        last_played=_as_int(item.get("last_played")),
        playtime_minutes=_as_int(item.get("playtime_minutes")),
    )


def load(path: Path | None = None) -> list[Game]:
    """Cached games, or an empty list when there is nothing usable."""
    target = Path(path) if path is not None else cache_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(payload, dict):
        return []
    try:
        version = int(payload.get("version") or 0)
    except (TypeError, ValueError):
        version = 0
    if version and version > VERSION:
        return []

    items = payload.get("games")
    if not isinstance(items, list):
        return []

    games: list[Game] = []
    for item in items:
        game = _from_dict(item)
        if game is not None:
            games.append(game)
    return games


def save(games: list[Game], path: Path | None = None) -> bool:
    """Write the cache atomically. Returns False when the disk refuses."""
    target = Path(path) if path is not None else cache_path()
    payload = {
        "version": VERSION,
        "games": [_to_dict(game) for game in games],
    }
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, target)
        return True
    except OSError:
        return False
