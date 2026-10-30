"""Release notes must carry the real CHANGELOG changes, not just a diff link."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "release_notes", ROOT / "packaging" / "release_notes.py"
)
assert _SPEC and _SPEC.loader
release_notes = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(release_notes)

CHANGELOG = """# Changelog

## v0.21.0

### Added

- Something new.

### Changed

- Something different.

## v0.20.2

- Old change.
"""


def test_extract_section_stops_at_the_next_version() -> None:
    section = release_notes.extract_section(CHANGELOG, "v0.21.0", "2026-10-30")

    assert section.startswith("## [0.21.0] - 2026-10-30")
    assert "Something new." in section
    assert "Something different." in section
    assert "Old change." not in section


def test_extract_section_accepts_versions_without_prefix() -> None:
    section = release_notes.extract_section(CHANGELOG, "0.21.0", "2026-10-30")

    assert section.startswith("## [0.21.0] - 2026-10-30")


def test_extract_section_fails_loudly_when_missing() -> None:
    with pytest.raises(ValueError):
        release_notes.extract_section(CHANGELOG, "v9.9.9", "2026-10-30")


def test_body_lists_installer_checksum_license_and_source(tmp_path) -> None:
    installer = tmp_path / "GameCenter-0.21.0-windows-setup.exe"
    installer.write_bytes(b"installer-bytes")
    section = release_notes.extract_section(CHANGELOG, "v0.21.0", "2026-10-30")

    body = release_notes.build_body(
        section, "v0.21.0", "2026-10-30", installer
    )

    digest = release_notes.sha256(installer)
    assert installer.name in body
    assert f"SHA-256: `{digest}`" in body
    assert "## License and source" in body
    assert f"https://github.com/{release_notes.REPO}/tree/v0.21.0" in body
    assert (tmp_path / (installer.name + ".sha256")).read_text(
        encoding="utf-8"
    ) == f"{digest}  {installer.name}\n"
