import pytest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "email": "duckling@example.com",
    "password": "quack-quack-123",
    "display_name": "Duckling",
    "timezone": "Asia/Bangkok",
}


async def register(client: AsyncClient, **overrides):
    return await client.post("/auth/register", json={**REGISTER_PAYLOAD, **overrides})


async def test_register_creates_user_without_exposing_password(client: AsyncClient):
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["display_name"] == "Duckling"
    assert body["timezone"] == "Asia/Bangkok"
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient):
    await register(client)

    response = await register(client, display_name="Impostor")

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("field", "value"),
    [("email", "not-an-email"), ("password", "short"), ("display_name", "")],
)
async def test_register_rejects_invalid_input(client: AsyncClient, field, value):
    response = await register(client, **{field: value})

    assert response.status_code == 422


async def test_login_returns_token_pair(client: AsyncClient):
    await register(client)

    response = await client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_rejects_wrong_password(client: AsyncClient):
    await register(client)

    response = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrong-password-123"},
    )

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "quack-quack-123"},
    )

    assert response.status_code == 401


async def test_refresh_returns_new_token_pair(client: AsyncClient):
    await register(client)
    tokens = (
        await client.post(
            "/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
    ).json()

    response = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_refresh_rejects_an_access_token(client: AsyncClient):
    await register(client)
    tokens = (
        await client.post(
            "/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
    ).json()

    response = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )

    assert response.status_code == 401


async def test_me_returns_the_logged_in_user(client: AsyncClient):
    await register(client)
    tokens = (
        await client.post(
            "/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
    ).json()

    response = await client.get(
        "/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == REGISTER_PAYLOAD["email"]


async def test_me_requires_a_token(client: AsyncClient):
    response = await client.get("/users/me")

    assert response.status_code == 401


async def test_me_rejects_a_bogus_token(client: AsyncClient):
    response = await client.get(
        "/users/me", headers={"Authorization": "Bearer not.a.real.token"}
    )

    assert response.status_code == 401
