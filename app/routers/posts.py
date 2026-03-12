"""
Post, Comment, and Like routes.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import PaginationParams, get_current_user, get_verified_user
from app.schemas.post import (
    CommentCreateRequest,
    CommentResponse,
    PaginatedResponse,
    PostCreateRequest,
    PostDetailResponse,
    PostResponse,
    PostUpdateRequest,
)
from app.services.post import CommentService, LikeService, PostService

router = APIRouter(prefix="/posts", tags=["posts"])


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------
@router.get("", response_model=PaginatedResponse)
async def list_posts(
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Search in title & content"),
    date_from: datetime | None = Query(None, description="Filter from date (ISO)"),
    date_to: datetime | None = Query(None, description="Filter to date (ISO)"),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    posts, total = await service.get_list(
        offset=pagination.offset,
        limit=pagination.page_size,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse(
        count=total,
        page=pagination.page,
        page_size=pagination.page_size,
        results=[
            PostResponse(
                id=p.id,
                title=p.title,
                content=p.content,
                author=p.author,
                likes_count=len(p.likes),
                comments_count=len(p.comments),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in posts
        ],
    )


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreateRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.create(user.id, data.title, data.content)
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        likes_count=0,
        comments_count=0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = PostService(db)
    post = await service.get_by_id(post_id)
    return PostDetailResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        likes_count=len(post.likes),
        comments_count=len(post.comments),
        created_at=post.created_at,
        updated_at=post.updated_at,
        comments=[
            CommentResponse(
                id=c.id,
                content=c.content,
                author=c.author,
                created_at=c.created_at,
            )
            for c in post.comments
        ],
        likes=[like.user_id for like in post.likes],
    )


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdateRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.update(
        post_id, user.id, **data.model_dump(exclude_unset=True)
    )
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        likes_count=len(post.likes) if post.likes else 0,
        comments_count=len(post.comments) if post.comments else 0,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    await service.delete(post_id, user.id)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
@router.get("/{post_id}/comments", response_model=PaginatedResponse)
async def list_comments(
    post_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    comments, total = await service.get_list(
        post_id, pagination.offset, pagination.page_size
    )
    return PaginatedResponse(
        count=total,
        page=pagination.page,
        page_size=pagination.page_size,
        results=[
            CommentResponse(
                id=c.id,
                content=c.content,
                author=c.author,
                created_at=c.created_at,
            )
            for c in comments
        ],
    )


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: uuid.UUID,
    data: CommentCreateRequest,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    comment = await service.create(post_id, user.id, data.content)
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        author=comment.author,
        created_at=comment.created_at,
    )


@router.delete("/{post_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CommentService(db)
    await service.delete(post_id, comment_id, user.id)


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------
@router.post("/{post_id}/like", status_code=201)
async def like_post(
    post_id: uuid.UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LikeService(db)
    await service.like(post_id, user.id)
    return {"message": "Post liked successfully"}


@router.delete("/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: uuid.UUID,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LikeService(db)
    await service.unlike(post_id, user.id)
