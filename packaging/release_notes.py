"""Build the GitHub release body from CHANGELOG.md.

GitHub's automatic notes only produce "Full Changelog" when a repository does
not use pull requests. GameCenter publishes the matching CHANGELOG section
instead, followed by the asset list (with SHA-256), the license and a link to
the exact source tag.

The CI workflow calls this before ``softprops/action-gh-release`` and passes the
generated file through ``body_path``. A missing CHANGELOG section is a hard
error on purpose: a release must never be published with only the comparison
link.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
REPO = "Amaru221/GameCenter"

# Matches "## v0.21.0", "## 0.21.0" and "## [0.21.0] - 2026-10-30".
_HEADING = re.compile(
    r"^##\s+\[?v?([^\]\s]+)\]?(?:\s*-\s*(\d{4}-\d{2}-\d{2}))?\s*$"
)


def clean_version(value: str) -> str:
    return str(value or "").strip().lstrip("vV")


def tag_for(version: str) -> str:
    cleaned = clean_version(version)
    return f"v{cleaned}" if cleaned else ""


def extract_section(text: str, version: str, release_date: str) -> str:
    """Return the CHANGELOG block for *version* with a dated heading."""
    wanted = clean_version(version)
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        match = _HEADING.match(line.strip())
        if match and clean_version(match.group(1)) == wanted:
            start = index
            break
    if start is None:
        raise ValueError(f"CHANGELOG.md has no section for {version!r}")

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    body = "\n".join(lines[start:end]).strip().splitlines()
    body[0] = f"## [{wanted}] - {release_date}"
    return "\n".join(body).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_body(
    section: str,
    version: str,
    release_date: str,
    installer: Path | None,
) -> str:
    tag = tag_for(version)
    parts = [section, "", "## Assets", ""]

    if installer is not None and installer.is_file():
        digest = sha256(installer)
        parts.append(
            f"- **{installer.name}** - recommended Windows installer "
            "(per-user; Start Menu and desktop shortcuts, uninstaller)."
        )
        parts.append(f"- SHA-256: `{digest}`")
        installer.with_name(installer.name + ".sha256").write_text(
            f"{digest}  {installer.name}\n", encoding="utf-8"
        )
    else:
        parts.append(
            "- Windows installer "
            f"(`GameCenter-{clean_version(version)}-windows-setup.exe`)."
        )
        parts.append("- SHA-256 checksum next to the installer.")

    parts.extend(
        [
            "",
            "## License and source",
            "",
            "GameCenter is licensed under **MIT**.",
            f"Source code for this release: https://github.com/{REPO}/tree/{tag}",
            "Third-party notices: "
            f"https://github.com/{REPO}/blob/{tag}/THIRD_PARTY_NOTICES.md",
            "This CI build is unsigned, so Windows SmartScreen may warn on "
            "first run.",
            "",
        ]
    )
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="tag or version, e.g. v0.21.0")
    parser.add_argument(
        "--changelog", type=Path, default=CHANGELOG, help="CHANGELOG.md path"
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="release date in YYYY-MM-DD (defaults to today)",
    )
    parser.add_argument(
        "--installer",
        type=Path,
        help="built installer; its SHA-256 is embedded and written next to it",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "release_notes.md",
        help="where to write the markdown body",
    )
    args = parser.parse_args(argv)

    try:
        text = args.changelog.read_text(encoding="utf-8")
        section = extract_section(text, args.version, args.date)
    except (OSError, ValueError) as exc:
        print(f"release notes: {exc}", file=sys.stderr)
        return 1

    body = build_body(section, args.version, args.date, args.installer)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    except OSError as exc:
        print(f"release notes: couldn't write {args.output}: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
