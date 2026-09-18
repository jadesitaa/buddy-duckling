from datetime import date, datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict


class HabitLogCreate(BaseModel):
    # Optional, so the common case is just POST with an empty body.
    # Must carry a timezone offset when given, so "when" is never ambiguous.
    logged_at_utc: AwareDatetime | None = None


class HabitLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    logged_at_utc: datetime
    log_date_local: date


class HabitLogCreated(BaseModel):
    """The new log plus the streak it produced, so the caller needs one request."""

    log: HabitLogRead
    current_streak: int
    longest_streak: int
