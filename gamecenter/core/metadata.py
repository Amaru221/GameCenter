"""Short game descriptions from the public Steam Store API.

The launcher already works offline for covers. Descriptions are an optional
extra: they are fetched once per game/language, cached under
``%APPDATA%/GameCenter/metadata.json`` and silently skipped when there is no
connection. Steam games use their AppID; other stores fall back to a Steam
Store title search with a conservative similarity threshold.
"""

from __future__ import annotations

import difflib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .. import __version__
from .models import Game
from .preferences import config_dir

CACHE_TTL = 30 * 24 * 3600
MISSING_TTL = 24 * 3600
MAX_DESCRIPTION = 900

_STEAM_LANGUAGES = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
}
_APP_DETAILS = "https://store.steampowered.com/api/appdetails"
_STORE_SEARCH = "https://store.steampowered.com/api/storesearch/"
_UA = f"GameCenter/{__version__}"
_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")


def enabled() -> bool:
    return os.environ.get("GC_NO_METADATA", "") == ""


def cache_path() -> Path:
    return config_dir() / "metadata.json"


def _read_cache() -> dict:
    try:
        data = json.loads(cache_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_cache(data: dict) -> None:
    path = cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def _clean(value: str) -> str:
    text = _TAGS.sub(" ", html.unescape(value or ""))
    return _SPACES.sub(" ", text).strip()


def _normalise(value: str) -> str:
    text = html.unescape(value or "").casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def _get_json(url: str, params: dict, timeout: int = 8) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query}", headers={"User-Agent": _UA}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    return data if isinstance(data, dict) else {}


def _search_app_id(title: str, language: str) -> str:
    payload = _get_json(
        _STORE_SEARCH,
        {"term": title, "l": language, "cc": "us"},
    )
    items = payload.get("items")
    if not isinstance(items, list):
        return ""

    wanted = _normalise(title)
    best = ""
    best_score = 0.0
    for item in items:
        if not isinstance(item, dict) or item.get("type") != "app":
            continue
        candidate = str(item.get("name") or "")
        score = difflib.SequenceMatcher(None, wanted, _normalise(candidate)).ratio()
        if score > best_score:
            best_score = score
            best = str(item.get("id") or "")

    return best if best_score >= 0.94 else ""


def _app_details(app_id: str, language: str) -> dict:
    payload = _get_json(
        _APP_DETAILS,
        {"appids": app_id, "l": language, "cc": "us"},
    )
    entry = payload.get(str(app_id))
    if not isinstance(entry, dict) or not entry.get("success"):
        return {}
    data = entry.get("data")
    if not isinstance(data, dict):
        return {}

    description = _clean(str(data.get("short_description") or ""))
    if not description:
        description = _clean(str(data.get("detailed_description") or ""))
    if len(description) > MAX_DESCRIPTION:
        description = description[:MAX_DESCRIPTION].rsplit(" ", 1)[0] + "…"

    developers = ", ".join(
        str(item) for item in data.get("developers") or [] if item
    )
    genres = ", ".join(
        str(item.get("description") or "")
        for item in data.get("genres") or []
        if isinstance(item, dict) and item.get("description")
    )
    release = data.get("release_date")
    release_date = str(release.get("date") or "") if isinstance(release, dict) else ""

    return {
        "description": description,
        "developers": developers,
        "genres": genres,
        "releaseDate": release_date,
        "found": bool(description or developers or genres),
    }


def cached(game: Game, language: str = "en") -> dict | None:
    """Fresh cached metadata, or ``None`` when it must be fetched again."""
    entry = _read_cache().get(game.id, {})
    if not isinstance(entry, dict):
        return None
    entry = entry.get(language)
    if not isinstance(entry, dict):
        return None

    try:
        updated = float(entry.get("updated") or 0)
    except (TypeError, ValueError):
        updated = 0.0
    ttl = CACHE_TTL if entry.get("found") else MISSING_TTL
    if time.time() - updated > ttl:
        return None

    return {
        "description": str(entry.get("description") or ""),
        "developers": str(entry.get("developers") or ""),
        "genres": str(entry.get("genres") or ""),
        "releaseDate": str(entry.get("releaseDate") or ""),
    }


def fetch(game: Game, language: str = "en") -> dict:
    """Fetch and cache a description. Returns empty strings when unavailable."""
    if not enabled():
        return {}

    steam_language = _STEAM_LANGUAGES.get(language, "english")
    app_id = game.app_id if game.source == "steam" and game.app_id.isdigit() else ""
    try:
        if not app_id:
            app_id = _search_app_id(game.title, steam_language)
        data = _app_details(app_id, steam_language) if app_id else {}
    except (OSError, ValueError, urllib.error.URLError):
        return {}

    entry = {
        "description": str(data.get("description") or ""),
        "developers": str(data.get("developers") or ""),
        "genres": str(data.get("genres") or ""),
        "releaseDate": str(data.get("releaseDate") or ""),
        "found": bool(data.get("found")),
        "updated": time.time(),
    }

    cache = _read_cache()
    per_game = cache.get(game.id)
    if not isinstance(per_game, dict):
        per_game = {}
    per_game[language] = entry
    cache[game.id] = per_game
    _write_cache(cache)

    return {
        "description": entry["description"],
        "developers": entry["developers"],
        "genres": entry["genres"],
        "releaseDate": entry["releaseDate"],
    }
