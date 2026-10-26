"""GameCenter-owned profile for each game.

The stores own their libraries and native playtime; this module keeps the
extra data that follows a game across platforms: score, status and the
traceability of manual data merges.

The file lives in ``%APPDATA%/GameCenter/profiles.json`` (or the platform
equivalent) and is keyed by game id. Nothing here depends on the store APIs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .preferences import config_dir

FILENAME = "profiles.json"

# Canonical status keys. The UI translates them.
STATUSES = (
    "playing",
    "ongoing",
    "beaten",
    "completed",
    "played",
    "plan",
    "onhold",
    "notplayed",
    "abandoned",
)
STATUS_SET = frozenset(STATUSES)


def path() -> Path:
    return config_dir() / FILENAME


def cover_dir() -> Path:
    """Where imported cover snapshots are kept for recaps and traceability."""
    return config_dir() / "recap_covers"


def _read() -> dict[str, dict]:
    try:
        raw = json.loads(path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict] = {}
    for game_id, entry in raw.items():
        if isinstance(entry, dict):
            out[str(game_id)] = entry
    return out


def _write(data: dict[str, dict]) -> None:
    try:
        target = path()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, target)
    except OSError:
        pass


def get(game_id: str) -> dict:
    entry = _read().get(game_id)
    return dict(entry) if isinstance(entry, dict) else {}


def update(game_id: str, **fields) -> dict:
    """Merge fields into one game's profile and return the stored entry."""
    data = _read()
    entry = data.get(game_id)
    entry = dict(entry) if isinstance(entry, dict) else {}
    entry.update(fields)
    data[game_id] = entry
    _write(data)
    return dict(entry)


def set_rating(game_id: str, rating: int | None) -> dict:
    """Store a 0-100 score, or clear it with ``None``."""
    if rating is None:
        return update(game_id, rating=None)
    try:
        value = int(rating)
    except (TypeError, ValueError):
        value = 0
    return update(game_id, rating=max(0, min(100, value)))


def set_status(game_id: str, status: str) -> dict:
    """Store a validated status key. An empty value clears the status."""
    value = str(status or "").strip().lower()
    if value and value not in STATUS_SET:
        return get(game_id)
    return update(game_id, status=value)


def add_merged_source(target_id: str, record: dict) -> dict:
    """Remember one imported entry on the target game, newest first."""
    data = _read()
    entry = data.get(target_id)
    entry = dict(entry) if isinstance(entry, dict) else {}
    sources = entry.get("merged_sources")
    sources = list(sources) if isinstance(sources, list) else []
    source_id = str(record.get("id") or "")
    sources = [
        item
        for item in sources
        if isinstance(item, dict) and str(item.get("id") or "") != source_id
    ]
    sources.insert(0, record)
    entry["merged_sources"] = sources
    data[target_id] = entry
    _write(data)
    return dict(entry)


def mark_merged(
    source_id: str,
    target_id: str,
    target_title: str,
    seconds: int,
    sessions: int,
    cover: str,
    at: int,
) -> dict:
    """Leave a permanent trace on the source entry."""
    return update(
        source_id,
        merged_into=target_id,
        merged_into_title=target_title,
        merged_at=at,
        merged_seconds=int(seconds),
        merged_sessions=int(sessions),
        merged_cover=cover,
        extra_seconds=0,
        extra_sessions=0,
        extra_last_played=0,
    )


def add_extra(
    game_id: str, seconds: int, sessions: int, last_played: int = 0
) -> dict:
    """Add imported time that must be layered on top of Steam's native time."""
    entry = get(game_id)
    try:
        current_seconds = int(entry.get("extra_seconds") or 0)
    except (TypeError, ValueError):
        current_seconds = 0
    try:
        current_sessions = int(entry.get("extra_sessions") or 0)
    except (TypeError, ValueError):
        current_sessions = 0
    try:
        current_last = int(entry.get("extra_last_played") or 0)
    except (TypeError, ValueError):
        current_last = 0
    return update(
        game_id,
        extra_seconds=current_seconds + max(0, int(seconds)),
        extra_sessions=current_sessions + max(0, int(sessions)),
        extra_last_played=max(current_last, int(last_played or 0)),
    )


def extra_seconds(game_id: str) -> int:
    try:
        return int(get(game_id).get("extra_seconds") or 0)
    except (TypeError, ValueError):
        return 0


def extra_sessions(game_id: str) -> int:
    try:
        return int(get(game_id).get("extra_sessions") or 0)
    except (TypeError, ValueError):
        return 0


def extra_last_played(game_id: str) -> int:
    try:
        return int(get(game_id).get("extra_last_played") or 0)
    except (TypeError, ValueError):
        return 0


def merged_seconds(game_id: str) -> int:
    """Native seconds already moved away from this entry by a merge."""
    try:
        return int(get(game_id).get("merged_seconds") or 0)
    except (TypeError, ValueError):
        return 0
