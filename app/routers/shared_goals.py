from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.habit import Habit
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.shared_goal import SharedGoal
from app.schemas.shared_goal import SharedGoalCreate, SharedGoalProgress, SharedGoalRead
from app.services.goals import load_sides

router = APIRouter(prefix="/partnerships/{partnership_id}/goals", tags=["shared goals"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
)


async def _get_my_accepted_partnership(
    partnership_id: int, current_user: CurrentUser, db: DbSession
) -> AccountabilityPartner:
    """Either side of an accepted partnership may manage its shared goals."""
    partnership = await db.scalar(
        select(AccountabilityPartner).where(AccountabilityPartner.id == partnership_id)
    )
    if partnership is None:
        raise NOT_FOUND

    habit = await db.get(Habit, partnership.habit_id)
    if current_user.id not in (habit.user_id, partnership.partner_user_id):
        raise NOT_FOUND
    if partnership.status is not PartnershipStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This partnership has not been accepted yet",
        )
    return partnership


async def _with_progress(
    db: DbSession, partnership: AccountabilityPartner, goal: SharedGoal
) -> SharedGoalProgress:
    sides = await load_sides(db, partnership)
    return SharedGoalProgress(
        **SharedGoalRead.model_validate(goal).model_dump(),
        current_streak_a=sides.current_streak_a if sides else 0,
        current_streak_b=sides.current_streak_b if sides else 0,
        reached_a=bool(sides and sides.reached_a(goal)),
        reached_b=bool(sides and sides.reached_b(goal)),
    )


@router.post("", response_model=SharedGoalProgress, status_code=status.HTTP_201_CREATED)
async def create_goal(
    partnership_id: int,
    payload: SharedGoalCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> SharedGoalProgress:
    partnership = await _get_my_accepted_partnership(partnership_id, current_user, db)
    if partnership.partner_habit_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Both sides need a habit paired before setting a shared goal",
        )

    goal = SharedGoal(partnership_id=partnership.id, **payload.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return await _with_progress(db, partnership, goal)


@router.get("", response_model=list[SharedGoalProgress])
async def list_goals(
    partnership_id: int, current_user: CurrentUser, db: DbSession
) -> list[SharedGoalProgress]:
    partnership = await _get_my_accepted_partnership(partnership_id, current_user, db)
    goals = await db.scalars(
        select(SharedGoal)
        .where(SharedGoal.partnership_id == partnership.id)
        .order_by(SharedGoal.created_at)
    )
    return [await _with_progress(db, partnership, goal) for goal in goals]


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    partnership_id: int, goal_id: int, current_user: CurrentUser, db: DbSession
) -> None:
    partnership = await _get_my_accepted_partnership(partnership_id, current_user, db)
    goal = await db.scalar(
        select(SharedGoal).where(
            SharedGoal.id == goal_id, SharedGoal.partnership_id == partnership.id
        )
    )
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shared goal not found"
        )

    await db.delete(goal)
    await db.commit()
