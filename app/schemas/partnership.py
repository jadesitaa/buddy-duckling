from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.partnership import PartnershipStatus


class PartnerInvite(BaseModel):
    partner_email: EmailStr


class PartnerAccept(BaseModel):
    """The partner may pair one of their own habits with the invitation."""

    partner_habit_id: int | None = None


class PartnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    partner_habit_id: int | None
    partner_user_id: int
    status: PartnershipStatus
    created_at: datetime
