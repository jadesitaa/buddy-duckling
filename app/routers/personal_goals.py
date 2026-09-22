from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.habit import Habit
from app.models.personal_goal import PersonalGoal
from app.routers.habits import get_own_habit
from app.schemas.personal_goal import PersonalGoalCreate, PersonalGoalProgress
from app.services.personal_goals import describe

habit_goals = APIRouter(prefix="/habits/{habit_id}/goals", tags=["personal goals"])
my_goals = APIRouter(prefix="/me", tags=["personal goals"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
)


@habit_goals.post(
    "", response_model=PersonalGoalProgress, status_code=status.HTTP_201_CREATED
)
async def create_goal(
    habit_id: int,
    payload: PersonalGoalCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> PersonalGoalProgress:
    habit = await get_own_habit(habit_id, current_user, db)

    goal = PersonalGoal(
        user_id=current_user.id, habit_id=habit.id, **payload.model_dump()
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return describe(goal, habit)


@habit_goals.get("", response_model=list[PersonalGoalProgress])
async def list_goals_for_habit(
    habit_id: int, current_user: CurrentUser, db: DbSession
) -> list[PersonalGoalProgress]:
    habit = await get_own_habit(habit_id, current_user, db)
    goals = await db.scalars(
        select(PersonalGoal)
        .where(PersonalGoal.habit_id == habit.id)
        .order_by(PersonalGoal.created_at)
    )
    return [describe(goal, habit) for goal in goals]


@my_goals.get("/goals", response_model=list[PersonalGoalProgress])
async def list_my_goals(
    current_user: CurrentUser, db: DbSession, include_achieved: bool = True
) -> list[PersonalGoalProgress]:
    """Every personal goal I have, across all my habits."""
    query = (
        select(PersonalGoal, Habit)
        .join(Habit, Habit.id == PersonalGoal.habit_id)
        .where(PersonalGoal.user_id == current_user.id)
        .order_by(PersonalGoal.created_at)
    )
    if not include_achieved:
        query = query.where(PersonalGoal.achieved_at.is_(None))

    rows = await db.execute(query)
    return [describe(goal, habit) for goal, habit in rows]


@habit_goals.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    habit_id: int, goal_id: int, current_user: CurrentUser, db: DbSession
) -> None:
    habit = await get_own_habit(habit_id, current_user, db)
    goal = await db.scalar(
        select(PersonalGoal).where(
            PersonalGoal.id == goal_id, PersonalGoal.habit_id == habit.id
        )
    )
    if goal is None:
        raise NOT_FOUND

    await db.delete(goal)
    await db.commit()
