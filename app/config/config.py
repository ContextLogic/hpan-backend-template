"""
this module defines the default configurations for both app and celery.
"""

import logging

from base_be_worker.queues.sqs import Queue
from jaeger_client import Config as JaegerConfig
from opentelemetry.sdk.resources import SERVICE_NAME, KUBERNETES_JOB_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider


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

    # flask server port, used for /metrics and /status
    port = 8080

    # ratelimit service
    ratelimit = {
        # change to http://ratelimit.service.consul:8080/json for prod use
        "ratelimit_url": "testing_ratelimit",
        # please create your own domain beforehand
        # at https://alki.i.wish.com or https://alki-stage.i.wish.com
        "ratelimit_domain": "test_ratelimit_domain",
    }

    # sentry
    sentry_dsn = "testing_sentry"

    # jaeger tracing (deprecated, please use opentelemetry instead)
    # tracing = JaegerConfig(
    #    config={
    #        "sampler": {
    #            "type": "const",
    #            "param": 1,
    #        },
    #    },
    #    service_name="python-backend-worker-template",
    #    validate=True,
    # )

    # Opentelemetry
    opentelemetry = TracerProvider(
        resource=Resource.create(
            {
                SERVICE_NAME: "python-backend-worker-template-opentelemetry",
                KUBERNETES_JOB_NAME: "python-backend-worker-template",
            }
        )
    )

    # queues
    queues = [
        Queue(
            queue_name="python-backend-worker-template-retry-demo",
            task="retry_demo",
            # change to your own ratelimit name
            ratelimit_name="python_backend_worker_template_retry_demo",
        ),
        Queue(
            queue_name="python-backend-worker-template-add",
            task="add",
            # change to your own ratelimit name
            ratelimit_name="python_backend_worker_template_add",
        ),
        Queue(
            queue_name="python-backend-worker-template-polymorphism-demo",
            task="PolymorphismTask",
            # change to your own ratelimit name
            ratelimit_name="python_backend_worker_template_polymorphism_demo",
        ),
    ]

    # fluent
    fluent = {
        "database": "td.mircosvc_demo",
        "table_suffix": "tahoe_stage",
        "host": "localhost",
        "port": 8889,
    }

    # prometheus
    prometheus = {
        "metrics_prefix": name,
    }

    # mongo
    mongo = {
        "uri": "mongogatenative-microsvcstage-online.service.consul:27017",
        "db": "python-backend-worker",
    }


class WorkerConfig:
    """
    WorkerConfig holds the celery configuration. For detailed celery configurations, please refer to
    https://docs.celeryproject.org/en/stable/userguide/configuration.html,
    It also holds the task_queues and task_routes built from the customized Queues object.
    """

    # defines sqs transport options, please refer to
    # https://docs.celeryproject.org/en/stable/getting-started/brokers/sqs.html#options
    # for more details
    broker_transport_options = {
        "region": "us-west-1",
        "polling_interval": 30,
        "wait_time_seconds": 15,
    }

    # use custom transport with ratelimiting feature
    broker_url = "app.transport.ratelimittransport://"

    # default task queue, any task without a defined route will be routed to the default sqs queue
    task_default_queue = "default-python-backend-worker-template"

    # worker will only ack message on task success/timeout/failure
    task_acks_late = True

    # worker ack message when on task_failure or task_timeout
    task_acks_on_failure_or_timeout = True

    # if worker lost, the message will be re-queued back to the queue.
    task_reject_on_worker_lost = True

    # defines the number of sub worker process
    worker_concurrency = 4

    # It is the multiplier to calculate the prefetch numbers. The calculation is
    # prefetch = worker_concurrency * worker_prefetch_multiplier.
    # The prefetch defines the the number of messages a single poll can get, this can reduce
    # the number of SQS api calls. Please note that, on SQS side this value will not exceed 10.
    worker_prefetch_multiplier = 2

    # whitelist the serializers.
    accept_content = ["pickle", "json"]
