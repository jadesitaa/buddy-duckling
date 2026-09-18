"""Badges are awarded on the log that reaches a milestone."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

NOW = "2026-03-10T12:00:00Z"  # Tuesday 10 March 2026, 19:00 in Bangkok
DAILY = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(NOW):
        yield


async def log_days(client: AsyncClient, habit_id: int, *days: int) -> dict:
    response = {}
    for day in days:
        response = (
            await client.post(
                f"/habits/{habit_id}/logs",
                json={"logged_at_utc": f"2026-03-{day:02d}T03:00:00Z"},
            )
        ).json()
    return response


async def test_no_badges_before_the_first_milestone(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    await log_days(auth_client, habit_id, 9, 10)  # a streak of 2

    assert (await auth_client.get("/me/badges")).json() == []


async def test_three_day_streak_earns_the_first_badge(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    await log_days(auth_client, habit_id, 8, 9, 10)

    badges = (await auth_client.get("/me/badges")).json()
    assert [item["badge"]["code"] for item in badges] == ["streak_3"]
    assert badges[0]["habit_id"] == habit_id


async def test_earning_a_badge_sends_a_notification(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    await log_days(auth_client, habit_id, 8, 9, 10)

    types = [
        item["type"] for item in (await auth_client.get("/me/notifications")).json()
    ]
    assert types == ["badge_earned"]


async def test_a_badge_is_never_awarded_twice_for_the_same_habit(
    auth_client: AsyncClient,
):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    await log_days(auth_client, habit_id, 6, 7, 8, 9, 10)  # passes 3 and keeps going

    badges = (await auth_client.get("/me/badges")).json()
    assert [item["badge"]["code"] for item in badges] == ["streak_3"]


async def test_a_week_long_streak_earns_both_milestones(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    await log_days(auth_client, habit_id, 4, 5, 6, 7, 8, 9, 10)

    codes = {
        item["badge"]["code"] for item in (await auth_client.get("/me/badges")).json()
    }
    assert codes == {"streak_3", "streak_7"}


async def test_the_same_badge_can_be_earned_on_a_second_habit(auth_client: AsyncClient):
    first = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    second = (
        await auth_client.post("/habits", json={**DAILY, "name": "Meditate"})
    ).json()["id"]

    await log_days(auth_client, first, 8, 9, 10)
    await log_days(auth_client, second, 8, 9, 10)

    badges = (await auth_client.get("/me/badges")).json()
    assert [item["badge"]["code"] for item in badges] == ["streak_3", "streak_3"]
    assert {item["habit_id"] for item in badges} == {first, second}


async def test_badges_are_private_to_their_owner(auth_client: AsyncClient, make_user):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 8, 9, 10)

    async with await make_user("buddy@example.com") as buddy:
        assert (await buddy.get("/me/badges")).json() == []

    assert len((await auth_client.get("/me/badges")).json()) == 1


async def test_badges_require_a_token(client: AsyncClient):
    assert (await client.get("/me/badges")).status_code == 401
