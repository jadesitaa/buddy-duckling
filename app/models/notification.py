from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class NotificationType(StrEnum):
    STREAK_BROKEN = "streak_broken"
    PARTNER_REQUEST = "partner_request"
    PARTNER_ACCEPTED = "partner_accepted"
    PARTNER_DECLINED = "partner_declined"
    WAITING_FOR_PARTNER = "waiting_for_partner"
    GOAL_ACHIEVED = "goal_achieved"
    BADGE_EARNED = "badge_earned"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    # The person who should see this, never the person who caused it.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type")
    )
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(String(500))
    # Optional pointers, so the UI can link straight to what happened.
    related_habit_id: Mapped[int | None] = mapped_column(
        ForeignKey("habits.id", ondelete="SET NULL"), default=None
    )
    related_partnership_id: Mapped[int | None] = mapped_column(
        ForeignKey("accountability_partners.id", ondelete="SET NULL"), default=None
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
