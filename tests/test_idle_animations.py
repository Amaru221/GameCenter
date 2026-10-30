"""Guardrails for the idle cost of the UI.

A QML animation with ``loops: Animation.Infinite`` keeps ticking even when its
owner is hidden (``visible: false`` / ``opacity: 0`` do not stop it), and every
tick makes Qt Quick repaint the whole window at the monitor refresh rate. That
is what used to keep GameCenter at ~180 fps, 17 % CPU and 12-30 % GPU while
sitting idle in the library.

These tests keep the pattern from coming back:

* every infinite animation must be gated by a ``running:`` binding, and
* Big Picture (the heaviest closed overlay) must only exist while it is open.

The runtime side of the same guardrail is ``tools/idle_probe.py``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("GC_NO_GAMEPAD", "1")
os.environ.setdefault("GC_NO_HOTKEYS", "1")
os.environ.setdefault("GC_NO_OVERLAY", "1")

QML_DIR = Path(__file__).resolve().parents[1] / "gamecenter" / "ui" / "qml"

_ANIMATION = re.compile(
    r"(?:^|\n)[ \t]*(?:SequentialAnimation|ParallelAnimation|NumberAnimation|"
    r"RotationAnimation|PropertyAnimation|ColorAnimation|Vector3dAnimation|"
    r"PathAnimation|SmoothedAnimation|SpringAnimation)\b[^\n{]*\{"
)


def _animation_blocks(text: str):
    """Yield ``(line, body)`` for every animation element block in ``text``."""
    for match in _ANIMATION.finditer(text):
        start = match.end() - 1  # the opening brace
        depth = 0
        index = start
        while index < len(text):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        line = text.count("\n", 0, match.start()) + 1
        yield line, text[start:index + 1]


def test_infinite_animations_are_gated() -> None:
    offenders = []
    for path in sorted(QML_DIR.glob("*.qml")):
        text = path.read_text(encoding="utf-8")
        for line, body in _animation_blocks(text):
            if "Animation.Infinite" not in body:
                continue
            if "running:" not in body:
                offenders.append(f"{path.name}:{line}")
    assert not offenders, (
        "Infinite animations keep the window repainting while hidden; add a "
        f"'running:' binding to each one: {offenders}"
    )


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def model(app, monkeypatch, tmp_path):
    from gamecenter.core import sources
    from gamecenter.core.models import Game
    from gamecenter.ui import library_model

    games = [
        Game(id="steam:1", title="Alpha Quest", source="steam", app_id="123"),
        Game(id="steam:2", title="Beta Racer", source="steam", app_id="456"),
    ]
    monkeypatch.setattr(
        library_model,
        "scan_all",
        lambda progress=None: sources._with_playtime(games),
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
    model = library_model.LibraryModel(
        download_art=False,
        settings_path=tmp_path / "settings.json",
        cache_path=tmp_path / "library_cache.json",
    )
    assert model.waitForScan(10)
    return model


def test_big_picture_is_created_only_while_open(app, model) -> None:
    from PySide6.QtCore import QObject
    from PySide6.QtTest import QTest

    from gamecenter.ui.app import create_engine

    engine = create_engine(model)
    root = engine.rootObjects()[0]
    app.processEvents()

    assert root.property("bigPictureMounted") is False
    assert root.findChild(QObject, "bigPicture") is None

    root.setProperty("bigPictureOpen", True)
    app.processEvents()

    picture = root.findChild(QObject, "bigPicture")
    assert picture is not None
    assert picture.property("opened") is True

    root.setProperty("bigPictureOpen", False)
    app.processEvents()
    # The item survives the 180 ms fade-out, then it is freed.
    QTest.qWait(450)
    app.processEvents()

    assert root.property("bigPictureMounted") is False
    assert root.findChild(QObject, "bigPicture") is None

    # Reopening mounts a fresh instance.
    root.setProperty("bigPictureOpen", True)
    app.processEvents()
    assert root.findChild(QObject, "bigPicture") is not None
