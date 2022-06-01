from abc import ABC
from celery import Task
import logging

logger = logging.getLogger(__name__)

class BaseTask(ABC, Task):
    autoretry_for = (ZeroDivisionError,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = 1
    retry_backoff_max = 600
    retry_jitter = True
