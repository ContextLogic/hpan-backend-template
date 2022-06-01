"""
tasks.function_based_tasks contains examples of function based celery task definition.
It contains a simple add task, and a demo task for retrying
"""

import time
from abc import ABC

from celery import current_app, Task


class RetryBaseTask(Task, ABC):
    """
    An example Retry BaseTask class used for demonstrating celery task auto retry on ZeroDivisionError
    with some retry strategy defined. For more examples and docs, please refer to
    https://docs.celeryproject.org/en/latest/userguide/tasks.html#task-inheritance
    """

    autoretry_for = (ZeroDivisionError,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = 1
    retry_backoff_max = 600
    retry_jitter = True


@current_app.task(
    name="retry_demo",  # task name, should be matching with the Queue definition in app.config.queues
    bind=True,
    base=RetryBaseTask,  # inherited the RetryBaseTask, so this task can be auto retried.
)
def retry_demo(self: Task, num: int) -> float:
    """
    a retry demo function called by retry_demo task, used for demoing celery auto retry on some specific exceptions.
    """
    time.sleep(2)
    return num / num


@current_app.task(
    name="add",
    bind=True,
    base=RetryBaseTask,
)
def add(self: Task, num1: int, num2: int) -> int:
    """
    a count function called by count task.
    """
    time.sleep(2)
    return num1 + num2
