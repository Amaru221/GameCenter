"""Artwork drawn at runtime: covers, the window background and the app icon.

Everything here is generated with QPainter from the game's title, so the
repository ships no images and nothing is downloaded.
"""

from __future__ import annotations

import hashlib
import random
import urllib.parse
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
    QPolygonF,
    QRadialGradient,
)


def _hue(title: str) -> float:
    return hashlib.sha256(title.encode("utf-8")).digest()[0] / 255.0


def _palette(title: str) -> tuple[QColor, QColor, QColor]:
    hue = _hue(title)
    top = QColor.fromHsvF(hue, 0.55, 0.42)
    bottom = QColor.fromHsvF((hue + 0.07) % 1.0, 0.70, 0.16)
    accent = QColor.fromHsvF((hue + 0.48) % 1.0, 0.65, 0.98)
    return top, bottom, accent


def render_cover(title: str, width: int = 336, height: int = 384) -> QImage:
    """Abstract box art for the cartridge label."""
    top, bottom, accent = _palette(title)
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QRectF(0, 0, width, height)

    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, top)
    gradient.setColorAt(1.0, bottom)
    painter.fillRect(rect, gradient)

    # Two soft halos, offset from the centre so each title differs.
    hue = _hue(title)
    for i, (fx, fy, radius, tint) in enumerate(
        (
            (0.25 + 0.5 * hue, 0.30, 0.55, accent),
            (0.80 - 0.4 * hue, 0.75, 0.45, top.lighter(135)),
        )
    ):
        glow = QRadialGradient(width * fx, height * fy, max(width, height) * radius)
        centre = QColor(tint)
        centre.setAlpha(150 if i == 0 else 110)
        edge = QColor(tint)
        edge.setAlpha(0)
        glow.setColorAt(0.0, centre)
        glow.setColorAt(1.0, edge)
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QPointF(width * fx, height * fy), width * radius, width * radius
        )

    # Diagonal bands in a corner, clipped to the canvas.
    painter.save()
    painter.setClipRect(rect)
    painter.setBrush(QColor(255, 255, 255, 18))
    for offset in range(-height, width + height, 46):
        band = QPolygonF(
            [
                QPointF(offset, height),
                QPointF(offset + 18, height),
                QPointF(offset + 18 + height, 0),
                QPointF(offset + height, 0),
            ]
        )
        painter.drawPolygon(band)
    painter.restore()

    # A large ring and a soft wedge give the art a poster-like composition.
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(255, 255, 255, 46), max(1.0, width * 0.012)))
    radius = width * 0.34
    painter.drawEllipse(QPointF(width * 0.78, height * 0.24), radius, radius)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 0, 0, 34))
    painter.drawPolygon(
        QPolygonF(
            [
                QPointF(width * 0.55, height * 0.46),
                QPointF(width, height * 0.30),
                QPointF(width, height * 0.72),
                QPointF(width * 0.70, height * 0.72),
            ]
        )
    )

    # Footer shade and title, set like a minimalist cover.
    footer = QLinearGradient(0, height * 0.40, 0, height)
    footer.setColorAt(0.0, QColor(0, 0, 0, 0))
    footer.setColorAt(1.0, QColor(0, 0, 0, 175))
    painter.fillRect(QRectF(0, height * 0.40, width, height * 0.60), footer)

    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)
    painter.drawRoundedRect(
        QRectF(width * 0.09, height * 0.545, width * 0.14, max(2.0, height * 0.012)),
        height * 0.006,
        height * 0.006,
    )

    text_rect = QRectF(width * 0.09, height * 0.58, width * 0.82, height * 0.27)
    _draw_title(painter, title.upper(), text_rect)

    painter.end()
    return image


def _draw_title(painter: QPainter, text: str, rect: QRectF) -> None:
    """Largest bold size that keeps the title inside `rect` (up to three lines)."""
    font = QFont("Sora")
    font.setWeight(QFont.Black)
    size = 46
    longest = max(text.split(), key=len, default="")
    while size > 14:
        font.setPixelSize(size)
        metrics = QFontMetrics(font)
        box = metrics.boundingRect(
            rect.toRect(),
            int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignBottom),
            text,
        )
        if metrics.horizontalAdvance(longest) <= rect.width() and box.height() <= rect.height():
            break
        size -= 2

    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255, 242))
    painter.drawText(
        rect, int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignBottom), text
    )


def render_label(art: QImage, source: str, meta: str, width: int = 512, height: int = 560) -> QImage:
    """The label texture applied to the front of the 3D DS cartridge."""
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor("#0a0c10"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    scaled = art.scaled(
        width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
    )
    sx = (scaled.width() - width) / 2
    sy = (scaled.height() - height) / 2
    painter.drawImage(QRectF(0, 0, width, height), scaled, QRectF(sx, sy, width, height))

    painter.fillRect(QRectF(0, 0, width, 52), QColor(10, 12, 16, 235))
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#eef2f7"))
    painter.drawEllipse(QPointF(28, 26), 14, 14)

    font = QFont("Chakra Petch")
    font.setPixelSize(15)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#0b0d10"))
    painter.drawText(QRectF(14, 12, 28, 28), Qt.AlignCenter, (source or "?")[:1].upper())
    painter.setPen(QColor("#eef2f7"))
    painter.drawText(
        QRectF(52, 0, width - 64, 52),
        Qt.AlignVCenter | Qt.AlignLeft,
        (source or "").upper(),
    )

    painter.fillRect(QRectF(0, height - 44, width, 44), QColor(10, 12, 16, 235))
    font.setPixelSize(12)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor("#c3ccda"))
    painter.drawText(
        QRectF(18, height - 44, width - 36, 44),
        Qt.AlignVCenter | Qt.AlignLeft,
        meta,
    )

    painter.end()
    return image


def render_background(width: int = 1920, height: int = 1200) -> QImage:
    """The blurred mesh behind the glass: soft coloured blobs on near-black."""
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor("#07080b"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setCompositionMode(QPainter.CompositionMode_Plus)

    blobs = (
        (0.10, 0.20, 0.46, QColor(92, 44, 205)),
        (0.52, 0.08, 0.42, QColor(24, 116, 184)),
        (0.88, 0.28, 0.38, QColor(22, 150, 96)),
        (0.72, 0.90, 0.44, QColor(206, 86, 34)),
        (0.28, 0.86, 0.42, QColor(48, 46, 196)),
        (0.44, 0.48, 0.30, QColor(176, 58, 140)),
    )
    for fx, fy, radius, colour in blobs:
        centre = QColor(colour)
        centre.setAlpha(238)
        edge = QColor(colour)
        edge.setAlpha(0)
        gradient = QRadialGradient(
            width * fx, height * fy, max(width, height) * radius
        )
        gradient.setColorAt(0.0, centre)
        gradient.setColorAt(1.0, edge)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(image.rect())

    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    # Darken the edges so the window frame does not compete with the cards.
    vignette = QRadialGradient(
        width * 0.5, height * 0.48, max(width, height) * 0.72
    )
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.70, QColor(0, 0, 0, 40))
    vignette.setColorAt(1.0, QColor(0, 0, 0, 170))
    painter.setBrush(vignette)
    painter.drawRect(image.rect())

    painter.fillRect(image.rect(), QColor(8, 10, 14, 26))
    painter.end()

    _add_grain(image)
    return image


def _add_grain(image: QImage) -> None:
    """A faint noise layer; makes the gradients look like a printed surface."""
    size = 128
    raw = bytearray(random.randbytes(size * size * 4))
    for i in range(3, len(raw), 4):
        raw[i] = 10
    noise = QImage(bytes(raw), size, size, QImage.Format_ARGB32)
    from PySide6.QtGui import QPixmap

    painter = QPainter(image)
    painter.setOpacity(0.5)
    painter.drawTiledPixmap(image.rect(), QPixmap.fromImage(noise))
    painter.end()


def render_app_icon(size: int = 256) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)

    rect = QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#3d444f"))
    gradient.setColorAt(0.5, QColor("#272c34"))
    gradient.setColorAt(1.0, QColor("#15181e"))
    painter.setPen(QPen(QColor("#555d6a"), max(1.0, size * 0.012)))
    painter.setBrush(gradient)
    painter.drawRoundedRect(rect, size * 0.22, size * 0.22)

    notch = QRectF(size * 0.34, size * 0.13, size * 0.32, size * 0.055)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#0a0b0e"))
    painter.drawRoundedRect(notch, size * 0.03, size * 0.03)

    label = QRectF(size * 0.18, size * 0.30, size * 0.64, size * 0.48)
    painter.setBrush(QColor("#0b0d11"))
    painter.drawRoundedRect(label, size * 0.06, size * 0.06)

    painter.setPen(QPen(QColor("#4cc9f0"), max(2.0, size * 0.018)))
    painter.drawLine(
        QPointF(size * 0.30, size * 0.66), QPointF(size * 0.70, size * 0.66)
    )

    font = QFont("Sora")
    font.setPixelSize(int(size * 0.22))
    font.setWeight(QFont.Black)
    painter.setFont(font)
    painter.setPen(QColor("#f2f5fa"))
    painter.drawText(label, Qt.AlignCenter, "GC")

    painter.end()
    return image


def app_icon() -> QIcon:
    return QIcon(_pixmap(render_app_icon()))


def _pixmap(image: QImage):
    from PySide6.QtGui import QPixmap

    return QPixmap.fromImage(image)


_COVER_KEYS: dict[str, tuple[str, str]] = {}
_ART_KEYS: dict[str, str] = {}


def art_key(path: str) -> str:
    """A stable key for a downloaded cover file, used by the ``art`` provider."""
    key = hashlib.sha1(f"art|{path}".encode("utf-8")).hexdigest()[:16]
    _ART_KEYS[key] = str(path)
    return key


class ArtProvider:
    """Loads a user-selected cover from disk, with a small mtime cache."""

    def __init__(self) -> None:
        self._files: dict[str, tuple[int, QImage]] = {}

    def request(self, image_id: str) -> QImage:
        path = _ART_KEYS.get(image_id)
        if not path:
            return QImage()
        try:
            stamp = Path(path).stat().st_mtime_ns
        except OSError:
            return QImage()
        hit = self._files.get(path)
        if hit is not None and hit[0] == stamp:
            return hit[1]
        image = QImage(path)
        if image.isNull():
            return QImage()
        if len(self._files) >= 200:
            self._files.clear()
        self._files[path] = (stamp, image)
        return image


def cover_key(title: str, app_id: str = "", revision: int = 0) -> str:
    """A short, URL-safe key for this title and cover revision.

    Bumping `revision` gives the same game a new key, which makes QML drop its
    cached image and ask the provider again (used when real art arrives).
    """
    raw = f"{title}|{app_id}|{revision}"
    key = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    _COVER_KEYS[key] = (title, app_id)
    return key


class CoverProvider:
    """QQuickImageProvider for ``image://cover/<key>``."""

    def __init__(self) -> None:
        self._procedural: dict[str, QImage] = {}
        self._files: dict[str, tuple[int, QImage]] = {}

    def request(self, image_id: str) -> QImage:
        from . import artwork

        key = image_id.split("?", 1)[0]
        title, app_id = _COVER_KEYS.get(key, (urllib.parse.unquote(key), ""))

        if app_id and artwork.enabled():
            path = artwork.cached_path(app_id)
            if path is not None:
                try:
                    stamp = path.stat().st_mtime_ns
                except OSError:
                    stamp = 0
                hit = self._files.get(app_id)
                if hit is not None and hit[0] == stamp:
                    return hit[1]
                image = QImage(str(path))
                if not image.isNull():
                    if len(self._files) >= 400:
                        self._files.clear()
                    self._files[app_id] = (stamp, image)
                    return image

        art = self._procedural.get(title)
        if art is None:
            art = render_cover(title)
            if len(self._procedural) >= 400:
                self._procedural.clear()
            self._procedural[title] = art
        return art


def background_size() -> QSize:
    return QSize(1920, 1200)
