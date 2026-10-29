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
# Keep a long timeline: statistics are derived from it, so trimming too early
# silently loses history. The cap is only a guardrail against a runaway file.
MAX_HISTORY = 5000


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


def all_summaries() -> dict[str, dict]:
    """Every fallback summary, including games no longer in any store."""
    data = _read(_fallback_path())
    out: dict[str, dict] = {}
    for game_id, entry in data.items():
        if isinstance(entry, dict):
            out[str(game_id)] = entry
    return out


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
    """Add one finished session to the game's playtime.

    There is deliberately no minimum duration: a two-minute session counts as
    much as a two-hour one. Sub-second sessions are rounded up to 1 s instead of
    being truncated away.
    """
    if game.source == "steam" or seconds <= 0:
        return
    total = max(1, int(round(seconds)))

    path = file_for(game)
    root_entry = _read(path) if path is not None else {}
    fallback_entry = _fallback_entry(game)
    base = root_entry or fallback_entry

    entry = {
        "seconds": int(base.get("seconds") or 0) + total,
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


def write_summary(
    game: Game, seconds: int, sessions: int, last_played: int = 0
) -> None:
    """Overwrite a non-Steam game summary, keeping the fallback mirror in sync."""
    if game.source == "steam":
        return
    entry = {
        "seconds": max(0, int(seconds)),
        "sessions": max(0, int(sessions)),
        "last_played": max(0, int(last_played or 0)),
        "title": game.title,
        "source": game.source,
    }
    path = file_for(game)
    if path is not None and _write(path, entry):
        _fallback_write(game.id, entry)
        return
    _fallback_write(game.id, entry)


def clear_summary(game: Game) -> None:
    """Drop a game's stored summary after its data has been merged elsewhere."""
    path = file_for(game)
    if path is not None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    data = _read(_fallback_path())
    if game.id in data:
        del data[game.id]
        _write(_fallback_path(), data)


def _history_key(item: dict) -> tuple[int, int, str, str] | None:
    try:
        return (
            int(item.get("start") or 0),
            int(item.get("seconds") or 0),
            str(item.get("title") or ""),
            str(item.get("source") or ""),
        )
    except (TypeError, ValueError, AttributeError):
        return None


def _history_start(item: dict) -> int:
    try:
        return int(item.get("start") or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def move_history(source_id: str, target_id: str) -> int:
    """Move timeline entries to another game id and return how many moved."""
    if not source_id or not target_id or source_id == target_id:
        return 0
    data = _read(history_path())
    entries = data.pop(source_id, [])
    target = data.get(target_id)
    target = list(target) if isinstance(target, list) else []

    seen = set()
    for item in target:
        if isinstance(item, dict):
            key = _history_key(item)
            if key is not None:
                seen.add(key)
    moved = 0
    for item in entries:
        if not isinstance(item, dict):
            continue
        key = _history_key(item)
        if key is None or key in seen:
            continue
        seen.add(key)
        target.append(item)
        moved += 1

    target.sort(key=_history_start)
    data[target_id] = target
    _write(history_path(), data)
    return moved


def add_history_entry(
    game: Game,
    started_at: float,
    seconds: float,
    imported: bool = False,
) -> None:
    """Append one already-finished entry, including synthetic imported time."""
    total = int(seconds)
    if total < 1:
        return
    path = history_path()
    data = _read(path)
    entries = data.get(game.id)
    entries = list(entries) if isinstance(entries, list) else []
    entry = {
        "start": int(started_at) or int(time.time()) - total,
        "seconds": total,
        "title": game.title,
        "source": game.source,
    }
    if imported:
        entry["imported"] = True
    entries.append(entry)
    data[game.id] = entries
    _write(path, data)


def record_session(game: Game, started_at: float, seconds: float) -> None:
    """Append one session to the global, per-game timeline.

    Every positive duration is stored: short sessions are real playtime too and
    the statistics view must be able to show them.
    """
    if seconds <= 0:
        return
    total = max(1, int(round(seconds)))

    path = history_path()
    data = _read(path)
    entries = data.get(game.id)
    if not isinstance(entries, list):
        entries = []

    entries.append(
        {
            "start": int(started_at or time.time() - total),
            "seconds": total,
            "title": game.title,
            "source": game.source,
        }
    )
    data[game.id] = entries[-MAX_HISTORY:]
    _write(path, data)


_HISTORY_CACHE: tuple[str, int, dict[str, list[dict]]] | None = None


def all_history() -> dict[str, list[dict]]:
    """Every stored session, grouped by game id (cached by path + mtime)."""
    global _HISTORY_CACHE
    path = history_path()
    try:
        stamp = path.stat().st_mtime_ns
    except OSError:
        return {}
    if (
        _HISTORY_CACHE is not None
        and _HISTORY_CACHE[0] == str(path)
        and _HISTORY_CACHE[1] == stamp
    ):
        return _HISTORY_CACHE[2]

    raw = _read(path)
    out: dict[str, list[dict]] = {}
    for game_id, entries in raw.items():
        if not isinstance(entries, list):
            continue
        parsed: list[dict] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            try:
                start = int(entry.get("start") or 0)
                seconds = int(entry.get("seconds") or 0)
            except (TypeError, ValueError):
                continue
            if seconds <= 0:
                continue
            parsed.append(
                {
                    "start": start,
                    "seconds": seconds,
                    "title": str(entry.get("title") or ""),
                    "source": str(entry.get("source") or ""),
                    "imported": bool(entry.get("imported")),
                }
            )
        if parsed:
            out[str(game_id)] = parsed
    _HISTORY_CACHE = (str(path), stamp, out)
    return out


def history_for(game: Game) -> list[dict]:
    """Finished sessions for a game, newest first."""
    entries = list(all_history().get(game.id, []))
    entries.sort(key=lambda item: item["start"], reverse=True)
    return entries
