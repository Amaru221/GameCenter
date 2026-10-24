"""Generate packaging/gamecenter.ico from the app's procedural icon."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PIL import Image  # noqa: E402

from gamecenter.ui import covers  # noqa: E402
from gamecenter.ui.app import _load_fonts  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)


def main() -> int:
    app = QGuiApplication([])
    _load_fonts()

    build = ROOT / "build" / "icons"
    build.mkdir(parents=True, exist_ok=True)

    largest = None
    for size in SIZES:
        image = covers.render_app_icon(size)
        path = build / f"icon-{size}.png"
        image.save(str(path))
        if size == SIZES[-1]:
            largest = Image.open(path).convert("RGBA")

    out = Path(__file__).with_name("gamecenter.ico")
    largest.save(out, format="ICO", sizes=[(size, size) for size in SIZES])
    print(f"icon: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
