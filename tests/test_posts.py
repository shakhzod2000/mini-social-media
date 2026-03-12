"""
Tests for posts, comments, and likes.

Covers: CRUD, permissions (verified/unverified, author-only),
self-like prevention, double-like prevention.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


class TestPostCRUD:
    """Tests for post CRUD operations."""

    async def test_create_post_verified(self, client: AsyncClient, verified_user: dict):
        response = await client.post(
            "/posts",
            json={"title": "My First Post", "content": "Hello world! This is my post."},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 201
        assert response.json()["title"] == "My First Post"

    async def test_create_post_unverified(self, client: AsyncClient, unverified_user: dict):
        response = await client.post(
            "/posts",
            json={"title": "My First Post", "content": "Hello world! This is my post."},
            headers=auth_header(unverified_user["access_token"]),
        )
        assert response.status_code == 403

    async def test_list_posts_unauthenticated(self, client: AsyncClient):
        response = await client.get("/posts")
        assert response.status_code == 200

    async def test_update_post_as_author(self, client: AsyncClient, verified_user: dict):
        # Create
        create_resp = await client.post(
            "/posts",
            json={"title": "Original Title", "content": "Original content here."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        # Update
        response = await client.patch(
            f"/posts/{post_id}",
            json={"title": "Updated Title"},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_update_post_as_non_author(self, client: AsyncClient, verified_user: dict):
        # Create post as verified user
        create_resp = await client.post(
            "/posts",
            json={"title": "Author Post Title", "content": "Author's content here."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        # Register another user
        await client.post(
            "/auth/register",
            json={
                "email": "other@example.com",
                "username": "otheruser",
                "full_name": "Other User",
                "password": "password123",
            },
        )
        resp = await client.post(
            "/auth/login",
            json={"email": "other@example.com", "password": "password123"},
        )
        other_token = resp.json()["access"]

        # Try to update as non-author
        response = await client.patch(
            f"/posts/{post_id}",
            json={"title": "Hacked!"},
            headers=auth_header(other_token),
        )
        assert response.status_code == 403

    async def test_delete_post_as_author(self, client: AsyncClient, verified_user: dict):
        create_resp = await client.post(
            "/posts",
            json={"title": "To Be Deleted", "content": "This post will be deleted."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        response = await client.delete(
            f"/posts/{post_id}",
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 204

    async def test_title_too_short(self, client: AsyncClient, verified_user: dict):
        response = await client.post(
            "/posts",
            json={"title": "Hi", "content": "Some content for the post."},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 422


class TestComments:
    """Tests for comment operations."""

    async def test_create_comment(self, client: AsyncClient, verified_user: dict):
        # Create post
        create_resp = await client.post(
            "/posts",
            json={"title": "Post for Comments", "content": "Content here."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        # Comment
        response = await client.post(
            f"/posts/{post_id}/comments",
            json={"content": "Great post!"},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 201

    async def test_create_comment_unverified(self, client: AsyncClient, verified_user: dict, unverified_user: dict):
        # Create post as verified
        create_resp = await client.post(
            "/posts",
            json={"title": "Post for Comments", "content": "Content here."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        # Try to comment as unverified
        response = await client.post(
            f"/posts/{post_id}/comments",
            json={"content": "I shouldn't be able to comment."},
            headers=auth_header(unverified_user["access_token"]),
        )
        assert response.status_code == 403

    async def test_delete_own_comment(self, client: AsyncClient, verified_user: dict):
        # Create post
        create_resp = await client.post(
            "/posts",
            json={"title": "Post for Deleting Comments", "content": "Content."},
            headers=auth_header(verified_user["access_token"]),
        )
        post_id = create_resp.json()["id"]

        # Comment
        comment_resp = await client.post(
            f"/posts/{post_id}/comments",
            json={"content": "To be deleted."},
            headers=auth_header(verified_user["access_token"]),
        )
        comment_id = comment_resp.json()["id"]

        # Delete
        response = await client.delete(
            f"/posts/{post_id}/comments/{comment_id}",
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 204


class TestLikes:
    """Tests for like operations."""

    async def _create_post_by_verified_user(self, client, verified_user):
        resp = await client.post(
            "/posts",
            json={"title": "Likeable Post Title", "content": "Content worth liking."},
            headers=auth_header(verified_user["access_token"]),
        )
        return resp.json()["id"]

    async def _create_other_user(self, client):
        await client.post(
            "/auth/register",
            json={
                "email": "liker@example.com",
                "username": "likeruser",
                "full_name": "Liker User",
                "password": "password123",
            },
        )
        resp = await client.post(
            "/auth/login",
            json={"email": "liker@example.com", "password": "password123"},
        )
        return resp.json()["access"]

    async def test_like_post(self, client: AsyncClient, verified_user: dict):
        post_id = await self._create_post_by_verified_user(client, verified_user)
        other_token = await self._create_other_user(client)

        response = await client.post(
            f"/posts/{post_id}/like",
            headers=auth_header(other_token),
        )
        assert response.status_code == 201

    async def test_self_like_prevention(self, client: AsyncClient, verified_user: dict):
        post_id = await self._create_post_by_verified_user(client, verified_user)

        response = await client.post(
            f"/posts/{post_id}/like",
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 400

    async def test_double_like_prevention(self, client: AsyncClient, verified_user: dict):
        post_id = await self._create_post_by_verified_user(client, verified_user)
        other_token = await self._create_other_user(client)

        await client.post(
            f"/posts/{post_id}/like",
            headers=auth_header(other_token),
        )
        response = await client.post(
            f"/posts/{post_id}/like",
            headers=auth_header(other_token),
        )
        assert response.status_code == 409

    async def test_unlike(self, client: AsyncClient, verified_user: dict):
        post_id = await self._create_post_by_verified_user(client, verified_user)
        other_token = await self._create_other_user(client)

        await client.post(
            f"/posts/{post_id}/like",
            headers=auth_header(other_token),
        )
        response = await client.delete(
            f"/posts/{post_id}/like",
            headers=auth_header(other_token),
        )
        assert response.status_code == 204
