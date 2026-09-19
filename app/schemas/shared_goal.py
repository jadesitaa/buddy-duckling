from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SharedGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    # What the two of them will do together when they both get there.
    reward_description: str | None = Field(default=None, max_length=500)
    # How long the two of them are committing to keep this up together.
    duration_days: int = Field(ge=1, le=365)
    # Each side gets its own target - they do not have to match, and they
    # default to the joint duration when left out.
    target_streak_a: int | None = Field(default=None, ge=1, le=365)
    target_streak_b: int | None = Field(default=None, ge=1, le=365)

    @model_validator(mode="after")
    def default_targets_to_the_duration(self):
        if self.target_streak_a is None:
            self.target_streak_a = self.duration_days
        if self.target_streak_b is None:
            self.target_streak_b = self.duration_days
        return self


class Milestone(BaseModel):
    percent: int
    days: int
    reached: bool


class SharedGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partnership_id: int
    title: str
    reward_description: str | None
    duration_days: int
    target_streak_a: int
    target_streak_b: int
    achieved_at: datetime | None
    created_at: datetime


class SharedGoalProgress(SharedGoalRead):
    """A goal plus where each side stands, ready to render."""

    current_streak_a: int
    current_streak_b: int
    reached_a: bool
    reached_b: bool

    # Joint progress: the pair only moves at the speed of whoever is behind.
    joint_days: int
    joint_percent: int
    days_remaining: int
    milestones: list[Milestone]

    # Which side the person asking is on, so a UI can say "you" and "them"
    # without working it out itself.
    my_side: str
