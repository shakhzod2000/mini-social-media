"""
Celery application configuration.
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "mini_social_media",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-unverified-users": {
            "task": "app.tasks.cleanup_unverified_users",
            "schedule": 3600.0,  # every hour
        },
        "cleanup-old-posts": {
            "task": "app.tasks.cleanup_old_posts",
            "schedule": 86400.0,  # every 24 hours
        },
    },
)
