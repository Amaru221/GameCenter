"""Shared test isolation for user-level GameCenter data."""

import pytest

from gamecenter.core import profiles


@pytest.fixture(autouse=True)
def isolate_profiles(monkeypatch, tmp_path):
    """Never read or write the developer's real profiles during tests."""
    monkeypatch.setattr(profiles, "path", lambda: tmp_path / "profiles.json")
    monkeypatch.setattr(
        profiles, "cover_dir", lambda: tmp_path / "recap_covers"
    )
