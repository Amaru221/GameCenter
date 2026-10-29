"""Short, synthesized UI sounds played through Qt Multimedia.

The cues are generated once with pure Python (no binary assets in the
repository) and cached as mono 16-bit WAV files in the user's cache folder.
``QSoundEffect`` then gives the low latency a console-style interface needs.

If Qt Multimedia is missing, there is no audio device, the QML platform is
headless (``offscreen``/``minimal``) or ``GC_NO_SOUND`` is set, the manager
becomes a silent no-op so tests and CI never depend on audio hardware.
"""

from __future__ import annotations

import hashlib
import io
import math
import os
import random
import sys
import wave
from array import array
from pathlib import Path

from PySide6.QtCore import Property, QObject, QStandardPaths, QUrl, Signal, Slot

try:  # pragma: no cover - the fallback only runs on stripped Qt builds
    from PySide6.QtMultimedia import QMediaDevices, QSoundEffect
except Exception:  # noqa: BLE001 - an optional dependency at runtime
    QMediaDevices = None  # type: ignore[assignment]
    QSoundEffect = None  # type: ignore[assignment]

SAMPLE_RATE = 44100
CUE_VERSION = 3
CUES = ("navigate", "open", "close", "tab", "launch", "toggle")
_VOICES = {"navigate": 3, "tab": 3, "toggle": 2}
_VOLUME = {
    "navigate": 0.26,
    "open": 0.34,
    "close": 0.30,
    "tab": 0.28,
    "launch": 0.42,
    "toggle": 0.22,
}


def _envelope(
    position: float, duration: float, attack: float, curve: float
) -> float:
    """Fast soft attack, then a smooth exponential-ish decay."""
    if position < 0.0 or position > duration:
        return 0.0
    if position < attack:
        return position / max(attack, 1e-6)
    tail = 1.0 - (position - attack) / max(duration - attack, 1e-6)
    return max(0.0, tail) ** curve


def _add_tone(
    buffer: list[float],
    *,
    start: float,
    duration: float,
    start_hz: float,
    end_hz: float | None = None,
    amplitude: float,
    attack: float = 0.004,
    curve: float = 5.0,
    partials: tuple[tuple[float, float], ...] = ((1.0, 1.0),),
) -> None:
    """Add a gliding tone with an arbitrary harmonic recipe."""
    if not buffer:
        return
    end_hz = start_hz if end_hz is None else end_hz
    first = int(start * SAMPLE_RATE)
    count = int(duration * SAMPLE_RATE)
    if first >= len(buffer):
        return
    count = min(count, len(buffer) - first)
    phase = 0.0
    step = 1.0 / SAMPLE_RATE
    span = max(duration, 1e-6)
    for index in range(count):
        moment = index * step
        ratio = moment / span
        frequency = start_hz + (end_hz - start_hz) * ratio
        phase += 2.0 * math.pi * frequency * step
        sample = 0.0
        for harmonic, weight in partials:
            sample += weight * math.sin(phase * harmonic)
        buffer[first + index] += (
            sample * amplitude * _envelope(moment, duration, attack, curve)
        )


def _add_air(
    buffer: list[float],
    *,
    start: float,
    duration: float,
    amplitude: float,
    seed: int,
    smooth: int = 18,
) -> None:
    """A tiny filtered-noise breath, used to make the cues feel airy."""
    first = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(buffer) - first)
    if count <= 0:
        return
    rng = random.Random(seed)
    history = 0.0
    for index in range(count):
        moment = index / SAMPLE_RATE
        history += (rng.uniform(-1.0, 1.0) - history) / smooth
        buffer[first + index] += (
            history * amplitude * _envelope(moment, duration, 0.01, 3.0)
        )


def _navigate() -> list[float]:
    duration = 0.060
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=duration,
        start_hz=1120.0,
        end_hz=980.0,
        amplitude=0.55,
        attack=0.002,
        curve=7.0,
        partials=((1.0, 1.0), (2.0, 0.16), (3.0, 0.05)),
    )
    _add_air(buffer, start=0.0, duration=0.012, amplitude=0.18, seed=11)
    return buffer


def _open() -> list[float]:
    duration = 0.260
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=0.245,
        start_hz=392.0,
        end_hz=587.33,
        amplitude=0.34,
        attack=0.018,
        curve=3.2,
        partials=((1.0, 1.0), (2.0, 0.22), (3.0, 0.08)),
    )
    _add_tone(
        buffer,
        start=0.018,
        duration=0.230,
        start_hz=783.99,
        end_hz=1174.66,
        amplitude=0.20,
        attack=0.014,
        curve=3.6,
        partials=((1.0, 1.0), (2.0, 0.14)),
    )
    _add_tone(
        buffer,
        start=0.060,
        duration=0.190,
        start_hz=2093.0,
        amplitude=0.06,
        attack=0.030,
        curve=2.4,
    )
    _add_air(buffer, start=0.0, duration=0.12, amplitude=0.075, seed=23)
    return buffer


def _close() -> list[float]:
    duration = 0.220
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=0.210,
        start_hz=880.0,
        end_hz=523.25,
        amplitude=0.34,
        attack=0.008,
        curve=3.6,
        partials=((1.0, 1.0), (2.0, 0.18), (3.0, 0.06)),
    )
    _add_tone(
        buffer,
        start=0.010,
        duration=0.195,
        start_hz=440.0,
        end_hz=261.63,
        amplitude=0.26,
        attack=0.008,
        curve=3.2,
        partials=((1.0, 1.0), (2.0, 0.12)),
    )
    _add_air(buffer, start=0.0, duration=0.09, amplitude=0.055, seed=37)
    return buffer


def _tab() -> list[float]:
    duration = 0.120
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=0.045,
        start_hz=698.46,
        end_hz=740.0,
        amplitude=0.48,
        attack=0.002,
        curve=8.0,
        partials=((1.0, 1.0), (2.0, 0.18)),
    )
    _add_tone(
        buffer,
        start=0.042,
        duration=0.060,
        start_hz=1046.5,
        end_hz=1174.66,
        amplitude=0.42,
        attack=0.002,
        curve=7.0,
        partials=((1.0, 1.0), (2.0, 0.14)),
    )
    _add_air(buffer, start=0.0, duration=0.018, amplitude=0.12, seed=51)
    return buffer


def _launch() -> list[float]:
    duration = 0.620
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=0.600,
        start_hz=110.0,
        end_hz=146.83,
        amplitude=0.32,
        attack=0.055,
        curve=2.0,
        partials=((1.0, 1.0), (2.0, 0.20), (3.0, 0.06)),
    )
    _add_tone(
        buffer,
        start=0.020,
        duration=0.560,
        start_hz=164.81,
        end_hz=220.0,
        amplitude=0.24,
        attack=0.050,
        curve=2.2,
        partials=((1.0, 1.0), (2.0, 0.16)),
    )
    _add_tone(
        buffer,
        start=0.060,
        duration=0.470,
        start_hz=329.63,
        end_hz=440.0,
        amplitude=0.16,
        attack=0.045,
        curve=2.4,
        partials=((1.0, 1.0), (2.0, 0.12)),
    )
    _add_tone(
        buffer,
        start=0.110,
        duration=0.360,
        start_hz=1318.51,
        amplitude=0.055,
        attack=0.080,
        curve=1.8,
    )
    _add_tone(
        buffer,
        start=0.150,
        duration=0.330,
        start_hz=1760.0,
        amplitude=0.035,
        attack=0.080,
        curve=1.8,
    )
    _add_air(buffer, start=0.0, duration=0.30, amplitude=0.10, seed=73, smooth=26)
    return buffer


def _toggle() -> list[float]:
    duration = 0.070
    size = int(duration * SAMPLE_RATE)
    buffer = [0.0] * size
    _add_tone(
        buffer,
        start=0.0,
        duration=duration,
        start_hz=1318.51,
        end_hz=1567.98,
        amplitude=0.42,
        attack=0.0015,
        curve=8.0,
        partials=((1.0, 1.0), (2.0, 0.12)),
    )
    _add_air(buffer, start=0.0, duration=0.010, amplitude=0.14, seed=91)
    return buffer


_BUILDERS = {
    "navigate": _navigate,
    "open": _open,
    "close": _close,
    "tab": _tab,
    "launch": _launch,
    "toggle": _toggle,
}


def _normalize(samples: list[float], peak: float = 0.78) -> list[float]:
    highest = max((abs(value) for value in samples), default=0.0)
    if highest <= 0.0:
        return samples
    scale = peak / highest
    return [value * scale for value in samples]


def wav_bytes(name: str) -> bytes:
    """Render one cue as a mono 16-bit PCM WAV file in memory."""
    builder = _BUILDERS.get(name)
    if builder is None:
        raise KeyError(f"unknown sound cue: {name}")

    samples = _normalize(builder())
    pcm = array("h")
    for value in samples:
        clipped = max(-1.0, min(1.0, value))
        pcm.append(int(round(clipped * 32767.0)))
    if sys.byteorder != "little":  # pragma: no cover - Windows is little-endian
        pcm.byteswap()

    stream = io.BytesIO()
    with wave.open(stream, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())
    return stream.getvalue()


def _cache_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    folder = Path(base) if base else Path.home() / ".cache" / "GameCenter"
    folder = folder / "sounds"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _cue_name(name: str) -> str:
    digest = hashlib.sha1(f"{name}|{CUE_VERSION}".encode("utf-8")).hexdigest()[:10]
    return f"gc-{name}-{digest}.wav"


def cue_path(name: str) -> Path:
    """The cached WAV for *name*, writing it on first use."""
    path = _cache_dir() / _cue_name(name)
    if not path.is_file():
        payload = wav_bytes(name)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    return path


class SoundManager(QObject):
    """QML-facing façade: one slot per interaction, with a persistent mute."""

    enabledChanged = Signal()

    def __init__(self, prefs=None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._enabled = bool(getattr(prefs, "sound_enabled", True))
        self._available = self._audio_available()
        self._effects: dict[str, list] = {}
        self._cursor: dict[str, int] = {}
        self._loaded = False

    # -- availability -----------------------------------------------------

    @staticmethod
    def _audio_available() -> bool:
        if QSoundEffect is None or QMediaDevices is None:
            return False
        if os.environ.get("GC_NO_SOUND"):
            return False
        platform = os.environ.get("QT_QPA_PLATFORM", "").split(":", 1)[0]
        if platform.lower() in {"offscreen", "minimal", "vnc"}:
            return False
        try:
            device = QMediaDevices.defaultAudioOutput()
            return device is not None and not device.isNull()
        except Exception:  # noqa: BLE001 - no multimedia backend at all
            return False

    # -- properties -------------------------------------------------------

    @Property(bool, notify=enabledChanged)
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.setEnabled(value)

    @Slot(bool)
    def setEnabled(self, value: bool) -> None:
        value = bool(value)
        if value == self._enabled:
            return
        self._enabled = value
        if self._prefs is not None:
            try:
                self._prefs.sound_enabled = value
            except Exception:  # noqa: BLE001 - settings must never break the UI
                pass
        if not value:
            for voices in self._effects.values():
                for effect in voices:
                    try:
                        effect.stop()
                    except Exception:  # noqa: BLE001
                        pass
        self.enabledChanged.emit()
        if value:
            self.preload()

    # -- playback ---------------------------------------------------------

    @Slot()
    def preload(self) -> None:
        """Build/load every cue. Safe to call more than once."""
        if not self._available or not self._enabled or QSoundEffect is None:
            return
        if self._loaded:
            return
        self._loaded = True
        for name in CUES:
            try:
                path = cue_path(name)
            except OSError:
                continue
            voices = []
            for _ in range(_VOICES.get(name, 2)):
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(_VOLUME.get(name, 0.3))
                voices.append(effect)
            self._effects[name] = voices

    def _play(self, name: str) -> None:
        if not self._enabled or not self._available:
            return
        self.preload()
        voices = self._effects.get(name)
        if not voices:
            return
        index = self._cursor.get(name, 0) % len(voices)
        self._cursor[name] = index + 1
        effect = voices[index]
        try:
            effect.stop()
            effect.play()
        except Exception:  # noqa: BLE001 - audio must never break navigation
            pass

    # -- QML slots --------------------------------------------------------

    @Slot()
    def navigate(self) -> None:
        self._play("navigate")

    @Slot()
    def open(self) -> None:
        self._play("open")

    @Slot()
    def close(self) -> None:
        self._play("close")

    @Slot()
    def tab(self) -> None:
        self._play("tab")

    @Slot()
    def launch(self) -> None:
        self._play("launch")

    @Slot()
    def toggle(self) -> None:
        self._play("toggle")
