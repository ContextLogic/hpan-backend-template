from queues.sqs import Queue, Queues

QUEUES = Queues(
    [
        Queue(
            queue_name="python-backend-worker-template-polymorphism-demo",
            task="polymorphism_task",
            ratelimit_name="python_backend_worker_template_polymorphism_demo",
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
