"""Turning a partnership row into something a UI can display."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.partnership import AccountabilityPartner
from app.models.user import User
from app.schemas.partnership import PartnershipRead


async def describe(
    db: AsyncSession, partnership: AccountabilityPartner
) -> PartnershipRead:
    habit = await db.get(Habit, partnership.habit_id)
    owner = await db.get(User, habit.user_id)
    partner = await db.get(User, partnership.partner_user_id)
    partner_habit = (
        await db.get(Habit, partnership.partner_habit_id)
        if partnership.partner_habit_id
        else None
    )

    return PartnershipRead(
        id=partnership.id,
        status=partnership.status,
        created_at=partnership.created_at,
        habit_id=habit.id,
        habit_name=habit.name,
        owner_user_id=owner.id,
        owner_display_name=owner.display_name,
        owner_avatar=owner.avatar,
        partner_user_id=partner.id,
        partner_display_name=partner.display_name,
        partner_email=partner.email,
        partner_avatar=partner.avatar,
        partner_habit_id=partner_habit.id if partner_habit else None,
        partner_habit_name=partner_habit.name if partner_habit else None,
    )


async def describe_all(
    db: AsyncSession, partnerships: list[AccountabilityPartner]
) -> list[PartnershipRead]:
    return [await describe(db, partnership) for partnership in partnerships]
