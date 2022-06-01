from celery.signals import task_prerun, task_postrun, task_retry, task_failure, task_success, task_internal_error, \
    task_received, task_rejected, task_revoked, task_unknown
import logging
from datetime import datetime
from app.queue_wrapper.queue_wrapper import QueueWrapper

logger = logging.getLogger(__name__)

task_runtime = {}


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, **kwargs):
    logger.info("start running %s[%s], args: %s", task.name, task_id, args)
    task_runtime[task_id] = datetime.now()


@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, retval=None, state=None, **kwargs):
    run_time = datetime.now() - task_runtime.get(task_id, 0)
    task_runtime.pop(task_id, None)
    logger.info("Task %s[%s] finished, retval: %s, state: %s, in %ss", task.name, task_id, retval,
                state, run_time.total_seconds())


@task_retry.connect
def task_retry_handler(request=None, reason=None, einfo=None, **kwargs):
    logger.info("Task %s[%s] retrying, reason: %s", request.get('task'), request.get('id'), reason)


@task_failure.connect
def task_failure_handler(task_id=None, **kwargs):
    task = kwargs.get('sender')
    queue = task.request.delivery_info.get('routing_key')
    dlq_queue = QueueWrapper.convert_full_to_dlq_name(queue)
    task.apply_async(args=task.request.args, task_id=task_id, queue=dlq_queue)
    logger.info("Task %s[%s] failed, sent to dlq: %s.", task.request.get('task'), task_id, dlq_queue)

@task_success.connect
def task_success_handler(**kwargs):
    task = kwargs.get('sender')
    task_name = task.request.task
    queue = task.request.delivery_info.get('routing_key')
    logger.info(task_name)
    logger.info(queue)

@task_internal_error.connect
def task_internal_error_handler(**kwargs):
    task = kwargs.get('sender')

@task_received.connect
def task_received_handler(**kwargs):
    pass

@task_rejected.connect
def task_rejected_handler(**kwargs):
    pass

@task_revoked.connect
def task_revoked_handler(**kwargs):
    pass

@task_unknown.connect
def task_unknonw_handler(**kwargs):
    pass
