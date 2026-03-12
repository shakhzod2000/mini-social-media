"""
Feed route — returns all users with their posts and likes (nested).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import PaginationParams
from app.models.post import Like, Post
from app.models.user import User
from app.schemas.post import FeedPostResponse, FeedUserResponse, PaginatedResponse

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=PaginatedResponse)
async def feed(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(
        None, description="Search in post title & content"
    ),
    date_from: str | None = Query(
        None, description="Filter from date (ISO)"
    ),
    date_to: str | None = Query(
        None, description="Filter to date (ISO)"
    ),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func

    # Build base query — users who have posts
    query = (
        select(User)
        .options(selectinload(User.posts).selectinload(Post.likes))
        .where(User.posts.any())
    )
    count_query = select(func.count(User.id)).where(User.posts.any())

    # Apply filters at the post level
    if search:
        query = query.where(
            User.posts.any(
                Post.title.ilike(f"%{search}%") | Post.content.ilike(f"%{search}%")
            )
        )
        count_query = count_query.where(
            User.posts.any(
                Post.title.ilike(f"%{search}%") | Post.content.ilike(f"%{search}%")
            )
        )

    if date_from:
        query = query.where(User.posts.any(Post.created_at >= date_from))
        count_query = count_query.where(User.posts.any(Post.created_at >= date_from))

    if date_to:
        query = query.where(User.posts.any(Post.created_at <= date_to))
        count_query = count_query.where(User.posts.any(Post.created_at <= date_to))

    query = (
        query.order_by(User.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )

    result = await db.execute(query)
    users = result.unique().scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    results = []
    for user in users:
        results.append(
            FeedUserResponse(
                username=user.username,
                posts=[
                    FeedPostResponse(
                        id=post.id,
                        title=post.title,
                        content=post.content,
                        likes=[like.user_id for like in post.likes],
                    )
                    for post in user.posts
                ],
            )
        )

    return PaginatedResponse(
        count=total,
        page=pagination.page,
        page_size=pagination.page_size,
        results=[r.model_dump() for r in results],
    )
