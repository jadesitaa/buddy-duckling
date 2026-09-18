from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.models.habit import Habit
from app.models.notification import NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.user import User
from app.routers.habits import get_own_habit
from app.schemas.partnership import PartnerAccept, PartnerInvite, PartnershipRead
from app.services.notifier import notify

habit_partners = APIRouter(prefix="/habits/{habit_id}/partners", tags=["partners"])
partners = APIRouter(prefix="/partners", tags=["partners"])
me_partners = APIRouter(prefix="/me", tags=["partners"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Partnership not found"
)


async def _get_pending_invite_for_me(
    partnership_id: int, current_user: CurrentUser, db: DbSession
) -> AccountabilityPartner:
    """Only the invited partner can answer an invite, and only while pending."""
    partnership = await db.scalar(
        select(AccountabilityPartner).where(AccountabilityPartner.id == partnership_id)
    )
    if partnership is None or partnership.partner_user_id != current_user.id:
        raise NOT_FOUND
    if partnership.status is not PartnershipStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This request was already {partnership.status.value}",
        )
    return partnership


@habit_partners.post(
    "", response_model=PartnershipRead, status_code=status.HTTP_201_CREATED
)
async def invite_partner(
    habit_id: int, payload: PartnerInvite, current_user: CurrentUser, db: DbSession
) -> AccountabilityPartner:
    habit = await get_own_habit(habit_id, current_user, db)

    partner = await db.scalar(select(User).where(User.email == payload.partner_email))
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user with that email"
        )
    if partner.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot be your own accountability partner",
        )

    partnership = AccountabilityPartner(habit_id=habit.id, partner_user_id=partner.id)
    db.add(partnership)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already invited this person for this habit",
        ) from None

    await notify(
        db,
        user_id=partner.id,
        type=NotificationType.PARTNER_REQUEST,
        title="New buddy request",
        body=f"{current_user.display_name} wants to be your buddy for {habit.name}.",
        related_habit_id=habit.id,
        related_partnership_id=partnership.id,
    )
    await db.commit()
    await db.refresh(partnership)
    return partnership


@habit_partners.get("", response_model=list[PartnershipRead])
async def list_habit_partners(
    habit_id: int, current_user: CurrentUser, db: DbSession
) -> list[AccountabilityPartner]:
    habit = await get_own_habit(habit_id, current_user, db)
    result = await db.scalars(
        select(AccountabilityPartner)
        .where(AccountabilityPartner.habit_id == habit.id)
        .order_by(AccountabilityPartner.created_at)
    )
    return list(result)


@me_partners.get("/partner-requests", response_model=list[PartnershipRead])
async def list_my_partner_requests(
    current_user: CurrentUser, db: DbSession, pending_only: bool = True
) -> list[AccountabilityPartner]:
    """Invitations other people sent to me."""
    query = select(AccountabilityPartner).where(
        AccountabilityPartner.partner_user_id == current_user.id
    )
    if pending_only:
        query = query.where(AccountabilityPartner.status == PartnershipStatus.PENDING)
    result = await db.scalars(query.order_by(AccountabilityPartner.created_at))
    return list(result)


@partners.put("/{partnership_id}/accept", response_model=PartnershipRead)
async def accept_partnership(
    partnership_id: int,
    payload: PartnerAccept,
    current_user: CurrentUser,
    db: DbSession,
) -> AccountabilityPartner:
    partnership = await _get_pending_invite_for_me(partnership_id, current_user, db)

    if payload.partner_habit_id is not None:
        # Pairing one of my own habits is optional, but it has to be mine.
        await get_own_habit(payload.partner_habit_id, current_user, db)
        partnership.partner_habit_id = payload.partner_habit_id

    partnership.status = PartnershipStatus.ACCEPTED

    habit = await db.get(Habit, partnership.habit_id)
    await notify(
        db,
        user_id=habit.user_id,
        type=NotificationType.PARTNER_ACCEPTED,
        title="Buddy request accepted",
        body=f"{current_user.display_name} is now your buddy for {habit.name}.",
        related_habit_id=habit.id,
        related_partnership_id=partnership.id,
    )
    await db.commit()
    await db.refresh(partnership)
    return partnership


@partners.put("/{partnership_id}/decline", response_model=PartnershipRead)
async def decline_partnership(
    partnership_id: int, current_user: CurrentUser, db: DbSession
) -> AccountabilityPartner:
    partnership = await _get_pending_invite_for_me(partnership_id, current_user, db)
    partnership.status = PartnershipStatus.DECLINED

    habit = await db.get(Habit, partnership.habit_id)
    await notify(
        db,
        user_id=habit.user_id,
        type=NotificationType.PARTNER_DECLINED,
        title="Buddy request declined",
        body=f"{current_user.display_name} declined your request for {habit.name}.",
        related_habit_id=habit.id,
        related_partnership_id=partnership.id,
    )
    await db.commit()
    await db.refresh(partnership)
    return partnership


@partners.delete("/{partnership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partnership(
    partnership_id: int, current_user: CurrentUser, db: DbSession
) -> None:
    """Either side can end a partnership."""
    partnership = await db.scalar(
        select(AccountabilityPartner).where(AccountabilityPartner.id == partnership_id)
    )
    if partnership is None:
        raise NOT_FOUND

    habit = await db.get(Habit, partnership.habit_id)
    if current_user.id not in (habit.user_id, partnership.partner_user_id):
        raise NOT_FOUND

    await db.delete(partnership)
    await db.commit()
