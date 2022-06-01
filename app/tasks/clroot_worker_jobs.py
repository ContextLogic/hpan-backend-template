"""
tasks.legacy_worker_jobs contains examples of queuing jobs to clroot queues, so that
legacy worker there can pick them up
"""

import boto3
import ujson
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Type
from ..config.config import WorkerConfig

from base_be_worker.fluent import FluentLogger
from celery import Task, current_app


logger = FluentLogger.get_logger("QueuedJob", logging.getLogger(__name__))


class QueueType(Enum):
    """
    enum class for queue types in clroot
    Please make sure they match the names appeared in
    https://github.com/ContextLogic/clroot/blob/master/sweeper/processing/queues.py
    """

    SMS_QUEUE_NAME_V2 = 0


class BaseQueuedJob(ABC):
    """
    Base Queued Job class
    """

    def __init__(self, job_id: str, queue_name: str, kwargs: dict) -> None:
        self.job_id = job_id
        self.queue_name = queue_name
        self.job_info = kwargs

        self.region = WorkerConfig.broker_transport_options.get("region", None)
        if self.region is None:
            logger.warning("Cannot find region in app/config/config.py, Use us-west-1 by default")
            self.region = "us-west-1"
        self.sqs = boto3.resource('sqs', region_name=self.region)
        self.job_queue = self.sqs.get_queue_by_name(QueueName=self.queue_name)

        self.job_body = None

    @classmethod
    def queue_job_cls(cls, queue_type: QueueType) -> Optional[Type["BaseQueuedJob"]]:
        """
        get job class given a queue type and kwargs for job-body
        """
        cls_map = {
            QueueType.SMS_QUEUE_NAME_V2: SweeperSmsV2,
        }
        if queue_type not in cls_map:
            raise Exception("queue type not found")
        return cls_map.get(queue_type)

    @abstractmethod
    def process(self) -> str:
        """
        abstract method for processing jobs
        """
        pass

    def __json__(self) -> dict:
        """
        for json encoding and decoding.
        """
        return {
            "job_id": self.job_id,
        }


class SweeperSmsV2(BaseQueuedJob):
    """
    sweeper_sms_v2 Type inherited from BaseQueuedJob
    """
    job_type = QueueType.SMS_QUEUE_NAME_V2
    # Job method should match the bound method defined in clroot
    job_method = "send_sms_v2"
    job_properties = {'content_type': {'DataType': 'String', 'StringValue': 'text/plain'}}

    def process(self) -> str:
        """
        Create job-body and queue the job to SMS_QUEUE_NAME_V2
        """
        logger.info("Processing sweeper_sms_v2")
        self.job_body = [self.job_method, [self.job_info.get('user_id', ''),
                                           self.job_info.get('phone_number', ''),
                                           self.job_info.get('country_code', ''),
                                           self.job_info.get('message', 'Empty'),
                                           self.job_info.get('sms_type', ''),
                                           self.job_info.get('campaign_id', '')],
                         {'_queued_time': time.time()}]
        resp = self.job_queue.send_message(MessageBody=ujson.dumps((self.job_body)),
                                           MessageAttributes=self.job_properties)
        return 'success'


@current_app.task(
    name="queued_task",
)
def queued_task(job: BaseQueuedJob) -> None:
    """
    queued job execution
    """
    time.sleep(1)
    job.process()
