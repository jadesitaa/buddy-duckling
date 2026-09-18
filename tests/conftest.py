from collections.abc import AsyncGenerator

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db import Base, get_db
from app.models.badge import Badge
from app.main import app

settings = get_settings()

# Mirrors the badge rows seeded by migration 862ce56f3f67.
BADGES = [
    {"code": "streak_3", "title": "Getting started", "milestone_days": 3},
    {"code": "streak_7", "title": "One week strong", "milestone_days": 7},
    {"code": "streak_14", "title": "Two weeks in", "milestone_days": 14},
    {"code": "streak_30", "title": "One month hero", "milestone_days": 30},
    {"code": "streak_100", "title": "Hundred days", "milestone_days": 100},
]


async def _create_test_database() -> None:
    """Create the test database if it does not exist yet."""
    url = settings.test_database_url
    db_name = url.rsplit("/", 1)[1]
    admin_dsn = url.replace("postgresql+asyncpg", "postgresql").rsplit("/", 1)[0]

    conn = await asyncpg.connect(f"{admin_dsn}/postgres")
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session")
async def engine():
    await _create_test_database()
    engine = create_async_engine(settings.test_database_url)
    # The schema is built once for the whole session. Dropping and recreating it
    # per test would hand asyncpg new ids for the enum types while it still has
    # the old ones cached, which fails with "cache lookup failed for type ...".
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """A clean database for every test - the rows go, the schema stays."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        # The badge rows are seeded by a migration, and TRUNCATE just removed
        # them, so put the same list back for every test.
        await conn.execute(insert(Badge), BADGES)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """An API client wired to the test database."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client: AsyncClient):
    """Register a user and return a client that is logged in as them."""

    async def _make_user(email: str = "duckling@example.com") -> AsyncClient:
        await client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "quack-quack-123",
                "display_name": email.split("@")[0],
                "timezone": "Asia/Bangkok",
            },
        )
        tokens = (
            await client.post(
                "/auth/login",
                json={"email": email, "password": "quack-quack-123"},
            )
        ).json()
        logged_in = AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        return logged_in

    return _make_user


@pytest.fixture
async def auth_client(make_user) -> AsyncGenerator[AsyncClient, None]:
    """A client logged in as the default test user."""
    async with await make_user() as logged_in:
        yield logged_in
