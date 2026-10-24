"""Find the games Steam has installed on this machine.

Steam keeps one manifest per installed app in ``<library>/steamapps`` and lists
every library in ``libraryfolders.vdf``. Reading those two files is enough to
build a library without asking Steam or the network anything.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from .. import vdf
from ..models import Game

SOURCE = "steam"
_FULLY_INSTALLED = 4  # StateFlags bit set once Steam has finished installing

# Steam installs runtimes and tools next to real games. Hide the obvious ones so
# they don't show up as cartridges. Matching by name keeps this safe: a game
# that merely contains "Proton" in its title is left alone.
_NON_GAME_NAMES = {
    "steamworks common redistributables",
    "proton experimental",
    "proton hotfix",
}
_NON_GAME_PREFIXES = ("steam linux runtime",)


def _looks_like_game(title: str) -> bool:
    lowered = title.casefold()
    return lowered not in _NON_GAME_NAMES and not lowered.startswith(_NON_GAME_PREFIXES)


def _registry_roots() -> list[Path]:
    """Steam locations recorded by the Windows installer."""
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows only
        return []

    out: list[Path] = []
    lookups = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    )
    for hive, subkey, name in lookups:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, name)
        except OSError:
            continue
        if value:
            out.append(Path(value))
    return out


def _common_roots() -> list[Path]:
    home = Path.home()
    if sys.platform == "win32":
        bases = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")]
        return [Path(b) / "Steam" for b in bases if b]
    if sys.platform == "darwin":
        return [home / "Library" / "Application Support" / "Steam"]
    return [
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
    ]


def steam_roots() -> list[Path]:
    """Existing Steam install directories, deduplicated."""
    candidates = _registry_roots() + _common_roots()
    seen: set[str] = set()
    roots: list[Path] = []
    for path in candidates:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            continue
        key = os.path.normcase(str(resolved))
        if key in seen or not resolved.is_dir():
            continue
        seen.add(key)
        roots.append(resolved)
    return roots


def library_folders(root: Path) -> list[Path]:
    """`root` plus every library listed in its libraryfolders.vdf."""
    libraries = [root]
    document = root / "steamapps" / "libraryfolders.vdf"
    if not document.is_file():
        return libraries
    try:
        tree = vdf.parse(document.read_text(encoding="utf-8", errors="replace"))
    except (OSError, vdf.VdfError):
        return libraries

    node = vdf.get_block(tree, "libraryfolders") or tree
    for key, value in node.items():
        if isinstance(value, dict):
            path = vdf.get(value, "path")
        elif key.isdigit():
            path = value  # older format: "1" "D:\\SteamLibrary"
        else:
            continue  # contentstatsid and friends
        if not isinstance(path, str) or not path:
            continue
        candidate = Path(path)
        if candidate.is_dir():
            libraries.append(candidate)

    seen: set[str] = set()
    unique: list[Path] = []
    for path in libraries:
        key = os.path.normcase(str(path.resolve()))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _int(value: str | None, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _read_manifest(manifest: Path, library: Path) -> Game | None:
    try:
        tree = vdf.parse(manifest.read_text(encoding="utf-8", errors="replace"))
    except (OSError, vdf.VdfError):
        return None

    state = vdf.get_block(tree, "AppState")
    if state is None:
        return None

    app_id = vdf.get(state, "appid", "") or ""
    title = (vdf.get(state, "name", "") or "").strip()
    if not app_id or not title or not _looks_like_game(title):
        return None

    flags = _int(vdf.get(state, "StateFlags"), -1)
    installed = True if flags < 0 else bool(flags & _FULLY_INSTALLED)

    install_dir = None
    folder = vdf.get(state, "installdir", "")
    if folder:
        install_dir = library / "steamapps" / "common" / folder

    return Game(
        id=f"{SOURCE}:{app_id}",
        title=title,
        source=SOURCE,
        app_id=app_id,
        install_dir=install_dir,
        launch_uri=f"steam://rungameid/{app_id}",
        installed=installed,
        size_bytes=_int(vdf.get(state, "SizeOnDisk")),
        last_played=_int(vdf.get(state, "LastPlayed")),
    )


def _playtime(root: Path) -> dict[str, int]:
    """Minutes per app id, from the most recently used account's localconfig."""
    userdata = root / "userdata"
    if not userdata.is_dir():
        return {}

    best: tuple[float, Path] | None = None
    try:
        accounts = [p for p in userdata.iterdir() if p.is_dir() and p.name.isdigit()]
    except OSError:
        return {}
    for account in accounts:
        config = account / "config" / "localconfig.vdf"
        try:
            mtime = config.stat().st_mtime
        except OSError:
            continue
        if best is None or mtime > best[0]:
            best = (mtime, config)
    if best is None:
        return {}

    try:
        tree = vdf.parse(best[1].read_text(encoding="utf-8", errors="replace"))
    except (OSError, vdf.VdfError):
        return {}

    node = tree
    for key in ("UserLocalConfigStore", "Software", "Valve", "Steam", "apps"):
        node = vdf.get_block(node, key)
        if node is None:
            return {}

    minutes: dict[str, int] = {}
    for app_id, entry in node.items():
        if isinstance(entry, dict):
            value = _int(vdf.get(entry, "Playtime"), 0)
            if value > 0:
                minutes[app_id] = value
    return minutes


def scan(roots: Iterable[Path] | None = None) -> list[Game]:
    """Every game installed in the given Steam roots (all detected ones by default)."""
    found: dict[str, Game] = {}
    for root in roots if roots is not None else steam_roots():
        root = Path(root)
        playtime = _playtime(root)
        for library in library_folders(root):
            steamapps = library / "steamapps"
            if not steamapps.is_dir():
                continue
            for manifest in steamapps.glob("appmanifest_*.acf"):
                game = _read_manifest(manifest, library)
                if game is None:
                    continue
                if game.app_id in playtime:
                    game = replace(game, playtime_minutes=playtime[game.app_id])
                found.setdefault(game.id, game)

    return sorted(found.values(), key=lambda g: (not g.installed, g.title.casefold()))
