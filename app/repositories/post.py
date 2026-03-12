"""
Post, Comment, and Like repositories — all database queries for posts.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.config import settings
from app.exceptions import ConflictError
from app.models.post import Comment, Like, Post


class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, author_id: uuid.UUID, title: str, content: str) -> Post:
        post = Post(author_id=author_id, title=title, content=content)
        self.db.add(post)
        await self.db.flush()
        # Reload with author relationship
        result = await self.db.execute(
            select(Post).options(joinedload(Post.author)).where(Post.id == post.id)
        )
        return result.scalar_one()

    async def get_by_id(self, post_id: uuid.UUID) -> Post | None:
        result = await self.db.execute(
            select(Post)
            .options(
                joinedload(Post.author),
                selectinload(Post.comments).joinedload(Comment.author),
                selectinload(Post.likes),
            )
            .where(Post.id == post_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_list(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[Post], int]:
        query = select(Post).options(
            joinedload(Post.author),
            selectinload(Post.comments),
            selectinload(Post.likes),
        )
        count_query = select(func.count(Post.id))

        if search:
            search_filter = Post.title.ilike(f"%{search}%") | Post.content.ilike(
                f"%{search}%"
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if date_from:
            query = query.where(Post.created_at >= date_from)
            count_query = count_query.where(Post.created_at >= date_from)

        if date_to:
            query = query.where(Post.created_at <= date_to)
            count_query = count_query.where(Post.created_at <= date_to)

        query = query.order_by(Post.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        posts = result.unique().scalars().all()

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return list(posts), total

    async def update(self, post: Post, **kwargs) -> Post:
        for key, value in kwargs.items():
            if value is not None:
                setattr(post, key, value)
        await self.db.flush()
        return post

    async def delete(self, post: Post) -> None:
        await self.db.delete(post)
        await self.db.flush()

    async def delete_older_than(self, days: int | None = None) -> int:
        cutoff_days = days or settings.POST_EXPIRY_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=cutoff_days)
        result = await self.db.execute(
            delete(Post).where(Post.created_at < cutoff)
        )
        return result.rowcount


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, post_id: uuid.UUID, author_id: uuid.UUID, content: str
    ) -> Comment:
        comment = Comment(post_id=post_id, author_id=author_id, content=content)
        self.db.add(comment)
        await self.db.flush()
        # Reload with author
        result = await self.db.execute(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.id == comment.id)
        )
        return result.scalar_one()

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        result = await self.db.execute(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_list_by_post(
        self, post_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Comment], int]:
        query = (
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(query)
        comments = result.unique().scalars().all()

        count_result = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.post_id == post_id)
        )
        total = count_result.scalar()
        return list(comments), total

    async def delete(self, comment: Comment) -> None:
        await self.db.delete(comment)
        await self.db.flush()


class LikeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Like:
        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("You have already liked this post")
        return like

    async def get_by_user_and_post(
        self, user_id: uuid.UUID, post_id: uuid.UUID
    ) -> Like | None:
        result = await self.db.execute(
            select(Like).where(Like.user_id == user_id, Like.post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, like: Like) -> None:
        await self.db.delete(like)
        await self.db.flush()
