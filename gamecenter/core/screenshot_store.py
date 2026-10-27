"""On-disk index that links screenshots to games and sessions.

Screenshots live under ``%APPDATA%/GameCenter/screenshots``. The JSON index
keeps the link between a file and the game/session that was running when it was
taken, so the detail timeline can show the right thumbnails even after the
session ends.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from .preferences import config_dir

INDEX_FILENAME = "screenshots.json"
MAX_ENTRIES = 5000
_STAMP = re.compile(r"-(\d{8}-\d{6})\.png$", re.IGNORECASE)


def _safe_title(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", title or "").strip("-._")[:60]


def index_path() -> Path:
    return config_dir() / INDEX_FILENAME


def _read() -> list[dict]:
    try:
        data = json.loads(index_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    entries: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "")
        if not path:
            continue
        entries.append(
            {
                "path": path,
                "gameId": str(item.get("gameId") or ""),
                "sessionId": str(item.get("sessionId") or ""),
                "sessionStartedAt": int(item.get("sessionStartedAt") or 0),
                "takenAt": int(item.get("takenAt") or 0),
                "title": str(item.get("title") or ""),
            }
        )
    return entries


def _write(entries: list[dict]) -> None:
    try:
        path = index_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(entries[-MAX_ENTRIES:], indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except OSError:
        pass


def record(
    path: Path | str,
    *,
    game_id: str,
    session_id: str = "",
    session_started_at: float = 0,
    title: str = "",
    taken_at: float | None = None,
) -> None:
    """Index one saved screenshot. Missing files are tolerated."""
    try:
        resolved = str(Path(path).resolve())
    except OSError:
        resolved = str(path)
    entry = {
        "path": resolved,
        "gameId": str(game_id or ""),
        "sessionId": str(session_id or ""),
        "sessionStartedAt": int(session_started_at or 0),
        "takenAt": int(taken_at if taken_at is not None else time.time()),
        "title": str(title or ""),
    }
    entries = [item for item in _read() if item["path"] != resolved]
    entries.append(entry)
    _write(entries)


def for_game(game_id: str, title: str = "") -> list[dict]:
    """Screenshots linked to a game, oldest first, with a QML-ready URL.

    Files taken before the index existed are recovered by their sanitized title
    prefix and ``YYYYMMDD-HHMMSS`` suffix.
    """
    if not game_id:
        return []
    result: list[dict] = []
    known: set[str] = set()
    for entry in _read():
        if entry["gameId"] != game_id:
            continue
        file_path = Path(entry["path"])
        if not file_path.is_file():
            continue
        known.add(str(file_path.resolve()))
        result.append(
            {
                **entry,
                "url": file_path.as_uri(),
            }
        )

    safe_title = _safe_title(title)
    if safe_title:
        folder = config_dir() / "screenshots"
        try:
            files = list(folder.glob(f"{safe_title}-*.png"))
        except OSError:
            files = []
        for file_path in files:
            try:
                resolved = str(file_path.resolve())
            except OSError:
                continue
            if resolved in known:
                continue
            match = _STAMP.search(file_path.name)
            if match is None:
                continue
            try:
                taken = datetime.strptime(
                    match.group(1), "%Y%m%d-%H%M%S"
                ).timestamp()
            except ValueError:
                continue
            result.append(
                {
                    "path": resolved,
                    "gameId": game_id,
                    "sessionId": "",
                    "sessionStartedAt": 0,
                    "takenAt": int(taken),
                    "title": title,
                    "url": file_path.as_uri(),
                }
            )

    result.sort(key=lambda item: (item["takenAt"], item["path"]))
    return result
