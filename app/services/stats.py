"""Read-only summaries for the stats and dashboard endpoints."""

from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.user import User
from app.schemas.stats import DashboardHabit, GoalProgressLine, HabitStats
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


async def build_goal_lines(db: AsyncSession, user: User) -> list[GoalProgressLine]:
    """Every goal the user is part of - their own and their shared ones."""
    from app.models.partnership import AccountabilityPartner, PartnershipStatus
    from app.models.personal_goal import PersonalGoal
    from app.models.shared_goal import SharedGoal
    from app.models.user import User as UserModel
    from app.services.goals import joint_percent, load_sides

    lines: list[GoalProgressLine] = []

    # Goals the user set for themselves.
    rows = await db.execute(
        select(PersonalGoal, Habit)
        .join(Habit, Habit.id == PersonalGoal.habit_id)
        .where(PersonalGoal.user_id == user.id)
        .order_by(PersonalGoal.created_at)
    )
    for goal, habit in rows:
        target = goal.target_days
        lines.append(
            GoalProgressLine(
                kind="personal",
                title=goal.title,
                habit_name=habit.name,
                current=habit.current_streak,
                target=target,
                percent=(
                    min(100, round(habit.current_streak / target * 100))
                    if target
                    else None
                ),
                achieved=goal.achieved_at is not None,
            )
        )

    # Goals shared with a buddy, from whichever side the user is on.
    my_habits = select(Habit.id).where(Habit.user_id == user.id)
    partnerships = await db.scalars(
        select(AccountabilityPartner).where(
            AccountabilityPartner.status == PartnershipStatus.ACCEPTED,
            or_(
                AccountabilityPartner.partner_user_id == user.id,
                AccountabilityPartner.habit_id.in_(my_habits),
            ),
        )
    )
    for partnership in partnerships:
        sides = await load_sides(db, partnership)
        if sides is None:
            continue

        mine_is_a = sides.side_of(user.id) == "a"
        owner_habit = await db.get(Habit, partnership.habit_id)
        partner_habit = await db.get(Habit, partnership.partner_habit_id)
        my_habit = owner_habit if mine_is_a else partner_habit
        buddy_id = sides.user_id_b if mine_is_a else sides.user_id_a
        buddy = await db.get(UserModel, buddy_id)

        goals = await db.scalars(
            select(SharedGoal)
            .where(SharedGoal.partnership_id == partnership.id)
            .order_by(SharedGoal.created_at)
        )
        for goal in goals:
            lines.append(
                GoalProgressLine(
                    kind="shared",
                    title=goal.title,
                    habit_name=my_habit.name if my_habit else "",
                    current=sides.joint_days(),
                    target=goal.duration_days,
                    percent=joint_percent(goal, sides),
                    achieved=goal.achieved_at is not None,
                    buddy_name=buddy.display_name if buddy else None,
                    my_streak=(
                        sides.current_streak_a if mine_is_a else sides.current_streak_b
                    ),
                    buddy_streak=(
                        sides.current_streak_b if mine_is_a else sides.current_streak_a
                    ),
                )
            )

    return lines
