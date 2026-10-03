import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)


@celery.task
def send_report(kind):
    return kind
