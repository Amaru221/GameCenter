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


def test_month_covers_and_year_highlights(library, sessions) -> None:
    covers = {
        "steam:a": "image://cover/alpha",
        "epic:b": "image://cover/beta",
    }
    data = stats.build(
        library, period="year", year=2026, now=NOW, covers=covers
    )
    months = data["months"]
    january = months[0]
    february = months[1]
    october = months[9]

    # January leads sessions (tied with October) and days played.
    assert january["topSessions"] is True
    assert january["topDays"] is True
    assert january["topHours"] is False
    # February is a shorter month.
    assert february["topHours"] is False
    # October leads hours and ties January on sessions.
    assert october["topHours"] is True
    assert october["topSessions"] is True
    assert october["topDays"] is False

    assert january["mostPlayed"]["name"] == "Alpha"
    assert january["mostPlayedCover"] == "image://cover/alpha"
    assert january["topGames"][0]["cover"] == "image://cover/alpha"


def test_months_without_data_have_no_highlights(library) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)
    assert all(
        not month["topHours"]
        and not month["topSessions"]
        and not month["topDays"]
        for month in data["months"]
    )
    assert data["months"][0]["mostPlayed"] == {}


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


def test_week_period_uses_day_buckets(library, sessions) -> None:
    data = stats.build(library, period="week", year=2026, now=NOW)

    assert data["bucketsKind"] == "day"
    assert len(data["buckets"]) == 7
    assert all(item["kind"] == "day" for item in data["buckets"])
    assert data["buckets"][-1]["number"] == "26"
    assert data["buckets"][-1]["sessionsCount"] == 2
    assert data["buckets"][-1]["hoursText"] == "2h 30m"
    assert data["buckets"][-1]["topDays"] is False
    assert data["topGame"]["name"] == "Alpha"
    assert len(data["river"]["labels"]) == 7
    assert sum(item["seconds"] for item in data["buckets"]) == data["seconds"]


def test_month_period_uses_week_buckets(library, sessions) -> None:
    data = stats.build(
        library, period="month", year=2026, month=9, now=NOW
    )

    assert data["bucketsKind"] == "week"
    assert data["buckets"]
    assert all(item["kind"] == "week" for item in data["buckets"])
    assert data["buckets"][0]["number"] == "W1"
    assert sum(item["seconds"] for item in data["buckets"]) == data["seconds"]
    assert len(data["river"]["labels"]) == len(data["buckets"])


def test_top_three_and_other_games(monkeypatch, tmp_path) -> None:
    games = [
        Game(id=f"steam:{index}", title=f"Game {index}", source="steam")
        for index in range(5)
    ]
    stamp = _ts(2026, 10, 20)
    for index, game in enumerate(games):
        playtime.record_session(game, stamp, 3600 * (index + 1))

    covers = {game.id: f"image://cover/{index}" for index, game in enumerate(games)}
    data = stats.build(
        games, period="year", year=2026, now=NOW, covers=covers
    )
    october = data["buckets"][9]

    assert [item["name"] for item in october["topGames"]] == [
        "Game 4",
        "Game 3",
        "Game 2",
    ]
    assert october["hasOtherGames"] is True
    assert october["otherHoursText"] == "3h 00m"
    assert october["topGames"][0]["cover"] == "image://cover/4"


def test_card_banners_highlight_one_unique_stat(library, sessions) -> None:
    data = stats.build(library, period="year", year=2026, now=NOW)
    october = data["buckets"][9]
    january = data["buckets"][0]
    february = data["buckets"][1]

    assert october["banner"]["label"] == "Busiest month"
    assert october["banner"]["value"] == october["hoursText"]
    assert october["banner"]["detail"] == "2026"
    assert january["banner"]["label"] == "Longest streak"
    assert january["banner"]["value"] == "2 days"
    assert february["banner"]["label"] == "Best day"


def test_year_review_payload(library, sessions) -> None:
    data = stats.year_review(library, 2026, now=NOW)

    assert data["year"] == 2026
    assert data["hasData"] is True
    assert data["sessionsCount"] == 5
    assert data["totalGames"] == 2
    assert data["activeMonthCount"] == 3
    assert data["topGame"]["name"] == "Alpha"
    assert data["topGame"]["sessionsCount"] == 4
    assert data["topGame"]["percentOfYear"] == 83
    assert data["bestDay"]["dateText"] == "26/10"
    assert data["bestDay"]["dayNumber"] == 26
    assert data["bestDay"]["topGame"]["name"] == "Alpha"
    assert data["longestStreak"]["days"] == 2
    assert data["longestStreak"]["rangeText"] == "05/01 - 06/01"
    assert data["busiestMonth"]["name"] == "October"
    assert data["mostSessionsMonth"]["name"] == "October"
    assert data["mostDaysMonth"]["name"] == "January"
    assert data["averageSessionText"] == "1h 12m"
    assert len(data["monthLabels"]) == 10
    assert len(data["monthSessions"]) == 10
    assert [item["name"] for item in data["topGames"]] == ["Alpha", "Beta"]
    assert [slide["type"] for slide in data["slides"]] == [
        "intro",
        "month",
        "month",
        "month",
        "topGame",
        "sessions",
        "streak",
        "bestDay",
        "busiest",
        "outro",
    ]


def test_year_review_without_data(library) -> None:
    data = stats.year_review(library, 2026, now=NOW)

    assert data["hasData"] is False
    assert data["activeMonths"] == []
    assert data["topGame"] == {}
    assert data["bestDay"] == {}
    assert data["longestStreak"] == {}
    assert data["slides"] == []
