"""Save the window to a PNG for design review. Development helper, not shipped."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, Qt, QTimer  # noqa: E402
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
    elif os.environ.get("GC_FLIP"):
        name = "screenshot-ds-back.png"
    elif os.environ.get("GC_STYLE"):
        name = f"screenshot-{os.environ['GC_STYLE']}.png"
    elif os.environ.get("GC_SETTINGS"):
        name = "screenshot-settings.png"
    elif os.environ.get("GC_ART"):
        name = (
            "screenshot-art-error.png"
            if os.environ["GC_ART"] == "error"
            else "screenshot-art.png"
        )
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

    if os.environ.get("GC_ART") and library._visible:
        from gamecenter.core import steamgriddb
        from gamecenter.ui import covers

        if os.environ["GC_ART"] != "error":
            def fake_grids(game, key, limit=5):
                return [
                    {
                        "id": i,
                        "url": "image://cover/"
                        + covers.cover_key(f"{game.title} art {i}", game.app_id, i),
                        "thumb": "image://cover/"
                        + covers.cover_key(f"{game.title} art {i}", game.app_id, i),
                    }
                    for i in range(5)
                ]

            steamgriddb.grids_for = fake_grids
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

    if os.environ.get("GC_FLIP"):
        def flip_first_card():
            def find(item, name):
                if item.objectName() == name:
                    return item
                for child in item.childItems():
                    hit = find(child, name)
                    if hit is not None:
                        return hit
                return None

            target = find(window.contentItem(), "dsFlip")
            if target is not None:
                target.setProperty("flipped", True)

        QTimer.singleShot(1400, flip_first_card)

    def grab() -> None:
        image = window.grabWindow()
        image.save(str(out))
        print(f"saved {out} ({image.width()}x{image.height()})")
        app.quit()

    QTimer.singleShot(int(os.environ.get("GC_WAIT", "4000")), grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
