"""
Tests for authentication endpoints.

Covers: registration, duplicates, login, protected endpoints,
email verification, profile update.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


class TestRegistration:
    """Tests for POST /auth/register"""

    async def test_successful_registration(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "strongpassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "verification_token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["is_verified"] is False

    async def test_duplicate_email(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "username": "user1",
                "full_name": "User One",
                "password": "password123",
            },
        )
        response = await client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "username": "user2",
                "full_name": "User Two",
                "password": "password123",
            },
        )
        assert response.status_code == 409

    async def test_duplicate_username(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "email": "a@example.com",
                "username": "sameuser",
                "full_name": "User A",
                "password": "password123",
            },
        )
        response = await client.post(
            "/auth/register",
            json={
                "email": "b@example.com",
                "username": "sameuser",
                "full_name": "User B",
                "password": "password123",
            },
        )
        assert response.status_code == 409

    async def test_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "full_name": "Test User",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    async def test_short_username(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",
                "full_name": "Test User",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    async def test_invalid_username_chars(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "user@name!",
                "full_name": "Test User",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    async def test_short_password(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "short",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login"""

    async def test_successful_login(self, client: AsyncClient):
        # Register first
        await client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "full_name": "Login User",
                "password": "password123",
            },
        )
        response = await client.post(
            "/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    async def test_wrong_password(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "email": "wrong@example.com",
                "username": "wronguser",
                "full_name": "Wrong User",
                "password": "password123",
            },
        )
        response = await client.post(
            "/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401


class TestMe:
    """Tests for GET /auth/me"""

    async def test_me_authenticated(self, client: AsyncClient, verified_user: dict):
        response = await client.get(
            "/auth/me", headers=auth_header(verified_user["access_token"])
        )
        assert response.status_code == 200
        assert response.json()["email"] == "verified@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401  # no Bearer token


class TestEmailVerification:
    """Tests for email verification flow."""

    async def test_verify_email(self, client: AsyncClient):
        # Register
        resp = await client.post(
            "/auth/register",
            json={
                "email": "verify@example.com",
                "username": "verifyuser",
                "full_name": "Verify User",
                "password": "password123",
            },
        )
        token = resp.json()["verification_token"]

        # Verify
        response = await client.post(
            "/auth/verify-email", json={"token": token}
        )
        assert response.status_code == 200
        assert response.json()["user"]["is_verified"] is True

    async def test_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/verify-email",
            json={"token": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 404


class TestProfileUpdate:
    """Tests for PATCH /users/me"""

    async def test_update_full_name(self, client: AsyncClient, verified_user: dict):
        response = await client.patch(
            "/users/me",
            json={"full_name": "Updated Name"},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_username(self, client: AsyncClient, verified_user: dict):
        response = await client.patch(
            "/users/me",
            json={"username": "newusername"},
            headers=auth_header(verified_user["access_token"]),
        )
        assert response.status_code == 200
        assert response.json()["username"] == "newusername"

    async def test_update_unauthenticated(self, client: AsyncClient):
        response = await client.patch(
            "/users/me", json={"full_name": "Hacker"}
        )
        assert response.status_code == 401
