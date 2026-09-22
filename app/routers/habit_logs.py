from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.models.habit_log import HabitLog
from app.routers.habits import get_own_habit
from app.schemas.habit_log import HabitLogCreate, HabitLogCreated, HabitLogRead
from app.services.badges import award_badges_for_streak
from app.services.goals import evaluate_goals_for_habit
from app.services.habit_logs import build_log, recalculate_streaks
from app.services.personal_goals import evaluate_personal_goals

router = APIRouter(prefix="/habits/{habit_id}/logs", tags=["habit logs"])


@router.post("", response_model=HabitLogCreated, status_code=status.HTTP_201_CREATED)
async def create_log(
    habit_id: int, payload: HabitLogCreate, current_user: CurrentUser, db: DbSession
) -> HabitLogCreated:
    habit = await get_own_habit(habit_id, current_user, db)
    log = build_log(habit, current_user, payload.logged_at_utc)
    db.add(log)

    try:
        await db.flush()
    except IntegrityError:
        # The UNIQUE(habit_id, log_date_local) constraint rejected the row.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This habit is already logged for that day",
        ) from None

    await recalculate_streaks(db, habit, current_user)
    await award_badges_for_streak(db, habit, current_user.id)
    await evaluate_personal_goals(db, habit)
    await evaluate_goals_for_habit(db, habit)
    await db.commit()
    await db.refresh(log)
    await db.refresh(habit)

    return HabitLogCreated(
        log=HabitLogRead.model_validate(log),
        current_streak=habit.current_streak,
        longest_streak=habit.longest_streak,
    )


@router.get("", response_model=list[HabitLogRead])
async def list_logs(
    habit_id: int, current_user: CurrentUser, db: DbSession
) -> list[HabitLog]:
    habit = await get_own_habit(habit_id, current_user, db)
    logs = await db.scalars(
        select(HabitLog)
        .where(HabitLog.habit_id == habit.id)
        .order_by(HabitLog.log_date_local.desc())
    )
    return list(logs)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    habit_id: int, log_id: int, current_user: CurrentUser, db: DbSession
) -> None:
    habit = await get_own_habit(habit_id, current_user, db)
    log = await db.scalar(
        select(HabitLog).where(HabitLog.id == log_id, HabitLog.habit_id == habit.id)
    )
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Habit log not found"
        )

    await db.delete(log)
    await db.flush()
    # Deleting a log can break a streak, so the streaks are recalculated here too.
    await recalculate_streaks(db, habit, current_user)
    await db.commit()
