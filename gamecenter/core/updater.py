"""Check GitHub Releases and install a newer GameCenter.

The API is used to discover the latest release and its installer. The installer
is downloaded into a local cache, checked against GitHub's SHA-256 digest and
then launched silently; the app quits so the installer can replace it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .. import __version__

REPO = "Amaru221/GameCenter"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = f"GameCenter/{__version__}"


class UpdateError(RuntimeError):
    """A friendly message for the UI."""


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    tag: str
    url: str
    name: str
    notes: str
    published_at: str
    installer_url: str = ""
    installer_size: int = 0
    digest: str = ""


def parse_version(value: str) -> tuple[int, ...]:
    """'v0.4.2-beta.1' -> (0, 4, 2). Missing pieces are ignored."""
    core = str(value or "").strip().lstrip("vV").split("-", 1)[0]
    parts: list[int] = []
    for piece in core.split("."):
        match = re.match(r"\d+", piece)
        if not match:
            break
        parts.append(int(match.group()))
    return tuple(parts) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def fetch_latest(timeout: int = 10) -> dict:
    request = urllib.request.Request(
        API,
        headers={
            "User-Agent": UA,
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError("No releases found on GitHub.") from exc
        raise UpdateError(f"GitHub answered with an error ({exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError("Couldn't reach GitHub.") from exc
    except ValueError as exc:
        raise UpdateError("GitHub sent an unexpected answer.") from exc

    if not isinstance(data, dict):
        raise UpdateError("GitHub sent an unexpected answer.")
    return data


def check(current: str = __version__, timeout: int = 10) -> UpdateInfo | None:
    data = fetch_latest(timeout)
    tag = str(data.get("tag_name") or "").strip()
    version = tag.lstrip("vV")
    if not version or not is_newer(version, current):
        return None

    assets = data.get("assets") if isinstance(data.get("assets"), list) else []
    installer = next(
        (
            asset
            for asset in assets
            if str(asset.get("name", "")).endswith("-windows-setup.exe")
        ),
        None,
    ) or {}

    return UpdateInfo(
        version=version,
        tag=tag,
        url=str(data.get("html_url") or f"https://github.com/{REPO}/releases/latest"),
        name=str(data.get("name") or f"GameCenter {version}"),
        notes=str(data.get("body") or ""),
        published_at=str(data.get("published_at") or ""),
        installer_url=str(installer.get("browser_download_url") or ""),
        installer_size=int(installer.get("size") or 0),
        digest=str(installer.get("digest") or ""),
    )


def download_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
    return base / "GameCenter" / "updates"


def installer_filename(info: UpdateInfo) -> str:
    name = Path(urllib.parse.urlparse(info.installer_url).path).name
    return name or f"GameCenter-{info.version}-setup.exe"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_digest(info: UpdateInfo) -> str:
    value = (info.digest or "").strip()
    if value.lower().startswith("sha256:"):
        value = value[7:].strip()
    return value.lower() if len(value) == 64 else ""


def download_installer(
    info: UpdateInfo,
    destination: Path | None = None,
    progress=None,
    timeout: int = 30,
) -> Path:
    """Download the release installer, verify it and return its local path."""
    if not info.installer_url:
        raise UpdateError("This release doesn't include an installer.")

    target = (
        Path(destination)
        if destination is not None
        else download_dir() / installer_filename(info)
    )
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UpdateError("Couldn't prepare the update folder.") from exc

    expected_size = int(info.installer_size or 0)
    expected_digest = _expected_digest(info)

    if target.is_file():
        try:
            size_ok = not expected_size or target.stat().st_size == expected_size
            digest_ok = not expected_digest or _sha256(target) == expected_digest
            if size_ok and digest_ok:
                if progress:
                    size = target.stat().st_size
                    progress(size, size)
                return target
        except OSError:
            pass

    part = target.with_name(target.name + ".part")
    request = urllib.request.Request(
        info.installer_url, headers={"User-Agent": UA}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            header = response.headers.get("Content-Length") if response.headers else None
            total = int(header or expected_size or 0)
            downloaded = 0
            with part.open("wb") as handle:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total)

        if total and downloaded != total:
            raise UpdateError("The update download was incomplete.")
        if expected_digest and _sha256(part) != expected_digest:
            raise UpdateError("The update file failed its integrity check.")
        os.replace(part, target)
        return target
    except UpdateError:
        part.unlink(missing_ok=True)
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        part.unlink(missing_ok=True)
        raise UpdateError("Couldn't download the update.") from exc


def launch_installer(path: Path) -> None:
    """Start the downloaded installer silently. The caller quits afterwards."""
    if sys.platform != "win32":
        raise UpdateError("Automatic installation is only available on Windows.")
    installer = Path(path)
    if not installer.is_file():
        raise UpdateError("The downloaded installer is missing.")
    try:
        subprocess.Popen(
            [
                str(installer),
                "/SILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
            ],
            cwd=str(installer.parent),
            close_fds=True,
        )
    except OSError as exc:
        raise UpdateError("Couldn't start the installer.") from exc
