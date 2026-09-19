from httpx import AsyncClient

HABIT = {"name": "Read 10 pages", "frequency_type": "daily", "frequency_target": 1}
BUDDY_HABIT = {"name": "Go running", "frequency_type": "weekly_n_times",
               "frequency_target": 3}
BUDDY_EMAIL = "buddy@example.com"


async def create_habit(client: AsyncClient, habit=HABIT) -> int:
    return (await client.post("/habits", json=habit)).json()["id"]


async def invite(client: AsyncClient, habit_id: int, email: str = BUDDY_EMAIL):
    return await client.post(
        f"/habits/{habit_id}/partners", json={"partner_email": email}
    )


async def test_invite_creates_a_pending_partnership(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)
    async with await make_user(BUDDY_EMAIL):
        response = await invite(auth_client, habit_id)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["partner_habit_id"] is None


async def test_invite_notifies_the_invited_user(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        await invite(auth_client, habit_id)

        notifications = (await buddy.get("/me/notifications")).json()

    assert len(notifications) == 1
    assert notifications[0]["type"] == "partner_request"
    assert notifications[0]["is_read"] is False


async def test_inviting_myself_is_rejected(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)

    response = await invite(auth_client, habit_id, "duckling@example.com")

    assert response.status_code == 400


async def test_inviting_an_unknown_email_is_not_found(auth_client: AsyncClient):
    habit_id = await create_habit(auth_client)

    response = await invite(auth_client, habit_id, "ghost@example.com")

    assert response.status_code == 404


async def test_inviting_the_same_person_twice_is_rejected(
    auth_client: AsyncClient, make_user
):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL):
        await invite(auth_client, habit_id)
        response = await invite(auth_client, habit_id)

    assert response.status_code == 409


async def test_cannot_invite_a_partner_to_someone_elses_habit(
    auth_client: AsyncClient, make_user
):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        response = await invite(buddy, habit_id, "duckling@example.com")

    assert response.status_code == 404


async def test_the_invited_user_sees_the_request(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        await invite(auth_client, habit_id)

        requests = (await buddy.get("/me/partner-requests")).json()

    assert len(requests) == 1
    assert requests[0]["habit_id"] == habit_id


async def test_accepting_pairs_the_buddys_own_habit(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]
        buddy_habit_id = await create_habit(buddy, BUDDY_HABIT)

        response = await buddy.put(
            f"/partners/{partnership_id}/accept",
            json={"partner_habit_id": buddy_habit_id},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    # The two sides are on completely different habits, which is allowed.
    assert body["partner_habit_id"] == buddy_habit_id
    assert body["habit_id"] == habit_id


async def test_accepting_notifies_the_inviter(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/accept", json={})

    notifications = (await auth_client.get("/me/notifications")).json()

    assert [item["type"] for item in notifications] == ["partner_accepted"]


async def test_declining_notifies_the_inviter(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]
        response = await buddy.put(f"/partners/{partnership_id}/decline")

    assert response.status_code == 200
    assert response.json()["status"] == "declined"
    notifications = (await auth_client.get("/me/notifications")).json()
    assert [item["type"] for item in notifications] == ["partner_declined"]


async def test_answering_twice_is_rejected(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/accept", json={})

        response = await buddy.put(f"/partners/{partnership_id}/decline")

    assert response.status_code == 409


async def test_the_inviter_cannot_accept_their_own_request(
    auth_client: AsyncClient, make_user
):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL):
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]

    response = await auth_client.put(f"/partners/{partnership_id}/accept", json={})

    assert response.status_code == 404


async def test_cannot_pair_a_habit_that_is_not_mine(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]

        # habit_id belongs to the inviter, not to the buddy.
        response = await buddy.put(
            f"/partners/{partnership_id}/accept", json={"partner_habit_id": habit_id}
        )

    assert response.status_code == 404


async def test_either_side_can_end_the_partnership(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]
        await buddy.put(f"/partners/{partnership_id}/accept", json={})

        response = await buddy.delete(f"/partners/{partnership_id}")

    assert response.status_code == 204
    assert (await auth_client.get(f"/habits/{habit_id}/partners")).json() == []


async def test_a_stranger_cannot_end_the_partnership(auth_client: AsyncClient, make_user):
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL):
        partnership_id = (await invite(auth_client, habit_id)).json()["id"]

    async with await make_user("stranger@example.com") as stranger:
        response = await stranger.delete(f"/partners/{partnership_id}")

    assert response.status_code == 404


async def test_partnership_carries_the_names_a_ui_needs(
    auth_client: AsyncClient, make_user
):
    """The invited side cannot read the inviter's habit, so names come along."""
    habit_id = await create_habit(auth_client)

    async with await make_user(BUDDY_EMAIL) as buddy:
        await invite(auth_client, habit_id)
        buddy_habit_id = await create_habit(buddy, BUDDY_HABIT)
        request = (await buddy.get("/me/partner-requests")).json()[0]

        assert request["habit_name"] == "Read 10 pages"
        assert request["owner_display_name"] == "duckling"
        assert request["partner_display_name"] == "buddy"
        assert request["partner_email"] == BUDDY_EMAIL
        assert request["partner_habit_name"] is None

        accepted = (
            await buddy.put(
                f"/partners/{request['id']}/accept",
                json={"partner_habit_id": buddy_habit_id},
            )
        ).json()

    assert accepted["partner_habit_name"] == "Go running"
