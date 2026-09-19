from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession
from app.models.avatar import AVATAR_CATALOG
from app.models.user import User
from app.schemas.user import AvatarOption, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
avatars = APIRouter(tags=["users"])


@avatars.get("/avatars", response_model=list[AvatarOption])
async def list_avatars() -> list[AvatarOption]:
    """The pickable ducklings. Open to anyone, so sign-up can show them too."""
    return [
        AvatarOption(code=code, title=meta["title"], description=meta["description"])
        for code, meta in AVATAR_CATALOG.items()
    ]


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.put("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate, current_user: CurrentUser, db: DbSession
) -> User:
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "timezone" in changes:
        try:
            ZoneInfo(changes["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unknown timezone - use an IANA name such as Asia/Bangkok",
            ) from None

    for field, value in changes.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user
