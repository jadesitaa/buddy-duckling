from httpx import AsyncClient

DAILY_HABIT = {
    "name": "Read 10 pages",
    "description": "Before bed",
    "frequency_type": "daily",
    "frequency_target": 1,
}
WEEKLY_HABIT = {
    "name": "Go running",
    "frequency_type": "weekly_n_times",
    "frequency_target": 3,
}


async def test_create_habit_starts_with_zero_streak(auth_client: AsyncClient):
    response = await auth_client.post("/habits", json=DAILY_HABIT)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Read 10 pages"
    assert body["frequency_type"] == "daily"
    assert body["current_streak"] == 0
    assert body["longest_streak"] == 0
    assert body["is_active"] is True


async def test_create_weekly_habit_keeps_its_target(auth_client: AsyncClient):
    response = await auth_client.post("/habits", json=WEEKLY_HABIT)

    assert response.status_code == 201
    assert response.json()["frequency_target"] == 3


async def test_create_rejects_daily_habit_with_target_above_one(
    auth_client: AsyncClient,
):
    response = await auth_client.post(
        "/habits", json={**DAILY_HABIT, "frequency_target": 3}
    )

    assert response.status_code == 422


async def test_create_requires_a_token(client: AsyncClient):
    response = await client.post("/habits", json=DAILY_HABIT)

    assert response.status_code == 401


async def test_list_returns_only_my_habits(auth_client: AsyncClient, make_user):
    await auth_client.post("/habits", json=DAILY_HABIT)
    async with await make_user("someone@example.com") as other:
        await other.post("/habits", json=WEEKLY_HABIT)

        their_habits = (await other.get("/habits")).json()

    my_habits = (await auth_client.get("/habits")).json()

    assert [h["name"] for h in my_habits] == ["Read 10 pages"]
    assert [h["name"] for h in their_habits] == ["Go running"]


async def test_list_hides_inactive_habits_unless_asked(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]
    await auth_client.put(f"/habits/{habit_id}", json={"is_active": False})

    assert (await auth_client.get("/habits")).json() == []
    assert len((await auth_client.get("/habits?include_inactive=true")).json()) == 1


async def test_get_habit_returns_it(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    response = await auth_client.get(f"/habits/{habit_id}")

    assert response.status_code == 200
    assert response.json()["id"] == habit_id


async def test_get_someone_elses_habit_is_not_found(
    auth_client: AsyncClient, make_user
):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    async with await make_user("someone@example.com") as other:
        response = await other.get(f"/habits/{habit_id}")

    assert response.status_code == 404


async def test_update_changes_only_the_fields_sent(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    response = await auth_client.put(f"/habits/{habit_id}", json={"name": "Read more"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Read more"
    assert body["description"] == "Before bed"


async def test_update_someone_elses_habit_is_not_found(
    auth_client: AsyncClient, make_user
):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    async with await make_user("someone@example.com") as other:
        response = await other.put(f"/habits/{habit_id}", json={"name": "Mine now"})

    assert response.status_code == 404


async def test_delete_removes_the_habit(auth_client: AsyncClient):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    response = await auth_client.delete(f"/habits/{habit_id}")

    assert response.status_code == 204
    assert (await auth_client.get(f"/habits/{habit_id}")).status_code == 404


async def test_delete_someone_elses_habit_is_not_found(
    auth_client: AsyncClient, make_user
):
    habit_id = (await auth_client.post("/habits", json=DAILY_HABIT)).json()["id"]

    async with await make_user("someone@example.com") as other:
        response = await other.delete(f"/habits/{habit_id}")

    assert response.status_code == 404
    assert (await auth_client.get(f"/habits/{habit_id}")).status_code == 200


async def test_unknown_habit_is_not_found(auth_client: AsyncClient):
    assert (await auth_client.get("/habits/9999")).status_code == 404
