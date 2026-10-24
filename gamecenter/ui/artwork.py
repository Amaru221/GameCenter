"""Optional cover art from Steam's public CDN.

The launcher works offline: covers are drawn locally when no cached art exists.
When a connection is available, the official portrait capsule for each installed
Steam game is fetched once and cached under the user's cache folder. Only the
numeric AppID leaves the machine.

Set ``GC_NO_ART=1`` to stay fully offline.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

from .. import __version__

CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "gamecenter" / "art"
_URL = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
_UA = f"GameCenter/{__version__}"
_MIN_BYTES = 1024
MAX_DOWNLOADS = 80


def enabled() -> bool:
    return os.environ.get("GC_NO_ART", "") == ""


def cached_path(app_id: str) -> Path | None:
    path = CACHE / f"{app_id}.jpg"
    try:
        if path.is_file() and path.stat().st_size >= _MIN_BYTES:
            return path
    except OSError:
        pass
    return None


def fetch(app_id: str) -> bool:
    """Download one portrait capsule. Returns True when it landed in the cache."""
    if not enabled() or not app_id.isdigit():
        return False
    target = CACHE / f"{app_id}.jpg"
    part = target.with_name(f"{app_id}.part")
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            _URL.format(appid=app_id), headers={"User-Agent": _UA}
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            data = response.read()
        if len(data) < _MIN_BYTES:
            return False
        part.write_bytes(data)
        os.replace(part, target)
        return True
    except (OSError, ValueError, urllib.error.URLError):
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        return False
