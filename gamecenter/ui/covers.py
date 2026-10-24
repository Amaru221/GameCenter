"""Portadas dibujadas al vuelo.

No hay imágenes en el repositorio: cada juego recibe un degradado estable a
partir de un hash de su título, sus iniciales y una etiqueta con el nombre.
Así la biblioteca se ve completa sin descargar nada.
"""

from __future__ import annotations

import hashlib
import re

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

WIDTH = 160
HEIGHT = 196
SCALE = 2
RADIUS = 10


def _initials(title: str) -> str:
    words = [w for w in re.split(r"[^\w]+", title) if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _palette(title: str) -> tuple[QColor, QColor, QColor]:
    digest = hashlib.sha256(title.encode("utf-8")).digest()
    hue = digest[0] / 255.0
    top = QColor.fromHsvF(hue, 0.55, 0.38)
    bottom = QColor.fromHsvF((hue + 0.06) % 1.0, 0.68, 0.18)
    accent = QColor.fromHsvF((hue + 0.45) % 1.0, 0.72, 0.95)
    return top, bottom, accent


def cover(title: str, width: int = WIDTH, height: int = HEIGHT, scale: int = SCALE) -> QPixmap:
    """A deterministic cartridge-like cover for `title`."""
    top, bottom, accent = _palette(title)
    pixmap = QPixmap(int(width * scale), int(height * scale))
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    rect = QRectF(0, 0, width, height)

    shape = QPainterPath()
    shape.addRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), RADIUS, RADIUS)

    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, top)
    gradient.setColorAt(1.0, bottom)
    painter.fillPath(shape, gradient)

    # Soft diagonal sheen, clipped to the rounded shape.
    painter.save()
    painter.setClipPath(shape)
    painter.setPen(QPen(QColor(255, 255, 255, 14), 9))
    for x in range(-height, int(width) + 26, 26):
        painter.drawLine(x, int(height), x + int(height), 0)
    band = QRectF(0, height * 0.66, width, height * 0.34)
    painter.fillRect(band, QColor(8, 10, 14, 120))
    painter.restore()

    # Accent tab, like the label on a cartridge.
    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)
    painter.drawRoundedRect(QRectF(13, 13, width * 0.24, 4), 2, 2)

    font = QFont("Segoe UI")
    font.setPixelSize(int(height * 0.26))
    font.setWeight(QFont.Bold)
    painter.setFont(font)
    painter.setPen(accent)
    painter.drawText(QRectF(0, 0, width, height * 0.66), Qt.AlignCenter, _initials(title))

    font.setPixelSize(11)
    font.setWeight(QFont.Medium)
    painter.setFont(font)
    painter.setPen(QColor(235, 238, 245, 230))
    label = QFontMetrics(font).elidedText(title, Qt.ElideRight, width - 26)
    painter.drawText(band.adjusted(13, 6, -13, -8), Qt.AlignLeft | Qt.AlignBottom, label)

    painter.end()
    return pixmap


def app_icon() -> QIcon:
    return QIcon(cover("GameCenter", 64, 64, 2))
