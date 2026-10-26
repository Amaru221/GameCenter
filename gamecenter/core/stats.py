"""Aggregate playtime history into the Statistics view model.

Everything is derived from ``playtime.all_history()`` (one entry per finished
session) joined with the current library for titles and store names. A session
is attributed to the local date on which it started.
"""

from __future__ import annotations

import calendar
import hashlib
import time
from datetime import date, datetime, timedelta

from . import i18n, playtime
from .models import Game

PALETTE = (
    "#4cc9f0",
    "#ff8c42",
    "#a78bfa",
    "#34d399",
    "#f472b6",
    "#facc15",
    "#60a5fa",
    "#fb7185",
)
OTHER_COLOR = "#64748b"
MONTH_KEYS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
PERIODS = ("week", "month", "year", "all")


def _catalog(language: str) -> dict[str, str]:
    return i18n.catalog(language)


def _month_name(catalog: dict[str, str], month: int) -> str:
    key = MONTH_KEYS[month - 1]
    return catalog.get(key, key)


def _short_month(name: str) -> str:
    return name[:3].capitalize()


def _duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes = rest // 60
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def _fill(template: str, *values) -> str:
    text = template
    for index, value in enumerate(values, 1):
        text = text.replace(f"%{index}", str(value))
    return text


def _color_for(game_id: str) -> str:
    digest = hashlib.sha1(game_id.encode("utf-8")).hexdigest()[:8]
    return PALETTE[int(digest, 16) % len(PALETTE)]


def _session_date(timestamp: int) -> date:
    return datetime.fromtimestamp(timestamp).date()


def _range(
    period: str, year: int, month: int, today: date
) -> tuple[date, date]:
    if period == "week":
        end = today if year == today.year else date(year, 12, 31)
        return end - timedelta(days=6), end

    if period == "month":
        if month >= 0:
            selected = month + 1
        elif year == today.year:
            selected = today.month
        else:
            selected = 12
        if year == today.year:
            selected = min(selected, today.month)
        start = date(year, selected, 1)
        last_day = calendar.monthrange(year, selected)[1]
        end = date(year, selected, last_day)
        if year == today.year and selected == today.month:
            end = today
        return start, end

    if period == "all":
        return date(2000, 1, 1), today

    return date(year, 1, 1), today if year == today.year else date(year, 12, 31)


def _previous_range(
    period: str, start: date, end: date
) -> tuple[date, date] | None:
    if period == "week":
        return start - timedelta(days=7), end - timedelta(days=7)
    if period == "month":
        if start.month == 1:
            previous = date(start.year - 1, 12, 1)
        else:
            previous = date(start.year, start.month - 1, 1)
        last_day = calendar.monthrange(previous.year, previous.month)[1]
        return previous, date(previous.year, previous.month, last_day)
    if period == "year":
        return date(start.year - 1, 1, 1), date(start.year - 1, 12, 31)
    return None


def _filter(sessions: list[dict], start: date, end: date) -> list[dict]:
    return [item for item in sessions if start <= item["date"] <= end]


def _longest_streak(days: set[date]) -> int:
    if not days:
        return 0
    ordered = sorted(days)
    best = current = 1
    for previous, current_day in zip(ordered, ordered[1:]):
        if current_day - previous == timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def _days_in_period(period: str, start: date, end: date, today: date) -> int:
    if period == "week":
        return 7
    if period == "month":
        if start.year == today.year and start.month == today.month:
            return today.day
        return calendar.monthrange(start.year, start.month)[1]
    if period == "year":
        if start.year == today.year:
            return (today - start).days + 1
        return (end - start).days + 1
    earliest = start
    if earliest <= today:
        return (today - earliest).days + 1
    return 1


def _all_sessions(games: list[Game]) -> list[dict]:
    library = {game.id: game for game in games}
    sessions: list[dict] = []
    for game_id, entries in playtime.all_history().items():
        game = library.get(game_id)
        for entry in entries:
            start = int(entry["start"])
            seconds = int(entry["seconds"])
            sessions.append(
                {
                    "game_id": game_id,
                    "title": game.title if game else (entry.get("title") or "Unknown game"),
                    "source": game.source if game else (entry.get("source") or ""),
                    "start": start,
                    "date": _session_date(start),
                    "seconds": seconds,
                }
            )
    return sessions


def _game_titles(sessions: list[dict], games: list[Game]) -> dict[str, str]:
    titles = {game.id: game.title for game in games}
    for session in sessions:
        titles.setdefault(session["game_id"], session["title"])
    return titles


def _top_games(
    sessions: list[dict],
    titles: dict[str, str],
    colors: dict[str, str],
    limit: int = 5,
) -> list[dict]:
    totals: dict[str, int] = {}
    for session in sessions:
        totals[session["game_id"]] = totals.get(session["game_id"], 0) + session["seconds"]
    if not totals:
        return []

    peak = max(totals.values()) or 1
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [
        {
            "gameId": game_id,
            "name": titles.get(game_id, "Unknown game"),
            "seconds": seconds,
            "hoursText": _duration(seconds),
            "percent": max(4, int(round(seconds / peak * 100))),
            "color": colors.get(game_id, _color_for(game_id)),
        }
        for game_id, seconds in ordered
    ]


def _months(
    year_sessions: list[dict],
    year: int,
    month_count: int,
    today: date,
    titles: dict[str, str],
    colors: dict[str, str],
    catalog: dict[str, str],
) -> list[dict]:
    months: list[dict] = []
    for month in range(1, month_count + 1):
        name = _month_name(catalog, month)
        days_in_month = calendar.monthrange(year, month)[1]
        current = [
            item
            for item in year_sessions
            if item["date"].month == month
        ]
        daily = [0] * days_in_month
        for session in current:
            daily[session["date"].day - 1] += session["seconds"]

        best_seconds = max(daily) if daily else 0
        best_index = daily.index(best_seconds) if best_seconds else -1
        best_date = date(year, month, best_index + 1) if best_index >= 0 else None
        best_timestamp = (
            int(datetime(best_date.year, best_date.month, best_date.day).timestamp())
            if best_date is not None
            else 0
        )
        total = sum(daily)
        played_days = len({item["date"] for item in current})
        session_count = len(current)

        months.append(
            {
                "monthIndex": month - 1,
                "number": f"{month:02d}",
                "name": name,
                "short": _short_month(name),
                "hoursText": _duration(total),
                "seconds": total,
                "daysPlayed": played_days,
                "bestDayText": _duration(best_seconds) if best_seconds else "—",
                "bestDayTimestamp": best_timestamp,
                "sessionsCount": session_count,
                "sessionsText": catalog.get("1 session", "1 session")
                if session_count == 1
                else _fill(catalog.get("%1 sessions", "%1 sessions"), session_count),
                "topGames": _top_games(current, titles, colors),
                "daily": daily,
                "maxDaily": max(1, best_seconds),
            }
        )
    return months


def _river(
    year_sessions: list[dict],
    year_totals: dict[str, int],
    titles: dict[str, str],
    colors: dict[str, str],
    month_count: int,
    catalog: dict[str, str],
) -> dict:
    months = [
        _short_month(_month_name(catalog, month))
        for month in range(1, month_count + 1)
    ]
    if not year_totals:
        return {"months": months, "layers": []}

    ordered = sorted(year_totals.items(), key=lambda item: (-item[1], item[0]))
    top = ordered[:4]
    used = {game_id for game_id, _seconds in top}
    layers: list[dict] = []

    for game_id, total in top:
        values = [0] * month_count
        for session in year_sessions:
            if session["game_id"] == game_id:
                values[session["date"].month - 1] += session["seconds"]
        layers.append(
            {
                "name": titles.get(game_id, "Unknown game"),
                "color": colors.get(game_id, _color_for(game_id)),
                "values": values,
                "totalSeconds": total,
            }
        )

    other_values = [0] * month_count
    other_total = 0
    for session in year_sessions:
        if session["game_id"] in used:
            continue
        other_values[session["date"].month - 1] += session["seconds"]
        other_total += session["seconds"]
    if other_total:
        layers.append(
            {
                "name": catalog.get("Other", "Other"),
                "color": OTHER_COLOR,
                "values": other_values,
                "totalSeconds": other_total,
            }
        )

    return {"months": months, "layers": layers}


def build(
    games: list[Game],
    period: str = "year",
    year: int | None = None,
    language: str = "en",
    month: int = -1,
    now: float | None = None,
) -> dict:
    timestamp = time.time() if now is None else now
    today = datetime.fromtimestamp(timestamp).date()
    if period not in PERIODS:
        period = "year"
    if year is None:
        year = today.year
    year = min(max(int(year), 2000), today.year)

    catalog = _catalog(language)
    sessions = _all_sessions(games)
    if period == "all" and sessions:
        start = min(item["date"] for item in sessions)
    else:
        start, end = _range(period, year, month, today)
    if period == "all":
        end = today
    period_sessions = _filter(sessions, start, end)
    total = sum(item["seconds"] for item in period_sessions)

    previous = _previous_range(period, start, end)
    previous_total = (
        sum(item["seconds"] for item in _filter(sessions, *previous))
        if previous is not None
        else 0
    )
    if period == "all" or previous_total <= 0:
        change_text = ""
    else:
        percent = int(round((total - previous_total) / previous_total * 100))
        if period == "year":
            label = str(previous[0].year)
        elif period == "week":
            label = catalog.get("previous week", "previous week")
        else:
            previous_name = _month_name(catalog, previous[0].month)
            label = f"{previous_name} {previous[0].year}"
        change_text = catalog.get(
            "{change}% vs {label}", "{change}% vs {label}"
        ).format(change=f"{percent:+d}", label=label)

    played_days = {item["date"] for item in period_sessions}
    streak = _longest_streak(played_days)
    days_total = _days_in_period(period, start, end, today)
    session_count = len(period_sessions)

    if session_count == 1:
        sessions_text = catalog.get("1 session", "1 session")
    else:
        sessions_text = _fill(
            catalog.get("%1 sessions", "%1 sessions"), session_count
        )

    days_text = (
        _fill(
            catalog.get("%1 of %2 days", "%1 of %2 days"),
            len(played_days),
            days_total,
        )
        if session_count
        else ""
    )
    streak_text = (
        _fill(catalog.get("%1-day streak", "%1-day streak"), streak)
        if session_count
        else ""
    )

    if period == "year":
        period_label = str(year)
    elif period == "week":
        period_label = catalog.get("This week", "This week")
    elif period == "month":
        period_label = f"{_month_name(catalog, start.month)} {start.year}"
    else:
        period_label = catalog.get("All time", "All time")

    year_sessions = [item for item in sessions if item["date"].year == year]
    year_totals: dict[str, int] = {}
    for session in year_sessions:
        year_totals[session["game_id"]] = (
            year_totals.get(session["game_id"], 0) + session["seconds"]
        )
    titles = _game_titles(sessions, games)
    ordered_ids = sorted(year_totals, key=lambda key: (-year_totals[key], key))
    colors = {
        game_id: PALETTE[index % len(PALETTE)]
        for index, game_id in enumerate(ordered_ids)
    }
    for game in games:
        colors.setdefault(game.id, _color_for(game.id))

    month_count = today.month if year == today.year else 12
    if year > today.year:
        month_count = 0
    months = _months(
        year_sessions, year, month_count, today, titles, colors, catalog
    )
    river = _river(
        year_sessions, year_totals, titles, colors, month_count, catalog
    )

    return {
        "period": period,
        "year": year,
        "month": month,
        "periodLabel": period_label,
        "timeText": _duration(total),
        "seconds": total,
        "changeText": change_text,
        "daysText": days_text,
        "daysPlayed": len(played_days),
        "daysTotal": days_total,
        "streakText": streak_text,
        "streak": streak,
        "sessionsText": sessions_text,
        "sessionsCount": session_count,
        "hasData": session_count > 0,
        "months": months,
        "river": river,
    }
