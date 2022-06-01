"""
queue_jobs defines the global singleton of queue_jobs client class.
the class provides method to queue jobs to clroot, so that legacy worker can pick them up
"""

import base64
import boto3
import logging
import ujson
from typing import Any, Tuple, Union
import zlib

from .exceptions import (OverSQSMessageLimitException,
                         QueueJobClientNotReady)


class QueueJobClient:
    """
    QueueJobClient defines a factory class for queuing jobs
    to clroot
    """

    _env: str = "local"
    _user_id: str = ""

    class _QueueJobClient:

        # Error for any job > 256K JSON. SQS can't handle jobs larger than this
        JOB_BODY_MAX_SIZE = 256 * 1024
        ZLIB_CONTENT_TYPE = "text/zlib"

        _ready = False

        def __init__(
                self,
                env: str,
                user_id: str,
                region_name: str,
                queue_name: str,
        ):
            self._env = env
            self._user_id = user_id
            self._queue_name = self._convert_queuename_to_full_name(queue_name)
            try:
                self._session = boto3.Session()
                self._sqs_client = self._session.client(
                    region_name=region_name,
                    service_name='sqs',
                    endpoint_url='https://sqs.{}.amazonaws.com'.format(region_name),
                )
                # This will throw QueueDoesNotExist if no such queue exists
                response = self._sqs_client.get_queue_url(
                    QueueName=self._queue_name,
                )
                self._queue_url = response['QueueUrl']
                self._ready = True
            except Exception as err:
                logging.critical("failed to initialize QueueJobClient: %s", err)

        def _convert_queuename_to_full_name(self, queue_name) -> str:
            """
            Convert a queue name to its full SQS name
            """
            if self._user_id == "":
                return f"{self._env}_{queue_name}"
            return f"{self._env}_{self._user_id}_{queue_name}"

        def _encode(self, job_body: Any, job_property: dict) -> Union[str, bytes]:
            """
            Encode job_body based on job_property so that it can be sent as payload
            of SQS message, if size is greater than 256KB
            This follows the way we do in clroot:
            https://github.com/ContextLogic/clroot/blob/master/cl/utils/sqs/encoder.py#L26
            """
            encoded_job_body = ujson.dumps(job_body)
            if (
                    "content_type" not in job_property
                    or job_property["content_type"]["StringValue"] == self.ZLIB_CONTENT_TYPE
            ):
                # encode in utf-8: https://stackoverflow.com/questions/53372006/python-3-6-3-zlib-compression
                encoded_job_body = zlib.compress(encoded_job_body.encode('utf-8'))
                encoded_job_body = base64.b64encode(encoded_job_body)
            return encoded_job_body

        def _process_job_body(self, job_body: Any, job_property: dict) -> Tuple[Union[str, bytes], dict]:
            """
            Encode job_body, if size is greater than 256 KB and type of plain text, compress it; raise an
            error otherwise. It will return the processed job_body and the new job_property
            This follows the way we do in clroot:
            https://github.com/ContextLogic/clroot/blob/master/cl/utils/sqs/processing.py#L952
            https://github.com/ContextLogic/clroot/blob/master/cl/utils/sqs/processing.py#L920
            """
            ret_job_property = job_property
            encoded_job_body = self._encode(job_body, ret_job_property)

            if len(encoded_job_body) > self.JOB_BODY_MAX_SIZE:
                # We are using StringValue instead of string_value since we are directly using SQS VPC
                # (qproxy in clroot), using string_value will raise an error:
                # Parameter validation failed: Unknown parameter in MessageAttributes.content_type: "string_value",
                # must be one of: StringValue, BinaryValue, StringListValues, BinaryListValues, DataType
                if ret_job_property != {} and ret_job_property["content_type"]["StringValue"] == "text/plain":
                    ret_job_property["content_type"]["StringValue"] = self.ZLIB_CONTENT_TYPE
                    encoded_job_body = self._encode(encoded_job_body, ret_job_property)
                    if len(encoded_job_body) > self.JOB_BODY_MAX_SIZE:
                        raise OverSQSMessageLimitException("Message size over SQS limit")
                else:
                    raise OverSQSMessageLimitException("Message size over SQS limit")
            return encoded_job_body, ret_job_property

        def queuejob(
                self,
                job_body: Any,
                job_property: dict,
        ) -> None:
            """
            Send one job to Amazon SQS queue, so that clroot worker can pick it up
            """
            try:
                if not self._ready:
                    raise QueueJobClientNotReady("QueueJobClient has not been initialized")
                encoded_job_body, ret_job_property = self._process_job_body(job_body, job_property)
                self._sqs_client.send_message(
                    QueueUrl=self._queue_url,
                    MessageBody=encoded_job_body,
                    MessageAttributes=ret_job_property
                )
                logging.info(
                    "Message sent: %s",
                    job_body
                )
            except Exception as err:
                logging.critical("failed to queue job due to %s", err)

        def queuejobs(
                self,
                job_bodies: list,
                job_properties: list,
        ) -> None:
            """
            Send multiple jobs to Amazon SQS queue, so that clroot worker can pick them up
            """

            def _packjob(body: Any, property: dict) -> dict:
                encoded_job_body, ret_job_property = self._process_job_body(body, property)
                return {
                    'body': encoded_job_body,
                    'attributes': ret_job_property
                }

            assert len(job_bodies) == len(job_properties)

            try:
                if not self._ready:
                    raise QueueJobClientNotReady("QueueJobClient has not been initialized")

                jobs = [_packjob(b, p) for b, p in zip(job_bodies, job_properties)]
                entries = [{
                    'Id': str(ind),
                    'MessageBody': msg['body'],
                    'MessageAttributes': msg['attributes']
                } for ind, msg in enumerate(jobs)]
                response = self._sqs_client.send_message_batch(
                    QueueUrl=self._queue_url,
                    Entries=entries,
                )
                if 'Successful' in response:
                    for msg_meta in response['Successful']:
                        logging.info(
                            "Job sent: %s: %s",
                            msg_meta['MessageId'],
                            jobs[int(msg_meta['Id'])]['body']
                        )

                if 'Failed' in response:
                    for msg_meta in response['Failed']:
                        logging.warning(
                            "Failed to send: %s: %s",
                            msg_meta['MessageId'],
                            jobs[int(msg_meta['Id'])]['body']
                        )
            except Exception as err:
                logging.critical("failed to queue jobs due to %s", err)

    @classmethod
    def init(cls, **kwargs: dict) -> None:
        """
        initialize the factory class
        """
        cls._env = kwargs.get("env", cls._env)
        cls._user_id = kwargs.get("user_id", "")

    @classmethod
    def get_queuejob_client(
            cls,
            region_name: str,
            queue_name: str,
            env: str = None,
            user_id: str = None
    ) -> _QueueJobClient:
        """
        Create a _QueueJobClient using this factory class
        """
        return cls._QueueJobClient(
            env or cls._env,
            user_id or cls._user_id,
            region_name,
            queue_name,
        )
