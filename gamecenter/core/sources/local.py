"""Games added manually from the + button."""

from __future__ import annotations

from ..manual import ManualLibrary
from ..models import Game

SOURCE = "local"


def scan() -> list[Game]:
    return ManualLibrary().games()
