"""Save the window to a PNG for design review. Development helper, not shipped."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, Qt, QTimer  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from gamecenter.ui.app import _load_fonts, create_engine  # noqa: E402
from gamecenter.ui.library_model import LibraryModel  # noqa: E402


def _demo_games():
    """A fictional library, so the public preview doesn't show a real one."""
    from gamecenter.core.models import Game

    specs = (
        ("Neon Drifter", "steam", "900001", 12.4, 3420, 1792000000, True),
        ("Echoes of Aether", "steam", "900002", 8.1, 890, 1791000000, True),
        ("Cobalt Frontier", "epic", "CobaltFrontier", 22.7, 0, 0, True),
        ("Paper Kingdom", "gog", "900003", 5.2, 1450, 1790000000, True),
        ("Night Shift", "battlenet", "Pro", 0.0, 0, 0, True),
        ("Pixel Rally", "riot", "pixel_rally.live", 3.9, 320, 1789000000, True),
        ("Hollow Circuit", "steam", "900004", 15.0, 0, 0, False),
        ("My Indie Game", "local", "my-indie", 1.2, 90, 1791500000, True),
    )
    return [
        Game(
            id=f"{source}:{app_id}",
            title=title,
            source=source,
            app_id=app_id,
            size_bytes=int(size_gb * 1024 ** 3),
            playtime_minutes=minutes,
            last_played=last_played,
            installed=installed,
        )
        for title, source, app_id, size_gb, minutes, last_played, installed in specs
    ]


def main() -> int:
    app = QApplication(sys.argv)
    _load_fonts()

    demo = bool(os.environ.get("GC_DEMO"))
    if demo:
        from gamecenter.ui import library_model

        library_model.scan_all = _demo_games

    library = LibraryModel(
        download_art=not demo,
        settings_path=Path(os.environ.get("TEMP", ".")) / "gamecenter-preview.json",
    )

    if os.environ.get("GC_STYLE"):
        library.setCartridgeStyle(os.environ["GC_STYLE"])

    if os.environ.get("GC_ACCENT"):
        library.setAccent(os.environ["GC_ACCENT"])

    if os.environ.get("GC_SOURCE"):
        library.setSourceFilter(os.environ["GC_SOURCE"])

    if os.environ.get("GC_SURFACE"):
        library.setSurfaceColor(os.environ["GC_SURFACE"])

    if os.environ.get("GC_CARTRIDGE"):
        library.setCartridgeColor(os.environ["GC_CARTRIDGE"])

    if os.environ.get("GC_UPDATE") or os.environ.get("GC_UPDATE_DIALOG"):
        from gamecenter.core.updater import UpdateInfo

        library._update_available = UpdateInfo(
            version="0.6.1",
            tag="v0.6.1",
            url="https://github.com/Amaru221/GameCenter/releases/tag/v0.6.1",
            name="GameCenter 0.6.1",
            notes="",
            published_at="",
        )
        library._update_dismissed = False
        library.updatesChanged.emit()

    if os.environ.get("GC_INSERT") and library._visible:
        from gamecenter.core.sessions import SessionTracker
        from gamecenter.ui import covers

        tracker = SessionTracker(running=lambda session: True)
        library._sessions = tracker
        game = library._visible[0]
        tracker.start(
            game, None, "image://cover/" + covers.cover_key(game.title, game.app_id)
        )

    if os.environ.get("GC_SESSION") and library._visible:
        # A fake running session, so the dock can be reviewed without launching.
        from gamecenter.core.sessions import SessionTracker
        from gamecenter.ui import covers

        tracker = SessionTracker(running=lambda session: True)
        library._sessions = tracker
        game = library._visible[0]
        session = tracker.start(
            game, None, "image://cover/" + covers.cover_key(game.title, game.app_id)
        )
        session.started_at -= 754
        tracker.changed.emit()

    engine = create_engine(library)
    roots = engine.rootObjects()
    if not roots:
        return 1

    window = roots[0]
    window.resize(1180, 800)
    window.show()

    name = "screenshot.png"
    if os.environ.get("GC_HOVER"):
        name = "screenshot-hover.png"
    elif os.environ.get("GC_DETAIL"):
        name = "screenshot-detail.png"
    elif os.environ.get("GC_SESSION"):
        name = "screenshot-session.png"
    elif os.environ.get("GC_UPDATE_DIALOG"):
        name = "screenshot-update-dialog.png"
    elif os.environ.get("GC_ADD"):
        name = "screenshot-add.png"
    elif os.environ.get("GC_SCAN"):
        name = "screenshot-scan.png"
    elif os.environ.get("GC_RESTORE"):
        name = "screenshot-restore.png"
    elif os.environ.get("GC_REMOVE"):
        name = "screenshot-remove.png"
    elif os.environ.get("GC_CONTEXT"):
        name = "screenshot-context.png"
    elif os.environ.get("GC_MENU"):
        name = "screenshot-menu.png"
    elif os.environ.get("GC_COLOR_SET"):
        name = "screenshot-color-set.png"
    elif os.environ.get("GC_COLOR"):
        name = "screenshot-color.png"
    elif os.environ.get("GC_DS3D_BACK"):
        name = "screenshot-ds3d-back.png"
    elif os.environ.get("GC_DS3D_DRAG"):
        name = "screenshot-ds3d-drag.png"
    elif os.environ.get("GC_DS3D"):
        name = "screenshot-ds3d.png"
    elif os.environ.get("GC_SOURCE"):
        name = "screenshot-filter.png"
    elif os.environ.get("GC_SURFACE") or os.environ.get("GC_CARTRIDGE"):
        name = "screenshot-colors.png"
    elif os.environ.get("GC_INSERT"):
        name = "screenshot-insert.png"
    elif os.environ.get("GC_STYLE"):
        name = f"screenshot-{os.environ['GC_STYLE']}.png"
    elif os.environ.get("GC_SETTINGS") and os.environ.get("GC_UPDATE"):
        name = "screenshot-settings-update.png"
    elif os.environ.get("GC_SETTINGS"):
        name = "screenshot-settings.png"
    elif os.environ.get("GC_UPDATE"):
        name = "screenshot-update.png"
    elif os.environ.get("GC_ART"):
        if os.environ["GC_ART"] == "error":
            name = "screenshot-art-error.png"
        elif os.environ["GC_ART"] == "more":
            name = "screenshot-art-more.png"
        else:
            name = "screenshot-art.png"
    elif os.environ.get("GC_ACCENT"):
        name = "screenshot-accent.png"
    out = Path(__file__).resolve().parents[1] / name

    if os.environ.get("GC_HOVER"):
        # Park the cursor over the first cartridge so the tilt shows up.
        QTimer.singleShot(1400, lambda: QTest.mouseMove(window, QPoint(140, 220)))
    if os.environ.get("GC_DETAIL"):
        QTimer.singleShot(
            1400,
            lambda: QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, QPoint(140, 220)
            ),
        )
    if os.environ.get("GC_SETTINGS"):
        QTimer.singleShot(1200, lambda: window.setProperty("settingsOpen", True))

    if os.environ.get("GC_UPDATE_DIALOG"):
        QTimer.singleShot(1200, lambda: window.setProperty("updateOpen", True))

    if os.environ.get("GC_ADD"):
        QTimer.singleShot(1200, lambda: window.setProperty("addOpen", True))

    if os.environ.get("GC_SCAN"):
        QTimer.singleShot(1800, lambda: library.scanStore(""))

    if os.environ.get("GC_RESTORE"):
        QTimer.singleShot(1400, library.restoreHiddenGames)

    if os.environ.get("GC_REMOVE"):
        QTimer.singleShot(1400, lambda: library.removeGame(0))

    if os.environ.get("GC_CONTEXT"):
        QTimer.singleShot(
            1400,
            lambda: QTest.mouseClick(
                window, Qt.RightButton, Qt.NoModifier, QPoint(140, 220)
            ),
        )

    if os.environ.get("GC_MENU"):
        def open_menu():
            def find(item, name):
                if item.objectName() == name:
                    return item
                for child in item.childItems():
                    hit = find(child, name)
                    if hit is not None:
                        return hit
                return None

            target = find(window.contentItem(), "topBar")
            if target is not None:
                QMetaObject.invokeMethod(target, "openMenu")

        QTimer.singleShot(1400, open_menu)

    if os.environ.get("GC_COLOR_SET"):
        QTimer.singleShot(
            1400, lambda: library.setGameCartridgeColor(0, "#ff6b6b")
        )

    if os.environ.get("GC_COLOR"):
        def open_color():
            def find(item, name):
                if item.objectName() == name:
                    return item
                for child in item.childItems():
                    hit = find(child, name)
                    if hit is not None:
                        return hit
                return None

            target = find(window.contentItem(), "libraryGrid")
            if target is not None:
                QMetaObject.invokeMethod(
                    target, "openColorPicker", Q_ARG("QVariant", 0)
                )

        QTimer.singleShot(1400, open_color)

    if (
        os.environ.get("GC_DS3D")
        or os.environ.get("GC_DS3D_BACK")
        or os.environ.get("GC_DS3D_DRAG")
    ):
        def open_ds3d():
            window.setProperty("detailIndex", 0)
            window.setProperty("detailGame", library.gameAt(0))
            window.setProperty("detailOpen", True)
            if os.environ.get("GC_DS3D_DRAG"):
                def drag_3d():
                    QTest.mousePress(
                        window, Qt.LeftButton, Qt.NoModifier, QPoint(280, 360)
                    )
                    for i in range(1, 9):
                        QTest.mouseMove(
                            window, QPoint(280 + i * 14, 360 - i * 3)
                        )
                        QTest.qWait(40)
                    QTest.mouseRelease(
                        window, Qt.LeftButton, Qt.NoModifier, QPoint(392, 336)
                    )

                QTimer.singleShot(3200, drag_3d)
            if os.environ.get("GC_DS3D_BACK"):
                def show_back():
                    def find(item, name):
                        if item.objectName() == name:
                            return item
                        for child in item.childItems():
                            hit = find(child, name)
                            if hit is not None:
                                return hit
                        return None

                    target = find(window.contentItem(), "ds3d")
                    if target is not None:
                        target.setProperty("yaw", 180)
                        target.setProperty("pitch", -8)

                QTimer.singleShot(3000, show_back)

        QTimer.singleShot(1200, open_ds3d)

    if os.environ.get("GC_ART") and library._visible:
        from gamecenter.core import steamgriddb
        from gamecenter.ui import covers

        if os.environ["GC_ART"] != "error":
            def fake_grids(game, key, page=0):
                if page > 0:
                    return [], False
                return [
                    {
                        "id": i,
                        "url": "image://cover/"
                        + covers.cover_key(f"{game.title} art {i}", game.app_id, i),
                        "thumb": "image://cover/"
                        + covers.cover_key(f"{game.title} art {i}", game.app_id, i),
                    }
                    for i in range(10)
                ], True

            steamgriddb.grids_page = fake_grids
            library._has_key = True
        else:
            library._has_key = False

        def open_art():
            window.setProperty("detailIndex", 0)
            window.setProperty("detailGame", library.gameAt(0))
            window.setProperty("detailOpen", True)
            window.setProperty("artOpen", True)
            library.loadArtOptions(0)

        QTimer.singleShot(1200, open_art)
        if os.environ["GC_ART"] == "more":
            QTimer.singleShot(2600, library.loadMoreArtOptions)

    if os.environ.get("GC_INSERT"):
        def start_insert():
            window.setProperty("detailIndex", 0)
            window.setProperty("detailGame", library.gameAt(0))
            window.setProperty("detailOpen", True)
            QTimer.singleShot(400, lambda: window.setProperty("demoInsert", True))

        QTimer.singleShot(900, start_insert)

    def grab() -> None:
        image = window.grabWindow()
        image.save(str(out))
        print(f"saved {out} ({image.width()}x{image.height()})")
        app.quit()

    if os.environ.get("GC_DS3D_DRAG"):
        default_wait = "6500"
    elif os.environ.get("GC_DS3D_BACK"):
        default_wait = "6500"
    else:
        default_wait = "4000"
    QTimer.singleShot(int(os.environ.get("GC_WAIT", default_wait)), grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
