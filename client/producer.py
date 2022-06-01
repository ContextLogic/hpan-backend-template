from app.tasks import tasks
from app.queues import QUEUES
from app.config.worker_config import WorkerConfig
from celery.signals import before_task_publish, after_task_publish
import logging

QUEUES.build_celery(env='local')
tasks.celery_app.config_from_object(WorkerConfig(QUEUES))

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

@before_task_publish.connect
def task_before_sent_handler(headers=None, routing_key=None, **kwargs):
    logger.info("Sending task: %s to queue: %s", headers.get('task'), routing_key)

@after_task_publish.connect
def task_after_sent_handler(headers=None, routing_key=None, **kwargs):
    logger.info("Successfully sent %s task with id: %s to queue: %s", headers.get('task'), headers.get('id'), routing_key)

@tasks.celery_app.task(
    queue='tcui-local-python-backend-worker-template-add'
)
def test(a):
    return a

for i in range(0, 10):
    tasks.count.delay(i)
    tasks.add.delay(i, i)


# res = tasks.count.apply_async(args=[2])


# test.delay(1)
# tasks.add.delay(1,2)

