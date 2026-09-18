from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SharedGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    reward_description: str | None = Field(default=None, max_length=500)
    # Each side gets its own target - they do not have to match.
    target_streak_a: int = Field(ge=1, le=365)
    target_streak_b: int = Field(ge=1, le=365)


class SharedGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partnership_id: int
    title: str
    reward_description: str | None
    target_streak_a: int
    target_streak_b: int
    achieved_at: datetime | None
    created_at: datetime


class SharedGoalProgress(SharedGoalRead):
    """A goal plus where each side currently stands."""

    current_streak_a: int
    current_streak_b: int
    reached_a: bool
    reached_b: bool
