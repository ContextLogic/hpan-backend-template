"""
celery_signals defines the signal handlers,
the handlers are mainly used for observability, e.g. metrics and tracing etc.
"""

# pylint: disable=unused-argument
import logging
from datetime import datetime
from typing import Any

from amqp import Message
from billiard.einfo import ExceptionInfo
from celery.app.task import Task
from celery.signals import (
    task_prerun,
    task_postrun,
    task_retry,
    task_failure,
    task_success,
    task_internal_error,
    task_received,
    task_rejected,
    task_revoked,
    task_unknown,
    worker_process_init,
    worker_process_shutdown,
)
from celery.worker.request import Request
from opentracing import global_tracer, set_global_tracer
from opentracing_instrumentation.client_hooks.celery import CeleryPatcher

from .metrics import PrometheusMetrics
from .queues.sqs import Queue, Queues
from .ratelimit import RatelimitClient
from .tracing import TracerFactory

logger = logging.getLogger(__name__)


def connect_signal_handlers() -> None:
    """
    connect all the celery signal handlers
    """
    worker_process_init.connect(worker_process_init_handler, weak=False)
    task_failure.connect(task_failure_handler, weak=False)
    task_internal_error.connect(task_internal_error_handler, weak=False)
    task_postrun.connect(task_postrun_handler, weak=False)
    task_prerun.connect(task_prerun_handler, weak=False)
    task_received.connect(task_received_handler, weak=False)
    task_rejected.connect(task_rejected_handler, weak=False)
    task_retry.connect(task_retry_handler, weak=False)
    task_revoked.connect(task_revoked_handler, weak=False)
    task_success.connect(task_success_handler, weak=False)
    task_unknown.connect(task_unknown_handler, weak=False)


def disconnect_signal_handlers() -> None:
    """
    disconnect all the celery signal handlers
    """
    worker_process_init.disconnect(worker_process_init_handler, weak=False)
    task_failure.disconnect(task_failure_handler, weak=False)
    task_internal_error.disconnect(task_internal_error_handler, weak=False)
    task_postrun.disconnect(task_postrun_handler, weak=False)
    task_prerun.disconnect(task_prerun_handler, weak=False)
    task_received.disconnect(task_received_handler, weak=False)
    task_rejected.disconnect(task_rejected_handler, weak=False)
    task_retry.disconnect(task_retry_handler, weak=False)
    task_revoked.disconnect(task_revoked_handler, weak=False)
    task_success.disconnect(task_success_handler, weak=False)
    task_unknown.disconnect(task_unknown_handler, weak=False)


def safe_extract(obj: object, attribute: str, default: Any = None) -> Any:
    """
    extract attribute value from an object, if non-existed, then return the default value.
    """
    if hasattr(obj, attribute):
        return getattr(obj, attribute)
    return default


def worker_process_init_handler(*args: list, **kwargs: dict) -> None:
    """
    when worker proecss initialized, we create a new tracer
    and install celery tracing patches for it.
    """
    tracer = TracerFactory.get_tracer()
    set_global_tracer(tracer)
    CeleryPatcher().install_patches()


def task_prerun_handler(task_id: str = None, task: Task = None, **kwargs: dict) -> None:
    """
    handler function gets run before a task gets executed. It mainly used for emitting metrics
    """
    task_name = safe_extract(task, "name")
    request = safe_extract(task, "request")
    delivery_info: dict = safe_extract(request, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="PRERUN"
    ).inc()

    now = datetime.now()
    request.prerun_timestamp = now

    received_timestamp = safe_extract(request, "received_timestamp")
    if received_timestamp:
        latency_time = now - received_timestamp
        PrometheusMetrics.TASKS_LATENCY_SECONDS.labels(  # type: ignore[union-attr]
            name=task_name, queue=queue
        ).observe(latency_time.total_seconds())

    logger.debug("Task %s[%s] from %s started", task_name, task_id, queue)

    # increase the ratelimit hit count, e.g. if the ratelimit of Add task is set to 10/s,
    # and 10 Add tasks run in 1 second, the consumer will not fetch any Add tasks from the queue.
    RatelimitClient.increase_hit(Queues.ratelimit_name(queue))  # type: ignore[arg-type]


def task_postrun_handler(
    task_id: str = None,
    task: Task = None,
    retval: object = None,
    state: str = None,
    **kwargs: dict
) -> None:
    """
    handler function gets run after a task gets executed. It mainly used for emitting metrics
    """
    task_name = safe_extract(task, "name")
    request = safe_extract(task, "request")
    prerun_timestamp = safe_extract(request, "prerun_timestamp")
    delivery_info = safe_extract(request, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="POSTRUN"
    ).inc()

    if prerun_timestamp:
        run_time = datetime.now() - prerun_timestamp
        PrometheusMetrics.TASKS_RUNTIME_SECONDS.labels(  # type: ignore[union-attr]
            name=task_name, queue=queue
        ).observe(run_time.total_seconds())
        logger.debug(
            "Task %s[%s] finished, retval: %s, state: %s, in %ss",
            task_name,
            task_id,
            retval,
            state,
            run_time.total_seconds(),
        )


def task_retry_handler(
    request: Task.request,
    reason: Exception = None,
    einfo: ExceptionInfo = None,
    **kwargs: dict
) -> None:
    """
    handler function gets run when a task gets retried. It mainly used for emitting metrics
    """
    task_name = request.get("task")
    delivery_info = safe_extract(request, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="RETRY"
    ).inc()

    logger.debug(
        "Task %s[%s] retrying, reason: %s",
        request.get("task"),
        request.get("id"),
        reason,
    )


def task_failure_handler(task_id: str = None, **kwargs: dict) -> None:
    """
    handler function gets run when a task execution failed. It mainly used for emitting metrics
    """
    task: Task = kwargs.get("sender")
    request = safe_extract(task, "request")
    task_name = safe_extract(request, "task")
    delivery_info = safe_extract(request, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="FAILED"
    ).inc()

    if queue:
        dlq_queue = Queue.convert_full_to_dlq_name(queue)
        task.apply_async(args=task.request.args, task_id=task_id, queue=dlq_queue)
        logger.debug(
            "Task %s[%s] failed, sent to dlq: %s.",
            task.request.get("task"),
            task_id,
            dlq_queue,
        )


def task_success_handler(**kwargs: dict) -> None:
    """
    handler function gets run when a task execution is successful.
    It is mainly used for emitting metrics
    """
    task = kwargs.get("sender")
    request = safe_extract(task, "request")
    delivery_info = safe_extract(request, "delivery_info", {})
    task_name = safe_extract(request, "task")
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="SUCCESS"
    ).inc()


def task_internal_error_handler(**kwargs: dict) -> None:
    """
    handler function gets run when an internal Celery error occurs while executing the task.
    It mainly used for emitting metrics
    """
    task = kwargs.get("sender")
    request = safe_extract(task, "request")
    delivery_info = safe_extract(request, "delivery_info", {})
    task_name = safe_extract(request, "task")
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="INTERNAL_ERROR"
    ).inc()


def task_received_handler(request: Request = None, **kwargs: dict) -> None:
    """
    handler function gets run when a task received by the consumer from the Queue.
    It mainly used for emitting metrics
    """
    delivery_info = safe_extract(request, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    message = safe_extract(request, "_message")
    headers = safe_extract(message, "headers", {})
    task_name = headers.get("task")
    PrometheusMetrics.CONSUMER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=task_name, queue=queue, state="RECEIVED"
    ).inc()

    message.headers["received_timestamp"] = datetime.now()


def task_rejected_handler(message: Message = None, **kwargs: dict) -> None:
    """
    handler function gets run when a worker receives
    an unknown type of message to one of its task queues.
    It is mainly used for emitting metrics
    """
    delivery_info = safe_extract(message, "delivery_info", {})
    sqs_queue = delivery_info.get("sqs_queue")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=None, queue=sqs_queue, state="REJECTED"
    ).inc()


def task_revoked_handler(
    request: Request = None,
    terminated: bool = None,
    signum: int = None,
    expired: bool = None,
    **kwargs: dict
) -> None:
    """
    handler function gets run when a task is revoked/terminated by the worker.
    It mainly used for emitting metrics
    """
    delivery_info = safe_extract(request, "delivery_info", {})
    format_map = {
        "task_name": safe_extract(request, "task"),
        "task_id": safe_extract(request, "task_id"),
        "queue": delivery_info.get("routing_key"),
        "terminated": terminated,
        "signum": signum,
        "expired": expired,
    }
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=format_map["task_name"], queue=format_map["queue"], state="REVOKED"
    ).inc()
    logger.debug(
        "Task {task_name}[{task_id] from {queue} gets revoked, "
        "terminated: {terminated}, signum: {signum}, expired: {"
        "expired}".format_map(format_map)
    )


def task_unknown_handler(
    name: str = None, message: Message = None, **kwargs: dict
) -> None:
    """
    handler function gets run when a worker
    receives a message for a task that’s not registered.
    It mainly used for emitting metrics
    """
    delivery_info = safe_extract(message, "delivery_info", {})
    queue = delivery_info.get("routing_key")
    PrometheusMetrics.WORKER_TASKS_COUNT.labels(  # type: ignore[union-attr]
        name=name, queue=queue, state="UNKNOWN"
    ).inc()
