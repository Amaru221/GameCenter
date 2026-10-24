"""Parsers for the non-Steam stores.

Each store is tested through its pure `game_from_values`/`parse_manifest`
helper, so the tests never depend on what is installed on the machine.
"""

import json

from gamecenter.core.sources import battlenet, epic, gog, riot


def test_epic_manifest(tmp_path) -> None:
    data = {
        "AppName": "Fortnite",
        "DisplayName": "Fortnite",
        "AppCategories": ["games", "applications"],
        "InstallLocation": str(tmp_path / "Fortnite"),
        "LaunchExecutable": "FortniteLauncher.exe",
        "CatalogItemId": "4fe75bbc5a674f4f9b356b5c90567da5",
        "InstallSize": 12345,
        "LastLaunchTime": "2026-10-20T10:00:00.000Z",
    }
    manifest = tmp_path / "Fortnite.item"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    game = epic.parse_manifest(manifest)

    assert game is not None
    assert game.id == "epic:Fortnite"
    assert game.title == "Fortnite"
    assert game.source_label == "Epic Games"
    assert game.launch_uri.startswith("com.epicgames.launcher://apps/")
    assert game.size_bytes == 12345
    assert game.last_played > 0


def test_epic_skips_incomplete_and_non_games(tmp_path) -> None:
    incomplete = tmp_path / "incomplete.item"
    incomplete.write_text(
        json.dumps({"AppName": "X", "DisplayName": "X", "bIsIncompleteInstall": True}),
        encoding="utf-8",
    )
    assert epic.parse_manifest(incomplete) is None

    plugin = tmp_path / "plugin.item"
    plugin.write_text(
        json.dumps(
            {
                "AppName": "UE_5.4",
                "DisplayName": "Unreal Engine",
                "AppCategories": ["assets"],
            }
        ),
        encoding="utf-8",
    )
    assert epic.parse_manifest(plugin) is None


def test_battlenet_reads_uninstall_values(tmp_path) -> None:
    values = {
        "DisplayName": "Overwatch",
        "Publisher": "Blizzard Entertainment",
        "InstallLocation": str(tmp_path / "Overwatch"),
        "DisplayIcon": str(tmp_path / "Overwatch" / "_retail_" / "Overwatch.exe"),
    }

    game = battlenet.game_from_values("Overwatch", values)

    assert game is not None
    assert game.id == "battlenet:overwatch"
    assert game.title == "Overwatch"
    assert game.source_label == "Battle.net"
    # The fake icon does not exist, so the launcher URI is the fallback.
    assert game.launch_uri == "battlenet://Pro"


def test_battlenet_skips_the_launcher_and_other_publishers() -> None:
    launcher = {
        "DisplayName": "Battle.net",
        "Publisher": "Blizzard Entertainment",
    }
    assert battlenet.game_from_values("Battle.net", launcher) is None

    other = {"DisplayName": "Something", "Publisher": "Other Studio"}
    assert battlenet.game_from_values("Something", other) is None


def test_riot_parses_product_and_uses_the_game_exe(tmp_path) -> None:
    install = tmp_path / "League of Legends"
    install.mkdir()
    (install / "LeagueClient.exe").write_bytes(b"")
    values = {"DisplayName": "League of Legends", "InstallLocation": str(install)}

    game = riot.game_from_values("Riot Game league_of_legends.live", values, client=None)

    assert game is not None
    assert game.id == "riot:league_of_legends"
    assert game.title == "League of Legends"
    assert game.executable is not None
    assert game.executable.name == "LeagueClient.exe"


def test_riot_uses_the_client_arguments(tmp_path) -> None:
    client = tmp_path / "RiotClientServices.exe"
    client.write_bytes(b"")

    game = riot.game_from_values(
        "Riot Game valorant.live", {"DisplayName": "VALORANT"}, client=client
    )

    assert game is not None
    assert game.executable == client
    assert game.launch_args == (
        "--launch-product=valorant",
        "--launch-patchline=live",
    )


def test_gog_reads_registry_values(tmp_path) -> None:
    exe = tmp_path / "game.exe"
    exe.write_bytes(b"")
    values = {
        "gameName": "The Witcher 3",
        "path": str(tmp_path),
        "exe": "game.exe",
        "launchParam": "-dx11",
    }

    game = gog.game_from_values("1207664643", values)

    assert game is not None
    assert game.id == "gog:1207664643"
    assert game.title == "The Witcher 3"
    assert game.source_label == "GOG"
    assert game.executable == exe
    assert game.launch_args == ("-dx11",)


def test_gog_prefers_the_launch_command(tmp_path) -> None:
    values = {
        "gameName": "Game",
        "path": str(tmp_path),
        "launchCommand": r'"C:\Games\Game\game.exe" /foo',
    }

    game = gog.game_from_values("1", values)

    assert game is not None
    assert game.launch_command.startswith('"C:\\Games')


def test_scan_all_survives_a_broken_source(monkeypatch) -> None:
    from gamecenter.core import sources

    class Broken:
        @staticmethod
        def scan():
            raise RuntimeError("boom")

    monkeypatch.setattr(sources, "SOURCES", (Broken,))
    assert sources.scan_all() == []
