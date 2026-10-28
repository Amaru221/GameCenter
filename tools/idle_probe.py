"""Measure how much the app renders and burns while nobody touches it.

Development helper, not shipped. It opens the real window, lets the startup
work settle and then counts the frames the window presents with no input.

A healthy build is almost silent when idle: a single running QML animation
(``loops: Animation.Infinite`` inside a closed overlay, for example) keeps the
whole window repainting at the monitor refresh rate, which is what this tool
catches.

    python tools/idle_probe.py
    python tools/idle_probe.py --seconds 10 --max-fps 1
    python tools/idle_probe.py --with-art        # keep the cover downloader on
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=6.0,
                        help="measurement window after the settle time")
    parser.add_argument("--settle", type=float, default=5.0,
                        help="seconds to wait for startup work (scan, first paint)")
    parser.add_argument("--max-fps", type=float, default=2.0,
                        help="fail when the idle window renders more than this")
    parser.add_argument("--with-art", action="store_true",
                        help="leave the cover downloader enabled")
    args = parser.parse_args()

    if not args.with_art:
        os.environ.setdefault("GC_NO_ART", "1")

    import psutil
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from gamecenter.ui.app import _load_fonts, create_engine
    from gamecenter.ui.library_model import LibraryModel

    app = QApplication(sys.argv[:1])
    _load_fonts()
    process = psutil.Process()

    library = LibraryModel(download_art=args.with_art)
    engine = create_engine(library)
    roots = engine.rootObjects()
    if not roots:
        print("Main.qml failed to load", file=sys.stderr)
        return 2
    window = roots[0]

    frames = {"count": 0}
    window.frameSwapped.connect(lambda: frames.__setitem__("count", frames["count"] + 1))

    state: dict[str, float] = {}

    def start() -> None:
        process.cpu_percent()  # discard the first (always 0) sample
        frames["count"] = 0
        state["t0"] = time.time()
        state["cpu0"] = process.cpu_percent(interval=None)

    def finish() -> None:
        elapsed = max(time.time() - state["t0"], 0.001)
        fps = frames["count"] / elapsed
        cpu = process.cpu_percent(interval=None)
        prints = []
        prints.append(f"window      {window.width()}x{window.height()}")
        prints.append(f"idle frames {frames['count']} in {elapsed:.1f}s -> {fps:.2f} fps")
        prints.append(f"process CPU {cpu:.2f} % (last sample)")
        monitor = window.screen().refreshRate() if window.screen() else 0
        if monitor:
            prints.append(f"monitor     {monitor:.0f} Hz")
        prints.append(f"budget      <= {args.max_fps:g} fps")
        for line in prints:
            print(line)
        ok = fps <= args.max_fps
        print("RESULT", "ok" if ok else "too much rendering while idle")
        app.exit(0 if ok else 1)

    QTimer.singleShot(int(args.settle * 1000), start)
    QTimer.singleShot(int((args.settle + args.seconds) * 1000), finish)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
