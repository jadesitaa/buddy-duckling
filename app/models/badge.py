from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Badge(Base):
    """A milestone anyone can earn. The rows are seeded by a migration."""

    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    milestone_days: Mapped[int] = mapped_column(Integer, index=True)


class UserBadge(Base):
    """One badge earned by one user on one habit."""

    __tablename__ = "user_badges"
    # The same badge can be earned again on a different habit, but never twice
    # on the same one.
    __table_args__ = (UniqueConstraint("user_id", "badge_id", "habit_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"))
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    badge: Mapped[Badge] = relationship(lazy="joined")
    habit: Mapped["Habit"] = relationship(lazy="joined")  # noqa: F821
