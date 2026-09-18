from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.badge import UserBadge
from app.schemas.badge import UserBadgeRead

router = APIRouter(prefix="/me/badges", tags=["badges"])


@router.get("", response_model=list[UserBadgeRead])
async def list_my_badges(current_user: CurrentUser, db: DbSession) -> list[UserBadge]:
    """Every badge I have earned, newest first."""
    result = await db.scalars(
        select(UserBadge)
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.earned_at.desc(), UserBadge.id.desc())
    )
    return list(result.unique())
