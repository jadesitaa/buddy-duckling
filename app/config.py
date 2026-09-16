from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Buddy Duckling"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://buddy:buddy@localhost:5433/buddy_duckling"


@lru_cache
def get_settings() -> Settings:
    return Settings()
