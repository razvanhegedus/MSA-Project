import uuid
import pytest
from httpx import AsyncClient

from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_auth_workflow(client: AsyncClient):
    """Verify registration, login, me endpoint, and token rotation for PLAYER and VENUE_OWNER."""
    uid = uuid.uuid4().hex[:8]
    owner_email = f"owner_{uid}@example.com"
    player_email = f"player_{uid}@example.com"
    password = "SecurePassword123!"

    # 1. Register VENUE_OWNER
    owner_reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": owner_email,
            "password": password,
            "full_name": "Pitch Owner",
            "phone": "+40712345678",
            "role": UserRole.VENUE_OWNER.value,
        },
    )
    assert owner_reg_resp.status_code == 201, owner_reg_resp.text
    owner_data = owner_reg_resp.json()
    assert owner_data["email"] == owner_email
    assert owner_data["role"] == UserRole.VENUE_OWNER.value
    assert "id" in owner_data

    # 2. Register PLAYER
    player_reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": player_email,
            "password": password,
            "full_name": "Football Player",
            "phone": "+40787654321",
            "role": UserRole.PLAYER.value,
        },
    )
    assert player_reg_resp.status_code == 201, player_reg_resp.text
    player_data = player_reg_resp.json()
    assert player_data["email"] == player_email
    assert player_data["role"] == UserRole.PLAYER.value

    # 3. Duplicate email registration rejected
    dup_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": owner_email,
            "password": password,
            "full_name": "Duplicate User",
            "phone": "+40711111111",
            "role": UserRole.VENUE_OWNER.value,
        },
    )
    assert dup_resp.status_code == 409

    # 4. Direct registration as ADMIN rejected
    admin_reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"admin_{uid}@example.com",
            "password": password,
            "full_name": "Admin User",
            "phone": "+40799999999",
            "role": UserRole.ADMIN.value,
        },
    )
    assert admin_reg_resp.status_code == 403

    # 5. Login as VENUE_OWNER
    owner_login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": owner_email,
            "password": password,
        },
    )
    assert owner_login_resp.status_code == 200
    owner_tokens = owner_login_resp.json()
    assert "access_token" in owner_tokens
    assert "refresh_token" in owner_tokens
    assert owner_tokens["token_type"] == "bearer"

    # 6. Login as PLAYER
    player_login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": player_email,
            "password": password,
        },
    )
    assert player_login_resp.status_code == 200
    player_tokens = player_login_resp.json()
    assert "access_token" in player_tokens
    assert "refresh_token" in player_tokens

    # 7. Invalid password rejected
    bad_login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": owner_email,
            "password": "WrongPassword!",
        },
    )
    assert bad_login_resp.status_code == 401

    # 8. Access /me endpoint with access token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == owner_email
    assert me_resp.json()["role"] == UserRole.VENUE_OWNER.value

    # 9. Rotate refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": owner_tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    rotated_tokens = refresh_resp.json()
    assert "access_token" in rotated_tokens
    assert "refresh_token" in rotated_tokens
    assert rotated_tokens["refresh_token"] != owner_tokens["refresh_token"]

    # 10. Attempting to reuse revoked old refresh token fails
    reused_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": owner_tokens["refresh_token"]},
    )
    assert reused_resp.status_code == 401

    # 11. Logout with current refresh token
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": rotated_tokens["refresh_token"]},
    )
    assert logout_resp.status_code == 200

    # 12. Token revoked after logout
    post_logout_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_tokens["refresh_token"]},
    )
    assert post_logout_refresh.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_control(client: AsyncClient):
    """Test require_role dependency using dynamically mounted test endpoints."""
    from fastapi import APIRouter, Depends
    from app.api.dependencies import require_role
    from app.models.base_entities import User
    from app.main import app

    test_router = APIRouter(prefix="/api/v1/test-roles")

    @test_router.get("/owner-only")
    async def owner_only_endpoint(user: User = Depends(require_role(UserRole.VENUE_OWNER))):
        return {"role": user.role.value, "access": "granted"}

    @test_router.get("/player-only")
    async def player_only_endpoint(user: User = Depends(require_role(UserRole.PLAYER))):
        return {"role": user.role.value, "access": "granted"}

    app.include_router(test_router)

    uid = uuid.uuid4().hex[:8]
    # Register & login Owner
    owner_email = f"role_owner_{uid}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": owner_email,
            "password": "Password123!",
            "full_name": "Test Owner",
            "phone": "+40711223344",
            "role": UserRole.VENUE_OWNER.value,
        },
    )
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": "Password123!"},
    )
    owner_token = owner_login.json()["access_token"]

    # Register & login Player
    player_email = f"role_player_{uid}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": player_email,
            "password": "Password123!",
            "full_name": "Test Player",
            "phone": "+40755667788",
            "role": UserRole.PLAYER.value,
        },
    )
    player_login = await client.post(
        "/api/v1/auth/login",
        json={"email": player_email, "password": "Password123!"},
    )
    player_token = player_login.json()["access_token"]

    # 1. Owner accesses owner-only: 200 OK
    resp = await client.get(
        "/api/v1/test-roles/owner-only",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["access"] == "granted"

    # 2. Player accesses owner-only: 403 Forbidden
    resp = await client.get(
        "/api/v1/test-roles/owner-only",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403

    # 3. Player accesses player-only: 200 OK
    resp = await client.get(
        "/api/v1/test-roles/player-only",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["access"] == "granted"

    # 4. Owner accesses player-only: 403 Forbidden
    resp = await client.get(
        "/api/v1/test-roles/player-only",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert resp.status_code == 403

