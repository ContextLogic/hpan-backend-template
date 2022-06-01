"""
main script to create a worker, configure the worker and start it.
"""

from base_be_worker.worker import Worker
from app.config.config import Config, WorkerConfig
from app.config.load import load_options_from_cli
from app.tasks import register_tasks
from wish_fluent_logger import configure_fluentd_logging

if __name__ == "__main__":
    load_options_from_cli()
    configure_fluentd_logging(
        host=Config.fluent["host"],
        port=Config.fluent["port"],
        database=Config.fluent["database"],
        table_suffix=Config.fluent["table_suffix"],
    )
    worker = Worker(
        "all",
        celery_worker_config=WorkerConfig,
        task_register_func=register_tasks,
        **vars(Config)
    )
    worker.start()
