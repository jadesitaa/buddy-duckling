from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.user import User
from app.services.streak import (
    calculate_current_streak,
    calculate_longest_streak,
    local_date_for,
    today_local,
)


async def recalculate_streaks(db: AsyncSession, habit: Habit, user: User) -> None:
    """Recompute a habit's streaks from its logs. Call after every log change."""
    logged_days = list(
        await db.scalars(
            select(HabitLog.log_date_local).where(HabitLog.habit_id == habit.id)
        )
    )

    habit.current_streak = calculate_current_streak(
        logged_days,
        today_local(user.timezone),
        habit.frequency_type,
        habit.frequency_target,
    )
    # The record is recomputed from the whole history, so backfilled days and
    # deleted logs are both reflected correctly.
    habit.longest_streak = calculate_longest_streak(
        logged_days, habit.frequency_type, habit.frequency_target
    )


def build_log(habit: Habit, user: User, logged_at_utc: datetime | None) -> HabitLog:
    moment = (logged_at_utc or datetime.now(UTC)).astimezone(UTC)
    return HabitLog(
        habit_id=habit.id,
        logged_at_utc=moment,
        log_date_local=local_date_for(moment, user.timezone),
    )
