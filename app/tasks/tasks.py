from celery.app import Celery
import logging
from app.tasks.base_task import BaseTask
import time

celery_app = Celery(
    name='python-backend-worker-template',
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=BaseTask,
)
def count(self, x):
    # time.sleep(3)
    # x/x
    return x


@celery_app.task(
    bind=True,
    base=BaseTask,
)
def add(self, x, y):
    return x + y

