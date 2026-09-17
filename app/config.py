from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Buddy Duckling"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://buddy:buddy@127.0.0.1:5433/buddy_duckling"
    test_database_url: str = (
        "postgresql+asyncpg://buddy:buddy@127.0.0.1:5433/buddy_duckling_test"
    )

    # Never ship the default secret - set JWT_SECRET_KEY in .env for real deployments.
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
