"""
main script to create a worker, configure the worker and start it.
"""

from base_be_worker.worker import Worker

from app.config.config import Config, WorkerConfig
from app.tasks import register_tasks

worker = Worker(
    "all",
    celery_worker_config=WorkerConfig,
    task_register_func=register_tasks,
    **vars(Config)
)

if __name__ == "__main__":
    worker.start()
