from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class PersonalGoal(Base):
    """A goal you set for yourself on one of your own habits.

    Unlike a shared goal there is no buddy and no negotiation, so
    `target_days` is optional: leave it out for an open-ended "just keep
    going" goal that tracks the streak without ever being finished.
    """

    __tablename__ = "personal_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    target_days: Mapped[int | None] = mapped_column(Integer, default=None)
    reward_description: Mapped[str | None] = mapped_column(String(500), default=None)
    achieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    habit: Mapped["Habit"] = relationship()  # noqa: F821
