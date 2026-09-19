"""Shared goal progress, milestones, and the notifications that come out of it."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.notification import Notification, NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.shared_goal import SharedGoal
from app.schemas.shared_goal import Milestone
from app.services.notifier import notify

# Quarter-way markers on the joint progress bar.
MILESTONE_PERCENTS = (25, 50, 75, 100)


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

    def joint_days(self) -> int:
        """A pair is only as far along as whoever is behind."""
        return min(self.current_streak_a, self.current_streak_b)

    def side_of(self, user_id: int) -> str:
        if user_id == self.user_id_a:
            return "a"
        return "b" if user_id == self.user_id_b else "none"


def joint_percent(goal: SharedGoal, sides: GoalSides) -> int:
    return min(100, round(sides.joint_days() / goal.duration_days * 100))


def milestones_for(goal: SharedGoal, sides: GoalSides) -> list[Milestone]:
    """Quarter markers, in days, with the ones already passed flagged."""
    done = sides.joint_days()
    markers = []
    for percent in MILESTONE_PERCENTS:
        days = max(1, round(goal.duration_days * percent / 100))
        markers.append(Milestone(percent=percent, days=days, reached=done >= days))
    return markers


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


def _with_plan(body: str, plan: str | None) -> str:
    """Reward text is always something the two of them do together."""
    return f"{body} Together you get: {plan}" if plan else body


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
                body=_with_plan(
                    f"You both kept {goal.title} going for {goal.duration_days} days.",
                    goal.reward_description,
                ),
                related_partnership_id=goal.partnership_id,
            )
        return

    # Exactly one side is done - tell them they are waiting on their buddy,
    # and what the two of them get to do once both are there.
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
            body=_with_plan(
                f"Now waiting for your buddy to reach theirs: {goal.title}.",
                goal.reward_description,
            ),
            related_partnership_id=goal.partnership_id,
        )
