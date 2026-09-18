from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class HabitLog(Base):
    __tablename__ = "habit_logs"
    # One log per habit per local day - the database, not the API, is what
    # guarantees a habit cannot be logged twice on the same day.
    __table_args__ = (UniqueConstraint("habit_id", "log_date_local"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), index=True
    )
    # The instant the log happened, always stored in UTC.
    logged_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # The same instant seen from the user's timezone - this is the "day" a
    # streak is counted on, and the only field streak maths looks at.
    log_date_local: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    habit: Mapped["Habit"] = relationship(back_populates="logs")  # noqa: F821
