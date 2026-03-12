"""
Pydantic schemas for posts, comments, likes, and feed.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Post schemas
# ---------------------------------------------------------------------------
class PostCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    content: str = Field(max_length=10_000)


class PostUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=255)
    content: str | None = Field(None, max_length=10_000)


class AuthorResponse(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    author: AuthorResponse
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostDetailResponse(PostResponse):
    comments: list["CommentResponse"] = []
    likes: list[uuid.UUID] = []


# ---------------------------------------------------------------------------
# Comment schemas
# ---------------------------------------------------------------------------
class CommentCreateRequest(BaseModel):
    content: str = Field(max_length=2_000)


class CommentResponse(BaseModel):
    id: uuid.UUID
    content: str
    author: AuthorResponse
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Feed schemas
# ---------------------------------------------------------------------------
class FeedPostResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    likes: list[uuid.UUID] = []

    model_config = {"from_attributes": True}


class FeedUserResponse(BaseModel):
    username: str
    posts: list[FeedPostResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Paginated response
# ---------------------------------------------------------------------------
class PaginatedResponse(BaseModel):
    count: int
    page: int
    page_size: int
    results: list
