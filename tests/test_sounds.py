"""Tests for the synthesized interface sounds and their settings toggle."""

import os
import wave
from io import BytesIO

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("GC_NO_GAMEPAD", "1")
os.environ.setdefault("GC_NO_HOTKEYS", "1")
os.environ.setdefault("GC_NO_OVERLAY", "1")

from gamecenter.core import sounds  # noqa: E402
from gamecenter.core.preferences import Preferences  # noqa: E402


def test_every_cue_is_a_valid_mono_wav() -> None:
    for name in sounds.CUES:
        payload = sounds.wav_bytes(name)
        assert payload[:4] == b"RIFF"
        assert payload[8:12] == b"WAVE"
        with wave.open(BytesIO(payload), "rb") as handle:
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 2
            assert handle.getframerate() == sounds.SAMPLE_RATE
            assert handle.getnframes() > 0
            frames = handle.readframes(handle.getnframes())
        assert any(byte != 0 for byte in frames)


def test_cue_file_is_written_once(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sounds, "_cache_dir", lambda: tmp_path)
    path = sounds.cue_path("navigate")
    assert path.is_file()
    assert path.suffix == ".wav"
    stamp = path.stat().st_mtime_ns
    again = sounds.cue_path("navigate")
    assert again == path
    assert again.stat().st_mtime_ns == stamp


def test_sound_manager_is_silent_in_headless_mode(monkeypatch) -> None:
    monkeypatch.setenv("GC_NO_SOUND", "1")

    class Prefs:
        sound_enabled = True

    manager = sounds.SoundManager(Prefs())
    assert manager.enabled is True
    assert manager._available is False

    # Every slot must be a harmless no-op without an audio device.
    for name in ("navigate", "open", "close", "tab", "launch", "toggle"):
        getattr(manager, name)()
    manager.preload()


def test_sound_preference_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    prefs = Preferences(path)
    assert prefs.sound_enabled is True

    prefs.sound_enabled = False
    assert Preferences(path).sound_enabled is False

    prefs.sound_enabled = True
    assert Preferences(path).sound_enabled is True


def test_sound_manager_persists_the_toggle(monkeypatch) -> None:
    monkeypatch.setenv("GC_NO_SOUND", "1")

    class Prefs:
        sound_enabled = True

    prefs = Prefs()
    manager = sounds.SoundManager(prefs)
    manager.setEnabled(False)
    assert manager.enabled is False
    assert prefs.sound_enabled is False

    manager.setEnabled(True)
    assert manager.enabled is True
    assert prefs.sound_enabled is True
