"""
this module defines the default configurations for both app and celery.
"""

from queues.sqs import Queue


class WorkerConfig:
    """
    WorkerConfig holds the celery configuration. For detailed celery configurations, please refer to
    https://docs.celeryproject.org/en/stable/userguide/configuration.html,
    It also holds the task_queues and task_routes built from the customized Queues object.
    """

    def __init__(self, queues: Queue, region: str = "us-west-1") -> None:
        # defines sqs transport options, please refer to
        # https://docs.celeryproject.org/en/stable/getting-started/brokers/sqs.html#options
        # for more details
        self.broker_transport_options = {
            "region": region,
            "polling_interval": 30,
            "wait_time_seconds": 15,
            "visibility_timeout": 60,
        }

        # use custom transport with ratelimiting feature
        self.broker_url = "app.utils.transport.ratelimittransport://"

        # default task queue, any task without a defined route will be routed to the default sqs queue
        self.task_default_queue = "default-python-backend-worker-template"

        # defines the list of task queues
        # you do not need to touch this in common cases
        self.task_queues = queues.celery_task_queues()

        # defines the routes, task to queue should be one-to-one mapping.
        # you do not need to touch this in common cases
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

        # whitelist the serializers.
        self.accept_content = ["pickle", "json"]


class Config:
    """
    Config holds the app's configuration in addition to celery worker configs, including flask server port,
    log level, environment, ratelimit configs, sentry configs etc.
    """

    log_level = "INFO"

    # local, dev, stage or prod
    # this also prepend to the final SQS queue name
    env = "local"

    # project name used for creating flask and celery worker
    name = "python-backend-worker-template"

    # ratelimit service
    ratelimit_host = "ratelimit.service.consul:8080"
    ratelimit_domain = "python-backend-worker-template"

    # flask server port
    server_port = 8080

    # sentry
    sentry_dsn = "https://ae0f12aa12d148eca4e1372c54e01cfa@sentry.infra.wish.com/226"

    # jaeger tracing
    jaeger_sampler_type = "const"
    jaeger_sampler_param = 1

    # fluentd/TD logger
    fluent_host = "localhost"
    fluent_port = 24224
    fluent_log_level = "INFO"
