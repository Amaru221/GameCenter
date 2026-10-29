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
WEEKDAY_KEYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
PERIODS = ("week", "month", "year", "all")


def _catalog(language: str) -> dict[str, str]:
    return i18n.catalog(language)


def _month_name(catalog: dict[str, str], month: int) -> str:
    key = MONTH_KEYS[month - 1]
    return catalog.get(key, key)


def _short_month(name: str) -> str:
    return name[:3].capitalize()


def _weekday_name(catalog: dict[str, str], day: date) -> str:
    key = WEEKDAY_KEYS[day.weekday()]
    return catalog.get(key, key)


def _short_weekday(name: str) -> str:
    return name[:3].capitalize()


def _duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes = rest // 60
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def _duration_detail(seconds: int) -> str:
    """Like _duration, but keeps seconds for sub-hour values."""
    seconds = max(0, int(seconds))
    if seconds <= 0:
        return "0m"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s" if secs else f"{minutes}m"
    return f"{secs}s"


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


def _longest_streak_range(
    days: set[date],
) -> tuple[int, date | None, date | None]:
    if not days:
        return 0, None, None
    ordered = sorted(days)
    best = current = 1
    best_start = best_end = ordered[0]
    current_start = ordered[0]
    for previous, current_day in zip(ordered, ordered[1:]):
        if current_day - previous == timedelta(days=1):
            current += 1
        else:
            current_start = current_day
            current = 1
        if current > best:
            best = current
            best_start = current_start
            best_end = current_day
    return best, best_start, best_end


def _sessions_text(catalog: dict[str, str], count: int) -> str:
    if count == 1:
        return catalog.get("1 session", "1 session")
    return _fill(catalog.get("%1 sessions", "%1 sessions"), count)


def _longest_session(sessions: list[dict]) -> dict:
    if not sessions:
        return {}
    item = max(sessions, key=lambda entry: (entry["seconds"], entry["start"]))
    day = item["date"]
    return {
        "seconds": int(item["seconds"]),
        "text": _duration_detail(item["seconds"]),
        "dateText": f"{day.day:02d}/{day.month:02d}",
        "timestamp": int(item["start"]),
        "game": item.get("title") or "",
        "gameId": item.get("game_id") or "",
    }


def _busiest_day(sessions: list[dict]) -> dict:
    """The day with the most sessions (ties: more time, then earlier date)."""
    if not sessions:
        return {}
    counts: dict[date, int] = {}
    totals: dict[date, int] = {}
    for item in sessions:
        day = item["date"]
        counts[day] = counts.get(day, 0) + 1
        totals[day] = totals.get(day, 0) + item["seconds"]
    best = max(
        counts,
        key=lambda day: (counts[day], totals[day], -day.toordinal()),
    )
    return {
        "dateText": f"{best.day:02d}/{best.month:02d}",
        "timestamp": int(datetime(best.year, best.month, best.day).timestamp()),
        "sessions": counts[best],
        "seconds": totals[best],
    }


def _busiest_month(sessions: list[dict]) -> dict:
    """The calendar month with the most sessions (ties: more time)."""
    if not sessions:
        return {}
    counts: dict[int, int] = {}
    totals: dict[int, int] = {}
    for item in sessions:
        month = item["date"].month
        counts[month] = counts.get(month, 0) + 1
        totals[month] = totals.get(month, 0) + item["seconds"]
    best = max(counts, key=lambda month: (counts[month], totals[month], -month))
    return {
        "monthIndex": best - 1,
        "sessions": counts[best],
        "seconds": totals[best],
    }


def _favorite_weekday(sessions: list[dict], catalog: dict[str, str]) -> dict:
    if not sessions:
        return {}
    counts: dict[int, int] = {}
    for item in sessions:
        weekday = item["date"].weekday()
        counts[weekday] = counts.get(weekday, 0) + 1
    best = max(counts, key=lambda weekday: (counts[weekday], -weekday))
    name = catalog.get(WEEKDAY_KEYS[best], WEEKDAY_KEYS[best])
    return {"name": name, "sessions": counts[best]}


def _highlight(label: str, value: str, detail: str = "", tint: str = "#facc15") -> dict:
    return {"label": label, "value": value, "detail": detail, "tint": tint}


def _bucket_highlights(
    kind: str,
    longest: dict,
    busiest: dict,
    average: int,
    games_count: int,
    session_count: int,
    catalog: dict[str, str],
) -> list[dict]:
    """Three contextual highlights for a day, week or month card."""
    if not session_count:
        return []
    highlights: list[dict] = []
    if longest:
        detail = longest.get("game") if kind == "day" else longest.get("dateText")
        highlights.append(
            _highlight(
                catalog.get("Longest session", "Longest session"),
                longest.get("text", ""),
                detail or "",
                "#4cc9f0",
            )
        )
    if kind in ("month", "week") and busiest.get("sessions", 0) > 1:
        highlights.append(
            _highlight(
                catalog.get("Busiest day", "Busiest day"),
                busiest.get("dateText", ""),
                _sessions_text(catalog, busiest["sessions"]),
                "#fb7185",
            )
        )
    highlights.append(
        _highlight(
            catalog.get("Average session", "Average session"),
            _duration_detail(average),
            "",
            "#a78bfa",
        )
    )
    if kind == "day" and games_count > 1:
        highlights.append(
            _highlight(
                catalog.get("Games played", "Games played"),
                str(games_count),
                "",
                "#34d399",
            )
        )
    return highlights[:3]


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
    covers: dict[str, str] | None = None,
    limit: int = 5,
) -> list[dict]:
    totals: dict[str, int] = {}
    for session in sessions:
        totals[session["game_id"]] = totals.get(session["game_id"], 0) + session["seconds"]
    if not totals:
        return []

    covers = covers or {}
    peak = max(totals.values()) or 1
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [
        {
            "gameId": game_id,
            "name": titles.get(game_id, "Unknown game"),
            "seconds": seconds,
            "hoursText": _duration_detail(seconds),
            "percent": max(4, int(round(seconds / peak * 100))),
            "color": colors.get(game_id, _color_for(game_id)),
            "cover": covers.get(game_id, ""),
        }
        for game_id, seconds in ordered
    ]


def _bucket_payload(
    current: list[dict],
    dates: list[date],
    daily: list[int],
    *,
    number: str,
    name: str,
    short: str,
    range_text: str,
    river_label: str,
    kind: str,
    month_index: int,
    catalog: dict[str, str],
    titles: dict[str, str],
    colors: dict[str, str],
    covers: dict[str, str],
) -> dict:
    """Build one generic card: a month, a week or a day."""
    total = sum(daily)
    best_seconds = max(daily) if daily else 0
    best_index = daily.index(best_seconds) if best_seconds else -1
    best_date = (
        dates[best_index]
        if 0 <= best_index < len(dates) and best_seconds
        else None
    )
    best_timestamp = (
        int(datetime(best_date.year, best_date.month, best_date.day).timestamp())
        if best_date is not None
        else 0
    )
    played_days = len({item["date"] for item in current})
    session_count = len(current)
    top_games = _top_games(current, titles, colors, covers, limit=3)
    shown_seconds = sum(item["seconds"] for item in top_games)
    other_seconds = max(0, total - shown_seconds)
    most_played = top_games[0] if top_games else {}
    streak = _longest_streak({item["date"] for item in current})

    longest = _longest_session(current)
    busiest = _busiest_day(current)
    average = int(total / session_count) if session_count else 0
    games_count = len({item["game_id"] for item in current})
    highlights = _bucket_highlights(
        kind, longest, busiest, average, games_count, session_count, catalog
    )

    if session_count == 1:
        sessions_text = catalog.get("1 session", "1 session")
    else:
        sessions_text = _fill(
            catalog.get("%1 sessions", "%1 sessions"), session_count
        )

    return {
        "bucketIndex": month_index,
        "monthIndex": month_index,
        "kind": kind,
        "number": number,
        "name": name,
        "short": short,
        "rangeText": range_text,
        "riverLabel": river_label,
        "hoursText": _duration_detail(total),
        "seconds": total,
        "daysPlayed": played_days,
        "daysInBucket": len(dates),
        "bestDayText": _duration_detail(best_seconds) if best_seconds else "—",
        "bestDayTimestamp": best_timestamp,
        "bestDayDateText": (
            f"{best_date.day:02d}/{best_date.month:02d}"
            if best_date is not None
            else ""
        ),
        "sessionsCount": session_count,
        "sessionsText": sessions_text,
        "streak": streak,
        "topGames": top_games,
        "mostPlayed": most_played,
        "mostPlayedCover": most_played.get("cover", ""),
        "mostPlayedName": most_played.get("name", ""),
        "mostPlayedHours": most_played.get("hoursText", ""),
        "otherGamesText": catalog.get("Other games", "Other games"),
        "otherHoursText": _duration_detail(other_seconds) if other_seconds else "",
        "hasOtherGames": other_seconds > 0,
        "longestSessionText": longest.get("text", ""),
        "longestSessionDateText": longest.get("dateText", ""),
        "longestSessionTimestamp": longest.get("timestamp", 0),
        "longestSessionGame": longest.get("game", ""),
        "busiestDayDateText": busiest.get("dateText", ""),
        "busiestDaySessions": busiest.get("sessions", 0),
        "busiestDaySessionsText": (
            _sessions_text(catalog, busiest["sessions"])
            if busiest.get("sessions")
            else ""
        ),
        "averageSessionText": _duration_detail(average) if session_count else "",
        "gamesCount": games_count,
        "highlights": highlights,
        "daily": daily,
        "maxDaily": max(1, best_seconds),
    }


def _bucket_banner(
    item: dict, catalog: dict[str, str], period_label: str
) -> dict:
    """One unique highlight per card, chosen by priority."""
    if not item.get("sessionsCount"):
        return {}
    kind = item.get("kind", "month")
    busiest_key = {
        "day": "Busiest day",
        "week": "Busiest week",
        "month": "Busiest month",
    }.get(kind, "Busiest month")

    if item.get("topHours"):
        return {
            "label": catalog.get(busiest_key, busiest_key),
            "value": item.get("hoursText", ""),
            "detail": period_label,
            "tint": "#facc15",
        }
    if item.get("streak", 0) >= 2:
        value = _fill(catalog.get("%1 days", "%1 days"), item["streak"])
        return {
            "label": catalog.get("Longest streak", "Longest streak"),
            "value": value,
            "detail": "",
            "tint": "#60a5fa",
        }
    if item.get("bestDayText") and item["bestDayText"] != "—":
        return {
            "label": catalog.get("Playtime", "Playtime"),
            "value": item["bestDayText"],
            "detail": item.get("bestDayDateText", ""),
            "tint": "#fb7185",
        }
    return {}


def _annotate_buckets(
    buckets: list[dict], catalog: dict[str, str], period_label: str
) -> list[dict]:
    max_hours = max((item["seconds"] for item in buckets), default=0)
    max_sessions = max((item["sessionsCount"] for item in buckets), default=0)
    max_days = max((item["daysPlayed"] for item in buckets), default=0)
    for item in buckets:
        item["topHours"] = max_hours > 0 and item["seconds"] == max_hours
        item["topSessions"] = max_sessions > 1 and item["sessionsCount"] == max_sessions
        item["topDays"] = max_days > 1 and item["daysPlayed"] == max_days
        item["banner"] = _bucket_banner(item, catalog, period_label)
    return buckets


def _months(
    year_sessions: list[dict],
    year: int,
    month_count: int,
    titles: dict[str, str],
    colors: dict[str, str],
    catalog: dict[str, str],
    covers: dict[str, str] | None = None,
) -> tuple[list[dict], list[list[dict]]]:
    covers = covers or {}
    months: list[dict] = []
    bucket_sessions: list[list[dict]] = []
    for month in range(1, month_count + 1):
        name = _month_name(catalog, month)
        days_in_month = calendar.monthrange(year, month)[1]
        current = [
            item
            for item in year_sessions
            if item["date"].month == month
        ]
        dates = [date(year, month, day) for day in range(1, days_in_month + 1)]
        daily = [0] * days_in_month
        for session in current:
            daily[session["date"].day - 1] += session["seconds"]

        months.append(
            _bucket_payload(
                current,
                dates,
                daily,
                number=f"{month:02d}",
                name=name,
                short=_short_month(name),
                range_text="",
                river_label=_short_month(name),
                kind="month",
                month_index=month - 1,
                catalog=catalog,
                titles=titles,
                colors=colors,
                covers=covers,
            )
        )
        bucket_sessions.append(current)

    _annotate_buckets(months, catalog, str(year))
    return months, bucket_sessions


def _day_buckets(
    period_sessions: list[dict],
    start: date,
    end: date,
    catalog: dict[str, str],
    titles: dict[str, str],
    colors: dict[str, str],
    covers: dict[str, str],
    period_label: str,
) -> tuple[list[dict], list[list[dict]]]:
    buckets: list[dict] = []
    bucket_sessions: list[list[dict]] = []
    day = start
    while day <= end:
        current = [item for item in period_sessions if item["date"] == day]
        total = sum(item["seconds"] for item in current)
        weekday = _weekday_name(catalog, day)
        short = _short_weekday(weekday)
        buckets.append(
            _bucket_payload(
                current,
                [day],
                [total],
                number=f"{day.day:02d}",
                name=weekday,
                short=short,
                range_text=f"{day.day:02d}/{day.month:02d}",
                river_label=f"{short} {day.day}",
                kind="day",
                month_index=day.month - 1,
                catalog=catalog,
                titles=titles,
                colors=colors,
                covers=covers,
            )
        )
        bucket_sessions.append(current)
        day += timedelta(days=1)

    _annotate_buckets(buckets, catalog, period_label)
    return buckets, bucket_sessions


def _week_buckets(
    period_sessions: list[dict],
    start: date,
    end: date,
    catalog: dict[str, str],
    titles: dict[str, str],
    colors: dict[str, str],
    covers: dict[str, str],
    period_label: str,
) -> tuple[list[dict], list[list[dict]]]:
    buckets: list[dict] = []
    bucket_sessions: list[list[dict]] = []
    month_short = _short_month(_month_name(catalog, start.month))
    cursor = start
    index = 1
    while cursor <= end:
        bucket_end = min(end, cursor + timedelta(days=6 - cursor.weekday()))
        dates: list[date] = []
        day = cursor
        while day <= bucket_end:
            dates.append(day)
            day += timedelta(days=1)

        current = [
            item
            for item in period_sessions
            if cursor <= item["date"] <= bucket_end
        ]
        daily = [0] * len(dates)
        for session in current:
            daily[(session["date"] - cursor).days] += session["seconds"]

        if len(dates) == 1:
            label = f"{dates[0].day} {month_short}"
        else:
            label = f"{dates[0].day}–{dates[-1].day} {month_short}"
        buckets.append(
            _bucket_payload(
                current,
                dates,
                daily,
                number=f"W{index}",
                name=label,
                short=f"W{index}",
                range_text=label,
                river_label=f"W{index}",
                kind="week",
                month_index=start.month - 1,
                catalog=catalog,
                titles=titles,
                colors=colors,
                covers=covers,
            )
        )
        bucket_sessions.append(current)
        cursor = bucket_end + timedelta(days=1)
        index += 1

    _annotate_buckets(buckets, catalog, period_label)
    return buckets, bucket_sessions


def _river(
    bucket_sessions: list[list[dict]],
    labels: list[str],
    titles: dict[str, str],
    colors: dict[str, str],
    catalog: dict[str, str],
) -> dict:
    labels = list(labels)
    if not any(bucket_sessions):
        return {"labels": labels, "months": labels, "layers": []}

    totals: dict[str, int] = {}
    for bucket in bucket_sessions:
        for session in bucket:
            totals[session["game_id"]] = (
                totals.get(session["game_id"], 0) + session["seconds"]
            )
    if not totals:
        return {"labels": labels, "months": labels, "layers": []}

    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    top = ordered[:4]
    used = {game_id for game_id, _seconds in top}
    layers: list[dict] = []

    for game_id, total in top:
        values = []
        for bucket in bucket_sessions:
            values.append(
                sum(
                    session["seconds"]
                    for session in bucket
                    if session["game_id"] == game_id
                )
            )
        layers.append(
            {
                "name": titles.get(game_id, "Unknown game"),
                "color": colors.get(game_id, _color_for(game_id)),
                "values": values,
                "totalSeconds": total,
            }
        )

    other_values = []
    other_total = 0
    for bucket in bucket_sessions:
        value = 0
        for session in bucket:
            if session["game_id"] not in used:
                value += session["seconds"]
                other_total += session["seconds"]
        other_values.append(value)
    if other_total:
        layers.append(
            {
                "name": catalog.get("Other", "Other"),
                "color": OTHER_COLOR,
                "values": other_values,
                "totalSeconds": other_total,
            }
        )

    return {"labels": labels, "months": labels, "layers": layers}


def build(
    games: list[Game],
    period: str = "year",
    year: int | None = None,
    language: str = "en",
    month: int = -1,
    now: float | None = None,
    covers: dict[str, str] | None = None,
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

    longest_session = _longest_session(period_sessions)
    busiest_day = _busiest_day(period_sessions)
    busiest_month = _busiest_month(period_sessions)
    favorite_weekday = _favorite_weekday(period_sessions, catalog)
    average_session = int(total / session_count) if session_count else 0
    if busiest_day:
        busiest_day["sessionsText"] = _sessions_text(
            catalog, busiest_day["sessions"]
        )
    if busiest_month:
        busiest_month["name"] = _month_name(
            catalog, busiest_month["monthIndex"] + 1
        )
        busiest_month["sessionsText"] = _sessions_text(
            catalog, busiest_month["sessions"]
        )

    highlights: list[dict] = []
    if longest_session:
        detail = longest_session.get("dateText", "")
        game_title = longest_session.get("game") or ""
        if game_title:
            detail = f"{detail} · {game_title}" if detail else game_title
        highlights.append(
            _highlight(
                catalog.get("Longest session", "Longest session"),
                longest_session.get("text", ""),
                detail,
                "#4cc9f0",
            )
        )
    if (
        period in ("year", "all")
        and busiest_month
        and busiest_month.get("sessions", 0) > 1
    ):
        month_name = _month_name(catalog, busiest_month["monthIndex"] + 1)
        highlights.append(
            _highlight(
                catalog.get("Busiest month", "Busiest month"),
                month_name,
                busiest_month.get("sessionsText", ""),
                "#facc15",
            )
        )
    elif busiest_day and busiest_day.get("sessions", 0) > 1:
        highlights.append(
            _highlight(
                catalog.get("Busiest day", "Busiest day"),
                busiest_day.get("dateText", ""),
                busiest_day.get("sessionsText", ""),
                "#fb7185",
            )
        )
    if session_count:
        highlights.append(
            _highlight(
                catalog.get("Average session", "Average session"),
                _duration_detail(average_session),
                "",
                "#a78bfa",
            )
        )
    if favorite_weekday and favorite_weekday.get("sessions", 0) > 1:
        highlights.append(
            _highlight(
                catalog.get("Favorite day", "Favorite day"),
                favorite_weekday.get("name", ""),
                _sessions_text(catalog, favorite_weekday["sessions"]),
                "#34d399",
            )
        )

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
    months, month_sessions = _months(
        year_sessions, year, month_count, titles, colors, catalog, covers
    )

    if period == "week":
        buckets, bucket_sessions = _day_buckets(
            period_sessions,
            start,
            end,
            catalog,
            titles,
            colors,
            covers or {},
            period_label,
        )
        buckets_kind = "day"
    elif period == "month":
        buckets, bucket_sessions = _week_buckets(
            period_sessions,
            start,
            end,
            catalog,
            titles,
            colors,
            covers or {},
            period_label,
        )
        buckets_kind = "week"
    else:
        buckets = months
        bucket_sessions = month_sessions
        buckets_kind = "month"

    river = _river(
        bucket_sessions,
        [item.get("riverLabel") or item.get("short", "") for item in buckets],
        titles,
        colors,
        catalog,
    )
    period_top = _top_games(period_sessions, titles, colors, covers, limit=1)
    top_game = period_top[0] if period_top else {}

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
        "buckets": buckets,
        "bucketsKind": buckets_kind,
        "topGame": top_game,
        "river": river,
        "highlights": highlights,
        "longestSession": longest_session,
        "busiestDay": busiest_day,
        "busiestMonth": busiest_month,
        "favoriteWeekday": favorite_weekday,
        "averageSessionText": (
            _duration_detail(average_session) if session_count else ""
        ),
    }



def year_review(
    games: list[Game],
    year: int,
    language: str = "en",
    covers: dict[str, str] | None = None,
    now: float | None = None,
) -> dict:
    """A year recap ready for the story-style presentation."""
    data = build(
        games,
        period="year",
        year=year,
        language=language,
        now=now,
        covers=covers,
    )
    catalog = _catalog(language)
    covers = covers or {}
    sessions = _all_sessions(games)
    year_sessions = [item for item in sessions if item["date"].year == data["year"]]
    titles = _game_titles(sessions, games)

    totals: dict[str, int] = {}
    for session in year_sessions:
        totals[session["game_id"]] = (
            totals.get(session["game_id"], 0) + session["seconds"]
        )
    ordered_ids = sorted(totals, key=lambda key: (-totals[key], key))
    colors = {
        game_id: PALETTE[index % len(PALETTE)]
        for index, game_id in enumerate(ordered_ids)
    }
    for game in games:
        colors.setdefault(game.id, _color_for(game.id))

    top_game = dict(data.get("topGame") or {})
    if top_game:
        game_id = str(top_game.get("gameId") or "")
        top_game["sessionsCount"] = sum(
            1 for item in year_sessions if item["game_id"] == game_id
        )
        top_game["percentOfYear"] = (
            int(round(top_game.get("seconds", 0) / data["seconds"] * 100))
            if data["seconds"]
            else 0
        )

    top_games = _top_games(year_sessions, titles, colors, covers, limit=3)

    by_day: dict[date, int] = {}
    for session in year_sessions:
        by_day[session["date"]] = (
            by_day.get(session["date"], 0) + session["seconds"]
        )
    best_day: dict = {}
    if by_day:
        best_date, best_seconds = max(
            by_day.items(), key=lambda item: (item[1], item[0])
        )
        day_sessions = [
            session for session in year_sessions if session["date"] == best_date
        ]
        day_top = _top_games(day_sessions, titles, colors, covers, limit=1)
        best_day = {
            "dateText": f"{best_date.day:02d}/{best_date.month:02d}",
            "dayNumber": best_date.day,
            "monthName": _month_name(catalog, best_date.month),
            "monthShort": _short_month(_month_name(catalog, best_date.month)),
            "hoursText": _duration_detail(best_seconds),
            "seconds": best_seconds,
            "sessionsCount": len(day_sessions),
            "topGame": day_top[0] if day_top else {},
        }

    streak_days, streak_start, streak_end = _longest_streak_range(
        {item["date"] for item in year_sessions}
    )
    longest_streak: dict = {}
    if streak_days:
        start_text = (
            f"{streak_start.day:02d}/{streak_start.month:02d}"
            if streak_start is not None
            else ""
        )
        end_text = (
            f"{streak_end.day:02d}/{streak_end.month:02d}"
            if streak_end is not None
            else ""
        )
        longest_streak = {
            "days": streak_days,
            "startText": start_text,
            "endText": end_text,
            "rangeText": (
                f"{start_text} - {end_text}" if streak_days > 1 else start_text
            ),
        }

    active_months = [
        month for month in data["months"] if month["sessionsCount"] > 0
    ]

    def _pick(key: str) -> dict:
        if not active_months:
            return {}
        return max(active_months, key=lambda month: (month[key], month["monthIndex"]))

    busiest_month = _pick("seconds")
    most_sessions_month = _pick("sessionsCount")
    most_days_month = _pick("daysPlayed")

    average_session = (
        int(data["seconds"] / data["sessionsCount"])
        if data["sessionsCount"]
        else 0
    )

    top_accent = top_game.get("color") or PALETTE[0]
    slides: list[dict] = []
    if data["hasData"]:
        slides.append({"type": "intro", "accent": top_accent})
        for month in active_months:
            most_played = month.get("mostPlayed") or {}
            slides.append(
                {
                    "type": "month",
                    "month": month,
                    "accent": most_played.get("color") or top_accent,
                }
            )
        if top_game:
            slides.append(
                {"type": "topGame", "game": top_game, "accent": top_accent}
            )
        if data["sessionsCount"]:
            slides.append({"type": "sessions", "accent": "#a78bfa"})
        if longest_streak.get("days", 0) > 1:
            slides.append(
                {
                    "type": "streak",
                    "streak": longest_streak,
                    "accent": "#60a5fa",
                }
            )
        if best_day:
            slides.append(
                {"type": "bestDay", "day": best_day, "accent": "#fb7185"}
            )
        if busiest_month:
            slides.append(
                {"type": "busiest", "month": busiest_month, "accent": "#facc15"}
            )
        slides.append({"type": "outro", "accent": top_accent})

    return {
        "year": data["year"],
        "timeText": data["timeText"],
        "seconds": data["seconds"],
        "changeText": data["changeText"],
        "daysText": data["daysText"],
        "daysPlayed": data["daysPlayed"],
        "daysTotal": data["daysTotal"],
        "streak": data["streak"],
        "streakText": data["streakText"],
        "sessionsText": data["sessionsText"],
        "sessionsCount": data["sessionsCount"],
        "hasData": data["hasData"],
        "months": data["months"],
        "activeMonths": active_months,
        "topGame": top_game,
        "topGames": top_games,
        "bestDay": best_day,
        "longestStreak": longest_streak,
        "busiestMonth": busiest_month,
        "mostSessionsMonth": most_sessions_month,
        "mostDaysMonth": most_days_month,
        "totalGames": len(totals),
        "activeMonthCount": len(active_months),
        "averageSessionText": _duration_detail(average_session),
        "monthLabels": [month["short"] for month in data["months"]],
        "monthTotals": [month["seconds"] for month in data["months"]],
        "monthSessions": [month["sessionsCount"] for month in data["months"]],
        "monthDays": [month["daysPlayed"] for month in data["months"]],
        "slides": slides,
    }
