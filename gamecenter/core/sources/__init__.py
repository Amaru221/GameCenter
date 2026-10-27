"""Every source exposes ``scan() -> list[Game]``.

A failure in one store never hides the games from the others: each scan is
isolated and logged.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from .. import playtime, profiles
from ..models import Game
from . import battlenet, epic, gog, local, riot, steam

log = logging.getLogger("gamecenter.sources")

SOURCES = (steam, epic, gog, battlenet, riot, local)


def _with_playtime(games: list[Game]) -> list[Game]:
    out: list[Game] = []
    for game in games:
        merged = profiles.merged_seconds(game.id)
        if merged:
            game = replace(
                game,
                playtime_minutes=max(0, game.playtime_minutes - merged // 60),
            )
        extra = profiles.extra_seconds(game.id)
        if extra:
            game = replace(
                game,
                playtime_minutes=game.playtime_minutes + extra // 60,
                last_played=max(
                    game.last_played, profiles.extra_last_played(game.id)
                ),
            )
        if game.source != "steam":
            playtime.restore_to_root(game)
            summary = playtime.summary_for(game)
            if summary:
                try:
                    seconds = int(summary.get("seconds") or 0)
                except (TypeError, ValueError):
                    seconds = 0
                try:
                    last_played = int(summary.get("last_played") or 0)
                except (TypeError, ValueError):
                    last_played = 0
                game = replace(
                    game,
                    playtime_minutes=seconds // 60,
                    last_played=last_played or game.last_played,
                )
        out.append(game)
    return out


def _dedupe(games: list[Game]) -> list[Game]:
    found: dict[str, Game] = {}
    for game in games:
        found.setdefault(game.id, game)
    return list(found.values())


def scan_all() -> list[Game]:
    found: list[Game] = []
    for module in SOURCES:
        try:
            games = module.scan()
        except Exception:  # noqa: BLE001 - a broken store must not break the app
            log.exception("Couldn't scan %s", module.__name__)
            continue
        found.extend(_with_playtime(games))
    return sorted(
        _dedupe(found), key=lambda g: (not g.installed, g.title.casefold())
    )


def scan_source(source: str) -> list[Game]:
    """Scan one store without touching the games from the other stores."""
    module = next(
        (item for item in SOURCES if getattr(item, "SOURCE", "") == source), None
    )
    if module is None:
        return []
    return _dedupe(_with_playtime(module.scan()))
