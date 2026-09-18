"""The daily job that notices broken streaks and warns the buddies."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

from app.services.streak_check import run_daily_streak_check

DAILY = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
WEEKLY = {"name": "Go running", "frequency_type": "weekly_n_times",
          "frequency_target": 3}
BUDDY_EMAIL = "buddy@example.com"

# Tokens are issued with the clock the test starts on, so time is frozen for the
# whole test - fixtures included - and moved forward with a nested freeze_time.
START = "2026-03-10T12:00:00Z"


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(START):
        yield


async def log_days(client: AsyncClient, habit_id: int, *days: int) -> None:
    for day in days:
        await client.post(
            f"/habits/{habit_id}/logs",
            json={"logged_at_utc": f"2026-03-{day:02d}T03:00:00Z"},
        )


async def test_a_live_streak_is_left_alone(auth_client: AsyncClient, db):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 8, 9, 10)

    broken = await run_daily_streak_check(db)

    assert broken == 0
    assert (await auth_client.get(f"/habits/{habit_id}")).json()["current_streak"] == 3


async def test_a_streak_survives_the_day_after(auth_client: AsyncClient, db):
    """Logged yesterday, nothing today yet - the day is not over, so no reset."""
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 8, 9, 10)

    with freeze_time("2026-03-11T12:00:00Z"):
        broken = await run_daily_streak_check(db)

    # Read back outside the jump: the access token was issued on the 10th and
    # would already have expired on the 11th.
    assert broken == 0
    assert (await auth_client.get(f"/habits/{habit_id}")).json()["current_streak"] == 3


async def test_a_missed_day_resets_the_streak_and_notifies(
    auth_client: AsyncClient, db
):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 8, 9, 10)

    # Two days later, still nothing logged.
    with freeze_time("2026-03-12T12:00:00Z"):
        broken = await run_daily_streak_check(db)

    assert broken == 1
    habit = (await auth_client.get(f"/habits/{habit_id}")).json()
    assert habit["current_streak"] == 0
    assert habit["longest_streak"] == 3  # the record survives

    # The 3 day streak also earned a badge, so look for the break specifically.
    types = [
        item["type"] for item in (await auth_client.get("/me/notifications")).json()
    ]
    assert types[0] == "streak_broken"


async def test_the_job_never_reports_the_same_break_twice(auth_client: AsyncClient, db):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 9, 10)

    with freeze_time("2026-03-12T12:00:00Z"):
        await run_daily_streak_check(db)
        await run_daily_streak_check(db)  # the hourly sweep runs again

    notifications = (await auth_client.get("/me/notifications")).json()

    assert len(notifications) == 1
    assert notifications[0]["type"] == "streak_broken"


async def test_an_accepted_buddy_is_notified(auth_client: AsyncClient, make_user, db):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 9, 10)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/accept", json={})
        await buddy.put("/me/notifications/read-all")

        with freeze_time("2026-03-12T12:00:00Z"):
            await run_daily_streak_check(db)

        buddy_notifications = (
            await buddy.get("/me/notifications?unread_only=true")
        ).json()

    assert [item["type"] for item in buddy_notifications] == ["streak_broken"]
    assert "duckling" in buddy_notifications[0]["title"]


async def test_a_pending_buddy_is_not_notified(auth_client: AsyncClient, make_user, db):
    """No notifications flow until the invitation is accepted."""
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 9, 10)

    async with await make_user(BUDDY_EMAIL) as buddy:
        await auth_client.post(
            f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
        )
        await buddy.put("/me/notifications/read-all")

        with freeze_time("2026-03-12T12:00:00Z"):
            await run_daily_streak_check(db)

        unread = (await buddy.get("/me/notifications?unread_only=true")).json()

    assert unread == []


async def test_notifications_are_bidirectional(auth_client: AsyncClient, make_user, db):
    """The buddy who accepted can break their own streak and warn the inviter."""
    habit_a = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_a}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]
        habit_b = (await buddy.post("/habits", json=DAILY)).json()["id"]
        await buddy.put(
            f"/partners/{partnership_id}/accept", json={"partner_habit_id": habit_b}
        )
        # Only the buddy has a streak, and only the buddy will break it.
        await log_days(buddy, habit_b, 9, 10)
        await auth_client.put("/me/notifications/read-all")

        with freeze_time("2026-03-12T12:00:00Z"):
            await run_daily_streak_check(db)

    unread = (await auth_client.get("/me/notifications?unread_only=true")).json()

    assert [item["type"] for item in unread] == ["streak_broken"]
    assert "buddy" in unread[0]["title"]


async def test_a_weekly_habit_is_not_reset_by_a_missed_day(
    auth_client: AsyncClient, db
):
    habit_id = (await auth_client.post("/habits", json=WEEKLY)).json()["id"]
    # Mon, Wed, Fri of the week of 2 March - the weekly target is met.
    await log_days(auth_client, habit_id, 2, 4, 6)

    # Several days later with nothing logged: a daily habit would be reset here,
    # a weekly one keeps its streak until the week itself falls short.
    with freeze_time("2026-03-12T12:00:00Z"):
        broken = await run_daily_streak_check(db)

    assert broken == 0
    assert (await auth_client.get(f"/habits/{habit_id}")).json()["current_streak"] == 1


async def test_an_inactive_habit_is_skipped(auth_client: AsyncClient, db):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 9, 10)
    await auth_client.put(f"/habits/{habit_id}", json={"is_active": False})

    with freeze_time("2026-03-12T12:00:00Z"):
        broken = await run_daily_streak_check(db)

    assert broken == 0
    assert (await auth_client.get("/me/notifications")).json() == []


async def test_each_user_is_judged_in_their_own_timezone(
    auth_client: AsyncClient, make_user, db
):
    """At 2026-03-11 20:00 UTC it is already the 12th in Bangkok, but still
    the 11th in London - so only the Bangkok user has missed a day."""
    bangkok_habit = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, bangkok_habit, 9, 10)

    async with await make_user("london@example.com") as london:
        await london.put("/users/me", json={"timezone": "Europe/London"})
        london_habit = (await london.post("/habits", json=DAILY)).json()["id"]
        await log_days(london, london_habit, 9, 10)

        with freeze_time("2026-03-11T20:00:00Z"):
            broken = await run_daily_streak_check(db)

        london_streak = (
            await london.get(f"/habits/{london_habit}")
        ).json()["current_streak"]

    assert broken == 1
    assert (await auth_client.get(f"/habits/{bangkok_habit}")).json()[
        "current_streak"
    ] == 0
    assert london_streak == 2
