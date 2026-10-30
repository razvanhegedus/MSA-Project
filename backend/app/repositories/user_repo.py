import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_entities import RefreshToken, User
from app.schemas.auth import UserRegisterRequest


class UserRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key ID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by case-insensitive normalized email."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        user_in: UserRegisterRequest,
        hashed_password: str,
    ) -> User:
        """Create and flush a new user record."""
        user = User(
            email=user_in.email.lower().strip(),
            hashed_password=hashed_password,
            full_name=user_in.full_name.strip(),
            phone=user_in.phone.strip(),
            role=user_in.role,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    @staticmethod
    async def create_refresh_token(
        session: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persist a new SHA-256 hashed refresh token."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        session.add(refresh_token)
        await session.flush()
        await session.refresh(refresh_token)
        return refresh_token

    @staticmethod
    async def get_refresh_token_by_hash(
        session: AsyncSession,
        token_hash: str,
    ) -> Optional[RefreshToken]:
        """Query a refresh token by its SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_refresh_token(
        session: AsyncSession,
        token_record: RefreshToken,
    ) -> None:
        """Mark a specific refresh token as revoked."""
        token_record.is_revoked = True
        await session.flush()

    @staticmethod
    async def revoke_all_user_tokens(
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        """Revoke all active refresh tokens for a user (e.g. security reset)."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        await session.execute(stmt)
        await session.flush()


user_repo = UserRepository()
