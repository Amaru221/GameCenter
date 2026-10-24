"""Battle.net: installed Blizzard games register under Windows' Uninstall keys."""

from __future__ import annotations

from pathlib import Path

from ..models import Game
from . import _registry

SOURCE = "battlenet"

_SKIP = {"battle.net", "blizzard entertainment", "blizzard uninstaller"}

# Used when the registry has no executable but the game is still installed.
_URIS = {
    "overwatch": "battlenet://Pro",
    "overwatch 2": "battlenet://Pro",
    "world of warcraft": "battlenet://WoW",
    "diablo iii": "battlenet://D3",
    "diablo iv": "battlenet://D4",
    "starcraft ii": "battlenet://S2",
    "hearthstone": "battlenet://WTCG",
    "heroes of the storm": "battlenet://Hero",
}

_IDS = {
    "overwatch": "Pro",
    "overwatch 2": "Pro",
    "world of warcraft": "WoW",
    "diablo iii": "D3",
    "diablo iv": "D4",
    "starcraft ii": "S2",
    "hearthstone": "WTCG",
    "heroes of the storm": "Hero",
}

_KNOWN_EXES = (
    "Overwatch.exe",
    "Wow.exe",
    "Diablo III.exe",
    "Diablo IV.exe",
    "SC2.exe",
    "Hearthstone.exe",
    "HeroesOfTheStorm.exe",
    "CoD.exe",
)


def _icon_path(value) -> Path | None:
    text = str(value or "").strip()
    if text.startswith('"'):
        end = text.find('"', 1)
        text = text[1:end] if end > 0 else text.strip('"')
    elif "," in text:
        text = text.split(",", 1)[0]
    text = text.strip().strip('"')
    if not text.casefold().endswith(".exe"):
        return None
    path = Path(text)
    return path if path.is_file() else None


def _find_exe(folder: Path) -> Path | None:
    if not folder.is_dir():
        return None
    for name in _KNOWN_EXES:
        candidate = folder / name
        if candidate.is_file():
            return candidate
    try:
        for child in folder.iterdir():
            if not child.is_dir():
                continue
            for name in _KNOWN_EXES:
                candidate = child / name
                if candidate.is_file():
                    return candidate
    except OSError:
        pass
    return None


def game_from_values(key_name: str, values: dict) -> Game | None:
    display = str(values.get("DisplayName") or "").strip()
    publisher = str(values.get("Publisher") or "").strip()
    if not display or "blizzard" not in publisher.casefold():
        return None
    if display.casefold() in _SKIP:
        return None

    install = str(values.get("InstallLocation") or "").strip()
    install_dir = Path(install) if install else None
    executable = _icon_path(values.get("DisplayIcon"))
    if executable is None and install_dir is not None:
        executable = _find_exe(install_dir)

    launch_uri = "" if executable is not None else _URIS.get(display.casefold(), "")

    return Game(
        id=f"{SOURCE}:{key_name.casefold()}",
        title=display,
        source=SOURCE,
        app_id=_IDS.get(display.casefold(), key_name),
        install_dir=install_dir,
        launch_uri=launch_uri,
        executable=executable,
    )


def scan() -> list[Game]:
    found: dict[str, Game] = {}
    for key_name, values in _registry.iter_uninstall():
        game = game_from_values(key_name, values)
        if game is not None:
            found.setdefault(game.id, game)
    return list(found.values())
