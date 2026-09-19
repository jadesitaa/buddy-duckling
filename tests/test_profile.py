"""Profile: display name and the fixed set of duck avatars."""

from httpx import AsyncClient

VALID_AVATARS = {"clover", "nerd", "bow", "adventurer", "foodie", "chill"}


async def test_avatar_catalog_is_public(client: AsyncClient):
    """Sign-up shows the ducks, so this list needs no token."""
    response = await client.get("/avatars")

    assert response.status_code == 200
    options = response.json()
    assert {option["code"] for option in options} == VALID_AVATARS
    assert all(option["title"] and option["description"] for option in options)


async def test_new_users_start_with_the_clover_duck(auth_client: AsyncClient):
    me = (await auth_client.get("/users/me")).json()

    assert me["avatar"] == "clover"


async def test_registering_can_pick_an_avatar(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "nerd@example.com",
            "password": "quack-quack-123",
            "display_name": "Nerdy",
            "avatar": "nerd",
        },
    )

    assert response.status_code == 201
    assert response.json()["avatar"] == "nerd"


async def test_changing_the_display_name_and_avatar(auth_client: AsyncClient):
    response = await auth_client.put(
        "/users/me", json={"display_name": "Jade", "avatar": "foodie"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Jade"
    assert body["avatar"] == "foodie"
    # It really was saved, not just echoed back.
    assert (await auth_client.get("/users/me")).json()["avatar"] == "foodie"


async def test_changing_one_field_leaves_the_other_alone(auth_client: AsyncClient):
    await auth_client.put("/users/me", json={"avatar": "bow"})

    response = await auth_client.put("/users/me", json={"display_name": "Jade"})

    assert response.json()["avatar"] == "bow"


async def test_an_unknown_avatar_is_rejected(auth_client: AsyncClient):
    response = await auth_client.put("/users/me", json={"avatar": "penguin"})

    assert response.status_code == 422
    # The stored value is untouched.
    assert (await auth_client.get("/users/me")).json()["avatar"] == "clover"


async def test_the_dashboard_carries_the_avatar(auth_client: AsyncClient):
    await auth_client.put("/users/me", json={"avatar": "chill"})

    assert (await auth_client.get("/me/dashboard")).json()["avatar"] == "chill"


async def test_a_buddy_sees_my_avatar(auth_client: AsyncClient, make_user):
    """Avatars are how one side recognises the other in a partnership."""
    await auth_client.put("/users/me", json={"avatar": "adventurer"})
    habit_id = (
        await auth_client.post(
            "/habits",
            json={"name": "Read", "frequency_type": "daily", "frequency_target": 1},
        )
    ).json()["id"]

    async with await make_user("buddy@example.com") as buddy:
        await buddy.put("/users/me", json={"avatar": "bow"})
        await auth_client.post(
            f"/habits/{habit_id}/partners", json={"partner_email": "buddy@example.com"}
        )
        request = (await buddy.get("/me/partner-requests")).json()[0]

    assert request["owner_avatar"] == "adventurer"
    assert request["partner_avatar"] == "bow"


async def test_profile_requires_a_token(client: AsyncClient):
    assert (await client.put("/users/me", json={"avatar": "nerd"})).status_code == 401
