"""Command-line entry point: the GUI by default, or a text scan."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from . import __version__
from .core import steam
from .core.models import Game


def _as_dict(game: Game) -> dict:
    return {
        "id": game.id,
        "title": game.title,
        "source": game.source,
        "app_id": game.app_id,
        "installed": game.installed,
        "install_dir": str(game.install_dir) if game.install_dir else None,
        "size_bytes": game.size_bytes,
        "last_played": game.last_played,
        "launch_uri": game.launch_uri,
    }


def _print_table(games: list[Game]) -> None:
    if not games:
        print("No games found.")
        return
    width = max(len(g.title) for g in games)
    print(f"{'TITLE':<{width}}  {'SOURCE':<8}  {'INSTALLED':<9}  SIZE")
    for g in games:
        size = f"{g.size_bytes / (1024 ** 3):.1f} GB" if g.size_bytes else "-"
        print(f"{g.title:<{width}}  {g.source:<8}  {'yes' if g.installed else 'no':<9}  {size}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamecenter",
        description="Local-first game library launcher.",
    )
    parser.add_argument("--scan", action="store_true", help="list detected games and exit")
    parser.add_argument("--json", action="store_true", help="with --scan, print JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.scan:
        games = steam.scan()
        if args.json:
            print(json.dumps([_as_dict(g) for g in games], indent=2, ensure_ascii=False))
        else:
            _print_table(games)
        return 0

    from .ui.main_window import run

    return run(list(sys.argv if argv is None else argv))
