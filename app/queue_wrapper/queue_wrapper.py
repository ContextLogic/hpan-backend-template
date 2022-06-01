from kombu import Queue
import boto3
import logging
from app.exception import InvalidAWSCredentialException, QueueNotInitializedException
import re

logger = logging.getLogger(__name__)


class QueueWrapper(object):
    """
    wraps the celery queue_wrapper.
    """
    DLQ_PREFIX = 'err'

    @classmethod
    def convert_full_to_dlq_name(cls, name):
        return '{dlq_prefix}-{queue_name}'.format(dlq_prefix=cls.DLQ_PREFIX, queue_name=name)

    @classmethod
    def convert_dlq_to_full_name(cls, dlq_name):
        return re.sub(r'^{}-'.format(cls.DLQ_PREFIX), '', dlq_name)

    @classmethod
    def convert_short_to_full_name(cls, name, env):
        return "{env}-{queue_name}".format(queue_name=name, env=env)

    @classmethod
    def convert_full_to_short_name(cls, full_name, env):
        return re.sub(r'^{}-'.format(env), '', full_name)

    @classmethod
    def convert_full_to_local_full_name(cls, full_name, user):
        return "{user}-{queue_name}".format(queue_name=full_name, user=user)

    @classmethod
    def convert_local_full_to_full_name(cls, full_name):
        return re.sub(r'^[a-zA-Z]-', '', full_name)

    def __init__(self, queue_name, task, ratelimit_name=None):
        self._short_name = queue_name
        self._task = task
        self._ratelimit_name = ratelimit_name
        self._celery_task_queue = None
        self._sqs_name = None

    def build_celery(self, env):
        self._sqs_name = self.convert_short_to_full_name(self._short_name, env)
        if env == 'local':
            try:
                user = boto3.client('sts').get_caller_identity().get('Arn').split('/')[1]
                self._sqs_name = self.convert_full_to_local_full_name(self._sqs_name, user)
            except Exception:
                logger.error('Please use a valid aws credential in env var when running in local env')
                raise InvalidAWSCredentialException()
        self._celery_task_queue = Queue(self._sqs_name)

    def sqs_name(self):
        if not self._sqs_name:
            raise QueueNotInitializedException()
        return self._sqs_name

    def task(self):
        return self._task

    def celery_task_queue(self):
        if not self._celery_task_queue:
            raise QueueNotInitializedException()
        return self._celery_task_queue

    def ratelimit_name(self):
        return self._ratelimit_name


class QueuesWrapper(object):
    """
    wraps a list of Queue to build a full list celery queue_wrapper configs e.g.
    task_queues and task_routes
    """

    def __init__(self, queues):
        self._queues = queues
        self._celery_task_queues = None

        self._celery_task_routes = None

    def queues(self):
        return self._queues

    def celery_task_queues(self):
        if not self._celery_task_queues:
            raise QueueNotInitializedException()
        return self._celery_task_queues

    def celery_task_routes(self):
        if not self._celery_task_routes:
            raise QueueNotInitializedException()
        return self._celery_task_routes

    def build_celery(self, env='local'):
        for q in self._queues:
            q.build_celery(env)
        self._celery_task_queues = [q.celery_task_queue() for q in self._queues]
        self._celery_task_routes = {
            q.task(): {
                'queue': q.sqs_name(),
            } for q in self._queues
        }

    def ratelimit_name(self, sqs_name):
        if not self._celery_task_queues:
            return
        for q in self._queues:
            if q.sqs_name() == sqs_name:
                return q.ratelimit_name()
