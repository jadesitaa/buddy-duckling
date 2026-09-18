"""Read-only summaries: per-habit stats and the dashboard."""

import pytest
from freezegun import freeze_time
from httpx import AsyncClient

NOW = "2026-03-10T12:00:00Z"  # Tuesday 10 March 2026, 19:00 in Bangkok
DAILY = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
WEEKLY = {"name": "Go running", "frequency_type": "weekly_n_times",
          "frequency_target": 3}
BUDDY_EMAIL = "buddy@example.com"


@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time(NOW):
        yield


async def log_days(client: AsyncClient, habit_id: int, *days: int) -> None:
    for day in days:
        await client.post(
            f"/habits/{habit_id}/logs",
            json={"logged_at_utc": f"2026-03-{day:02d}T03:00:00Z"},
        )


async def test_stats_for_a_habit_with_no_logs(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    stats = (await auth_client.get(f"/habits/{habit_id}/stats")).json()

    assert stats["total_logs"] == 0
    assert stats["first_log_date"] is None
    assert stats["last_log_date"] is None
    assert stats["logged_today"] is False
    assert stats["completion_rate_30d"] == 0
    assert stats["current_streak"] == 0


async def test_stats_summarise_the_logs(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 6, 8, 9, 10)

    stats = (await auth_client.get(f"/habits/{habit_id}/stats")).json()

    assert stats["total_logs"] == 4
    assert stats["first_log_date"] == "2026-03-06"
    assert stats["last_log_date"] == "2026-03-10"
    assert stats["logged_today"] is True
    assert stats["current_streak"] == 3  # the 8th, 9th and 10th
    assert stats["completion_rate_30d"] == round(4 / 30, 3)


async def test_logs_this_week_counts_the_current_week_only(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=WEEKLY)).json()["id"]
    # 2 + 4 + 6 March is last week; 9 + 10 March is this week.
    await log_days(auth_client, habit_id, 2, 4, 6, 9, 10)

    stats = (await auth_client.get(f"/habits/{habit_id}/stats")).json()

    assert stats["logs_this_week"] == 2
    assert stats["frequency_target"] == 3


async def test_stats_of_someone_elses_habit_are_not_found(
    auth_client: AsyncClient, make_user
):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        response = await buddy.get(f"/habits/{habit_id}/stats")

    assert response.status_code == 404


async def test_dashboard_of_a_brand_new_user(auth_client: AsyncClient):
    dashboard = (await auth_client.get("/me/dashboard")).json()

    assert dashboard["display_name"] == "duckling"
    assert dashboard["timezone"] == "Asia/Bangkok"
    assert dashboard["today_local"] == "2026-03-10"
    assert dashboard["active_habits"] == 0
    assert dashboard["habits"] == []
    assert dashboard["badges_earned"] == 0
    assert dashboard["unread_notifications"] == 0


async def test_dashboard_shows_what_is_done_today(auth_client: AsyncClient):
    done = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await auth_client.post("/habits", json={**DAILY, "name": "Meditate"})
    await log_days(auth_client, done, 9, 10)

    dashboard = (await auth_client.get("/me/dashboard")).json()

    assert dashboard["active_habits"] == 2
    assert dashboard["logged_today"] == 1
    by_name = {habit["name"]: habit for habit in dashboard["habits"]}
    assert by_name["Read 10 pages"]["logged_today"] is True
    assert by_name["Read 10 pages"]["current_streak"] == 2
    assert by_name["Meditate"]["logged_today"] is False


async def test_dashboard_hides_inactive_habits(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await auth_client.put(f"/habits/{habit_id}", json={"is_active": False})

    dashboard = (await auth_client.get("/me/dashboard")).json()

    assert dashboard["active_habits"] == 0


async def test_dashboard_counts_badges_and_notifications(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY)).json()["id"]
    await log_days(auth_client, habit_id, 8, 9, 10)  # earns the 3 day badge

    dashboard = (await auth_client.get("/me/dashboard")).json()

    assert dashboard["badges_earned"] == 1
    assert dashboard["unread_notifications"] == 1


async def test_dashboard_counts_buddy_activity_from_both_sides(
    auth_client: AsyncClient, make_user
):
    habit_a = (await auth_client.post("/habits", json=DAILY)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_a}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]

        # Before accepting: the buddy has a request waiting, I have none.
        buddy_dashboard = (await buddy.get("/me/dashboard")).json()
        assert buddy_dashboard["pending_partner_requests"] == 1
        assert (await auth_client.get("/me/dashboard")).json()[
            "pending_partner_requests"
        ] == 0

        habit_b = (await buddy.post("/habits", json=DAILY)).json()["id"]
        await buddy.put(
            f"/partners/{partnership_id}/accept", json={"partner_habit_id": habit_b}
        )
        await auth_client.post(
            f"/partnerships/{partnership_id}/goals",
            json={"title": "Ice cream", "target_streak_a": 5, "target_streak_b": 5},
        )

        buddy_dashboard = (await buddy.get("/me/dashboard")).json()

    my_dashboard = (await auth_client.get("/me/dashboard")).json()

    # Both sides see the same partnership and the same open goal.
    assert my_dashboard["accepted_partnerships"] == 1
    assert my_dashboard["active_shared_goals"] == 1
    assert buddy_dashboard["accepted_partnerships"] == 1
    assert buddy_dashboard["active_shared_goals"] == 1


async def test_dashboard_requires_a_token(client: AsyncClient):
    assert (await client.get("/me/dashboard")).status_code == 401
