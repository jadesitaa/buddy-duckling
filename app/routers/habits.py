from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.habit import Habit
from app.schemas.habit import HabitCreate, HabitRead, HabitUpdate

router = APIRouter(prefix="/habits", tags=["habits"])


async def get_own_habit(habit_id: int, current_user: CurrentUser, db: DbSession) -> Habit:
    """Load a habit, or 404 if it does not exist or belongs to someone else.

    Answering 404 rather than 403 keeps other people's habit ids unguessable.
    """
    habit = await db.scalar(select(Habit).where(Habit.id == habit_id))
    if habit is None or habit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found"
        )
    return habit


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
async def create_habit(
    payload: HabitCreate, current_user: CurrentUser, db: DbSession
) -> Habit:
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


@router.get("", response_model=list[HabitRead])
async def list_habits(
    current_user: CurrentUser, db: DbSession, include_inactive: bool = False
) -> list[Habit]:
    query = select(Habit).where(Habit.user_id == current_user.id)
    if not include_inactive:
        query = query.where(Habit.is_active.is_(True))
    result = await db.scalars(query.order_by(Habit.created_at))
    return list(result)


@router.get("/{habit_id}", response_model=HabitRead)
async def get_habit(habit_id: int, current_user: CurrentUser, db: DbSession) -> Habit:
    return await get_own_habit(habit_id, current_user, db)


@router.put("/{habit_id}", response_model=HabitRead)
async def update_habit(
    habit_id: int, payload: HabitUpdate, current_user: CurrentUser, db: DbSession
) -> Habit:
    habit = await get_own_habit(habit_id, current_user, db)
    # exclude_unset so an omitted field keeps its current value.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    await db.commit()
    await db.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit_id: int, current_user: CurrentUser, db: DbSession) -> None:
    habit = await get_own_habit(habit_id, current_user, db)
    await db.delete(habit)
    await db.commit()
