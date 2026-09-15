from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
