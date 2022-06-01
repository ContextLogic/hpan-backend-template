"""
sqs module defines the abstraction of celery Queue and task routes.
Queue class enforces the naming convention of the sqs queue
given the different environment.
Queues class provides the singleton to quickly build celery queues
and task routes used by celery application.
"""

import logging
import re
from typing import Optional

import boto3
from kombu import Queue as KombuQueue

from ..exception import InvalidAWSCredentialException, QueueNotInitializedException

logger = logging.getLogger(__name__)


class Queue:
    """
    wraps the celery queues.
    """

    DLQ_PREFIX = "err"

    @classmethod
    def convert_full_to_dlq_name(cls, name: str) -> str:
        """
        convert a sqs queue name to its DLQ name
        """
        return f"{cls.DLQ_PREFIX}-{name}"

    @classmethod
    def convert_dlq_to_full_name(cls, dlq_name: str) -> str:
        """
        convert a DLQ name to its normal sqs queue name
        """
        return re.sub(r"^{}-".format(cls.DLQ_PREFIX), "", dlq_name)

    @classmethod
    def convert_short_to_full_name(cls, name: str, env: str) -> str:
        """
        convert a short sqs queue to its full sqs name
        """
        return f"{env}-{name}"

    @classmethod
    def convert_full_to_short_name(cls, full_name: str, env: str) -> str:
        """
        convert a full sqs name to its short name
        """
        return re.sub(r"^{}-".format(env), "", full_name)

    @classmethod
    def convert_full_to_local_full_name(cls, full_name: str, user: str) -> str:
        """
        prepend user id to the queue name, this is needed for local env
        """
        return f"{user}-{full_name}"

    @classmethod
    def convert_local_full_to_full_name(cls, full_name: str) -> str:
        """
        stripe off the user id from the queue name used in local env.
        """
        return re.sub(r"^[a-zA-Z]+-", "", full_name)

    def __init__(
        self, queue_name: str, task: str, ratelimit_name: Optional[str] = None
    ) -> None:
        self._short_name: str = queue_name
        self._task: str = task
        self._ratelimit_name: Optional[str] = ratelimit_name
        self._celery_task_queue: list = []
        self._sqs_name: str = ""

    def build_celery(self, env: str) -> None:
        """
        given the env, build the celery routes and queues
        """
        self._sqs_name = self.convert_short_to_full_name(self._short_name, env)
        if env == "local":
            try:
                user = (
                    boto3.client("sts").get_caller_identity().get("Arn").split("/")[1]
                )
                self._sqs_name = self.convert_full_to_local_full_name(
                    self._sqs_name, user
                )
            except Exception as err:
                logger.error(
                    "Please use a valid aws credential in env var when running in local env"
                )
                raise InvalidAWSCredentialException() from err
        self._celery_task_queue = KombuQueue(self._sqs_name)

    def sqs_name(self) -> str:
        """
        return the sqs queue name, a complete full name
        """
        if not self._sqs_name:
            raise QueueNotInitializedException()
        return self._sqs_name

    def task(self) -> str:
        """
        return the task name associated to the queue
        """
        return self._task

    def celery_task_queue(self) -> KombuQueue:
        """
        return the celery queue object
        """
        if not self._celery_task_queue:
            raise QueueNotInitializedException()
        return self._celery_task_queue

    def ratelimit_name(self) -> Optional[str]:
        """
        return the ratelimit name associated to this queue, if has any
        """
        return self._ratelimit_name


class Queues:
    """
    wraps a list of Queue to build a full list celery queues configs e.g.
    task_queues and task_routes
    """

    _queues: list = []
    _env: str = "local"
    _celery_task_queues: list = []
    _celery_task_routes: dict = {}

    @classmethod
    def queues(cls) -> list:
        """
        return list of queues
        """
        return cls._queues

    @classmethod
    def celery_task_queues(cls) -> list:
        """
        return list of celery queue objects
        """
        if not cls._celery_task_queues:
            raise QueueNotInitializedException()
        return cls._celery_task_queues

    @classmethod
    def celery_task_routes(cls) -> dict:
        """
        return celery task routes
        """
        if not cls._celery_task_routes:
            raise QueueNotInitializedException()
        return cls._celery_task_routes

    @classmethod
    def init(cls, queues: list, env: str = "local") -> None:
        """
        given the queue-task mapping and env, build the celery task queues and celery task routes.
        """
        cls._queues = queues
        for queue in cls._queues:
            queue.build_celery(env)
        cls._celery_task_queues = [queue.celery_task_queue() for queue in cls._queues]
        cls._celery_task_routes = {
            queue.task(): {
                "queue": queue.sqs_name(),
            }
            for queue in cls._queues
        }

    @classmethod
    def ratelimit_name(cls, sqs_name: str) -> Optional[str]:
        """
        given the sqs queue name, return the ratelimiter name.
        """
        if not cls._celery_task_queues:
            return None
        for queue in cls._queues:
            if queue.sqs_name() == sqs_name:
                return queue.ratelimit_name()
        return None
