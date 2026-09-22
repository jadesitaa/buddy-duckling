"""Goals you set for yourself: optional target, progress, no buddy involved."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

NOW = "2026-03-10T12:00:00Z"  # Tuesday 10 March 2026, 19:00 in Bangkok
DAILY = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(NOW):
        yield


async def make_habit(client: AsyncClient) -> int:
    return (await client.post("/habits", json=DAILY)).json()["id"]


async def log_days(client: AsyncClient, habit_id: int, *days: int) -> None:
    for day in days:
        await client.post(
            f"/habits/{habit_id}/logs",
            json={"logged_at_utc": f"2026-03-{day:02d}T03:00:00Z"},
        )


async def test_a_goal_with_a_target_tracks_progress(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)
    await auth_client.post(
        f"/habits/{habit_id}/goals", json={"title": "Read for a week", "target_days": 4}
    )

    await log_days(auth_client, habit_id, 9, 10)

    goal = (await auth_client.get(f"/habits/{habit_id}/goals")).json()[0]
    assert goal["current_streak"] == 2
    assert goal["target_days"] == 4
    assert goal["percent"] == 50
    assert goal["days_remaining"] == 2
    assert goal["achieved_at"] is None


async def test_a_goal_without_a_target_just_counts(auth_client: AsyncClient):
    """A solo goal needs no deadline to be useful."""
    habit_id = await make_habit(auth_client)
    await auth_client.post(f"/habits/{habit_id}/goals", json={"title": "Keep reading"})

    await log_days(auth_client, habit_id, 9, 10)

    goal = (await auth_client.get(f"/habits/{habit_id}/goals")).json()[0]
    assert goal["target_days"] is None
    assert goal["current_streak"] == 2
    assert goal["percent"] is None
    assert goal["days_remaining"] is None
    assert goal["achieved_at"] is None


async def test_reaching_the_target_finishes_the_goal_and_notifies(
    auth_client: AsyncClient,
):
    habit_id = await make_habit(auth_client)
    await auth_client.post(
        f"/habits/{habit_id}/goals",
        json={"title": "Two days", "target_days": 2, "reward_description": "A nap"},
    )

    await log_days(auth_client, habit_id, 9, 10)

    goal = (await auth_client.get(f"/habits/{habit_id}/goals")).json()[0]
    assert goal["achieved_at"] is not None
    assert goal["percent"] == 100
    assert goal["days_remaining"] == 0

    achieved = [
        item
        for item in (await auth_client.get("/me/notifications")).json()
        if item["type"] == "goal_achieved"
    ]
    assert "A nap" in achieved[0]["body"]


async def test_an_open_ended_goal_is_never_achieved(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)
    await auth_client.post(f"/habits/{habit_id}/goals", json={"title": "Forever"})

    await log_days(auth_client, habit_id, 6, 7, 8, 9, 10)

    goal = (await auth_client.get(f"/habits/{habit_id}/goals")).json()[0]
    assert goal["current_streak"] == 5
    assert goal["achieved_at"] is None
    assert (await auth_client.get("/me/notifications")).json()[0]["type"] != "goal_achieved"


async def test_a_finished_goal_is_only_announced_once(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)
    await auth_client.post(
        f"/habits/{habit_id}/goals", json={"title": "Two days", "target_days": 2}
    )

    await log_days(auth_client, habit_id, 8, 9, 10)  # passes the target and keeps going

    achieved = [
        item
        for item in (await auth_client.get("/me/notifications")).json()
        if item["type"] == "goal_achieved"
    ]
    assert len(achieved) == 1


async def test_progress_never_exceeds_one_hundred_percent(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)
    await auth_client.post(
        f"/habits/{habit_id}/goals", json={"title": "One day", "target_days": 1}
    )

    await log_days(auth_client, habit_id, 6, 7, 8, 9, 10)

    goal = (await auth_client.get(f"/habits/{habit_id}/goals")).json()[0]
    assert goal["percent"] == 100
    assert goal["days_remaining"] == 0


async def test_my_goals_lists_every_habit(auth_client: AsyncClient):
    first = await make_habit(auth_client)
    second = (
        await auth_client.post("/habits", json={**DAILY, "name": "Meditate"})
    ).json()["id"]
    await auth_client.post(f"/habits/{first}/goals", json={"title": "Read more"})
    await auth_client.post(
        f"/habits/{second}/goals", json={"title": "Sit still", "target_days": 30}
    )

    goals = (await auth_client.get("/me/goals")).json()

    assert [goal["title"] for goal in goals] == ["Read more", "Sit still"]
    assert [goal["habit_name"] for goal in goals] == ["Read 10 pages", "Meditate"]


async def test_deleting_a_goal(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)
    goal_id = (
        await auth_client.post(f"/habits/{habit_id}/goals", json={"title": "Read more"})
    ).json()["id"]

    response = await auth_client.delete(f"/habits/{habit_id}/goals/{goal_id}")

    assert response.status_code == 204
    assert (await auth_client.get("/me/goals")).json() == []


async def test_cannot_set_a_goal_on_someone_elses_habit(
    auth_client: AsyncClient, make_user
):
    habit_id = await make_habit(auth_client)

    async with await make_user("buddy@example.com") as buddy:
        response = await buddy.post(
            f"/habits/{habit_id}/goals", json={"title": "Mine now"}
        )

    assert response.status_code == 404


async def test_goals_are_private(auth_client: AsyncClient, make_user):
    habit_id = await make_habit(auth_client)
    await auth_client.post(f"/habits/{habit_id}/goals", json={"title": "Read more"})

    async with await make_user("buddy@example.com") as buddy:
        assert (await buddy.get("/me/goals")).json() == []


async def test_a_zero_day_target_is_rejected(auth_client: AsyncClient):
    habit_id = await make_habit(auth_client)

    response = await auth_client.post(
        f"/habits/{habit_id}/goals", json={"title": "Nope", "target_days": 0}
    )

    assert response.status_code == 422
