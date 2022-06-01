class WorkerConfig(object):
    def __init__(self, queues, region='us-west-1'):

        # defines sqs transport options, please refer to
        # https://docs.celeryproject.org/en/stable/getting-started/brokers/sqs.html#options
        # for more details
        self.broker_transport_options = {
            'region': region,
            'polling_interval': 30,
            'wait_time_seconds': 15,
            'visibility_timeout': 3600,
        }

        # use custom transport
        self.broker_url = "app.transport.transport.ratelimittransport://"

        # default task queue, any task without a defined route will be routed to the default sqs queue
        self.task_default_queue = 'default-python-backend-worker-template'

        # defines the list of task queues
        self.task_queues = queues.celery_task_queues()

        # defines the routes, task to queue should be one-to-one mapping.
        self.task_routes = queues.celery_task_routes()

        # celery configs, please refer to https://docs.celeryproject.org/en/stable/userguide/configuration.html for
        # more details.

        # worker will only ack message on task success/timeout/failure
        self.task_acks_late = True

        # worker ack message when on task_failure or task_timeout
        self.task_acks_on_failure_or_timeout = True

        # if worker lost, the message will be re-queued back to the queue.
        self.task_reject_on_worker_lost = True

        # defines the number of sub worker process
        self.worker_concurrency = 8

        # It is the multiplier to calculate the prefetch numbers. The calculation is
        # prefetch = worker_concurrency * worker_prefetch_multiplier.
        # The prefetch defines the the number of messages a single poll can get, this can reduce
        # the number of SQS api calls. Please note that, on SQS side this value will not exceed 10.
        self.worker_prefetch_multiplier = 1
