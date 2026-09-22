from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PersonalGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    # Optional on purpose: a goal with nobody else involved does not need a
    # deadline to be useful.
    target_days: int | None = Field(default=None, ge=1, le=365)
    reward_description: str | None = Field(default=None, max_length=500)


class PersonalGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    title: str
    target_days: int | None
    reward_description: str | None
    achieved_at: datetime | None
    created_at: datetime


class PersonalGoalProgress(PersonalGoalRead):
    habit_name: str
    current_streak: int
    # Both are None for an open-ended goal - there is nothing to be a
    # percentage of, and nothing left to count down.
    percent: int | None
    days_remaining: int | None
