"""Streak maths.

Everything here works on *local* dates that were already converted from UTC by
`local_date_for`, so no function below ever has to think about timezones again.
"""

from collections import Counter
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.habit import FrequencyType


def local_date_for(moment: datetime, timezone_name: str) -> date:
    """The calendar day `moment` falls on, seen from the user's timezone."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(ZoneInfo(timezone_name)).date()


def today_local(timezone_name: str) -> date:
    return local_date_for(datetime.now(UTC), timezone_name)


def _week_start(day: date) -> date:
    """The Monday of the calendar week `day` belongs to."""
    return day - timedelta(days=day.weekday())


def _daily_streak(logged_days: set[date], today: date) -> int:
    # A daily habit is only "alive" if it was logged today or yesterday;
    # anything older means a day was missed, which resets the streak to 0.
    if today in logged_days:
        cursor = today
    elif today - timedelta(days=1) in logged_days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in logged_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _weekly_streak(logged_days: Iterable[date], today: date, target: int) -> int:
    """Count consecutive calendar weeks that reached `target` logs.

    A week is never judged before it is over, so the current week only adds to
    the streak once its target is met - it can never break it.
    """
    per_week = Counter(_week_start(day) for day in logged_days)

    cursor = _week_start(today)
    if per_week[cursor] < target:
        cursor -= timedelta(weeks=1)

    streak = 0
    while per_week[cursor] >= target:
        streak += 1
        cursor -= timedelta(weeks=1)
    return streak


def calculate_current_streak(
    logged_days: Iterable[date],
    today: date,
    frequency_type: FrequencyType,
    frequency_target: int,
) -> int:
    days = set(logged_days)
    if not days:
        return 0
    if frequency_type is FrequencyType.DAILY:
        return _daily_streak(days, today)
    return _weekly_streak(days, today, frequency_target)


def _longest_run(days: Iterable[date], step: timedelta) -> int:
    """Longest run of values spaced exactly `step` apart."""
    ordered = sorted(set(days))
    if not ordered:
        return 0

    longest = run = 1
    for previous, current in zip(ordered, ordered[1:], strict=False):
        run = run + 1 if current - previous == step else 1
        longest = max(longest, run)
    return longest


def calculate_longest_streak(
    logged_days: Iterable[date],
    frequency_type: FrequencyType,
    frequency_target: int,
) -> int:
    """The best run the habit ever had - it looks at the whole history.

    Kept separate from the current streak because logs can be backfilled: a run
    that ended last month is still the user's record.
    """
    days = set(logged_days)
    if not days:
        return 0

    if frequency_type is FrequencyType.DAILY:
        return _longest_run(days, timedelta(days=1))

    per_week = Counter(_week_start(day) for day in days)
    weeks_on_target = [
        week for week, count in per_week.items() if count >= frequency_target
    ]
    return _longest_run(weeks_on_target, timedelta(weeks=1))
