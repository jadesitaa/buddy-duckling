# Import every model here so Alembic autogenerate can see them.
from app.models.badge import Badge, UserBadge
from app.models.habit import FrequencyType, Habit
from app.models.habit_log import HabitLog
from app.models.notification import Notification, NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.personal_goal import PersonalGoal
from app.models.shared_goal import SharedGoal
from app.models.user import User

__all__ = [
    "AccountabilityPartner",
    "Badge",
    "FrequencyType",
    "Habit",
    "HabitLog",
    "Notification",
    "NotificationType",
    "PartnershipStatus",
    "PersonalGoal",
    "SharedGoal",
    "User",
    "UserBadge",
]
