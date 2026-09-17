import os
from celery import Celery

# Fetch Redis broker URL from environment, fallback to sensible local dev default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "youtube_automation_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Optional configuration (e.g., timezone, task tracking)
celery_app.conf.update(
    task_track_started=True,
    timezone="UTC"
)

@celery_app.task
def dummy_test_task(x, y):
    """
    A minimal deterministic test task to verify Celery works.
    DO NOT place business logic here.
    """
    return x + y
