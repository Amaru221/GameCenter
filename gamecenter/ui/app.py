"""Boot the Qt Quick interface."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, QTimer, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from .. import __version__
from ..core.gamepad import GamepadManager
from ..core.screenshots import ScreenshotManager
from ..core.sounds import SoundManager
from ..core.startup_movies import StartupMovieManager
from . import covers
from .library_model import LibraryModel

QML_DIR = Path(__file__).resolve().parent / "qml"
FONT_DIR = Path(__file__).resolve().parent / "fonts"


class CoverImageProvider(QQuickImageProvider):
    """Serves ``image://cover/<title>`` from the procedural cover renderer."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._covers = covers.CoverProvider()

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:
        image = self._covers.request(image_id)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


class ArtImageProvider(QQuickImageProvider):
    """Serves ``image://art/<key>`` for covers chosen from SteamGridDB."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._art = covers.ArtProvider()

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:
        image = self._art.request(image_id)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


class BackgroundImageProvider(QQuickImageProvider):
    """Serves the blurred mesh background, rendered once."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._image: QImage | None = None

    def requestImage(self, image_id: str, size: QSize, requested_size: QSize) -> QImage:
        if self._image is None:
            self._image = covers.render_background()
        if size is not None:
            size.setWidth(self._image.width())
            size.setHeight(self._image.height())
        return self._image


def _load_fonts() -> None:
    for path in sorted(FONT_DIR.glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(path))


def create_engine(library: LibraryModel) -> QQmlApplicationEngine:
    # The native styles refuse custom backgrounds and delegates; Basic does not.
    QQuickStyle.setStyle("Basic")

    engine = QQmlApplicationEngine()
    engine.addImageProvider("cover", CoverImageProvider())
    engine.addImageProvider("art", ArtImageProvider())
    engine.addImageProvider("bg", BackgroundImageProvider())
    engine.rootContext().setContextProperty("Library", library)
    engine.rootContext().setContextProperty("Sessions", library.sessions)
    engine.rootContext().setContextProperty("Tr", library.translator)
    gamepad = GamepadManager(library._prefs)
    gamepad.setParent(engine)
    engine.rootContext().setContextProperty("Gamepad", gamepad)

    screenshots = ScreenshotManager(library._prefs, library.sessions)
    screenshots.setParent(engine)
    engine.rootContext().setContextProperty("Screenshots", screenshots)
    gamepad.screenshot.connect(screenshots.captureIfPlaying)

    sounds = SoundManager(library._prefs)
    sounds.setParent(engine)
    engine.rootContext().setContextProperty("Sounds", sounds)

    movies = StartupMovieManager(library._prefs)
    movies.setParent(engine)
    engine.rootContext().setContextProperty("StartupMovies", movies)

    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    # Generate/load the cues just after the first frame so opening the window
    # is never blocked by audio synthesis on the very first run. The timer is
    # parented to the engine, so tearing the engine down cancels it safely.
    preload_timer = QTimer(engine)
    preload_timer.setSingleShot(True)
    preload_timer.timeout.connect(sounds.preload)
    preload_timer.start(600)
    if engine.rootObjects() and not os.environ.get("GC_NO_OVERLAY"):
        overlay = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(QML_DIR / "ScreenshotOverlay.qml")),
        )
        overlay_window = overlay.create()
        if overlay_window is not None:
            engine._screenshot_component = overlay
            engine._screenshot_overlay = overlay_window
    return engine


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("GameCenter")
    app.setApplicationDisplayName("GameCenter")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("GameCenter")
    if sys.platform != "win32":
        app.setDesktopFileName("io.github.gamecenter.GameCenter")

    _load_fonts()
    app.setWindowIcon(covers.app_icon())

    library = LibraryModel()
    engine = create_engine(library)
    if not engine.rootObjects():
        return 1
    return app.exec()
