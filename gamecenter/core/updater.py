"""Check GitHub Releases for a newer GameCenter.

Read-only: it asks the public API for the latest release and compares versions.
It never downloads or runs anything; the UI opens the release page so the user
can install the update consciously.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from .. import __version__

REPO = "Amaru221/GameCenter"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = f"GameCenter/{__version__}"


class UpdateError(RuntimeError):
    """A friendly message for the UI."""


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    tag: str
    url: str
    name: str
    notes: str
    published_at: str
    installer_url: str = ""
    installer_size: int = 0
    digest: str = ""


def parse_version(value: str) -> tuple[int, ...]:
    """'v0.4.2-beta.1' -> (0, 4, 2). Missing pieces are ignored."""
    core = str(value or "").strip().lstrip("vV").split("-", 1)[0]
    parts: list[int] = []
    for piece in core.split("."):
        match = re.match(r"\d+", piece)
        if not match:
            break
        parts.append(int(match.group()))
    return tuple(parts) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def fetch_latest(timeout: int = 10) -> dict:
    request = urllib.request.Request(
        API,
        headers={
            "User-Agent": UA,
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError("No releases found on GitHub.") from exc
        raise UpdateError(f"GitHub answered with an error ({exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError("Couldn't reach GitHub.") from exc
    except ValueError as exc:
        raise UpdateError("GitHub sent an unexpected answer.") from exc

    if not isinstance(data, dict):
        raise UpdateError("GitHub sent an unexpected answer.")
    return data


def check(current: str = __version__, timeout: int = 10) -> UpdateInfo | None:
    data = fetch_latest(timeout)
    tag = str(data.get("tag_name") or "").strip()
    version = tag.lstrip("vV")
    if not version or not is_newer(version, current):
        return None

    assets = data.get("assets") if isinstance(data.get("assets"), list) else []
    installer = next(
        (
            asset
            for asset in assets
            if str(asset.get("name", "")).endswith("-windows-setup.exe")
        ),
        None,
    ) or {}

    return UpdateInfo(
        version=version,
        tag=tag,
        url=str(data.get("html_url") or f"https://github.com/{REPO}/releases/latest"),
        name=str(data.get("name") or f"GameCenter {version}"),
        notes=str(data.get("body") or ""),
        published_at=str(data.get("published_at") or ""),
        installer_url=str(installer.get("browser_download_url") or ""),
        installer_size=int(installer.get("size") or 0),
        digest=str(installer.get("digest") or ""),
    )
