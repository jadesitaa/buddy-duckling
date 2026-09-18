# Import every model here so Alembic autogenerate can see them.
from app.models.habit import FrequencyType, Habit
from app.models.habit_log import HabitLog
from app.models.notification import Notification, NotificationType
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.user import User

__all__ = [
    "AccountabilityPartner",
    "FrequencyType",
    "Habit",
    "HabitLog",
    "Notification",
    "NotificationType",
    "PartnershipStatus",
    "User",
]
