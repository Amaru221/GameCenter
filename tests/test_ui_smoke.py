"""Tests for the Qt model and the procedural artwork.

The window itself is loaded once, headlessly, so a broken QML file fails the
suite instead of only showing up when someone runs the app.
"""

import os
import time
from datetime import date

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("GC_NO_GAMEPAD", "1")

from gamecenter.core.models import Game  # noqa: E402
from gamecenter.ui import covers, library_model  # noqa: E402


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def games() -> list[Game]:
    return [
        Game(
            id="steam:1",
            title="Alpha Quest",
            source="steam",
            app_id="123",
            last_played=100,
        ),
        Game(
            id="steam:2",
            title="Beta Racer",
            source="steam",
            installed=False,
            playtime_minutes=120,
        ),
        Game(
            id="epic:3",
            title="Gamma Flight",
            source="epic",
            last_played=300,
            playtime_minutes=30,
        ),
    ]


@pytest.fixture
def model(app, monkeypatch, games, tmp_path):
    monkeypatch.setattr(library_model, "scan_all", lambda: games)
    monkeypatch.setattr(library_model.credentials, "get_key", lambda: "")
    monkeypatch.setattr(
        library_model.playtime, "_fallback_path", lambda: tmp_path / "playtime.json"
    )
    monkeypatch.setattr(
        library_model.playtime, "history_path", lambda: tmp_path / "history.json"
    )
    monkeypatch.setattr(library_model.artwork, "CACHE", tmp_path / "art")
    monkeypatch.setattr(
        library_model.metadata, "cache_path", lambda: tmp_path / "metadata.json"
    )
    return library_model.LibraryModel(
        download_art=False, settings_path=tmp_path / "settings.json"
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

    model.setSort("most")
    titles = [model.data(model.index(i, 0), library_model.ROLE_TITLE) for i in range(3)]
    assert titles == ["Beta Racer", "Gamma Flight", "Alpha Quest"]


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


def test_launch_starts_a_session(model, monkeypatch) -> None:
    monkeypatch.setattr(library_model, "launch_game", lambda game: 4321)

    session_id = model.launch(0)

    assert session_id == "s1"
    assert model.sessions.count == 1
    assert model.sessions.list[0]["id"] == session_id
    assert model.sessions.list[0]["title"] == "Gamma Flight"


def test_session_card_exposes_cartridge_data(model) -> None:
    card = model.sessionCard("steam:1")
    assert card["title"] == "Alpha Quest"
    assert card["source"] == "Steam"
    assert card["meta"] == "STEAM · 123 · ALPH"
    assert card["cover"].startswith("image://cover/")
    assert card["cartridgeColor"] == model.cartridgeColor
    assert model.sessionCard("missing:1") == {}


def test_big_picture_games_and_launch_by_id(model, monkeypatch) -> None:
    games = model.bigPictureGames
    assert [game["title"] for game in games] == [
        "Alpha Quest",
        "Beta Racer",
        "Gamma Flight",
    ]
    assert games[0]["favorite"] is False
    assert games[0]["cover"].startswith("image://cover/")

    monkeypatch.setattr(library_model, "launch_game", lambda game: 4321)
    session_id = model.launchById("epic:3")
    assert session_id == "s1"
    assert model.sessions.list[0]["title"] == "Gamma Flight"

    assert model.toggleFavoriteById("steam:1") is True
    assert model.bigPictureGames[0]["favorite"] is True
    assert model.toggleFavoriteById("steam:1") is False
    assert model.launchById("missing:1") == ""


def test_big_picture_detail_by_id(model, monkeypatch) -> None:
    cached = {
        "description": "A tiny space adventure.",
        "developers": "Studio One",
        "genres": "Adventure",
        "releaseDate": "2024",
    }
    monkeypatch.setattr(
        library_model.metadata, "cached", lambda game, language: cached
    )

    detail = model.gameDetailById("steam:1")
    assert detail["id"] == "steam:1"
    assert detail["title"] == "Alpha Quest"
    assert detail["detailsLoaded"] is False

    model.loadDetailsById("steam:1")
    detail = model.gameDetailById("steam:1")
    assert detail["description"] == "A tiny space adventure."
    assert detail["detailsLoaded"] is True
    assert detail["history"] == []


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


def test_appearance_properties(model) -> None:
    model.setAccent("#ff6b6b")
    assert model.accent == "#ff6b6b"
    assert len(model.palette) >= 12
    assert all(colour.startswith("#") for colour in model.palette)

    model.setCartridgeStyle("ds")
    assert model.cartridgeStyle == "ds"

    model.setCartridgeStyle("nope")
    assert model.cartridgeStyle == "ds"

    model.setSurfaceColor("#1f2a33")
    assert model.surfaceColor == "#1f2a33"
    model.setCartridgeColor("#5b616b")
    assert model.cartridgeColor == "#5b616b"
    assert len(model.surfacePalette) >= 8
    assert len(model.cartridgePalette) >= 8


def test_source_options_have_labels(model) -> None:
    options = model.sourceOptions
    assert {option["value"] for option in options} == {
        "steam",
        "epic",
        "gog",
        "battlenet",
        "riot",
    }
    assert {option["text"] for option in options} == {
        "Steam",
        "Epic Games",
        "GOG",
        "Battle.net",
        "Riot",
    }


def test_language_switches_and_persists(model) -> None:
    assert model.translator.language == "en"

    model.translator.setLanguage("es")

    assert model.translator.language == "es"
    assert model.translator.strings["Settings"] == "Ajustes"
    assert model.translator.strings["Most played"] == "Más jugados"
    assert model._prefs.language == "es"

    model.translator.setLanguage("en")
    assert model.translator.language == "en"


def test_every_language_has_the_full_catalog() -> None:
    from gamecenter.core import i18n

    keys = set(i18n.catalog("en"))
    assert keys
    for code, _name in i18n.LANGUAGES:
        assert set(i18n.catalog(code)) == keys
    assert i18n.catalog("es")["1 game"] == "1 juego"


def test_game_at_returns_detail_data(model) -> None:
    model.setQuery("alpha")
    model.setCartridgeStyle("classic")
    assert model.gameAt(0)["texture"] == ""
    model.setCartridgeStyle("ds")
    detail = model.gameAt(0)
    assert detail["title"] == "Alpha Quest"
    assert detail["source"] == "Steam"
    assert detail["appId"] == "123"
    assert detail["cover"].startswith("image://cover/")
    assert detail["cartridgeColor"] == model.cartridgeColor
    assert detail["texture"].startswith("file:///")
    assert detail["hasFolder"] is False
    assert detail["lastPlayed"].startswith("Played")
    assert detail["description"] == ""
    assert detail["detailsLoaded"] is False
    assert detail["history"] == []


def test_game_detail_loads_cached_description(model, monkeypatch) -> None:
    description = {
        "description": "A tiny space adventure.",
        "developers": "Studio One",
        "genres": "Adventure",
        "releaseDate": "2024",
    }
    monkeypatch.setattr(
        library_model.metadata,
        "cached",
        lambda game, language: description,
    )

    model.loadDetails(0)
    detail = model.gameAt(0)

    assert detail["description"] == description["description"]
    assert detail["developers"] == description["developers"]
    assert detail["genres"] == description["genres"]
    assert detail["releaseDate"] == description["releaseDate"]
    assert detail["detailsLoaded"] is True


def test_session_ended_records_a_timeline_entry_for_steam(model) -> None:
    game = model._all[0]
    session = model._sessions.start(game, None, "")
    session.started_at = 1_700_000_000

    model._session_ended(session, 90)

    row = next(
        index for index, item in enumerate(model._visible) if item.id == game.id
    )
    detail = model.gameAt(row)
    assert detail["sessionCount"] == 1
    assert detail["history"][0]["timestamp"] == 1_700_000_000
    assert detail["history"][0]["seconds"] == 90
    assert detail["historyTotalText"] == "2 min"
    assert library_model.playtime.seconds_for(game) == 0


def test_remove_store_game_and_restore(model) -> None:
    model.setQuery("alpha")

    model.removeGame(0)
    assert model.rowCount() == 0
    assert model.hiddenCount == 1

    model.refresh()
    assert model.rowCount() == 0

    model.restoreHiddenGames()
    assert model.rowCount() == 1
    assert model.hiddenCount == 0


def test_scan_store_replaces_only_that_source(model, monkeypatch) -> None:
    replacement = Game(id="steam:9", title="New Steam", source="steam")
    monkeypatch.setattr(
        library_model,
        "scan_source",
        lambda source: [replacement] if source == "steam" else [],
    )

    model.scanStore("steam")

    ids = {game.id for game in model._visible}
    assert "steam:9" in ids
    assert "steam:1" not in ids
    assert "epic:3" in ids


def test_art_pagination_reveals_batches(model) -> None:
    game = model._at(0)
    assert game is not None
    model._art_game = game
    options = [
        {"id": index, "url": f"u{index}", "thumb": f"t{index}"}
        for index in range(7)
    ]

    model._on_art_options(options, 0, game.id, False)
    assert len(model.artOptions) == 5
    assert model.artTotal == 7
    assert model.artHasMore is True

    model.loadMoreArtOptions()
    assert len(model.artOptions) == 7
    assert model.artHasMore is False


def test_per_game_cartridge_color(model) -> None:
    assert model.cartridgeColorAt(0) == model.cartridgeColor

    model.setGameCartridgeColor(0, "#ff6b6b")
    assert model.cartridgeColorAt(0) == "#ff6b6b"
    assert model.gameAt(0)["cartridgeColor"] == "#ff6b6b"
    assert (
        model.data(model.index(0, 0), library_model.ROLE_CARTRIDGE_COLOR)
        == "#ff6b6b"
    )

    model.setCartridgeColor("#123456")
    assert model.cartridgeColorAt(1) == "#123456"
    assert model.cartridgeColorAt(0) == "#ff6b6b"

    model.resetGameCartridgeColor(0)
    assert model.cartridgeColorAt(0) == "#123456"


def test_art_provider_loads_a_chosen_file(app, tmp_path) -> None:
    from PySide6.QtGui import QColor, QImage

    path = tmp_path / "chosen.png"
    image = QImage(120, 180, QImage.Format_RGB32)
    image.fill(QColor("#00ff00"))
    assert image.save(str(path))

    key = covers.art_key(str(path))
    loaded = covers.ArtProvider().request(key)

    assert (loaded.width(), loaded.height()) == (120, 180)


def test_steamgrid_key_is_saved(model, monkeypatch) -> None:
    saved = {}

    def fake_set(key):
        saved["key"] = key
        return True

    monkeypatch.setattr(library_model.credentials, "set_key", fake_set)

    model.saveSteamGridKey("  abc123  ")

    assert saved["key"] == "abc123"
    assert model.hasSteamGridKey is True
    assert "Saved" in model.credentialsMessage


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


def test_qml_reacts_to_language_change(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    heading = root.findChild(QObject, "headingLabel")
    assert heading is not None
    assert heading.property("text") == "ALL GAMES"

    model.translator.setLanguage("es")
    app.processEvents()

    assert heading.property("text") == "TODOS LOS JUEGOS"
    combo = root.findChild(QObject, "languageCombo")
    assert combo is not None
    assert combo.property("value") == "es"

    model.translator.setLanguage("en")
    app.processEvents()
    assert heading.property("text") == "ALL GAMES"


def test_qml_slot_shows_last_running_session(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    slot = root.findChild(QObject, "slotCartridge")
    assert slot is not None
    assert slot.property("active") is False

    first = model._sessions.start(model._all[0], None, "")
    app.processEvents()
    assert slot.property("active") is True
    assert slot.property("game")["title"] == "Alpha Quest"

    second = model._sessions.start(model._all[1], None, "")
    app.processEvents()
    assert slot.property("game")["title"] == "Beta Racer"

    model._sessions.eject(second.id)
    app.processEvents()
    assert slot.property("game")["title"] == "Alpha Quest"

    model._sessions.eject(first.id)
    app.processEvents()
    assert slot.property("active") is False


def test_qml_slot_waits_for_the_insertion_animation(app, model) -> None:
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    slot = root.findChild(QObject, "slotCartridge")
    effect = root.findChild(QObject, "insertEffect")
    assert slot is not None and effect is not None

    first = model._sessions.start(model._all[0], None, "")
    app.processEvents()
    assert slot.property("game")["title"] == "Alpha Quest"

    effect.setProperty("running", True)
    second = model._sessions.start(model._all[1], None, "")
    app.processEvents()
    # The previous cartridge stays in the slot while the next one flies in.
    assert slot.property("game")["title"] == "Alpha Quest"

    QMetaObject.invokeMethod(root, "commitSlot", Q_ARG("QVariant", second.id))
    app.processEvents()
    assert slot.property("game")["title"] == "Beta Racer"

    effect.setProperty("running", False)
    model._sessions.eject(second.id)
    app.processEvents()
    assert slot.property("game")["title"] == "Alpha Quest"
    model._sessions.eject(first.id)


def test_qml_detail_updates_when_the_description_arrives(app, model, monkeypatch) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    cached = {
        "description": "A tiny space adventure.",
        "developers": "Studio One",
        "genres": "Adventure",
        "releaseDate": "2024",
    }
    monkeypatch.setattr(
        library_model.metadata, "cached", lambda game, language: cached
    )

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    assert root.findChild(QObject, "favoriteButton") is not None

    root.setProperty("detailIndex", 0)
    root.setProperty("detailGame", model.gameAt(0))
    root.setProperty("detailOpen", True)
    model.loadDetails(0)
    app.processEvents()

    detail = root.property("detailGame")
    if hasattr(detail, "toVariant"):
        detail = detail.toVariant()
    assert detail["description"] == "A tiny space adventure."
    assert detail["detailsLoaded"] is True


def test_qml_stats_view_loads_the_year_summary(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    game = model._all[0]
    library_model.playtime.record_session(game, int(time.time()), 600)

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.setProperty("currentView", "stats")
    app.processEvents()

    stats = root.findChild(QObject, "statsView")
    assert stats is not None
    assert stats.property("visible") is True

    data = stats.property("statsData")
    if hasattr(data, "toVariant"):
        data = data.toVariant()
    assert data["year"] == date.today().year
    assert data["sessionsCount"] == 1
    assert data["months"]
    assert data["river"]["layers"]


def test_qml_big_picture_navigation_and_exit_confirmation(app, model) -> None:
    from PySide6.QtCore import Q_ARG, QMetaObject, QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.setProperty("bigPictureOpen", True)
    app.processEvents()

    picture = root.findChild(QObject, "bigPicture")
    assert picture is not None
    assert picture.property("opened") is True

    games = picture.property("games")
    if hasattr(games, "toVariant"):
        games = games.toVariant()
    assert len(games) == 3

    QMetaObject.invokeMethod(picture, "moveSelection", Q_ARG("QVariant", 1))
    app.processEvents()
    assert picture.property("selectedIndex") == 1

    QMetaObject.invokeMethod(picture, "requestExit")
    app.processEvents()
    assert picture.property("exitConfirmOpen") is True

    QMetaObject.invokeMethod(picture, "activateExitFocus")
    app.processEvents()
    assert picture.property("exitConfirmOpen") is False


def test_qml_big_picture_opens_the_game_detail(app, model, monkeypatch) -> None:
    from PySide6.QtCore import QMetaObject, QObject

    from gamecenter.ui.app import create_engine

    cached = {
        "description": "A tiny space adventure.",
        "developers": "Studio One",
        "genres": "Adventure",
        "releaseDate": "2024",
    }
    monkeypatch.setattr(
        library_model.metadata, "cached", lambda game, language: cached
    )

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.setProperty("bigPictureOpen", True)
    app.processEvents()

    picture = root.findChild(QObject, "bigPicture")
    assert picture is not None
    QMetaObject.invokeMethod(picture, "openDetail")
    app.processEvents()

    assert picture.property("detailOpen") is True
    detail = picture.property("detailGame")
    if hasattr(detail, "toVariant"):
        detail = detail.toVariant()
    assert detail["id"] == "steam:1"
    assert detail["description"] == "A tiny space adventure."
