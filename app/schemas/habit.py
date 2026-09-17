from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.habit import FrequencyType


class HabitBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    frequency_type: FrequencyType = FrequencyType.DAILY
    frequency_target: int = Field(default=1, ge=1, le=7)

    @model_validator(mode="after")
    def check_target_matches_frequency(self):
        if self.frequency_type is FrequencyType.DAILY and self.frequency_target != 1:
            raise ValueError("a daily habit must have frequency_target = 1")
        return self


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    """Every field is optional - only what is sent gets changed."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class HabitRead(HabitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    current_streak: int
    longest_streak: int
    is_active: bool
    created_at: datetime
