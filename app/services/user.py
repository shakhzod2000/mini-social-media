"""
User service — profile updates and cleanup.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def get_profile(self, user):
        return user

    async def update_profile(self, user, **kwargs):
        return await self.user_repo.update(user, **kwargs)

    async def cleanup_unverified(self, hours: int | None = None) -> int:
        return await self.user_repo.delete_unverified_older_than(hours)
