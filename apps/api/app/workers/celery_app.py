from celery import Celery

from app.core.settings import settings

celery_app = Celery(
    "job_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks.resume_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Resume processing involves an LLM call (skill extraction) that can take
    # several seconds — a short soft-time-limit would kill it mid-flight.
    task_soft_time_limit=120,
    task_time_limit=180,
)
