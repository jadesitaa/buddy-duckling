"""API-level tests for logging habits, with freezegun controlling "now"."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

# Every test in this file pretends "now" is Tuesday 10 March 2026, 12:00 UTC
# (19:00 in Bangkok), so streaks are measured against a fixed "today".
NOW = "2026-03-10T12:00:00Z"


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(NOW):
        yield

DAILY_HABIT = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
WEEKLY_HABIT = {
    "name": "Go running",
    "frequency_type": "weekly_n_times",
    "frequency_target": 3,
}


async def create_habit(client: AsyncClient, habit=DAILY_HABIT) -> int:
    return (await client.post("/habits", json=habit)).json()["id"]


async def log(client: AsyncClient, habit_id: int, at: str | None = None):
    payload = {"logged_at_utc": at} if at else {}
    return await client.post(f"/habits/{habit_id}/logs", json=payload)


async def test_first_log_starts_a_streak_of_one(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)

    response = await log(auth_client, habit_id, "2026-03-10T03:00:00Z")

    assert response.status_code == 201
    body = response.json()
    assert body["current_streak"] == 1
    assert body["longest_streak"] == 1
    assert body["log"]["log_date_local"] == "2026-03-10"


async def test_five_consecutive_days_build_a_streak_of_five(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)

    for day in range(6, 11):
        response = await log(auth_client, habit_id, f"2026-03-{day:02d}T03:00:00Z")

    assert response.json()["current_streak"] == 5


async def test_a_missed_day_resets_the_streak(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)
    for day in (6, 7, 8):
        await log(auth_client, habit_id, f"2026-03-{day:02d}T03:00:00Z")

    # Nothing on the 9th - the streak is broken and starts over on the 10th.
    response = await log(auth_client, habit_id, "2026-03-10T03:00:00Z")

    body = response.json()
    assert body["current_streak"] == 1
    assert body["longest_streak"] == 3  # the old run is still remembered


async def test_logging_the_same_day_twice_is_rejected(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)
    await log(auth_client, habit_id, "2026-03-10T03:00:00Z")

    response = await log(auth_client, habit_id, "2026-03-10T09:00:00Z")

    assert response.status_code == 409


async def test_midnight_local_time_counts_as_the_new_day(auth_client: AsyncClient):
    """The user is in Asia/Bangkok (UTC+7), so 17:00 UTC is 00:00 the next day."""
    habit_id = await create_habit(auth_client)

    late = await log(auth_client, habit_id, "2026-03-09T16:59:59Z")
    midnight = await log(auth_client, habit_id, "2026-03-09T17:00:00Z")

    assert late.json()["log"]["log_date_local"] == "2026-03-09"
    assert midnight.json()["log"]["log_date_local"] == "2026-03-10"
    # Two different local days in a row - a streak of 2, not a duplicate.
    assert midnight.json()["current_streak"] == 2


async def test_a_users_timezone_decides_their_local_day(make_user):
    """The same instant is a different day for users in different timezones."""
    same_instant = "2026-03-09T23:30:00Z"

    async with await make_user("bangkok@example.com") as bangkok:
        habit_id = await create_habit(bangkok)
        bangkok_day = (await log(bangkok, habit_id, same_instant)).json()

    async with await make_user("london@example.com") as london:
        await london.put("/users/me", json={"timezone": "Europe/London"})
        habit_id = await create_habit(london)
        london_day = (await log(london, habit_id, same_instant)).json()

    assert bangkok_day["log"]["log_date_local"] == "2026-03-10"
    assert london_day["log"]["log_date_local"] == "2026-03-09"


async def test_weekly_habit_is_not_reset_by_a_missed_day(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client, WEEKLY_HABIT)

    # Mon, Wed, Fri of the week of 2026-03-02 - target of 3 reached.
    for day in ("02", "04", "06"):
        response = await log(auth_client, habit_id, f"2026-03-{day}T03:00:00Z")

    # Days were missed in between, but the week itself hit its target.
    assert response.json()["current_streak"] == 1


async def test_weekly_habit_counts_consecutive_weeks(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client, WEEKLY_HABIT)

    for day in ("02", "04", "06", "09", "11", "13"):
        response = await log(auth_client, habit_id, f"2026-03-{day}T03:00:00Z")

    assert response.json()["current_streak"] == 2


async def test_deleting_a_log_recalculates_the_streak(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)
    for day in (8, 9, 10):
        created = (await log(auth_client, habit_id, f"2026-03-{day:02d}T03:00:00Z")).json()
    assert created["current_streak"] == 3

    # Remove the middle day - the streak is now only the 10th.
    logs = (await auth_client.get(f"/habits/{habit_id}/logs")).json()
    middle = next(item for item in logs if item["log_date_local"] == "2026-03-09")
    response = await auth_client.delete(f"/habits/{habit_id}/logs/{middle['id']}")

    assert response.status_code == 204
    assert (await auth_client.get(f"/habits/{habit_id}")).json()["current_streak"] == 1


async def test_logs_are_listed_newest_first(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)
    for day in (8, 9, 10):
        await log(auth_client, habit_id, f"2026-03-{day:02d}T03:00:00Z")

    logs = (await auth_client.get(f"/habits/{habit_id}/logs")).json()

    assert [item["log_date_local"] for item in logs] == [
        "2026-03-10",
        "2026-03-09",
        "2026-03-08",
    ]


async def test_cannot_log_someone_elses_habit(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user("someone@example.com") as other:
        response = await log(other, habit_id, "2026-03-10T03:00:00Z")

    assert response.status_code == 404


async def test_logging_requires_a_token(client: AsyncClient, auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)

    response = await client.post(f"/habits/{habit_id}/logs", json={})

    assert response.status_code == 401
