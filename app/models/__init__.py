# Import every model here so Alembic autogenerate can see them.
from app.models.habit import FrequencyType, Habit
from app.models.user import User

__all__ = ["FrequencyType", "Habit", "User"]
