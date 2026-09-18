"""Shared goals: each side chases its own target, on its own habit."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

# Tuesday 10 March 2026, 19:00 in Bangkok.
NOW = "2026-03-10T12:00:00Z"

DAILY = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
WEEKLY = {"name": "Go running", "frequency_type": "weekly_n_times",
          "frequency_target": 3}
BUDDY_EMAIL = "buddy@example.com"
GOAL = {
    "title": "Ice cream together",
    "reward_description": "The good place downtown",
    "target_streak_a": 3,
    "target_streak_b": 2,
}


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(NOW):
        yield


async def log_days(client: AsyncClient, habit_id: int, *days: int) -> dict:
    """Log a habit on the given days of March 2026, 10:00 Bangkok time."""
    response = {}
    for day in days:
        response = (
            await client.post(
                f"/habits/{habit_id}/logs",
                json={"logged_at_utc": f"2026-03-{day:02d}T03:00:00Z"},
            )
        ).json()
    return response


@pytest.fixture
async def paired(auth_client: AsyncClient, make_user):
    """An accepted partnership: the owner and a buddy, each with their own habit."""
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

        yield {
            "owner": auth_client,
            "buddy": buddy,
            "partnership_id": partnership_id,
            "habit_a": habit_a,
            "habit_b": habit_b,
        }


async def test_create_goal_starts_unachieved(paired):
    response = await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    assert response.status_code == 201
    body = response.json()
    assert body["achieved_at"] is None
    assert body["target_streak_a"] == 3
    assert body["target_streak_b"] == 2
    assert body["reached_a"] is False
    assert body["reached_b"] is False


async def test_both_sides_can_see_the_goal(paired):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    from_buddy = await paired["buddy"].get(
        f"/partnerships/{paired['partnership_id']}/goals"
    )

    assert [goal["title"] for goal in from_buddy.json()] == ["Ice cream together"]


async def test_a_stranger_cannot_see_the_goal(paired, make_user):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    async with await make_user("stranger@example.com") as stranger:
        response = await stranger.get(
            f"/partnerships/{paired['partnership_id']}/goals"
        )

    assert response.status_code == 404


async def test_progress_follows_each_side_separately(paired):
    goal_id = (
        await paired["owner"].post(
            f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
        )
    ).json()["id"]
    assert goal_id

    # Side A reaches its target of 3; side B has done nothing yet.
    await log_days(paired["owner"], paired["habit_a"], 8, 9, 10)

    goal = (
        await paired["owner"].get(f"/partnerships/{paired['partnership_id']}/goals")
    ).json()[0]

    assert goal["current_streak_a"] == 3
    assert goal["current_streak_b"] == 0
    assert goal["reached_a"] is True
    assert goal["reached_b"] is False
    assert goal["achieved_at"] is None


async def test_the_first_side_is_told_it_is_waiting(paired):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    await log_days(paired["owner"], paired["habit_a"], 8, 9, 10)

    types = [
        item["type"]
        for item in (await paired["owner"].get("/me/notifications")).json()
    ]
    assert "waiting_for_partner" in types
    # The buddy is not told anything yet - they have not finished.
    buddy_types = [
        item["type"]
        for item in (await paired["buddy"].get("/me/notifications")).json()
    ]
    assert "waiting_for_partner" not in buddy_types


async def test_waiting_is_only_announced_once(paired):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    # Keep logging after the target is already met.
    await log_days(paired["owner"], paired["habit_a"], 6, 7, 8, 9, 10)

    waiting = [
        item
        for item in (await paired["owner"].get("/me/notifications")).json()
        if item["type"] == "waiting_for_partner"
    ]
    assert len(waiting) == 1


async def test_goal_is_achieved_only_when_both_sides_finish(paired):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    await log_days(paired["owner"], paired["habit_a"], 8, 9, 10)
    goal = (
        await paired["owner"].get(f"/partnerships/{paired['partnership_id']}/goals")
    ).json()[0]
    assert goal["achieved_at"] is None  # still waiting on side B

    # Side B now reaches its own, different target of 2.
    await log_days(paired["buddy"], paired["habit_b"], 9, 10)

    goal = (
        await paired["buddy"].get(f"/partnerships/{paired['partnership_id']}/goals")
    ).json()[0]
    assert goal["achieved_at"] is not None
    assert goal["reached_a"] is True
    assert goal["reached_b"] is True


async def test_both_sides_are_notified_when_the_goal_is_achieved(paired):
    await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
    )

    await log_days(paired["owner"], paired["habit_a"], 8, 9, 10)
    await log_days(paired["buddy"], paired["habit_b"], 9, 10)

    for side in ("owner", "buddy"):
        types = [
            item["type"] for item in (await paired[side].get("/me/notifications")).json()
        ]
        assert "goal_achieved" in types


async def test_the_two_sides_can_be_on_different_habit_types(auth_client, make_user):
    """Side A on a daily habit, side B on a weekly one - both still count."""
    habit_a = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_a}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]
        habit_b = (await buddy.post("/habits", json=WEEKLY)).json()["id"]
        await buddy.put(
            f"/partners/{partnership_id}/accept", json={"partner_habit_id": habit_b}
        )
        await auth_client.post(
            f"/partnerships/{partnership_id}/goals",
            json={**GOAL, "target_streak_a": 2, "target_streak_b": 1},
        )

        await log_days(auth_client, habit_a, 9, 10)
        # One full week on target is a weekly streak of 1.
        await log_days(buddy, habit_b, 2, 4, 6)

        goal = (
            await buddy.get(f"/partnerships/{partnership_id}/goals")
        ).json()[0]

    assert goal["current_streak_a"] == 2
    assert goal["current_streak_b"] == 1
    assert goal["achieved_at"] is not None


async def test_goal_needs_an_accepted_partnership(auth_client: AsyncClient, make_user):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL):
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]

        response = await auth_client.post(
            f"/partnerships/{partnership_id}/goals", json=GOAL
        )

    assert response.status_code == 409


async def test_goal_needs_both_habits_paired(auth_client: AsyncClient, make_user):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]
        # Accepted without pairing a habit of their own.
        await buddy.put(f"/partners/{partnership_id}/accept", json={})

        response = await auth_client.post(
            f"/partnerships/{partnership_id}/goals", json=GOAL
        )

    assert response.status_code == 409


async def test_either_side_can_delete_a_goal(paired):
    goal_id = (
        await paired["owner"].post(
            f"/partnerships/{paired['partnership_id']}/goals", json=GOAL
        )
    ).json()["id"]

    response = await paired["buddy"].delete(
        f"/partnerships/{paired['partnership_id']}/goals/{goal_id}"
    )

    assert response.status_code == 204
    assert (
        await paired["owner"].get(f"/partnerships/{paired['partnership_id']}/goals")
    ).json() == []


async def test_invalid_targets_are_rejected(paired):
    response = await paired["owner"].post(
        f"/partnerships/{paired['partnership_id']}/goals",
        json={**GOAL, "target_streak_a": 0},
    )

    assert response.status_code == 422
