"""Start games and reveal their folders, with one small platform switch."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .models import Game


class LaunchError(RuntimeError):
    """The game has no known way to start."""


def open_uri(uri: str) -> None:
    """Hand a URI (steam://, heroic:// …) to the operating system."""
    if sys.platform == "win32":
        os.startfile(uri)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch(game: Game) -> None:
    """Start `game`, preferring the store's own launcher."""
    if game.launch_uri:
        open_uri(game.launch_uri)
        return
    if game.executable is not None and game.executable.is_file():
        subprocess.Popen(
            [str(game.executable)],
            cwd=str(game.executable.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    raise LaunchError(f"Don't know how to start {game.title!r}.")
