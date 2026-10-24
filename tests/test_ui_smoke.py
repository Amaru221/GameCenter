"""Tests for the Qt model and the procedural artwork.

The window itself is loaded once, headlessly, so a broken QML file fails the
suite instead of only showing up when someone runs the app.
"""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from gamecenter.core.models import Game  # noqa: E402
from gamecenter.ui import covers, library_model  # noqa: E402


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def games() -> list[Game]:
    return [
        Game(id="steam:1", title="Alpha Quest", source="steam", app_id="123", last_played=100),
        Game(id="steam:2", title="Beta Racer", source="steam", installed=False),
        Game(id="epic:3", title="Gamma Flight", source="epic", last_played=300),
    ]


@pytest.fixture
def model(app, monkeypatch, games, tmp_path):
    monkeypatch.setattr(library_model, "scan_all", lambda: games)
    return library_model.LibraryModel(
        download_art=False, favorites_path=tmp_path / "settings.json"
    )


def test_model_lists_and_filters(model) -> None:
    assert model.rowCount() == 3

    model.setQuery("alpha")
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), library_model.ROLE_TITLE) == "Alpha Quest"

    model.setQuery("")
    assert model.rowCount() == 3

    model.setSourceFilter("epic")
    assert model.rowCount() == 1
    assert model.data(model.index(0, 0), library_model.ROLE_SOURCE) == "Epic Games"

    model.setSourceFilter("")
    assert model.rowCount() == 3


def test_model_sorts(model) -> None:
    model.setSort("title")
    titles = [model.data(model.index(i, 0), library_model.ROLE_TITLE) for i in range(3)]
    assert titles == ["Alpha Quest", "Beta Racer", "Gamma Flight"]

    model.setSort("recent")
    titles = [model.data(model.index(i, 0), library_model.ROLE_TITLE) for i in range(3)]
    assert titles[0] == "Gamma Flight"


def test_meta_line_has_store_id_and_tag(model) -> None:
    model.setQuery("alpha")
    meta = model.data(model.index(0, 0), library_model.ROLE_META)
    assert meta == "STEAM · 123 · ALPH"


def test_cover_is_generated(app) -> None:
    image = covers.render_cover("Half-Life 2")
    assert not image.isNull()
    assert image.width() == 336
    assert image.height() == 384


def test_background_is_generated(app) -> None:
    image = covers.render_background(640, 400)
    assert not image.isNull()
    assert image.size().width() == 640


def test_favorites_toggle_and_filter(model) -> None:
    assert model.rowCount() == 3

    model.toggleFavorite(0)
    assert model.data(model.index(0, 0), library_model.ROLE_FAVORITE) is True

    model.setFavoritesOnly(True)
    assert model.rowCount() == 1

    model.setFavoritesOnly(False)
    assert model.rowCount() == 3

    model.toggleFavorite(0)
    assert model.data(model.index(0, 0), library_model.ROLE_FAVORITE) is False


def test_source_options_have_labels(model) -> None:
    options = model.sourceOptions
    assert {option["value"] for option in options} == {"steam", "epic"}
    assert {option["text"] for option in options} == {"Steam", "Epic Games"}


def test_game_at_returns_detail_data(model) -> None:
    model.setQuery("alpha")
    detail = model.gameAt(0)
    assert detail["title"] == "Alpha Quest"
    assert detail["source"] == "Steam"
    assert detail["appId"] == "123"
    assert detail["cover"].startswith("image://cover/")
    assert detail["hasFolder"] is False
    assert detail["lastPlayed"].startswith("Played")


def test_provider_prefers_cached_art(app, tmp_path, monkeypatch) -> None:
    from PySide6.QtGui import QColor, QImage

    from gamecenter.ui import artwork

    monkeypatch.setattr(artwork, "CACHE", tmp_path)
    poster = QImage(600, 900, QImage.Format_RGB32)
    poster.fill(QColor("#ff0000"))
    assert poster.save(str(tmp_path / "730.jpg"), "JPEG")

    key = covers.cover_key("Counter-Strike 2", "730")
    image = covers.CoverProvider().request(key)
    assert (image.width(), image.height()) == (600, 900)


def test_provider_falls_back_to_procedural_art(app, tmp_path, monkeypatch) -> None:
    from gamecenter.ui import artwork

    monkeypatch.setattr(artwork, "CACHE", tmp_path)
    key = covers.cover_key("No Art Game", "999999")
    image = covers.CoverProvider().request(key)
    assert (image.width(), image.height()) == (336, 384)


def test_qml_window_loads(app, model) -> None:
    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    roots = engine.rootObjects()
    assert roots, "Main.qml failed to load"
    assert roots[0].property("title") == "GameCenter"
