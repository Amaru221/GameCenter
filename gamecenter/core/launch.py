"""Start games and reveal their folders, with one small platform switch."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from .i18n import tr
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


def launch(game: Game) -> int | None:
    """Start `game`; returns the process id when the store gave us one."""
    if game.launch_uri:
        open_uri(game.launch_uri)
        return None

    if game.launch_command:
        # A trusted command line from the store's own registry entry.
        args = game.launch_command if sys.platform == "win32" else shlex.split(game.launch_command)
        process = subprocess.Popen(
            args,
            cwd=str(game.install_dir) if game.install_dir and game.install_dir.is_dir() else None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid

    if game.executable is not None and game.executable.is_file():
        process = subprocess.Popen(
            [str(game.executable), *game.launch_args],
            cwd=str(game.executable.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return process.pid

    raise LaunchError(tr("Don't know how to start {title}.", title=repr(game.title)))
