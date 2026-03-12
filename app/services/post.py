"""
Post, Comment, and Like services — business logic.
"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.repositories.post import CommentRepository, LikeRepository, PostRepository


class PostService:
    def __init__(self, db: AsyncSession):
        self.post_repo = PostRepository(db)

    async def create(self, author_id: uuid.UUID, title: str, content: str):
        return await self.post_repo.create(author_id, title, content)

    async def get_by_id(self, post_id: uuid.UUID):
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("Post not found")
        return post

    async def get_list(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        return await self.post_repo.get_list(offset, limit, search, date_from, date_to)

    async def update(
        self, post_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ):
        post = await self.get_by_id(post_id)
        if post.author_id != user_id:
            raise ForbiddenError("You can only edit your own posts")
        return await self.post_repo.update(post, **kwargs)

    async def delete(self, post_id: uuid.UUID, user_id: uuid.UUID):
        post = await self.get_by_id(post_id)
        if post.author_id != user_id:
            raise ForbiddenError("You can only delete your own posts")
        await self.post_repo.delete(post)

    async def cleanup_old_posts(self, days: int | None = None) -> int:
        return await self.post_repo.delete_older_than(days)


class CommentService:
    def __init__(self, db: AsyncSession):
        self.comment_repo = CommentRepository(db)
        self.post_repo = PostRepository(db)

    async def create(
        self, post_id: uuid.UUID, author_id: uuid.UUID, content: str
    ):
        # Verify post exists
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("Post not found")
        return await self.comment_repo.create(post_id, author_id, content)

    async def get_list(
        self, post_id: uuid.UUID, offset: int = 0, limit: int = 20
    ):
        return await self.comment_repo.get_list_by_post(post_id, offset, limit)

    async def delete(
        self, post_id: uuid.UUID, comment_id: uuid.UUID, user_id: uuid.UUID
    ):
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise NotFoundError("Comment not found")
        if comment.post_id != post_id:
            raise NotFoundError("Comment not found for this post")
        if comment.author_id != user_id:
            raise ForbiddenError("You can only delete your own comments")
        await self.comment_repo.delete(comment)


class LikeService:
    def __init__(self, db: AsyncSession):
        self.like_repo = LikeRepository(db)
        self.post_repo = PostRepository(db)

    async def like(self, post_id: uuid.UUID, user_id: uuid.UUID):
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise NotFoundError("Post not found")
        if post.author_id == user_id:
            raise BadRequestError("You cannot like your own post")
        return await self.like_repo.create(user_id, post_id)

    async def unlike(self, post_id: uuid.UUID, user_id: uuid.UUID):
        like = await self.like_repo.get_by_user_and_post(user_id, post_id)
        if not like:
            raise NotFoundError("Like not found")
        await self.like_repo.delete(like)
