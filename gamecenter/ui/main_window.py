"""The main window: a searchable shelf of the games found on this machine."""

from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..core import steam
from ..core.launch import LaunchError, launch, open_folder
from ..core.models import Game
from . import covers, theme


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GameCenter")
        self.setWindowIcon(covers.app_icon())
        self.resize(1080, 720)
        self.setMinimumSize(760, 520)

        self._games: list[Game] = []
        self._build_ui()
        self._build_menu()
        self.reload()

    # -- construction -----------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("Header")
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 14, 20, 14)
        row.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("GameCenter")
        title.setObjectName("Title")
        subtitle = QLabel("Your local game library")
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        row.addLayout(titles)
        row.addStretch(1)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search games...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(260)

        self.source = QComboBox()
        self.source.setFixedWidth(140)
        self.source.addItem("All stores", None)

        self.refresh = QPushButton("Refresh")

        row.addWidget(self.search)
        row.addWidget(self.source)
        row.addWidget(self.refresh)
        outer.addWidget(header)

        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(covers.WIDTH, covers.HEIGHT))
        self.grid.setGridSize(QSize(covers.WIDTH + 32, covers.HEIGHT + 58))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(6)
        self.grid.setUniformItemSizes(True)
        self.grid.setWordWrap(True)
        self.grid.setTextElideMode(Qt.ElideRight)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)

        self.empty = QLabel("Looking for games...")
        self.empty.setObjectName("Empty")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setWordWrap(True)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.grid)
        self.stack.addWidget(self.empty)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 12, 20, 12)
        body_layout.addWidget(self.stack)
        outer.addWidget(body, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")

        self.search.textChanged.connect(self._apply_filter)
        self.source.currentIndexChanged.connect(self._apply_filter)
        self.refresh.clicked.connect(self.reload)
        self.grid.itemDoubleClicked.connect(self._launch_item)
        self.grid.customContextMenuRequested.connect(self._context_menu)

    def _build_menu(self) -> None:
        library = self.menuBar().addMenu("&Library")

        refresh = QAction("Refresh", self)
        refresh.setShortcut(QKeySequence.Refresh)
        refresh.triggered.connect(self.reload)
        library.addAction(refresh)

        library.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        library.addAction(quit_action)

        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("About GameCenter", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    # -- data -------------------------------------------------------------

    def reload(self) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self._games = steam.scan()
        finally:
            QApplication.restoreOverrideCursor()
        self._populate()

    def _populate(self) -> None:
        self.grid.clear()
        for game in self._games:
            item = QListWidgetItem(QIcon(covers.cover(game.title)), game.title)
            item.setData(Qt.UserRole, game)
            tip = f"{game.title}\n{game.source_label}"
            if game.size_gb:
                tip += f"\n{game.size_gb:.1f} GB"
            item.setToolTip(tip)
            self.grid.addItem(item)

        self._sync_sources()
        self._apply_filter()

    def _sync_sources(self) -> None:
        current = self.source.currentData()
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem("All stores", None)
        for source in sorted({g.source for g in self._games}):
            self.source.addItem(source.capitalize(), source)
        index = self.source.findData(current)
        self.source.setCurrentIndex(index if index >= 0 else 0)
        self.source.blockSignals(False)

    def _apply_filter(self) -> None:
        query = self.search.text().strip().casefold()
        source = self.source.currentData()
        visible = 0
        for i in range(self.grid.count()):
            item = self.grid.item(i)
            game: Game = item.data(Qt.UserRole)
            matches = (not query or query in game.title.casefold()) and (
                source is None or game.source == source
            )
            item.setHidden(not matches)
            visible += int(matches)

        if not self._games:
            self.empty.setText(
                "No Steam library found.\n"
                "Install a game with Steam and press Refresh."
            )
            self.stack.setCurrentWidget(self.empty)
        elif not visible:
            self.empty.setText("No games match your filters.")
            self.stack.setCurrentWidget(self.empty)
        else:
            self.stack.setCurrentWidget(self.grid)

        self._update_status(visible)

    def _update_status(self, visible: int | None = None) -> None:
        total = len(self._games)
        installed = sum(1 for g in self._games if g.installed)
        if visible is None or visible == total:
            message = f"{total} games · {installed} installed"
        else:
            message = f"{visible} of {total} games · {installed} installed"
        self.statusBar().showMessage(message)

    # -- actions ----------------------------------------------------------

    def _launch_item(self, item: QListWidgetItem) -> None:
        self._launch(item.data(Qt.UserRole))

    def _launch(self, game: Game) -> None:
        try:
            launch(game)
        except (LaunchError, OSError) as exc:
            QMessageBox.warning(self, "GameCenter", f"Couldn't start {game.title}:\n{exc}")
            return
        self.statusBar().showMessage(f"Launching {game.title}...", 6000)

    def _context_menu(self, position) -> None:
        item = self.grid.itemAt(position)
        if item is None:
            return
        game: Game = item.data(Qt.UserRole)

        menu = QMenu(self)
        start = menu.addAction("Launch")
        menu.addSeparator()
        folder = menu.addAction("Open install folder")
        folder.setEnabled(bool(game.install_dir and game.install_dir.is_dir()))
        copy_id = menu.addAction("Copy App ID")

        chosen = menu.exec(self.grid.viewport().mapToGlobal(position))
        if chosen is start:
            self._launch(game)
        elif chosen is folder and game.install_dir is not None:
            try:
                open_folder(game.install_dir)
            except OSError as exc:
                QMessageBox.warning(self, "GameCenter", str(exc))
        elif chosen is copy_id:
            QApplication.clipboard().setText(game.app_id)
            self.statusBar().showMessage("App ID copied", 3000)

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About GameCenter",
            f"<b>GameCenter</b> {__version__}<br>"
            "A local-first game library launcher.<br><br>"
            "Released under the MIT license.",
        )


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("GameCenter")
    app.setApplicationDisplayName("GameCenter")
    app.setOrganizationName("GameCenter")
    app.setStyle("Fusion")
    app.setStyleSheet(theme.STYLESHEET)
    app.setWindowIcon(covers.app_icon())

    window = MainWindow()
    window.show()
    return app.exec()
