"""Manual games: executable discovery and persistence."""

import sys
from pathlib import Path

from gamecenter.core.manual import ManualLibrary, find_executables


def _exe(folder: Path, name: str) -> Path:
    path = folder / (name + (".exe" if sys.platform == "win32" else ""))
    path.write_bytes(b"")
    if sys.platform != "win32":
        path.chmod(0o755)
    return path


def test_find_executables(tmp_path) -> None:
    root = tmp_path / "Game"
    root.mkdir()
    exe = _exe(root, "Game")
    nested = root / "bin"
    nested.mkdir()
    nested_exe = _exe(nested, "Nested")

    found = find_executables(root)

    assert exe in found
    assert nested_exe in found


def test_add_persists_and_reloads(tmp_path) -> None:
    root = tmp_path / "Game"
    root.mkdir()
    exe = _exe(root, "Game")
    path = tmp_path / "manual.json"

    library = ManualLibrary(path)
    game = library.add("My Game", str(root), str(exe))

    assert game.source == "local"
    assert game.source_label == "Local"
    assert game.title == "My Game"
    assert game.executable == exe
    assert game.install_dir == root

    again = ManualLibrary(path)
    assert [entry.title for entry in again.games()] == ["My Game"]


def test_add_detects_the_executable(tmp_path) -> None:
    root = tmp_path / "Game"
    root.mkdir()
    exe = _exe(root, "Game")
    library = ManualLibrary(tmp_path / "manual.json")

    game = library.add("My Game", str(root))

    assert game.executable == exe


def test_remove(tmp_path) -> None:
    root = tmp_path / "Game"
    root.mkdir()
    exe = _exe(root, "Game")
    path = tmp_path / "manual.json"
    library = ManualLibrary(path)
    game = library.add("My Game", str(root), str(exe))

    library.remove(game.id)

    assert ManualLibrary(path).games() == []
