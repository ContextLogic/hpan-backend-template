from kombu.transport.SQS import Transport, Channel
from vine import promise
from .ratelimit import Ratelimiter
from app.queues import QUEUES


class RatelimitChannel(Channel):

    def _schedule_queue(self, queue):
        if queue in self._active_queues:
            if self.qos.can_consume() and not Ratelimiter.ratelimit(QUEUES.ratelimit_name(queue)):
                self._get_bulk_async(
                    queue, callback=promise(self._loop1, (queue,)),
                )
            else:
                self._loop1(queue)


class ratelimittransport(Transport):
    Channel = RatelimitChannel

