"""
Pytest fixtures for testing.

Uses a separate SQLite in-memory database for tests (no Docker needed).
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.dependencies import create_access_token
from app.main import app
from app.models.base import Base

# Use SQLite for tests (no Postgres needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db

# Disable rate limiting for tests
app.state.limiter.enabled = False


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def verified_user(client: AsyncClient) -> dict:
    """Register and verify a user, return user data + access token."""
    # Register
    resp = await client.post(
        "/auth/register",
        json={
            "email": "verified@example.com",
            "username": "verifieduser",
            "full_name": "Verified User",
            "password": "password123",
        },
    )
    data = resp.json()
    verification_token = data["verification_token"]

    # Verify email
    await client.post(
        "/auth/verify-email",
        json={"token": verification_token},
    )

    # Login to get tokens
    resp = await client.post(
        "/auth/login",
        json={"email": "verified@example.com", "password": "password123"},
    )
    tokens = resp.json()

    return {
        "user": data["user"],
        "access_token": tokens["access"],
        "refresh_token": tokens["refresh"],
    }


@pytest.fixture
async def unverified_user(client: AsyncClient) -> dict:
    """Register a user without verifying, return user data + access token."""
    resp = await client.post(
        "/auth/register",
        json={
            "email": "unverified@example.com",
            "username": "unverifieduser",
            "full_name": "Unverified User",
            "password": "password123",
        },
    )
    data = resp.json()

    # Login to get tokens
    resp = await client.post(
        "/auth/login",
        json={"email": "unverified@example.com", "password": "password123"},
    )
    tokens = resp.json()

    return {
        "user": data["user"],
        "access_token": tokens["access"],
        "refresh_token": tokens["refresh"],
    }


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
