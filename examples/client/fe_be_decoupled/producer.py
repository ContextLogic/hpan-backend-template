from celery import Celery

celery_app = Celery()
celery_app.config_from_object("worker_config")

for i in range(1, 10):
    celery_app.send_task("add", args=(i, i))
    celery_app.send_task("retry_demo", args=(i,))
