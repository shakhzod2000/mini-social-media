"""
Auth service — business logic for registration, login, token refresh, email verification.
"""

import uuid

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.exceptions import BadRequestError, NotFoundError, UnauthorizedError
from app.repositories.user import UserRepository, VerificationTokenRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.token_repo = VerificationTokenRepository(db)

    async def register(
        self,
        email: str,
        username: str,
        full_name: str,
        password: str,
    ):
        password_hash = pwd_context.hash(password)
        user = await self.user_repo.create(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=password_hash,
        )
        verification_token = await self.token_repo.create(user.id)
        return user, verification_token

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not pwd_context.verify(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        return {
            "access": create_access_token(user.id),
            "refresh": create_refresh_token(user.id),
        }

    async def refresh_token(self, refresh: str) -> dict:
        payload = decode_token(refresh)
        if payload.get("type") != "refresh":
            raise BadRequestError("Invalid token type — expected refresh token")

        user_id = uuid.UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        return {
            "access": create_access_token(user.id),
            "refresh": create_refresh_token(user.id),
        }

    async def verify_email(self, token_str: str):
        token_uuid = uuid.UUID(token_str)
        token = await self.token_repo.get_by_token(token_uuid)
        if not token:
            raise NotFoundError("Verification token not found")
        if token.is_expired:
            raise BadRequestError("Verification token has expired")

        user = await self.user_repo.get_by_id(token.user_id)
        if not user:
            raise NotFoundError("User not found")

        user = await self.user_repo.update(user, is_verified=True)
        await self.token_repo.delete(token)
        return user

    async def resend_verification(self, user):
        if user.is_verified:
            raise BadRequestError("Email is already verified")
        token = await self.token_repo.create(user.id)
        return token
