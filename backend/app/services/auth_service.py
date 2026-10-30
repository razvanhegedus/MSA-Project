from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.models.base_entities import User
from app.models.enums import UserRole
from app.repositories.user_repo import user_repo
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest


class AuthService:
    @staticmethod
    async def register_user(
        session: AsyncSession,
        user_in: UserRegisterRequest,
    ) -> User:
        """Register a new user enforcing unique email and allowed roles."""
        # 1. Enforce allowed roles for self-registration
        if user_in.role not in [UserRole.PLAYER, UserRole.VENUE_OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is only permitted for PLAYER or VENUE_OWNER roles.",
            )

        # 2. Check if email already exists
        existing_user = await user_repo.get_by_email(session, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        # 3. Hash password and persist user
        hashed_password = get_password_hash(user_in.password)
        new_user = await user_repo.create_user(
            session=session,
            user_in=user_in,
            hashed_password=hashed_password,
        )

        # 4. Commit transaction
        await session.commit()
        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        credentials: UserLoginRequest,
    ) -> User:
        """Authenticate user by email and password."""
        user = await user_repo.get_by_email(session, credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    async def issue_tokens_for_user(
        session: AsyncSession,
        user: User,
    ) -> TokenResponse:
        """Generate JWT access token and SHA-256 hashed refresh token pair."""
        # 1. Access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        claims = {
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name,
        }
        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=access_token_expires,
        )

        # 2. Refresh token
        raw_refresh_token = generate_refresh_token()
        hashed_token = hash_refresh_token(raw_refresh_token)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await user_repo.create_refresh_token(
            session=session,
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=refresh_expires_at,
        )

        # 3. Commit transaction
        await session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    async def refresh_tokens(
        session: AsyncSession,
        raw_refresh_token: str,
    ) -> TokenResponse:
        """Validate and rotate an existing refresh token, issuing a new token pair."""
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await user_repo.get_refresh_token_by_hash(session, token_hash)

        if not token_record or token_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        now = datetime.now(timezone.utc)
        if token_record.expires_at < now:
            await user_repo.revoke_refresh_token(session, token_record)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await user_repo.get_by_id(session, token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with this refresh token no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Rotate token: revoke used token
        await user_repo.revoke_refresh_token(session, token_record)

        # Issue new token pair
        return await AuthService.issue_tokens_for_user(session, user)

    @staticmethod
    async def revoke_refresh_token(
        session: AsyncSession,
        raw_refresh_token: str,
    ) -> None:
        """Revoke a refresh token on logout."""
        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await user_repo.get_refresh_token_by_hash(session, token_hash)
        if token_record and not token_record.is_revoked:
            await user_repo.revoke_refresh_token(session, token_record)
            await session.commit()


auth_service = AuthService()
