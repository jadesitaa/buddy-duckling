"""Personal goals: progress, and marking one finished."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.notification import NotificationType
from app.models.personal_goal import PersonalGoal
from app.schemas.personal_goal import PersonalGoalProgress, PersonalGoalRead
from app.services.notifier import notify


def describe(goal: PersonalGoal, habit: Habit) -> PersonalGoalProgress:
    streak = habit.current_streak
    target = goal.target_days

    return PersonalGoalProgress(
        **PersonalGoalRead.model_validate(goal).model_dump(),
        habit_name=habit.name,
        current_streak=streak,
        percent=min(100, round(streak / target * 100)) if target else None,
        days_remaining=max(0, target - streak) if target else None,
    )


async def evaluate_personal_goals(db: AsyncSession, habit: Habit) -> None:
    """Finish any goal on this habit whose target the streak just reached.

    Open-ended goals (no target) are never "achieved" - they are a running
    tally, not a finish line.
    """
    goals = await db.scalars(
        select(PersonalGoal).where(
            PersonalGoal.habit_id == habit.id,
            PersonalGoal.achieved_at.is_(None),
            PersonalGoal.target_days.is_not(None),
        )
    )

    for goal in goals:
        if habit.current_streak < goal.target_days:
            continue

        goal.achieved_at = datetime.now(UTC)
        body = f"{goal.target_days} days of {habit.name}. That was all you."
        if goal.reward_description:
            body = f"{body} Enjoy: {goal.reward_description}"
        await notify(
            db,
            user_id=goal.user_id,
            type=NotificationType.GOAL_ACHIEVED,
            title=f"Goal reached: {goal.title}",
            body=body,
            related_habit_id=habit.id,
        )
