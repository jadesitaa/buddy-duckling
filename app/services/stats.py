"""Read-only summaries for the stats and dashboard endpoints."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.user import User
from app.schemas.stats import DashboardHabit, HabitStats
from app.services.streak import today_local

WINDOW_DAYS = 30


async def _logged_days(db: AsyncSession, habit_id: int) -> list[date]:
    return list(
        await db.scalars(
            select(HabitLog.log_date_local).where(HabitLog.habit_id == habit_id)
        )
    )


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


async def build_habit_stats(db: AsyncSession, habit: Habit, user: User) -> HabitStats:
    days = sorted(await _logged_days(db, habit.id))
    today = today_local(user.timezone)
    window_start = today - timedelta(days=WINDOW_DAYS - 1)
    week_start = _week_start(today)

    return HabitStats(
        habit_id=habit.id,
        name=habit.name,
        frequency_type=habit.frequency_type,
        frequency_target=habit.frequency_target,
        current_streak=habit.current_streak,
        longest_streak=habit.longest_streak,
        total_logs=len(days),
        first_log_date=days[0] if days else None,
        last_log_date=days[-1] if days else None,
        logged_today=today in days,
        completion_rate_30d=round(
            sum(1 for day in days if window_start <= day <= today) / WINDOW_DAYS, 3
        ),
        logs_this_week=sum(1 for day in days if week_start <= day <= today),
    )


async def build_dashboard_habits(
    db: AsyncSession, user: User
) -> tuple[list[DashboardHabit], date]:
    today = today_local(user.timezone)

    habits = list(
        await db.scalars(
            select(Habit)
            .where(Habit.user_id == user.id, Habit.is_active.is_(True))
            .order_by(Habit.created_at)
        )
    )
    logged_today_ids = set(
        await db.scalars(
            select(HabitLog.habit_id).where(
                HabitLog.habit_id.in_([habit.id for habit in habits] or [0]),
                HabitLog.log_date_local == today,
            )
        )
    )

    return [
        DashboardHabit(
            habit_id=habit.id,
            name=habit.name,
            frequency_type=habit.frequency_type,
            current_streak=habit.current_streak,
            longest_streak=habit.longest_streak,
            logged_today=habit.id in logged_today_ids,
        )
        for habit in habits
    ], today


async def count_rows(db: AsyncSession, model, *conditions) -> int:
    count = await db.scalar(
        select(func.count()).select_from(model).where(*conditions)
    )
    return count or 0
