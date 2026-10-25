from gamecenter.core.preferences import DEFAULT_ACCENT, Preferences


def test_favorites_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"

    prefs = Preferences(path)
    assert not prefs.is_favorite("steam:1")
    assert prefs.toggle_favorite("steam:1") is True
    assert prefs.is_favorite("steam:1")

    reloaded = Preferences(path)
    assert reloaded.is_favorite("steam:1")
    assert reloaded.toggle_favorite("steam:1") is False
    assert not Preferences(path).is_favorite("steam:1")


def test_appearance_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"

    prefs = Preferences(path)
    assert prefs.accent == DEFAULT_ACCENT
    assert prefs.cartridge_style == "classic"

    prefs.accent = "#ff6b6b"
    prefs.cartridge_style = "ds"
    prefs.surface_color = "#1f2a33"
    prefs.cartridge_color = "#5b616b"

    again = Preferences(path)
    assert again.accent == "#ff6b6b"
    assert again.cartridge_style == "ds"
    assert again.surface_color == "#1f2a33"
    assert again.cartridge_color == "#5b616b"

    prefs.accent = "not-a-colour"
    assert prefs.accent == "#ff6b6b"
    prefs.cartridge_style = "nope"
    assert prefs.cartridge_style == "ds"
    prefs.surface_color = "nope"
    assert prefs.surface_color == "#1f2a33"


def test_cover_override_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    prefs = Preferences(path)

    assert prefs.cover_for("steam:1") == ""
    prefs.set_cover("steam:1", "C:/art/grid-1.png")
    assert prefs.cover_for("steam:1").endswith("grid-1.png")
    assert Preferences(path).cover_for("steam:1").endswith("grid-1.png")

    prefs.set_cover("steam:1", None)
    assert prefs.cover_for("steam:1") == ""


def test_game_cartridge_color_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    prefs = Preferences(path)

    assert prefs.cartridge_color_for("steam:1") == ""
    prefs.set_cartridge_color("steam:1", "#ff6b6b")
    assert prefs.cartridge_color_for("steam:1") == "#ff6b6b"
    assert Preferences(path).cartridge_color_for("steam:1") == "#ff6b6b"

    prefs.set_cartridge_color("steam:1", None)
    assert prefs.cartridge_color_for("steam:1") == ""


def test_update_preferences_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"

    prefs = Preferences(path)
    assert prefs.check_updates is True
    assert prefs.last_update_check == 0

    prefs.check_updates = False
    prefs.last_update_check = 123.5

    again = Preferences(path)
    assert again.check_updates is False
    assert again.last_update_check == 123.5


def test_missing_file_is_default(tmp_path) -> None:
    prefs = Preferences(tmp_path / "missing" / "settings.json")
    assert not prefs.is_favorite("steam:1")
    assert prefs.accent == DEFAULT_ACCENT
