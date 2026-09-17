from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth, habits, users

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(users.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
