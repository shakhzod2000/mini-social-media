# Mini Social Media API

A RESTful backend for a mini social media platform built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. Features JWT authentication, email verification, posts, comments, likes, rate limiting, and periodic task management with Celery.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd mini-social-media

# 2. Copy environment variables
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. The API is available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

That's it! The entrypoint automatically runs Alembic migrations.

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login, get JWT tokens | No |
| POST | `/auth/refresh` | Refresh access token | No |
| GET | `/auth/me` | Get current user profile | Yes |
| POST | `/auth/verify-email` | Verify email with token | No |
| POST | `/auth/resend-verification` | Resend verification token | Yes |
| POST | `/auth/cleanup-unverified` | Delete stale unverified users | Yes |

### User Profile

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| PATCH | `/users/me` | Update profile (username, full_name) | Yes |

### Posts

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/posts` | List posts (paginated, searchable) | No |
| POST | `/posts` | Create a post | Yes (verified) |
| GET | `/posts/{id}` | Get post detail with comments & likes | No |
| PATCH | `/posts/{id}` | Update post (author only) | Yes |
| DELETE | `/posts/{id}` | Delete post (author only) | Yes |

### Comments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/posts/{id}/comments` | List comments for a post | No |
| POST | `/posts/{id}/comments` | Add a comment | Yes (verified) |
| DELETE | `/posts/{post_id}/comments/{comment_id}` | Delete comment (author only) | Yes |

### Likes

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/posts/{id}/like` | Like a post | Yes |
| DELETE | `/posts/{id}/like` | Unlike a post | Yes |

### Feed

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/feed` | All users with posts & likes (nested) | No |

### Query Parameters (GET /posts & GET /feed)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number | `?page=2` |
| `page_size` | Items per page (max 100) | `?page_size=10` |
| `search` | Search in title & content | `?search=fastapi` |
| `date_from` | Posts from date (ISO format) | `?date_from=2025-01-01` |
| `date_to` | Posts until date (ISO format) | `?date_to=2025-12-31` |

---

## Example Requests

### Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john_doe",
    "full_name": "John Doe",
    "password": "securepass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Create Post (with token)
```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "My First Post",
    "content": "Hello world!"
  }'
```

---

## Project Structure

```
mini-social-media/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Pydantic settings (from .env)
│   ├── database.py              # SQLAlchemy async engine & session
│   ├── dependencies.py          # JWT auth, pagination DI
│   ├── exceptions.py            # Exception hierarchy & handlers
│   ├── models/                  # SQLAlchemy models
│   │   ├── base.py              # UUID PK + timestamp mixins
│   │   ├── user.py              # User, EmailVerificationToken
│   │   └── post.py              # Post, Comment, Like
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── user.py              # Auth & user schemas
│   │   └── post.py              # Post, comment, like schemas
│   ├── repositories/            # Data access layer (SQLAlchemy queries)
│   │   ├── user.py              # UserRepository, TokenRepository
│   │   └── post.py              # PostRepository, CommentRepository, LikeRepository
│   ├── services/                # Business logic layer
│   │   ├── auth.py              # Registration, login, verification
│   │   ├── user.py              # Profile, cleanup
│   │   └── post.py              # Posts, comments, likes logic
│   ├── routers/                 # API route handlers (thin)
│   │   ├── auth.py              # /auth/* routes
│   │   ├── users.py             # /users/* routes
│   │   ├── posts.py             # /posts/* routes
│   │   └── feed.py              # /feed route
│   ├── celery_app.py            # Celery configuration
│   └── tasks.py                 # Periodic cleanup tasks
├── alembic/                     # Database migrations
├── tests/                       # pytest + httpx tests
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # app + db + redis + celery
└── requirements/                # Split requirements
```

## Architecture

The project follows a **Router → Service → Repository** layered architecture:

- **Repository Layer**: All database queries (SQLAlchemy) are encapsulated in repository classes. No other layer touches the ORM directly.
- **Service Layer**: Business logic lives here. Services call repositories and enforce rules (permissions, validation, uniqueness). They raise custom exceptions on errors.
- **Router Layer**: Thin route handlers that validate input via Pydantic schemas, delegate to services, and return HTTP responses. No business logic.

## Running Tests

```bash
# Run all tests inside Docker
docker compose exec app pip install aiosqlite && docker compose exec app pytest tests/ -v

# Or locally (with a virtualenv)
pip install -r requirements/test.txt aiosqlite
pytest tests/ -v
```

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

## Tech Stack

- **Python 3.11** + **FastAPI** + **Pydantic v2**
- **SQLAlchemy 2.0** (async) + **Alembic** — ORM & migrations
- **PostgreSQL 16** — primary database
- **Redis 7** — Celery broker
- **Celery** — periodic background tasks
- **python-jose** + **passlib** — JWT authentication
- **slowapi** — rate limiting on login
- **Docker** + **Docker Compose** — containerization
- **pytest** + **httpx** — async testing
- **ruff** — linting & formatting
- **GitHub Actions** — CI (lint + test)
