from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.avatar import DuckAvatar
from app.models.partnership import PartnershipStatus


class PartnerInvite(BaseModel):
    partner_email: EmailStr


class PartnerAccept(BaseModel):
    """The partner may pair one of their own habits with the invitation."""

    partner_habit_id: int | None = None


class PartnershipRead(BaseModel):
    """A pairing, with enough names in it that a UI never has to guess.

    The invited side cannot read the inviter's habit directly - it is not
    theirs - so the names are resolved here instead.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: PartnershipStatus
    created_at: datetime

    # The side that sent the invite.
    habit_id: int
    habit_name: str
    owner_user_id: int
    owner_display_name: str
    owner_avatar: DuckAvatar

    # The side that was invited.
    partner_user_id: int
    partner_display_name: str
    partner_email: EmailStr
    partner_avatar: DuckAvatar
    partner_habit_id: int | None
    partner_habit_name: str | None
