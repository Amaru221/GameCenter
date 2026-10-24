"""Every source exposes ``scan() -> list[Game]``.

A failure in one store never hides the games from the others: each scan is
isolated and logged.
"""

from __future__ import annotations

import logging

from ..models import Game
from . import battlenet, epic, gog, local, riot, steam

log = logging.getLogger("gamecenter.sources")

SOURCES = (steam, epic, gog, battlenet, riot, local)


def scan_all() -> list[Game]:
    found: dict[str, Game] = {}
    for module in SOURCES:
        try:
            games = module.scan()
        except Exception:  # noqa: BLE001 - a broken store must not break the app
            log.exception("Couldn't scan %s", module.__name__)
            continue
        for game in games:
            found.setdefault(game.id, game)
    return sorted(found.values(), key=lambda g: (not g.installed, g.title.casefold()))
