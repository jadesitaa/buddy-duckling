"""Badge awarding - checked on every successful log."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge, UserBadge
from app.models.habit import Habit
from app.models.notification import NotificationType
from app.services.notifier import notify


async def award_badges_for_streak(
    db: AsyncSession, habit: Habit, user_id: int
) -> list[UserBadge]:
    """Give the user any badge whose milestone the current streak just reached.

    Milestones at or below the current streak are all checked, not just an exact
    match, so a backfilled log that jumps a streak from 5 to 10 still awards the
    7-day badge that was skipped over.
    """
    milestones = await db.scalars(
        select(Badge).where(Badge.milestone_days <= habit.current_streak)
    )

    already_earned = set(
        await db.scalars(
            select(UserBadge.badge_id).where(
                UserBadge.user_id == user_id, UserBadge.habit_id == habit.id
            )
        )
    )

    awarded = []
    for badge in milestones:
        if badge.id in already_earned:
            continue

        user_badge = UserBadge(user_id=user_id, badge_id=badge.id, habit_id=habit.id)
        db.add(user_badge)
        awarded.append(user_badge)

        await notify(
            db,
            user_id=user_id,
            type=NotificationType.BADGE_EARNED,
            title=f"Badge earned: {badge.title}",
            body=f"{habit.name} is on a {habit.current_streak} day streak. Keep going!",
            related_habit_id=habit.id,
        )

    await db.flush()
    return awarded
