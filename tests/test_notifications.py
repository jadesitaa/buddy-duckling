from httpx import AsyncClient

HABIT = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
BUDDY_EMAIL = "buddy@example.com"


async def make_two_notifications(auth_client: AsyncClient, make_user) -> None:
    """Invite a buddy, have them decline, then invite again - two notifications."""
    habit_id = (await auth_client.post("/habits", json=HABIT)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (
            await auth_client.post(
                f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
            )
        ).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/decline")

        second_habit_id = (
            await auth_client.post("/habits", json={**HABIT, "name": "Meditate"})
        ).json()["id"]
        partnership_id = (
            await auth_client.post(
                f"/habits/{second_habit_id}/partners",
                json={"partner_email": BUDDY_EMAIL},
            )
        ).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/decline")


async def test_notifications_start_empty(auth_client: AsyncClient):
    assert (await auth_client.get("/me/notifications")).json() == []
    assert (await auth_client.get("/me/notifications/unread-count")).json() == {
        "unread": 0
    }


async def test_unread_count_follows_new_notifications(
    auth_client: AsyncClient, make_user
):
    await make_two_notifications(auth_client, make_user)

    assert (await auth_client.get("/me/notifications/unread-count")).json() == {
        "unread": 2
    }


async def test_marking_one_as_read_lowers_the_count(
    auth_client: AsyncClient, make_user
):
    await make_two_notifications(auth_client, make_user)
    first = (await auth_client.get("/me/notifications")).json()[0]

    response = await auth_client.put(f"/notifications/{first['id']}/read")

    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert (await auth_client.get("/me/notifications/unread-count")).json() == {
        "unread": 1
    }


async def test_unread_only_filter(auth_client: AsyncClient, make_user):
    await make_two_notifications(auth_client, make_user)
    first = (await auth_client.get("/me/notifications")).json()[0]
    await auth_client.put(f"/notifications/{first['id']}/read")

    unread = (await auth_client.get("/me/notifications?unread_only=true")).json()

    assert len(unread) == 1
    assert unread[0]["id"] != first["id"]


async def test_read_all_clears_the_count(auth_client: AsyncClient, make_user):
    await make_two_notifications(auth_client, make_user)

    response = await auth_client.put("/me/notifications/read-all")

    assert response.json() == {"unread": 0}
    assert all(
        item["is_read"] for item in (await auth_client.get("/me/notifications")).json()
    )


async def test_i_only_see_my_own_notifications(auth_client: AsyncClient, make_user):
    habit_id = (await auth_client.post("/habits", json=HABIT)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        await auth_client.post(
            f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
        )
        buddy_notifications = (await buddy.get("/me/notifications")).json()

    # The invite notification belongs to the buddy, not to the inviter.
    assert len(buddy_notifications) == 1
    assert (await auth_client.get("/me/notifications")).json() == []


async def test_cannot_mark_someone_elses_notification_as_read(
    auth_client: AsyncClient, make_user
):
    habit_id = (await auth_client.post("/habits", json=HABIT)).json()["id"]

    async with await make_user(BUDDY_EMAIL) as buddy:
        await auth_client.post(
            f"/habits/{habit_id}/partners", json={"partner_email": BUDDY_EMAIL}
        )
        buddy_notification_id = (await buddy.get("/me/notifications")).json()[0]["id"]

    response = await auth_client.put(f"/notifications/{buddy_notification_id}/read")

    assert response.status_code == 404


async def test_notifications_require_a_token(client: AsyncClient):
    assert (await client.get("/me/notifications")).status_code == 401
