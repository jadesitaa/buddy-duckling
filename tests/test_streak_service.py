"""Unit tests for the streak maths, with no database or HTTP involved."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models.habit import FrequencyType
from app.services.streak import (
    calculate_current_streak,
    calculate_longest_streak,
    local_date_for,
)

TODAY = date(2026, 3, 10)  # a Tuesday


def days_back(*offsets: int) -> list[date]:
    return [TODAY - timedelta(days=offset) for offset in offsets]


def daily_streak(logged_days, today: date = TODAY) -> int:
    return calculate_current_streak(logged_days, today, FrequencyType.DAILY, 1)


def weekly_streak(logged_days, target: int, today: date = TODAY) -> int:
    return calculate_current_streak(
        logged_days, today, FrequencyType.WEEKLY_N_TIMES, target
    )


class TestDaily:
    def test_no_logs_means_no_streak(self):
        assert daily_streak([]) == 0

    @pytest.mark.parametrize("length", [1, 2, 5, 30])
    def test_n_consecutive_days_build_a_streak_of_n(self, length):
        assert daily_streak(days_back(*range(length))) == length

    def test_a_missed_day_resets_the_streak_to_zero(self):
        # Logged up to the day before yesterday, then nothing.
        assert daily_streak(days_back(2, 3, 4)) == 0

    def test_a_streak_survives_until_the_end_of_the_next_day(self):
        # Logged yesterday but not yet today - still alive, not broken.
        assert daily_streak(days_back(1, 2, 3)) == 3

    def test_only_the_run_touching_today_counts(self):
        # A long run last week does not add to a fresh run started today.
        assert daily_streak(days_back(0, 5, 6, 7, 8)) == 1

    def test_logging_twice_on_the_same_day_counts_once(self):
        assert daily_streak([TODAY, TODAY]) == 1


class TestWeeklyNTimes:
    def test_target_met_this_week_counts_as_one_week(self):
        # Mon + Tue of the current week, target 2.
        assert weekly_streak(days_back(0, 1), target=2) == 1

    def test_an_unfinished_current_week_does_not_break_the_streak(self):
        # Only 1 of 3 done so far this week, but last week hit its target.
        last_week = days_back(6, 7, 8)  # Wed, Tue, Mon of last week
        assert weekly_streak([*days_back(0), *last_week], target=3) == 1

    def test_consecutive_weeks_stack_up(self):
        this_week = days_back(0, 1)
        last_week = days_back(7, 8)
        two_weeks_ago = days_back(14, 15)
        assert weekly_streak([*this_week, *last_week, *two_weeks_ago], target=2) == 3

    def test_a_week_below_target_breaks_the_streak(self):
        this_week = days_back(0, 1)
        last_week = days_back(7)  # only 1 of 2 - misses the target
        two_weeks_ago = days_back(14, 15)
        assert weekly_streak([*this_week, *last_week, *two_weeks_ago], target=2) == 1

    def test_a_missed_day_alone_does_not_reset_a_weekly_habit(self):
        """The rule that resets a daily habit must not apply here."""
        logged = days_back(4, 6)  # nothing yesterday or today
        assert daily_streak(logged) == 0
        assert weekly_streak(logged, target=2) == 1


class TestLocalDate:
    def test_utc_and_bangkok_can_fall_on_different_days(self):
        late_evening_utc = datetime(2026, 3, 9, 23, 30, tzinfo=ZoneInfo("UTC"))

        assert local_date_for(late_evening_utc, "UTC") == date(2026, 3, 9)
        # 23:30 UTC is already 06:30 the next morning in Bangkok (UTC+7).
        assert local_date_for(late_evening_utc, "Asia/Bangkok") == date(2026, 3, 10)

    def test_midnight_local_belongs_to_the_day_that_starts(self):
        midnight_bangkok = datetime(2026, 3, 10, 17, 0, tzinfo=ZoneInfo("UTC"))

        assert local_date_for(midnight_bangkok, "Asia/Bangkok") == date(2026, 3, 11)

    def test_one_second_before_midnight_still_belongs_to_the_old_day(self):
        almost_midnight = datetime(2026, 3, 10, 16, 59, 59, tzinfo=ZoneInfo("UTC"))

        assert local_date_for(almost_midnight, "Asia/Bangkok") == date(2026, 3, 10)


class TestLongestStreak:
    def test_it_remembers_a_run_that_already_ended(self):
        # A 3-day run last week, nothing since - the record still stands.
        logged = days_back(5, 6, 7)

        assert daily_streak(logged) == 0
        assert calculate_longest_streak(logged, FrequencyType.DAILY, 1) == 3

    def test_it_reports_the_best_of_several_runs(self):
        logged = [*days_back(0, 1), *days_back(5, 6, 7, 8), *days_back(20)]

        assert calculate_longest_streak(logged, FrequencyType.DAILY, 1) == 4

    def test_weekly_counts_consecutive_weeks_on_target(self):
        logged = [*days_back(6, 7), *days_back(13, 14), *days_back(27, 28)]

        assert calculate_longest_streak(logged, FrequencyType.WEEKLY_N_TIMES, 2) == 2

    def test_no_logs_means_no_record(self):
        assert calculate_longest_streak([], FrequencyType.DAILY, 1) == 0
