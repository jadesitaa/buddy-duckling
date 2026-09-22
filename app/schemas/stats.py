from datetime import date

from pydantic import BaseModel

from app.models.avatar import DuckAvatar
from app.models.habit import FrequencyType


class HabitStats(BaseModel):
    habit_id: int
    name: str
    frequency_type: FrequencyType
    frequency_target: int
    current_streak: int
    longest_streak: int
    total_logs: int
    first_log_date: date | None
    last_log_date: date | None
    logged_today: bool
    # Share of the last 30 local days that were logged, 0.0 - 1.0.
    completion_rate_30d: float
    logs_this_week: int


class DashboardHabit(BaseModel):
    habit_id: int
    name: str
    frequency_type: FrequencyType
    current_streak: int
    longest_streak: int
    logged_today: bool


class GoalProgressLine(BaseModel):
    """One goal, flattened so a home screen can render it without branching.

    `kind` says where it came from: a goal you set yourself, or one you share
    with a buddy. A shared goal moves at the pace of whoever is behind, so its
    `current` is the pair's joint progress, not yours alone.
    """

    kind: str  # "personal" | "shared"
    title: str
    habit_name: str
    current: int
    target: int | None
    percent: int | None
    achieved: bool
    buddy_name: str | None = None
    my_streak: int | None = None
    buddy_streak: int | None = None


class Dashboard(BaseModel):
    display_name: str
    avatar: DuckAvatar
    timezone: str
    # "Today" as the user sees it, which is what every streak is judged against.
    today_local: date
    active_habits: int
    logged_today: int
    habits: list[DashboardHabit]
    badges_earned: int
    unread_notifications: int
    pending_partner_requests: int
    accepted_partnerships: int
    active_shared_goals: int
    goals: list[GoalProgressLine]
