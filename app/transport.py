"""
customized transport class with ratelimiter feature,
celery worker should use this transport if queue-level ratelimiting is needed.
"""

from abc import ABC

from base_be_worker.queues.sqs import Queues
from base_be_worker.ratelimit import RatelimitClient
from kombu.transport.SQS import Transport, Channel
from vine import promise


class RatelimitChannel(ABC, Channel):
    """
    A ratelimit Channel inherited from kombu SQS Channel class,
    modified the _schedule_queue function to
    add ratelimiting feature when polling from queues.
    """

    def _schedule_queue(self, queue: str) -> None:
        if queue in self._active_queues:
            if self.qos.can_consume() and not RatelimitClient.ratelimit(
                Queues.ratelimit_name(queue)  # type: ignore[arg-type]
            ):
                self._get_bulk_async(
                    queue,
                    callback=promise(self._loop1, (queue,)),
                )
            else:
                self._loop1(queue)


# pylint: disable=invalid-name
class ratelimittransport(ABC, Transport):
    """
    A ratelimit transport class inherited from kombu SQS Transport class, overwrite the Channel
    to use the RatelimitChannel
    """

    Channel = RatelimitChannel
