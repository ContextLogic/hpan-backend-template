from celery.signals import task_prerun, task_postrun, task_retry, task_failure, task_success, task_internal_error, \
    task_received, task_rejected, task_revoked, task_unknown
import logging
from datetime import datetime
from queues.sqs import Queue
from app.metrics.metrics import WORKER_TASKS_COUNT, CONSUMER_TASKS_COUNT, TASKS_RUNTIME_SECONDS, TASKS_LATENCY_SECONDS

logger = logging.getLogger(__name__)


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, **kwargs):
    task_name = safe_extract(task, 'name')
    request = safe_extract(task, 'request')
    delivery_info = safe_extract(request, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='PRERUN').inc()

    now = datetime.now()
    request.prerun_timestamp = now

    received_timestamp = safe_extract(request, 'received_timestamp')
    if received_timestamp:
        latency_time = now - received_timestamp
        TASKS_LATENCY_SECONDS.labels(name=task_name, queue=queue).observe(latency_time.total_seconds())

    logger.debug("Task %s[%s] from %s started", task_name, task_id, queue)


@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, retval=None, state=None, **kwargs):
    task_name = safe_extract(task, 'name')
    request = safe_extract(task, 'request')
    prerun_timestamp = safe_extract(request, 'prerun_timestamp')
    delivery_info = safe_extract(request, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='POSTRUN').inc()

    if prerun_timestamp:
        run_time = datetime.now() - prerun_timestamp
        TASKS_RUNTIME_SECONDS.labels(name=task_name, queue=queue).observe(run_time.total_seconds())
        logger.debug("Task %s[%s] finished, retval: %s, state: %s, in %ss", task_name, task_id, retval,
                 state, run_time.total_seconds())


@task_retry.connect
def task_retry_handler(request=None, reason=None, einfo=None, **kwargs):
    task_name = request.get('task')
    delivery_info = safe_extract(request, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='RETRY').inc()

    logger.debug("Task %s[%s] retrying, reason: %s", request.get('task'), request.get('id'), reason)


@task_failure.connect
def task_failure_handler(task_id=None, **kwargs):
    task = kwargs.get('sender')
    request = safe_extract(task, 'request')
    task_name = safe_extract(request, 'task')
    delivery_info = safe_extract(request, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='FAILED').inc()

    if queue:
        dlq_queue = Queue.convert_full_to_dlq_name(queue)
        task.apply_async(args=task.request.args, task_id=task_id, queue=dlq_queue)
        logger.debug("Task %s[%s] failed, sent to dlq: %s.", task.request.get('task'), task_id, dlq_queue)


@task_success.connect
def task_success_handler(**kwargs):
    task = kwargs.get('sender')
    request = safe_extract(task, 'request')
    delivery_info = safe_extract(request, 'delivery_info', {})
    task_name = safe_extract(request, 'task')
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='SUCCESS').inc()


@task_internal_error.connect
def task_internal_error_handler(**kwargs):
    task = kwargs.get('sender')
    request = safe_extract(task, 'request')
    delivery_info = safe_extract(request, 'delivery_info', {})
    task_name = safe_extract(request, 'task')
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=task_name, queue=queue, state='INTERNAL_ERROR').inc()


@task_received.connect
def task_received_handler(request=None, **kwargs):
    delivery_info = safe_extract(request, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    message = safe_extract(request, '_message')
    headers = safe_extract(message, 'headers', {})
    task_name = headers.get('task')
    CONSUMER_TASKS_COUNT.labels(name=task_name, queue=queue, state='RECEIVED').inc()

    message.headers['received_timestamp'] = datetime.now()


@task_rejected.connect
def task_rejected_handler(message=None, **kwargs):
    delivery_info = safe_extract(message, 'delivery_info', {})
    sqs_queue = delivery_info.get('sqs_queue')
    WORKER_TASKS_COUNT.labels(name=None, queue=sqs_queue, state='REJECTED').inc()


@task_revoked.connect
def task_revoked_handler(request=None, terminated=None, signum=None, expired=None, **kwargs):
    delivery_info = safe_extract(request, 'delivery_info', {})
    format_map = {
        'task_name': safe_extract(request, 'task'),
        'task_id': safe_extract(request, 'task_id'),
        'queue': delivery_info.get('routing_key'),
        'terminated': terminated,
        'signum': signum,
        'expired': expired,
    }
    WORKER_TASKS_COUNT.labels(name=format_map['task_name'], queue=format_map['queue'], state='REVOKED').inc()
    logger.debug('Task {task_name}[{task_id] from {queue} gets revoked, terminated: {terminated}, signum: {signum}, '
                 'expired: {expired}'.format_map(format_map))


@task_unknown.connect
def task_unknonw_handler(name=None, message=None, **kwargs):
    delivery_info = safe_extract(message, 'delivery_info', {})
    queue = delivery_info.get('routing_key')
    WORKER_TASKS_COUNT.labels(name=name, queue=queue, state='UNKNOWN').inc()


def safe_extract(object, attribute, default=None):
    if hasattr(object, attribute):
        return getattr(object, attribute)
    return default
