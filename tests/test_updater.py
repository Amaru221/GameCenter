"""Update checking and download helpers (no network)."""

import hashlib

import pytest

from gamecenter.core import updater


def _info(**overrides) -> updater.UpdateInfo:
    values = {
        "version": "0.5.0",
        "tag": "v0.5.0",
        "url": "",
        "name": "",
        "notes": "",
        "published_at": "",
        "installer_url": "https://example.test/GameCenter-setup.exe",
        "installer_size": 0,
        "digest": "",
    }
    values.update(overrides)
    return updater.UpdateInfo(**values)


class _Response:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0
        self.headers = {"Content-Length": str(len(data))}

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._data):
            return b""
        if size < 0:
            chunk = self._data[self._offset :]
            self._offset = len(self._data)
            return chunk
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_parse_version() -> None:
    assert updater.parse_version("v0.4.2") == (0, 4, 2)
    assert updater.parse_version("0.4.2-beta.1") == (0, 4, 2)
    assert updater.parse_version("1.0") == (1, 0)
    assert updater.parse_version("") == (0,)


def test_is_newer() -> None:
    assert updater.is_newer("0.4.2", "0.4.1")
    assert updater.is_newer("0.5", "0.4.9")
    assert not updater.is_newer("0.4.1", "0.4.1")
    assert not updater.is_newer("0.4.0", "0.4.1")


def test_check_returns_the_installer(monkeypatch) -> None:
    release = {
        "tag_name": "v0.5.0",
        "html_url": "https://github.com/Amaru221/GameCenter/releases/tag/v0.5.0",
        "name": "GameCenter 0.5.0",
        "body": "Notes",
        "published_at": "2026-10-24T00:00:00Z",
        "assets": [
            {
                "name": "GameCenter-0.5.0-windows-setup.exe",
                "browser_download_url": "https://example.test/GameCenter-setup.exe",
                "size": 1234,
                "digest": "sha256:abc",
            },
            {"name": "source.zip", "browser_download_url": "https://example.test/src.zip"},
        ],
    }
    monkeypatch.setattr(updater, "fetch_latest", lambda timeout=10: release)

    info = updater.check("0.4.1")

    assert info is not None
    assert info.version == "0.5.0"
    assert info.tag == "v0.5.0"
    assert info.installer_url.endswith("GameCenter-setup.exe")
    assert info.installer_size == 1234
    assert info.digest == "sha256:abc"


def test_check_without_a_newer_version(monkeypatch) -> None:
    monkeypatch.setattr(
        updater, "fetch_latest", lambda timeout=10: {"tag_name": "v0.4.1", "assets": []}
    )
    assert updater.check("0.4.1") is None


def test_check_propagates_errors(monkeypatch) -> None:
    def boom(timeout=10):
        raise updater.UpdateError("Couldn't reach GitHub.")

    monkeypatch.setattr(updater, "fetch_latest", boom)

    with pytest.raises(updater.UpdateError):
        updater.check("0.4.1")


def test_download_installer_verifies_and_reports_progress(
    monkeypatch, tmp_path
) -> None:
    payload = b"installer-bytes" * 100
    digest = hashlib.sha256(payload).hexdigest()
    info = _info(
        installer_size=len(payload),
        digest=f"sha256:{digest}",
    )
    monkeypatch.setattr(
        updater.urllib.request,
        "urlopen",
        lambda request, timeout=30: _Response(payload),
    )
    progress: list[tuple[int, int]] = []
    target = tmp_path / "GameCenter-setup.exe"

    result = updater.download_installer(
        info,
        destination=target,
        progress=lambda done, total: progress.append((done, total)),
    )

    assert result == target
    assert target.read_bytes() == payload
    assert progress[-1] == (len(payload), len(payload))


def test_download_installer_rejects_a_bad_digest(monkeypatch, tmp_path) -> None:
    payload = b"not-the-real-installer" * 100
    info = _info(
        installer_size=len(payload),
        digest="sha256:" + "0" * 64,
    )
    monkeypatch.setattr(
        updater.urllib.request,
        "urlopen",
        lambda request, timeout=30: _Response(payload),
    )
    target = tmp_path / "GameCenter-setup.exe"

    with pytest.raises(updater.UpdateError):
        updater.download_installer(info, destination=target)

    assert not target.exists()
    assert not target.with_name(target.name + ".part").exists()


def test_download_installer_needs_a_url() -> None:
    with pytest.raises(updater.UpdateError):
        updater.download_installer(_info(installer_url=""))
