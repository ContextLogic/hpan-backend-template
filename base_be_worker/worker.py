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

from .celery_signals import connect_signal_handlers
from .fluent import FluentLogger
from .ratelimit import RatelimitClient
from .sentry import init as sentry_init
from .metrics import PrometheusMetrics
from .tracing import TracerFactory
from .vault import VaultClient
from .queue_jobs import QueueJobClient

from base_be_worker.queues.sqs import Queues


def _init(*init_options: list, **root_args: dict) -> None:
    """
    initialized all or selected utils
    keyword args: env, queues, prometheus, fluent, sentry_dsn, ratelimit, tracing, vault
    """

    def _init_queue() -> None:
        """
        init queue
        """
        # get env
        env = root_args.get("env", "local")

        # init Queues
        queues = root_args.get("queues", [])
        Queues.init(queues, env)

    def _init_metrics() -> None:
        """
        init metrics
        """
        metrics_config = root_args.get("prometheus", {})
        PrometheusMetrics.init(**metrics_config)

    def _init_fluent() -> None:
        """
        init fluent
        """
        fluent_config = root_args.get("fluent", {})
        FluentLogger.init(**fluent_config)

    def _init_sentry() -> None:
        """
        init sentry
        """
        env = root_args.get("env", "local")
        sentry_dsn = root_args.get("sentry_dsn")
        sentry_init(sentry_dsn, env)

    def _init_ratelimit() -> None:
        """
        init the global rate limiter client instance
        """
        ratelimit_args = root_args.get("ratelimit", {})
        ratelimit_domain = ratelimit_args.get("ratelimit_domain", "python-backend-worker-template")
        ratelimit_url = ratelimit_args.get("ratelimit_url", "http://ratelimit-stage.service.consul:8080/json")
        RatelimitClient.init(
            domain=ratelimit_domain,
            url=ratelimit_url,
            default_ratelimit_name="default",
        )

    def _init_tracing() -> None:
        """
        init tracer factory class
        """
        tracer_config = root_args.get("tracing")
        if tracer_config:
            TracerFactory.init(tracer_config)

    def _init_vault() -> None:
        """
        init vault client
        """
        vault_config = root_args.get("vault", {})
        VaultClient.init(**vault_config)

    def _init_queuejob() -> None:
        """
        init queuejob client
        """
        queuejob_args = root_args.get("queuejob", {})
        QueueJobClient.init(**queuejob_args)

    init_func_map = {
        'queue': _init_queue,
        'metrics': _init_metrics,
        'fluent': _init_fluent,
        'sentry': _init_sentry,
        'ratelimit': _init_ratelimit,
        'tracing': _init_tracing,
        'vault': _init_vault,
        'queuejob': _init_queuejob,
    }

    if 'all' in init_options:
        for _, init_func in init_func_map.items():
            init_func()
        return

    for init_opt in init_options:
        if init_opt in init_func_map:
            init_func_map[init_opt]()


def _create_worker(**kwargs: dict) -> WorkController:
    """
    Configures the Celery app and creates a Celery workerController(main worker process).

    keyword args: name, celery_worker_config, task_register_func, log_level
    """
    name = kwargs.get("name")

    # create a celery app
    celery_app = Celery(name=name)
    celery_worker_config = kwargs.get("celery_worker_config")
    if celery_worker_config:
        celery_app.config_from_object(celery_worker_config, force=True)

    # install celery signal handlers
    connect_signal_handlers()

    # if a task_register_function provided, we call it to register tasks
    task_register_func = kwargs.get("task_register_func")
    if task_register_func:
        task_register_func()

    # create the celery worker controller
    worker = celery_app.Worker(
        name=name,
        loglevel=kwargs.get("log_level", "INFO"),
    )
    return worker


def _cleanup_prom_tmp_dir() -> None:
    """
    when quitting the app, it cleans up temporary directory
    used by prometheus in multiprocess mode.
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


class Worker:
    """
    Worker class defines the abstract for worker and server. It also initializes other utils
    e.g. queues, metrics, vault, tracing, fluent, sentry, ratelimit project-widely.
    """

    def __init__(self, *init_option, **kwargs):
        """
        keyword args: name, celery_worker_config, task_register_func, log_level, port,
        env, queues, prometheus, fluent, sentry_dsn, ratelimit, tracing, vault

        """
        # init different utils
        _init(*init_option, **kwargs)

        # set up task_queues and task_routes for celery
        celery_worker_config = kwargs.get('celery_worker_config', {})
        celery_worker_config.task_queues = Queues.celery_task_queues()
        celery_worker_config.task_routes = Queues.celery_task_routes()
        kwargs['celery_worker_config'] = celery_worker_config

        self.worker = _create_worker(**kwargs)
        self.server = self._create_http_server(**kwargs)

    def _create_http_server(self, **kwargs) -> WSGIServer:
        """
        Create a WSGI server based on a flask_app given a celery WorkerController,
        this WSGI server provides two http endpoints.

        1. GET /status, it checks the WorkerController status,
        return 200 if the WorkerController is running properly.
        return 503 if the WorkerController is dead.

        2. GET /metrics, it exposes the prometheus metrics
        to be able to be scraped by Prom servers.

        keyword args: name, port
        """
        flask_app = Flask(kwargs.get("name", "flask_server"))
        flask_app.wsgi_app = DispatcherMiddleware(  # type: ignore[assignment]
            flask_app.wsgi_app,
            {
                "/metrics": make_wsgi_app(registry=PrometheusMetrics.WORKER_REGISTRY),
            },
        )

        # pylint: disable=unused-variable
        @flask_app.route("/status")
        def health_check() -> Tuple[dict, int]:
            """
            health check handler for /status endpoints
            :return: json of worker info
            """
            worker_state = self.worker.blueprint.state
            stats = {}
            if worker_state == RUN:
                stats = self.worker.stats()
                stats["state"] = "RUNNING"
            else:
                stats = self.worker.info()
                stats["state"] = "TERMINATED"
            return {"status": stats}, 200 if worker_state == RUN else 503

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        return WSGIServer(("", kwargs.get('port', 8080)), flask_app, log=log)

    def start(self) -> None:
        """
        A blocking function that starts the WorkerController in another thread and launches the WSGI server and listen to
        the port.
        """

        def stop(signum: int, stack: FrameType) -> None:
            """
            wrapper function of WorkerSever.stop(), it needs to match the signal handler function's signature.
            """
            logging.info("caught SIGNUM: %d, stopping...", signum)
            self.worker.stop()
            self.server.stop()
            _cleanup_prom_tmp_dir()

        signal(SIGTERM, stop)
        signal(SIGINT, stop)

        logging.info("starting celery worker...")
        worker_process = Thread(name="worker", target=self.worker.start)
        worker_process.start()

        logging.info("starting server...")
        self.server.serve_forever()

        worker_process.join()
