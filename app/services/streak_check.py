"""The daily sweep that notices broken streaks.

Nobody is told anything while a streak is alive; this job is what turns a
missed day into a notification for the user and for their accepted buddies.
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.notification import NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.user import User
from app.services.notifier import notify
from app.services.streak import calculate_current_streak, today_local


async def _notify_partners(db: AsyncSession, habit: Habit, owner: User) -> None:
    """Tell everyone in an accepted partnership with this habit. Both directions:
    the habit can be the one that was invited about, or the one paired on accept.
    """
    partnerships = await db.scalars(
        select(AccountabilityPartner).where(
            AccountabilityPartner.status == PartnershipStatus.ACCEPTED,
            or_(
                AccountabilityPartner.habit_id == habit.id,
                AccountabilityPartner.partner_habit_id == habit.id,
            ),
        )
    )

    for partnership in partnerships:
        if partnership.habit_id == habit.id:
            # The owner sent this invite, so the other side is the partner.
            buddy_id = partnership.partner_user_id
        else:
            other_habit = await db.get(Habit, partnership.habit_id)
            buddy_id = other_habit.user_id if other_habit else None

        if buddy_id is None or buddy_id == owner.id:
            continue

        await notify(
            db,
            user_id=buddy_id,
            type=NotificationType.STREAK_BROKEN,
            title=f"{owner.display_name} broke a streak",
            body=f"Their streak on {habit.name} has reset. Maybe check in on them?",
            related_habit_id=habit.id,
            related_partnership_id=partnership.id,
        )


async def run_daily_streak_check(db: AsyncSession) -> int:
    """Reset every streak that was broken since the last run.

    Returns how many habits were reset. Safe to run as often as you like: a
    habit whose streak is already 0 is never reported twice.
    """
    habits = await db.scalars(
        select(Habit).where(Habit.is_active.is_(True), Habit.current_streak > 0)
    )

    broken = 0
    for habit in habits:
        owner = await db.get(User, habit.user_id)
        if owner is None:
            continue

        logged_days = list(
            await db.scalars(
                select(HabitLog.log_date_local).where(HabitLog.habit_id == habit.id)
            )
        )
        # "Today" is the owner's today, not the server's.
        streak_now = calculate_current_streak(
            logged_days,
            today_local(owner.timezone),
            habit.frequency_type,
            habit.frequency_target,
        )
        if streak_now > 0:
            continue

        habit.current_streak = 0
        broken += 1

        await notify(
            db,
            user_id=owner.id,
            type=NotificationType.STREAK_BROKEN,
            title="Streak reset",
            body=f"{habit.name} lost its streak. Every day is a fresh start!",
            related_habit_id=habit.id,
        )
        await _notify_partners(db, habit, owner)

    await db.commit()
    return broken
