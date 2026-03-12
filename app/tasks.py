"""
Celery tasks for periodic cleanup.

These tasks use synchronous SQLAlchemy sessions since Celery workers
run in a separate process without an async event loop.
"""

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app
from app.config import settings


def get_sync_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    return Session(engine)


@celery_app.task(name="app.tasks.cleanup_unverified_users")
def cleanup_unverified_users():
    """Delete unverified users older than the configured threshold."""
    from app.models.user import User

    session = get_sync_session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=settings.UNVERIFIED_USER_CLEANUP_HOURS
        )
        result = session.execute(
            delete(User).where(User.is_verified.is_(False), User.created_at < cutoff)
        )
        session.commit()
        count = result.rowcount
        return f"Deleted {count} unverified user(s)"
    finally:
        session.close()


@celery_app.task(name="app.tasks.cleanup_old_posts")
def cleanup_old_posts():
    """Delete posts older than the configured threshold."""
    from app.models.post import Post

    session = get_sync_session()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=settings.POST_EXPIRY_DAYS
        )
        result = session.execute(delete(Post).where(Post.created_at < cutoff))
        session.commit()
        count = result.rowcount
        return f"Deleted {count} old post(s)"
    finally:
        session.close()
