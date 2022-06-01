from queues.sqs import Queue, Queues

QUEUES = Queues(
    [
        Queue(
            queue_name="python-backend-worker-template-add",
            task="add",
        ),
        Queue(
            queue_name="python-backend-worker-template-retry-demo",
            task="retry_demo",
        ),
    ],
)
QUEUES.build_celery(env="local")

broker_transport_options = {
    "region": "us-west-1",
}
broker_url = "sqs://"

task_queues = QUEUES.celery_task_queues()

task_routes = QUEUES.celery_task_routes()
