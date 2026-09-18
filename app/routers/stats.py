from fastapi import APIRouter
from sqlalchemy import or_, select

from app.deps import CurrentUser, DbSession
from app.models.badge import UserBadge
from app.models.habit import Habit
from app.models.notification import Notification
from app.models.partnership import AccountabilityPartner, PartnershipStatus
from app.models.shared_goal import SharedGoal
from app.routers.habits import get_own_habit
from app.schemas.stats import Dashboard, HabitStats
from app.services.stats import build_dashboard_habits, build_habit_stats, count_rows

habit_stats = APIRouter(prefix="/habits/{habit_id}", tags=["stats"])
dashboard = APIRouter(prefix="/me", tags=["stats"])


def _partnerships_of(user_id: int):
    """A partnership is mine whether I sent the invite or accepted one."""
    my_habits = select(Habit.id).where(Habit.user_id == user_id)
    return or_(
        AccountabilityPartner.partner_user_id == user_id,
        AccountabilityPartner.habit_id.in_(my_habits),
    )


@habit_stats.get("/stats", response_model=HabitStats)
async def read_habit_stats(
    habit_id: int, current_user: CurrentUser, db: DbSession
) -> HabitStats:
    habit = await get_own_habit(habit_id, current_user, db)
    return await build_habit_stats(db, habit, current_user)


@dashboard.get("/dashboard", response_model=Dashboard)
async def read_dashboard(current_user: CurrentUser, db: DbSession) -> Dashboard:
    """Everything a home screen needs, in a single request."""
    habits, today = await build_dashboard_habits(db, current_user)
    mine = _partnerships_of(current_user.id)

    my_accepted_partnerships = select(AccountabilityPartner.id).where(
        AccountabilityPartner.status == PartnershipStatus.ACCEPTED, mine
    )

    return Dashboard(
        display_name=current_user.display_name,
        timezone=current_user.timezone,
        today_local=today,
        active_habits=len(habits),
        logged_today=sum(1 for habit in habits if habit.logged_today),
        habits=habits,
        badges_earned=await count_rows(
            db, UserBadge, UserBadge.user_id == current_user.id
        ),
        unread_notifications=await count_rows(
            db,
            Notification,
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        ),
        pending_partner_requests=await count_rows(
            db,
            AccountabilityPartner,
            AccountabilityPartner.partner_user_id == current_user.id,
            AccountabilityPartner.status == PartnershipStatus.PENDING,
        ),
        accepted_partnerships=await count_rows(
            db,
            AccountabilityPartner,
            AccountabilityPartner.status == PartnershipStatus.ACCEPTED,
            mine,
        ),
        active_shared_goals=await count_rows(
            db,
            SharedGoal,
            SharedGoal.achieved_at.is_(None),
            SharedGoal.partnership_id.in_(my_accepted_partnerships),
        ),
    )
