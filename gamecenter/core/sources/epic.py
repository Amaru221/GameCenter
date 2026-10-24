"""Epic Games Store: the launcher writes one JSON manifest per installed app.

The manifests live under ``%ProgramData%``. Older launchers used
``EpicGamesLauncher``; current ones use ``Epic\\EpicGamesLauncher``. Both are
checked.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ..models import Game

SOURCE = "epic"


def manifest_dirs() -> list[Path]:
    program_data = Path(os.environ.get("ProgramData", r"C:\ProgramData"))
    candidates = (
        program_data / "EpicGamesLauncher" / "Data" / "Manifests",
        program_data / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests",
    )
    return [path for path in candidates if path.is_dir()]


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _timestamp(value) -> int:
    if not value:
        return 0
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return 0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def parse_manifest(path: Path) -> Game | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("bIsIncompleteInstall"):
        return None

    categories = {str(c).casefold() for c in data.get("AppCategories") or []}
    if categories and "games" not in categories:
        return None

    app_name = str(data.get("AppName") or "").strip()
    title = str(data.get("DisplayName") or data.get("AppTitle") or app_name).strip()
    if not app_name or not title:
        return None
    if app_name.upper().startswith("UE_") or "unreal engine" in title.casefold():
        return None

    install = str(data.get("InstallLocation") or "").strip()
    install_dir = Path(install) if install else None
    executable = None
    exe_name = str(data.get("LaunchExecutable") or "").strip()
    if install_dir is not None and exe_name:
        candidate = install_dir / exe_name
        if candidate.is_file():
            executable = candidate

    catalog = str(data.get("CatalogItemId") or data.get("CatalogItemID") or "").strip()
    launch_uri = (
        f"com.epicgames.launcher://apps/{catalog}?action=launch&silent=true"
        if catalog
        else ""
    )

    return Game(
        id=f"{SOURCE}:{app_name}",
        title=title,
        source=SOURCE,
        app_id=app_name,
        install_dir=install_dir,
        launch_uri=launch_uri,
        executable=executable,
        size_bytes=_int(data.get("InstallSize")),
        last_played=_timestamp(data.get("LastLaunchTime") or data.get("LastRunTime")),
    )


def scan() -> list[Game]:
    found: dict[str, Game] = {}
    for directory in manifest_dirs():
        for manifest in directory.glob("*.item"):
            game = parse_manifest(manifest)
            if game is not None:
                found.setdefault(game.id, game)
    return list(found.values())
