from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.base_entities import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new PLAYER or VENUE_OWNER",
)
async def register(
    user_in: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user account with role PLAYER or VENUE_OWNER."""
    new_user = await auth_service.register_user(session, user_in)
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and return JWT + Refresh Token pair",
)
async def login(
    credentials: UserLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate credentials and issue a 15-minute access token + 7-day refresh token."""
    user = await auth_service.authenticate_user(session, credentials)
    return await auth_service.issue_tokens_for_user(session, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new token pair",
)
async def refresh_tokens(
    refresh_in: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Submit a valid refresh token to receive a fresh access token and rotated refresh token."""
    return await auth_service.refresh_tokens(session, refresh_in.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token",
)
async def logout(
    refresh_in: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Revoke an active refresh token, rendering it unusable for subsequent sessions."""
    await auth_service.revoke_refresh_token(session, refresh_in.refresh_token)
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the profile data of the currently authenticated bearer token user."""
    return current_user
