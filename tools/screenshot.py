"""Save the window to a PNG for design review. Development helper, not shipped."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QPoint, QTimer  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from gamecenter.ui.app import _load_fonts, create_engine  # noqa: E402
from gamecenter.ui.library_model import LibraryModel  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    _load_fonts()
    library = LibraryModel()
    engine = create_engine(library)
    roots = engine.rootObjects()
    if not roots:
        return 1

    window = roots[0]
    window.resize(1180, 800)
    window.show()

    out = Path(__file__).resolve().parents[1] / (
        "screenshot-hover.png" if os.environ.get("GC_HOVER") else "screenshot.png"
    )

    if os.environ.get("GC_HOVER"):
        # Park the cursor over the first cartridge so the tilt shows up.
        QTimer.singleShot(1400, lambda: QTest.mouseMove(window, QPoint(140, 220)))

    def grab() -> None:
        image = window.grabWindow()
        image.save(str(out))
        print(f"saved {out} ({image.width()}x{image.height()})")
        app.quit()

    QTimer.singleShot(int(os.environ.get("GC_WAIT", "4000")), grab)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
