from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PartnershipStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class AccountabilityPartner(Base):
    """One buddy pairing: habit owner invites partner_user to keep them honest.

    Nothing is notified until status is ACCEPTED - there is no auto-linking.
    """

    __tablename__ = "accountability_partners"
    __table_args__ = (UniqueConstraint("habit_id", "partner_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # The habit of the person who sent the invite.
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), index=True
    )
    # The habit the partner picks when accepting - the two sides can be
    # working on completely different habits.
    partner_habit_id: Mapped[int | None] = mapped_column(
        ForeignKey("habits.id", ondelete="SET NULL"), default=None
    )
    partner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[PartnershipStatus] = mapped_column(
        Enum(PartnershipStatus, name="partnership_status"),
        default=PartnershipStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    habit: Mapped["Habit"] = relationship(foreign_keys=[habit_id])  # noqa: F821
    partner_habit: Mapped["Habit | None"] = relationship(  # noqa: F821
        foreign_keys=[partner_habit_id]
    )
    partner_user: Mapped["User"] = relationship()  # noqa: F821
