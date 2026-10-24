from pathlib import Path

from gamecenter.core import steam


def _vdf_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _steam_tree(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "Steam"
    second = tmp_path / "SecondLibrary"
    (root / "steamapps").mkdir(parents=True, exist_ok=True)
    (second / "steamapps").mkdir(parents=True, exist_ok=True)
    _write(
        root / "steamapps" / "libraryfolders.vdf",
        f'''
        "libraryfolders"
        {{
            "0" {{ "path" "{_vdf_path(root)}" }}
            "1" {{ "path" "{_vdf_path(second)}" }}
            "contentstatsid" "123456"
        }}
        ''',
    )
    return root, second


def _manifest(library: Path, app_id: int, name: str, flags: int = 4, size: int = 0) -> None:
    _write(
        library / "steamapps" / f"appmanifest_{app_id}.acf",
        f'''
        "AppState"
        {{
            "appid"       "{app_id}"
            "name"        "{name}"
            "StateFlags"  "{flags}"
            "installdir"  "{name}"
            "SizeOnDisk"  "{size}"
            "LastPlayed"  "1700000000"
        }}
        ''',
    )


def test_scan_reads_every_library(tmp_path: Path) -> None:
    root, second = _steam_tree(tmp_path)
    _manifest(root, 220, "Half-Life 2", size=1000)
    _manifest(second, 570, "Dota 2", flags=2)

    games = steam.scan(roots=[root])

    assert [g.id for g in games] == ["steam:220", "steam:570"]
    half_life = games[0]
    assert half_life.title == "Half-Life 2"
    assert half_life.installed is True
    assert half_life.install_dir == root / "steamapps" / "common" / "Half-Life 2"
    assert half_life.launch_uri == "steam://rungameid/220"
    assert half_life.size_bytes == 1000
    assert half_life.last_played == 1700000000
    assert games[1].installed is False


def test_same_game_in_two_libraries_is_listed_once(tmp_path: Path) -> None:
    root, second = _steam_tree(tmp_path)
    _manifest(root, 220, "Half-Life 2")
    _manifest(second, 220, "Half-Life 2")

    assert len(steam.scan(roots=[root])) == 1


def test_broken_manifests_are_skipped(tmp_path: Path) -> None:
    root, _ = _steam_tree(tmp_path)
    _write(root / "steamapps" / "appmanifest_1.acf", '"AppState" { "appid" "1" }')
    _write(root / "steamapps" / "appmanifest_2.acf", "not a vdf document {{{")
    _manifest(root, 3, "Working Game")

    games = steam.scan(roots=[root])

    assert [g.app_id for g in games] == ["3"]


def test_tools_and_runtimes_are_hidden(tmp_path: Path) -> None:
    root, second = _steam_tree(tmp_path)
    _manifest(root, 228980, "Steamworks Common Redistributables")
    _manifest(second, 1070560, "Steam Linux Runtime 1.0 (scout)")
    _manifest(root, 220, "Half-Life 2")

    games = steam.scan(roots=[root])

    assert [g.title for g in games] == ["Half-Life 2"]


def test_old_libraryfolders_format(tmp_path: Path) -> None:
    root = tmp_path / "Steam"
    second = tmp_path / "OldLibrary"
    (root / "steamapps").mkdir(parents=True)
    (second / "steamapps").mkdir(parents=True)
    _write(
        root / "steamapps" / "libraryfolders.vdf",
        f'"libraryfolders" {{ "1" "{_vdf_path(second)}" }}',
    )
    _manifest(second, 440, "Team Fortress 2")

    games = steam.scan(roots=[root])

    assert [g.title for g in games] == ["Team Fortress 2"]


def test_no_roots_gives_empty_list() -> None:
    assert steam.scan(roots=[]) == []
