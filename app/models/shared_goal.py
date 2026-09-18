from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SharedGoal(Base):
    """A reward two buddies unlock together.

    Each side chases its own target on its own habit: side A is the habit owner
    who sent the invite, side B is the partner who accepted. `achieved_at` is
    only set once BOTH sides have independently reached their own target, which
    can happen on different days.
    """

    __tablename__ = "shared_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    partnership_id: Mapped[int] = mapped_column(
        ForeignKey("accountability_partners.id", ondelete="CASCADE"), index=True
    )
    target_streak_a: Mapped[int] = mapped_column(Integer)
    target_streak_b: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(120))
    reward_description: Mapped[str | None] = mapped_column(String(500), default=None)
    achieved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    partnership: Mapped["AccountabilityPartner"] = relationship()  # noqa: F821
