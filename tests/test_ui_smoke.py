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
os.environ.setdefault("GC_NO_HOTKEYS", "1")

from gamecenter.core.models import Game  # noqa: E402
from gamecenter.ui import covers, library_model  # noqa: E402


@pytest.fixture(scope="session")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def release_qml_engines():
    # Each QML test creates an engine; collect it before the next one so a
    # delayed destruction cannot happen inside another engine's event loop.
    yield
    import gc

    gc.collect()


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
    from gamecenter.core import sources

    monkeypatch.setattr(
        library_model, "scan_all", lambda: sources._with_playtime(games)
    )
    monkeypatch.setattr(library_model.credentials, "get_key", lambda: "")
    monkeypatch.setattr(
        library_model.playtime, "_fallback_path", lambda: tmp_path / "playtime.json"
    )
    monkeypatch.setattr(
        library_model.playtime, "history_path", lambda: tmp_path / "history.json"
    )
    monkeypatch.setattr(
        library_model.profiles, "path", lambda: tmp_path / "profiles.json"
    )
    monkeypatch.setattr(
        library_model.profiles, "cover_dir", lambda: tmp_path / "recap_covers"
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


def test_qml_insertion_layers_put_the_cartridge_behind_the_dock(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    plate = root.findChild(QObject, "insertPlate")
    slot = root.findChild(QObject, "slotCartridge")
    effect = root.findChild(QObject, "insertEffect")
    dock = root.findChild(QObject, "dock")

    assert plate is not None
    assert slot is not None
    assert effect is not None
    assert dock is not None
    # Dark plate < inserted cartridge < flying cartridge < dock front face.
    assert plate.property("z") < slot.property("z")
    assert slot.property("z") < effect.property("z")
    assert effect.property("z") < dock.property("z")


def test_qml_screenshot_shortcut_setting(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    combo = root.findChild(QObject, "screenshotShortcutCombo")
    assert combo is not None
    assert combo.property("value") == "ctrl+pagedown"

    screenshots = engine.rootContext().contextProperty("Screenshots")
    assert screenshots is not None
    screenshots.setShortcut("f12")
    app.processEvents()

    assert screenshots.property("shortcut") == "f12"
    assert combo.property("value") == "f12"


def test_qml_stats_cards_show_cover_and_highlights(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    game = model._all[0]
    library_model.playtime.record_session(game, int(time.time()), 600)

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.resize(1180, 800)
    root.show()
    root.setProperty("currentView", "stats")
    app.processEvents()

    carousel = root.findChild(QObject, "monthCarousel")
    assert carousel is not None
    app.processEvents()

    # Delegate items live in the visual tree (contentItem), not in the QObject
    # child list of the ListView.
    def walk(item):
        yield item
        for child in item.childItems():
            yield from walk(child)

    content = carousel.property("contentItem")
    items = list(walk(content))
    badges = [
        item for item in items
        if item.objectName() == "highlightBadge"
        and item.property("visible") is True
    ]
    covers = [
        item for item in items
        if item.objectName() == "monthPlayedCover"
        and item.property("visible") is True
    ]
    assert badges
    assert covers


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
    root.resize(1180, 800)
    root.show()
    app.processEvents()

    # The library dock (Ready/clock/cartridge slot) is only for the library.
    dock = root.findChild(QObject, "dock")
    layer = root.findChild(QObject, "libraryDock")
    assert dock is not None and layer is not None
    assert layer.property("visible") is True

    root.setProperty("currentView", "stats")
    app.processEvents()

    assert layer.property("visible") is False

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

    # The carousel lists the current month first and January last.
    months = stats.property("months")
    if hasattr(months, "toVariant"):
        months = months.toVariant()
    order = [month["monthIndex"] for month in months]
    assert order == sorted(order, reverse=True)
    assert order[0] == len(order) - 1


def test_qml_detail_is_fullscreen_with_a_pinned_rotatable_cartridge(app, model) -> None:
    from PySide6.QtCore import QObject, QPoint, Qt
    from PySide6.QtTest import QTest

    from gamecenter.ui.app import create_engine

    model.setCartridgeStyle("ds")
    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.resize(1180, 800)
    root.show()
    app.processEvents()
    root.setProperty("detailIndex", 0)
    root.setProperty("detailGame", model.gameAt(0))
    root.setProperty("detailOpen", True)
    app.processEvents()
    QTest.qWait(260)

    detail = root.findChild(QObject, "gameDetail")
    assert detail is not None
    assert detail.property("backdropItem") is not None
    # The modal fills the window instead of the old centered panel.
    assert detail.property("width") == root.property("width")
    assert detail.property("height") == root.property("height")

    card = root.findChild(QObject, "detailCartridge")
    assert card is not None
    assert card.property("visible") is True
    # Pinned to the top-left corner and wide enough for the rotated model.
    assert card.property("x") == 24
    assert card.property("y") == 72
    assert card.property("width") >= 300
    assert card.property("height") >= 360
    # The cartridge is not inside the clipped scroller, so the 3D model is never
    # cut by a frame.
    scroller = detail.findChild(QObject, "detailScroller")
    assert scroller is not None
    ancestor = card.parent()
    while ancestor is not None:
        assert ancestor is not scroller
        ancestor = ancestor.parent()

    # Dragging rotates the model but never moves it.
    ds = root.findChild(QObject, "ds3d")
    assert ds is not None
    yaw = ds.property("yaw")
    start = QPoint(
        int(card.property("x") + card.property("width") / 2),
        int(card.property("y") + card.property("height") / 2),
    )
    QTest.mousePress(root, Qt.LeftButton, Qt.NoModifier, start)
    for i in range(1, 6):
        QTest.mouseMove(root, QPoint(start.x() + i * 8, start.y() - i * 4))
        QTest.qWait(20)
    QTest.mouseRelease(
        root, Qt.LeftButton, Qt.NoModifier, QPoint(start.x() + 40, start.y() - 20)
    )
    app.processEvents()
    assert ds.property("yaw") != yaw
    assert card.property("x") == 24
    assert card.property("y") == 72


def test_qml_search_hides_in_stats_and_clears_focus_outside(app, model) -> None:
    from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
    from PySide6.QtTest import QTest

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.show()
    app.processEvents()

    top = root.findChild(QObject, "topBar")
    box = root.findChild(QObject, "searchBox")
    assert top is not None and box is not None
    assert box.property("visible") is True

    QMetaObject.invokeMethod(top, "focusSearch")
    app.processEvents()
    assert top.property("searchFocused") is True

    QTest.mouseClick(root, Qt.LeftButton, Qt.NoModifier, QPoint(640, 400))
    app.processEvents()
    assert top.property("searchFocused") is False

    root.setProperty("currentView", "stats")
    app.processEvents()
    assert box.property("visible") is False
    assert top.property("searchFocused") is False


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

    QMetaObject.invokeMethod(picture, "cycleMode", Q_ARG("QVariant", 1))
    app.processEvents()
    assert picture.property("carouselMode") == "flat"
    carousel = root.findChild(QObject, "bigPictureCarousel")
    assert carousel is not None
    assert carousel.property("mode") == "flat"

    QMetaObject.invokeMethod(picture, "cycleMode", Q_ARG("QVariant", 1))
    app.processEvents()
    assert picture.property("carouselMode") == "ring"
    assert carousel.property("mode") == "ring"

    QMetaObject.invokeMethod(picture, "cycleMode", Q_ARG("QVariant", 1))
    app.processEvents()
    assert picture.property("carouselMode") == "wheel"
    assert carousel.property("mode") == "wheel"


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


def test_gamepad_cursor_toggle(app) -> None:
    from gamecenter.core.gamepad import GamepadManager

    manager = GamepadManager()
    manager._hide_cursor()
    assert manager._cursor_hidden is True
    manager.showCursor()
    assert manager._cursor_hidden is False


def test_game_profile_rating_and_status(model) -> None:
    assert model.setGameRating("epic:3", 87) is True
    assert model.setGameStatus("epic:3", "playing") is True

    detail = model.gameDetailById("epic:3")
    assert detail["rating"] == 87
    assert detail["hasRating"] is True
    assert detail["status"] == "playing"
    assert detail["mergedSources"] == []

    assert model.setGameRating("epic:3", 140) is True
    assert model.gameDetailById("epic:3")["rating"] == 100
    assert model.setGameStatus("epic:3", "nonsense") is False
    assert model.setGameStatus("epic:3", "") is True
    assert model.gameDetailById("epic:3")["status"] == ""


def test_merge_moves_playtime_sessions_and_cover(model) -> None:
    from gamecenter.core import playtime

    source = next(game for game in model._all if game.id == "steam:2")
    target = next(game for game in model._all if game.id == "epic:3")
    playtime.write_summary(target, 1800, 2, 1_700_000_000)
    playtime.record_session(source, 1_700_000_100, 3000)

    result = model.mergeGameData("steam:2", "epic:3", True)

    assert result["ok"] is True
    detail = model.gameDetailById("epic:3")
    assert detail["mergedSources"][0]["id"] == "steam:2"
    assert detail["mergedSources"][0]["cover"].startswith("image://art/")
    assert "2" in detail["playtimeText"]
    assert detail["sessionCount"] >= 2
    assert model.rowCount() == 2
    assert model.rowForId("epic:3") >= 0
    assert model.rowForId("steam:2") == -1
    assert model._prefs.is_hidden("steam:2")
    assert library_model.profiles.merged_seconds("steam:2") == 7200
    assert library_model.profiles.get("steam:2")["merged_into"] == "epic:3"
    assert library_model.profiles.extra_seconds("epic:3") == 0
    assert model._prefs.cover_for("epic:3")


def test_merge_into_steam_layers_imported_time(model) -> None:
    from gamecenter.core import playtime

    source = next(game for game in model._all if game.id == "epic:3")
    playtime.write_summary(source, 3600, 1, 1_700_000_000)
    playtime.record_session(source, 1_700_000_100, 3600)

    result = model.mergeGameData("epic:3", "steam:1", False)

    assert result["ok"] is True
    assert library_model.profiles.extra_seconds("steam:1") == 3600
    detail = model.gameDetailById("steam:1")
    assert "1" in detail["playtimeText"]
    assert detail["mergedSources"][0]["id"] == "epic:3"
    assert model.rowCount() == 3
    assert playtime.seconds_for(source) == 0


def test_qml_game_profile_panel_loads(app, model) -> None:
    from PySide6.QtCore import QObject

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    root.setProperty("detailIndex", 0)
    root.setProperty("detailGame", model.gameAt(0))
    root.setProperty("detailOpen", True)
    app.processEvents()

    detail = root.findChild(QObject, "gameDetail")
    assert detail is not None
    detail.setProperty("profileOpen", True)
    app.processEvents()

    panel = root.findChild(QObject, "gameProfilePanel")
    assert panel is not None
    assert panel.property("expanded") is True
    assert panel.property("sourceId") == ""
    combo = panel.findChild(QObject, "profileSourceCombo")
    assert combo is not None
    assert combo.property("currentIndex") == -1
    candidates = panel.property("candidateModel")
    if hasattr(candidates, "toVariant"):
        candidates = candidates.toVariant()
    assert len(candidates) == 2


def test_merge_from_a_removed_entry(model) -> None:
    from gamecenter.core import playtime

    removed = Game(id="epic:removed", title="Removed Game", source="epic")
    playtime.write_summary(removed, 1800, 2, 1_700_000_000)
    playtime.record_session(removed, 1_700_000_100, 1800)

    candidates = model.mergeCandidates("epic:3")
    entry = next(item for item in candidates if item["id"] == "epic:removed")
    assert entry["orphan"] is True
    assert entry["seconds"] == 1800
    assert entry["sessions"] == 2

    result = model.mergeGameData("epic:removed", "epic:3", False)

    assert result["ok"] is True
    detail = model.gameDetailById("epic:3")
    assert detail["mergedSources"][0]["id"] == "epic:removed"
    assert playtime.seconds_for(removed) == 0
    assert playtime.history_for(removed) == []
    assert model.rowCount() == 3
    assert all(
        item["id"] != "epic:removed"
        for item in model.mergeCandidates("epic:3")
    )


def test_a_source_can_only_be_merged_once(model) -> None:
    from gamecenter.core import playtime

    source = next(game for game in model._all if game.id == "epic:3")
    playtime.write_summary(source, 1800, 1, 1_700_000_000)

    assert model.mergeGameData("epic:3", "steam:1", False)["ok"] is True
    second = model.mergeGameData("epic:3", "steam:1", False)

    assert second["ok"] is False
    assert "already" in second["message"].casefold()
