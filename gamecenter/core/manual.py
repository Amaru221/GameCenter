"""Games added by hand: a title, a root folder and an executable."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .i18n import tr
from .models import Game
from .preferences import config_dir

SOURCE = "local"
MAX_EXECUTABLES = 80


def manual_path() -> Path:
    return config_dir() / "manual.json"


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return text[:40] or "game"


def find_executables(folder: Path, limit: int = MAX_EXECUTABLES) -> list[Path]:
    """Executables in `folder`, up to two levels deep, sorted by name."""
    if not folder.is_dir():
        return []

    found: dict[str, Path] = {}
    if sys.platform == "win32":
        patterns = ("*.exe", "*/*.exe", "*/*/*.exe")
    else:
        patterns = ("*", "*/*", "*/*/*")

    for pattern in patterns:
        try:
            candidates = folder.glob(pattern)
        except OSError:
            continue
        for path in candidates:
            try:
                if not path.is_file():
                    continue
                if sys.platform == "win32":
                    if path.suffix.casefold() != ".exe":
                        continue
                elif not os.access(path, os.X_OK):
                    continue
            except OSError:
                continue
            key = str(path.resolve()).casefold()
            found.setdefault(key, path)
            if len(found) >= limit:
                break
        if len(found) >= limit:
            break

    return sorted(found.values(), key=lambda path: path.name.casefold())


@dataclass(frozen=True)
class ManualGame:
    id: str
    title: str
    folder: str
    executable: str

    def to_game(self) -> Game:
        return Game(
            id=self.id,
            title=self.title,
            source=SOURCE,
            app_id=self.id.split(":", 1)[-1],
            install_dir=Path(self.folder),
            executable=Path(self.executable),
            installed=True,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ManualGame | None":
        try:
            game_id = str(data["id"])
            title = str(data["title"]).strip()
            folder = str(data["folder"])
            executable = str(data["executable"])
        except (KeyError, TypeError, ValueError):
            return None
        if not game_id or not title or not folder or not executable:
            return None
        return cls(game_id, title, folder, executable)


class ManualLibrary:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or manual_path()
        self._games: list[ManualGame] = self._load()

    def _load(self) -> list[ManualGame]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        games = []
        for entry in data:
            if isinstance(entry, dict):
                game = ManualGame.from_dict(entry)
                if game is not None:
                    games.append(game)
        return games

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    [
                        {
                            "id": game.id,
                            "title": game.title,
                            "folder": game.folder,
                            "executable": game.executable,
                        }
                        for game in self._games
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )
            os.replace(tmp, self.path)
        except OSError:
            pass

    def games(self) -> list[Game]:
        return [game.to_game() for game in self._games]

    def add(self, title: str, folder: str, executable: str = "") -> Game:
        title = (title or "").strip()
        folder_path = Path(folder).expanduser()
        if not title:
            raise ValueError(tr("Give the game a title."))
        if not folder_path.is_dir():
            raise ValueError(tr("Choose a valid root folder."))

        exe = Path(executable).expanduser() if executable else None
        if exe is None or not exe.is_file():
            candidates = find_executables(folder_path)
            if not candidates:
                raise ValueError(tr("No executable found in that folder."))
            exe = candidates[0]
        if not exe.is_file():
            raise ValueError(tr("That executable doesn't exist."))

        game_id = f"{SOURCE}:{_slug(title)}-{hashlib.sha1(str(folder_path.resolve()).encode('utf-8')).hexdigest()[:6]}"
        self._games = [game for game in self._games if game.id != game_id]
        self._games.append(ManualGame(game_id, title, str(folder_path), str(exe)))
        self._save()
        return self._games[-1].to_game()

    def remove(self, game_id: str) -> None:
        before = len(self._games)
        self._games = [game for game in self._games if game.id != game_id]
        if len(self._games) != before:
            self._save()
