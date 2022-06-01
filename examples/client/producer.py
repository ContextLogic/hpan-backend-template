from celery.signals import before_task_publish, after_task_publish
import logging
from celery import Celery

# QUEUES.build_celery(env='local')
# tasks.celery_app.config_from_object(WorkerConfig(QUEUES))


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

@before_task_publish.connect
def task_before_sent_handler(headers=None, routing_key=None, **kwargs):
    logger.info("Sending task: %s to queue: %s", headers.get('task'), routing_key)

@after_task_publish.connect
def task_after_sent_handler(headers=None, routing_key=None, **kwargs):
    logger.info("Successfully sent %s task with id: %s to queue: %s", headers.get('task'), headers.get('id'), routing_key)


celery_app = Celery()
celery_app.config_from_object('worker_config')

# celery_app.send_task('app.tasks.tasks.add', args=(1,1))
celery_app.send_task('app.tasks.tasks.count', args=(0,))


# for i in range(0, 10):
#     tasks.count.delay(i)
#     tasks.add.delay(i, i)


# res = tasks.count.apply_async(args=[2])


# test.delay(1)
# tasks.add.delay(1,2)

