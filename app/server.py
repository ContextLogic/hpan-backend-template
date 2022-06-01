"""
server module is the main, where creates a flask server and celery app/worker, initializes all the utils
and start the server/worker process.
"""

import logging
import os
from os import getenv
from pathlib import Path
from signal import signal, SIGINT, SIGTERM
from threading import Thread
from types import FrameType
from typing import Tuple

from celery import Celery
from celery.bootsteps import RUN
from celery.worker import WorkController
from flask import Flask
from gevent.pywsgi import WSGIServer
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from app.config import CONF, CELERY_WORKER_CONFIG
from app.tasks import register_tasks
from app.utils.celery_signals import connect_signal_handlers
from app.utils.fluent import FluentLogger
from app.utils.metrics import worker_registry
from app.utils.ratelimit import RatelimitClient
from app.utils.sentry import init_sentry


def create_http_server(worker: WorkController) -> WSGIServer:
    """
    Create a WSGI server based on a flask_app given a celery WorkerController, this WSGI server provides two http
    endpoints.
    1. GET /status, it checks the WorkerController status, return 200 if the WorkerController is running properly.
    return 503 if the WorkerController is dead.
    2. GET /metrics, it exposes the prometheus metrics to be able to be scraped by Prom servers.
    """
    flask_app = Flask(CONF.name)
    flask_app.wsgi_app = DispatcherMiddleware(  # type: ignore[assignment]
        flask_app.wsgi_app,
        {
            "/metrics": make_wsgi_app(registry=worker_registry),
        },
    )

    # pylint: disable=unused-variable
    @flask_app.route("/status")
    def health_check() -> Tuple[dict, int]:
        """
        health check handler for /status endpoints
        :return: json of worker info
        """
        worker_state = worker.blueprint.state
        stats = {}
        if worker_state == RUN:
            stats = worker.stats()
            stats["state"] = "RUNNING"
        else:
            stats = worker.info()
            stats["state"] = "TERMINATED"
        return {"status": stats}, 200 if worker_state == RUN else 503

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    return WSGIServer(("", CONF.server_port), flask_app, log=log)


def create_worker() -> WorkController:
    """
    Configures the Celery app and creates a Celery workerController(main worker process).
    """
    celery_app = Celery(name=CONF.name)
    celery_app.config_from_object(CELERY_WORKER_CONFIG)
    connect_signal_handlers()
    register_tasks()

    worker = celery_app.Worker(
        name=CONF.name,
        loglevel=CONF.log_level,
    )
    return worker


def cleanup_prom_tmp_dir() -> None:
    """
    when quitting the app, it cleans up temporary directory used by prometheus in multiprocess mode.
    """
    prometheus_multiproc_dir = getenv(
        "prometheus_multiproc_dir", "./prometheus_multiproc_dir"
    )
    for tmp_file in Path(prometheus_multiproc_dir).glob("*"):
        try:
            os.remove(tmp_file)
        except OSError as err:
            logging.info(
                "failed to delete %s/%s: %s",
                prometheus_multiproc_dir,
                tmp_file,
                err.strerror,
            )
    try:
        os.rmdir(prometheus_multiproc_dir)
    except OSError as err:
        logging.info(
            "failed to delete the empty dir %s: %s",
            prometheus_multiproc_dir,
            err.strerror,
        )


def start(worker: WorkController, server: WSGIServer) -> None:
    """
    A blocking function that starts the WorkerController in another thread and launches the WSGI server and listen to
    the port.
    """

    def stop(signum: int, stack: FrameType) -> None:
        """
        wrapper function of WorkerSever.stop(), it needs to match the signal handler function's signature.
        """
        logging.info("caught SIGNUM: %d, stopping...", signum)
        worker.stop()
        server.stop()
        cleanup_prom_tmp_dir()

    signal(SIGTERM, stop)
    signal(SIGINT, stop)

    logging.info("starting celery worker...")
    worker_process = Thread(name="worker", target=worker.start)
    worker_process.start()

    logging.info("starting server...")
    server.serve_forever()

    worker_process.join()


def init_utils() -> None:
    """
    initialized all utils
    """
    # sentry
    init_sentry(CONF.sentry_dsn, CONF.env)

    # a global rate limiter client instance
    RatelimitClient.init(
        domain=CONF.ratelimit_domain,
        host=CONF.ratelimit_host,
        default_ratelimit_name="default",
    )

    # fluent logger
    FluentLogger.init(
        CONF.env, CONF.fluent_host, CONF.fluent_port, CONF.fluent_log_level
    )


if __name__ == "__main__":
    celery_worker = create_worker()
    init_utils()
    http_server = create_http_server(celery_worker)
    start(celery_worker, http_server)
