"""Shared goal progress and the notifications that come out of it."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.notification import Notification, NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.shared_goal import SharedGoal
from app.services.notifier import notify


@dataclass(frozen=True)
class GoalSides:
    """Who is on each side of a goal, and how far along they are."""

    user_id_a: int
    user_id_b: int
    current_streak_a: int
    current_streak_b: int

    def reached_a(self, goal: SharedGoal) -> bool:
        return self.current_streak_a >= goal.target_streak_a

    def reached_b(self, goal: SharedGoal) -> bool:
        return self.current_streak_b >= goal.target_streak_b


async def load_sides(
    db: AsyncSession, partnership: AccountabilityPartner
) -> GoalSides | None:
    """Side A is the inviter's habit, side B the habit the partner paired."""
    habit_a = await db.get(Habit, partnership.habit_id)
    habit_b = (
        await db.get(Habit, partnership.partner_habit_id)
        if partnership.partner_habit_id
        else None
    )
    if habit_a is None or habit_b is None:
        return None

    return GoalSides(
        user_id_a=habit_a.user_id,
        user_id_b=habit_b.user_id,
        current_streak_a=habit_a.current_streak,
        current_streak_b=habit_b.current_streak,
    )


async def _already_notified(
    db: AsyncSession, goal: SharedGoal, user_id: int, type: NotificationType
) -> bool:
    """Keep a goal from re-notifying the same person on every later log."""
    existing = await db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.type == type,
            Notification.related_partnership_id == goal.partnership_id,
        )
    )
    return existing is not None


async def evaluate_goals_for_habit(db: AsyncSession, habit: Habit) -> None:
    """Re-check every shared goal this habit takes part in. Call after a log change."""
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
        sides = await load_sides(db, partnership)
        if sides is None:
            continue

        goals = await db.scalars(
            select(SharedGoal).where(
                SharedGoal.partnership_id == partnership.id,
                SharedGoal.achieved_at.is_(None),
            )
        )
        for goal in goals:
            await _evaluate_goal(db, goal, sides)


async def _evaluate_goal(db: AsyncSession, goal: SharedGoal, sides: GoalSides) -> None:
    reached_a, reached_b = sides.reached_a(goal), sides.reached_b(goal)

    if reached_a and reached_b:
        goal.achieved_at = datetime.now(UTC)
        for user_id in (sides.user_id_a, sides.user_id_b):
            await notify(
                db,
                user_id=user_id,
                type=NotificationType.GOAL_ACHIEVED,
                title="Shared goal achieved!",
                body=f"You and your buddy both hit your targets. Time for: {goal.title}",
                related_partnership_id=goal.partnership_id,
            )
        return

    # Exactly one side is done - tell them they are waiting on their buddy.
    if reached_a or reached_b:
        waiting_user_id = sides.user_id_a if reached_a else sides.user_id_b
        if await _already_notified(
            db, goal, waiting_user_id, NotificationType.WAITING_FOR_PARTNER
        ):
            return
        await notify(
            db,
            user_id=waiting_user_id,
            type=NotificationType.WAITING_FOR_PARTNER,
            title="You reached your target!",
            body=f"Now waiting for your buddy to reach theirs: {goal.title}",
            related_partnership_id=goal.partnership_id,
        )
