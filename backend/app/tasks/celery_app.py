from celery import Celery
from app.config import settings

celery = Celery("app", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    worker_prefetch_multiplier=1,
)

import app.tasks.pipeline  # noqa: E402,F401
