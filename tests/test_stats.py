"""Aggregated statistics for the Statistics view."""

from datetime import datetime

import pytest

from gamecenter.core import playtime, stats
from gamecenter.core.models import Game


@pytest.fixture(autouse=True)
def isolated_history(monkeypatch, tmp_path):
    monkeypatch.setattr(
        playtime, "history_path", lambda: tmp_path / "history.json"
    )


def _ts(year: int, month: int, day: int, hour: int = 12) -> int:
    return int(datetime(year, month, day, hour).timestamp())


@pytest.fixture
def library() -> list[Game]:
    return [
        Game(id="steam:a", title="Alpha", source="steam", app_id="1"),
        Game(id="epic:b", title="Beta", source="epic", app_id="b"),
    ]


@pytest.fixture
def sessions(library):
    alpha, beta = library
    playtime.record_session(alpha, _ts(2025, 12, 31), 1800)
    playtime.record_session(alpha, _ts(2026, 1, 5), 3600)
    playtime.record_session(alpha, _ts(2026, 1, 6), 1800)
    playtime.record_session(alpha, _ts(2026, 2, 10), 7200)
    playtime.record_session(alpha, _ts(2026, 10, 26), 5400)
    playtime.record_session(beta, _ts(2026, 10, 26), 3600)


NOW = datetime(2026, 10, 26, 18, 0).timestamp()


def test_year_summary(library, sessions) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)

    assert data["timeText"] == "6h 00m"
    assert data["seconds"] == 21600
    assert data["sessionsCount"] == 5
    assert data["daysPlayed"] == 4
    assert data["daysTotal"] == 299
    assert data["daysText"] == "4 of 299 days"
    assert data["streak"] == 2
    assert data["streakText"] == "2-day streak"
    assert data["changeText"].endswith("vs 2025")
    assert data["periodLabel"] == "2026"


def test_month_cards(library, sessions) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)
    months = data["months"]

    assert len(months) == 10
    january = months[0]
    assert january["name"] == "January"
    assert january["number"] == "01"
    assert january["hoursText"] == "1h 30m"
    assert january["daysPlayed"] == 2
    assert january["sessionsCount"] == 2
    assert january["bestDayText"] == "1h 00m"
    assert january["topGames"][0]["name"] == "Alpha"
    assert len(january["daily"]) == 31

    october = months[9]
    assert october["hoursText"] == "2h 30m"
    assert [item["name"] for item in october["topGames"]] == ["Alpha", "Beta"]


def test_month_period_uses_the_selected_month(library, sessions) -> None:
    data = stats.build(
        library, period="month", year=2026, month=0, now=NOW
    )

    assert data["periodLabel"] == "January 2026"
    assert data["timeText"] == "1h 30m"
    assert data["sessionsCount"] == 2


def test_all_time_starts_at_the_earliest_session(library, sessions) -> None:
    data = stats.build(library, period="all", year=2026, now=NOW)

    assert data["timeText"] == "6h 30m"
    assert data["daysTotal"] == 300
    assert data["changeText"] == ""


def test_river_layer_values(library, sessions) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)
    river = data["river"]

    assert len(river["months"]) == 10
    names = [layer["name"] for layer in river["layers"]]
    assert "Alpha" in names
    alpha = next(layer for layer in river["layers"] if layer["name"] == "Alpha")
    assert alpha["values"][0] == 5400  # January
    assert alpha["values"][9] == 5400  # October
    assert all(layer["color"].startswith("#") for layer in river["layers"])


def test_months_are_localised(library, sessions) -> None:
    data = stats.build(
        library, period="year", year=2026, language="es", now=NOW
    )

    assert data["months"][0]["name"] == "Enero"
    assert data["months"][0]["short"] == "Ene"
    assert data["daysText"].endswith("días")


def test_empty_year(library) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)

    assert data["timeText"] == "0m"
    assert data["hasData"] is False
    assert data["months"]
    assert data["river"]["layers"] == []
