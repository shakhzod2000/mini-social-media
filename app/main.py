"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.exceptions import register_exception_handlers
from app.routers import auth, feed, posts, users
from app.routers.auth import limiter

app = FastAPI(
    title="Mini Social Media API",
    description="REST API for a mini social media platform.",
    version="1.0.0",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Custom exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(feed.router)


@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "mini-social-media"}
