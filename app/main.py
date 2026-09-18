from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.scheduler import create_scheduler
from app.routers import (
    auth,
    badges,
    habit_logs,
    habits,
    notifications,
    partnerships,
    shared_goals,
    stats,
    users,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the background jobs with the app, stop them with it.

    Tests turn the scheduler off (SCHEDULER_ENABLED=false) so they can call the
    job directly instead of waiting for a trigger to fire.
    """
    scheduler = create_scheduler() if settings.scheduler_enabled else None
    if scheduler:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
app.include_router(partnerships.habit_partners)
app.include_router(partnerships.partners)
app.include_router(partnerships.me_partners)
app.include_router(shared_goals.router)
app.include_router(badges.router)
app.include_router(notifications.me_notifications)
app.include_router(notifications.notifications)
app.include_router(stats.habit_stats)
app.include_router(stats.dashboard)
app.include_router(users.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
