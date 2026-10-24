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

    again = Preferences(path)
    assert again.accent == "#ff6b6b"
    assert again.cartridge_style == "ds"

    prefs.accent = "not-a-colour"
    assert prefs.accent == "#ff6b6b"
    prefs.cartridge_style = "nope"
    assert prefs.cartridge_style == "ds"


def test_cover_override_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    prefs = Preferences(path)

    assert prefs.cover_for("steam:1") == ""
    prefs.set_cover("steam:1", "C:/art/grid-1.png")
    assert prefs.cover_for("steam:1").endswith("grid-1.png")
    assert Preferences(path).cover_for("steam:1").endswith("grid-1.png")

    prefs.set_cover("steam:1", None)
    assert prefs.cover_for("steam:1") == ""


def test_missing_file_is_default(tmp_path) -> None:
    prefs = Preferences(tmp_path / "missing" / "settings.json")
    assert not prefs.is_favorite("steam:1")
    assert prefs.accent == DEFAULT_ACCENT
