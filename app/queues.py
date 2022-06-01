from app.queue_wrapper.queue_wrapper import QueueWrapper, QueuesWrapper

QUEUES = QueuesWrapper(
    [
        QueueWrapper(
            queue_name='python-backend-worker-template-add',
            task='app.tasks.tasks.add',
            ratelimit_name='python_backend_worker_template_add',
        ),
        QueueWrapper(
            queue_name='python-backend-worker-template-count',
            task='app.tasks.tasks.count',
            ratelimit_name='python_backend_worker_template_count',
        )
    ],
)
