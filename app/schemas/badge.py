from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BadgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    milestone_days: int


class UserBadgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    earned_at: datetime
    badge: BadgeRead
