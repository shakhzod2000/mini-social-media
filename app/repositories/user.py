"""
User and VerificationToken repositories — all database queries for users.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import ConflictError
from app.models.user import EmailVerificationToken, User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError(
                "User with this email or username already exists"
            )
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("Username already taken")
        return user

    async def delete_unverified_older_than(self, hours: int | None = None) -> int:
        cutoff_hours = hours or settings.UNVERIFIED_USER_CLEANUP_HOURS
        cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)
        result = await self.db.execute(
            delete(User).where(
                User.is_verified.is_(False),
                User.created_at < cutoff,
            )
        )
        return result.rowcount


class VerificationTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID) -> EmailVerificationToken:
        # Delete existing tokens for this user
        await self.db.execute(
            delete(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user_id
            )
        )
        token = EmailVerificationToken(
            user_id=user_id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS),
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_token(self, token: uuid.UUID) -> EmailVerificationToken | None:
        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token == token
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, token: EmailVerificationToken) -> None:
        await self.db.delete(token)
        await self.db.flush()
