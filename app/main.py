from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth, habit_logs, habits, notifications, partnerships, users

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
app.include_router(partnerships.habit_partners)
app.include_router(partnerships.partners)
app.include_router(partnerships.me_partners)
app.include_router(notifications.me_notifications)
app.include_router(notifications.notifications)
app.include_router(users.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
