"""Riot Games: the installer writes ``Riot Game <product>.<patchline>`` keys.

Games are started through the Riot Client, which takes the product and
patchline as arguments. If the client is missing, the game executable is used
directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..models import Game
from . import _registry

SOURCE = "riot"

_TITLES = {
    "league_of_legends": "League of Legends",
    "valorant": "VALORANT",
    "bacon": "Legends of Runeterra",
    "lor": "Legends of Runeterra",
}
_SKIP_PRODUCTS = {"riot_client", "riot client"}
_UNSET = object()


def _split_key(name: str) -> tuple[str, str] | None:
    prefix = "riot game "
    if not name.casefold().startswith(prefix):
        return None
    rest = name[len(prefix) :].strip()
    if not rest:
        return None
    if "." in rest:
        product, patchline = rest.rsplit(".", 1)
    else:
        product, patchline = rest, "live"
    return product.strip(), (patchline.strip() or "live")


def _riot_client() -> Path | None:
    bases = (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(r"C:\Riot Games"),
    )
    for base in bases:
        for candidate in (
            base / "Riot Games" / "Riot Client" / "RiotClientServices.exe",
            base / "Riot Client" / "RiotClientServices.exe",
        ):
            if candidate.is_file():
                return candidate
    return None


def _find_exe(folder: Path, product: str) -> Path | None:
    names = {
        "league_of_legends": ("LeagueClient.exe", "League of Legends.exe"),
        "valorant": ("VALORANT.exe",),
    }.get(product, ())
    for name in names:
        try:
            for candidate in folder.rglob(name):
                if candidate.is_file():
                    return candidate
        except OSError:
            continue
    return None


def game_from_values(key_name: str, values: dict, client=_UNSET) -> Game | None:
    parts = _split_key(key_name)
    if parts is None:
        return None
    product, patchline = parts
    if product.casefold() in _SKIP_PRODUCTS:
        return None

    display = str(values.get("DisplayName") or "").strip()
    if not display:
        display = _TITLES.get(product, product.replace("_", " ").title())

    install = str(values.get("InstallLocation") or "").strip()
    install_dir = Path(install) if install else None

    executable = None
    args: tuple[str, ...] = ()
    if client is _UNSET:
        client = _riot_client()
    if client is not None:
        executable = client
        args = (f"--launch-product={product}", f"--launch-patchline={patchline}")
    elif install_dir is not None:
        executable = _find_exe(install_dir, product)

    if executable is None:
        return None

    return Game(
        id=f"{SOURCE}:{product.casefold()}",
        title=display,
        source=SOURCE,
        app_id=f"{product}.{patchline}",
        install_dir=install_dir,
        executable=executable,
        launch_args=args,
    )


def scan() -> list[Game]:
    found: dict[str, Game] = {}
    for key_name, values in _registry.iter_uninstall():
        game = game_from_values(key_name, values)
        if game is not None:
            found.setdefault(game.id, game)
    return list(found.values())
