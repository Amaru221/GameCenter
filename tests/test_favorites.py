from gamecenter.core.favorites import Favorites


def test_favorites_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"

    favorites = Favorites(path)
    assert "steam:1" not in favorites
    assert favorites.toggle("steam:1") is True
    assert "steam:1" in favorites

    reloaded = Favorites(path)
    assert "steam:1" in reloaded
    assert reloaded.toggle("steam:1") is False
    assert "steam:1" not in Favorites(path)


def test_missing_file_is_an_empty_set(tmp_path) -> None:
    favorites = Favorites(tmp_path / "missing" / "settings.json")
    assert "steam:1" not in favorites
