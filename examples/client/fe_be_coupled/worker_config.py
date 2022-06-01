from base_be_worker.queues.sqs import Queue, Queues

Queues.init(
    queues=[
        Queue(
            queue_name="python-backend-worker-template-polymorphism-demo",
            task="polymorphism_task",
            ratelimit_name="python_backend_worker_template_polymorphism_demo",
        ),
    ],
    env="local",
)

broker_transport_options = {
    "region": "us-west-1",
}
broker_url = "sqs://"

task_queues = Queues.celery_task_queues()

task_routes = Queues.celery_task_routes()
