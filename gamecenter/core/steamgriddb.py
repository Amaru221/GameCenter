"""SteamGridDB artwork search.

The API needs a personal key (stored by credentials.py). For Steam games the
numeric AppID is used directly; for the other stores the title is looked up.
Results are fetched page by page; the picker shows them in small batches.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .. import __version__
from .i18n import tr
from .models import Game

API = "https://www.steamgriddb.com/api/v2"
UA = f"GameCenter/{__version__}"
DIMENSIONS = "600x900,342x482"
PAGE_SIZE = 50
MAX_OPTIONS = 5


class SteamGridDBError(RuntimeError):
    """A friendly error for the UI."""


def _get(path: str, key: str, params: dict | None = None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise SteamGridDBError(tr("SteamGridDB rejected the API key.")) from exc
        raise SteamGridDBError(
            tr("SteamGridDB answered with an error ({code}).", code=exc.code)
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SteamGridDBError(tr("Couldn't reach SteamGridDB.")) from exc
    except ValueError as exc:
        raise SteamGridDBError(tr("SteamGridDB sent an unexpected answer.")) from exc

    if not isinstance(payload, dict) or not payload.get("success"):
        raise SteamGridDBError(tr("SteamGridDB didn't return any results."))
    return payload.get("data")


def grids_page(game: Game, key: str, page: int = 0) -> tuple[list[dict], bool]:
    """Portrait grids from one API page, plus whether another page may exist."""
    params = {"dimensions": DIMENSIONS, "types": "static", "page": page}
    if game.source == "steam" and game.app_id.isdigit():
        data = _get(f"/grids/steam/{game.app_id}", key, params)
    else:
        found = _get("/search/autocomplete/" + urllib.parse.quote(game.title), key)
        if not isinstance(found, list) or not found:
            return [], False
        data = _get(f"/grids/game/{found[0]['id']}", key, params)

    if not isinstance(data, list):
        return [], False

    portrait = [
        grid
        for grid in data
        if int(grid.get("height") or 0) > int(grid.get("width") or 0)
    ]
    options = [
        {
            "id": grid.get("id"),
            "url": grid.get("url"),
            "thumb": grid.get("thumb") or grid.get("url"),
        }
        for grid in portrait
    ]
    return options, len(data) >= PAGE_SIZE


def grids_for(game: Game, key: str, limit: int = MAX_OPTIONS) -> list[dict]:
    options, _ = grids_page(game, key, 0)
    return options[:limit]


def download(url: str, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".png"
    name = "sgdb-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + suffix
    target = folder / name
    part = target.with_name(target.name + ".part")

    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SteamGridDBError(tr("Couldn't download that artwork.")) from exc

    if len(data) < 1024:
        raise SteamGridDBError(tr("That artwork came back empty."))
    part.write_bytes(data)
    os.replace(part, target)
    return target
