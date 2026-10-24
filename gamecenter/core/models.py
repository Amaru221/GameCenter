"""The data the rest of the app works with."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SOURCE_LABELS = {
    "steam": "Steam",
    "epic": "Epic Games",
    "gog": "GOG",
    "battlenet": "Battle.net",
    "riot": "Riot",
    "local": "Local",
}


@dataclass(frozen=True)
class Game:
    """One entry in the library.

    `id` is namespaced by source ("steam:220") so two stores can never collide.
    `launch_uri` is used when the store knows how to start the game itself;
    `executable` is the fallback for games launched directly.
    """

    id: str
    title: str
    source: str
    app_id: str = ""
    install_dir: Path | None = None
    launch_uri: str = ""
    launch_command: str = ""
    executable: Path | None = None
    launch_args: tuple[str, ...] = ()
    installed: bool = True
    size_bytes: int = 0
    last_played: int = 0
    playtime_minutes: int = 0

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.source, self.source.capitalize())

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3) if self.size_bytes else 0.0
