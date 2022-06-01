"""
config.queues defines the queue task mapping with ratelimiting (optional),  therefore celery worker is able to know how
to process the task using which function.
"""

from queues.sqs import Queue, Queues

# queues definition, maps sqs queues with a task function and a ratelimiter
QUEUES = Queues(
    [
        Queue(
            queue_name="python-backend-worker-template-retry-demo",
            task="retry_demo",
            ratelimit_name="python_backend_worker_template_retry_demo",
        ),
        Queue(
            queue_name="python-backend-worker-template-add",
            task="add",
            ratelimit_name="python_backend_worker_template_add",
        ),
        Queue(
            queue_name="python-backend-worker-template-polymorphism-demo",
            task="PolymorphismTask",
            ratelimit_name="python_backend_worker_template_polymorphism_demo",
        ),
    ],
)
