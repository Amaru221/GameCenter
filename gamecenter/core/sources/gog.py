"""GOG: installed games register under ``GOG.com\\Games``.

Each subkey is a product id with ``gameName``, ``path``, ``exe`` and often a
full ``launchCommand``. GOG Galaxy's SQLite database is not needed for games
installed through Galaxy, because they also register here.
"""

from __future__ import annotations

import shlex
from pathlib import Path

from ..models import Game
from . import _registry

SOURCE = "gog"


def _roots():
    winreg = _registry._winreg()
    if winreg is None:
        return ()
    return (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\GOG.com\Games",
            winreg.KEY_WOW64_32KEY,
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\GOG.com\Games",
            winreg.KEY_WOW64_64KEY,
        ),
        (winreg.HKEY_CURRENT_USER, r"Software\GOG.com\Games", 0),
    )


def game_from_values(app_id: str, values: dict) -> Game | None:
    title = str(values.get("gameName") or "").strip()
    if not title:
        return None

    install = str(values.get("path") or "").strip()
    install_dir = Path(install) if install else None

    command = str(values.get("launchCommand") or "").strip()
    exe = str(values.get("exe") or "").strip()
    params = str(values.get("launchParam") or "").strip()

    executable = None
    args: tuple[str, ...] = ()
    if not command and exe:
        candidate = Path(exe)
        if not candidate.is_absolute() and install_dir is not None:
            candidate = install_dir / exe
        if candidate.is_file():
            executable = candidate
            args = tuple(shlex.split(params)) if params else ()

    if not command and executable is None:
        return None

    return Game(
        id=f"{SOURCE}:{app_id}",
        title=title,
        source=SOURCE,
        app_id=app_id,
        install_dir=install_dir,
        launch_command=command,
        executable=executable,
        launch_args=args,
    )


def scan() -> list[Game]:
    found: dict[str, Game] = {}
    for hive, path, view in _roots():
        for app_id, values in _registry.iter_subkeys(hive, path, view):
            game = game_from_values(app_id, values)
            if game is not None:
                found.setdefault(game.id, game)
    return list(found.values())
