"""GameCenter-owned profiles: score, status and merge traceability."""

import pytest

from gamecenter.core import profiles


@pytest.fixture(autouse=True)
def isolated_profiles(monkeypatch, tmp_path):
    monkeypatch.setattr(profiles, "path", lambda: tmp_path / "profiles.json")
    monkeypatch.setattr(
        profiles, "cover_dir", lambda: tmp_path / "recap_covers"
    )


def test_rating_is_clamped_and_can_be_cleared() -> None:
    profiles.set_rating("epic:1", 87)
    assert profiles.get("epic:1")["rating"] == 87

    profiles.set_rating("epic:1", 140)
    assert profiles.get("epic:1")["rating"] == 100

    profiles.set_rating("epic:1", -5)
    assert profiles.get("epic:1")["rating"] == 0

    profiles.set_rating("epic:1", None)
    assert profiles.get("epic:1")["rating"] is None


def test_status_is_validated() -> None:
    profiles.set_status("steam:2", "playing")
    assert profiles.get("steam:2")["status"] == "playing"

    profiles.set_status("steam:2", "ONGOING")
    assert profiles.get("steam:2")["status"] == "ongoing"

    profiles.set_status("steam:2", "unknown")
    assert profiles.get("steam:2")["status"] == "ongoing"

    profiles.set_status("steam:2", "")
    assert profiles.get("steam:2")["status"] == ""


def test_merged_sources_are_upserted_newest_first() -> None:
    first = {"id": "steam:1", "title": "Old", "cover_path": "a.png"}
    second = {"id": "gog:2", "title": "Other", "cover_path": "b.png"}

    profiles.add_merged_source("epic:3", first)
    profiles.add_merged_source("epic:3", second)
    profiles.add_merged_source(
        "epic:3", {**first, "title": "Old updated", "cover_path": "c.png"}
    )

    sources = profiles.get("epic:3")["merged_sources"]
    assert [item["id"] for item in sources] == ["steam:1", "gog:2"]
    assert sources[0]["title"] == "Old updated"
    assert sources[0]["cover_path"] == "c.png"


def test_mark_merged_and_extra_layers() -> None:
    profiles.add_extra("steam:2", 3600, 2, 1_700_000_100)
    profiles.add_extra("steam:2", 1800, 1, 1_700_000_200)

    assert profiles.extra_seconds("steam:2") == 5400
    assert profiles.extra_sessions("steam:2") == 3
    assert profiles.extra_last_played("steam:2") == 1_700_000_200

    profiles.mark_merged(
        "steam:1",
        "epic:3",
        "New game",
        seconds=7200,
        sessions=4,
        cover="cover.png",
        at=1_700_000_000,
    )
    profiles.mark_merged(
        "steam:2",
        "epic:3",
        "New game",
        seconds=5400,
        sessions=3,
        cover="cover2.png",
        at=1_700_000_300,
    )

    entry = profiles.get("steam:1")
    assert entry["merged_into"] == "epic:3"
    assert entry["merged_into_title"] == "New game"
    assert entry["merged_seconds"] == 7200
    assert profiles.merged_seconds("steam:1") == 7200
    assert profiles.extra_seconds("steam:2") == 0
