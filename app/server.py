from flask import Flask
from signal import signal, SIGINT, SIGTERM
from types import FrameType
from threading import Thread
from app.tasks.tasks import celery_app
from app.config.config import CONF
from app.config.worker_config import WorkerConfig
from app.config.queues import QUEUES
from app.sentry.sentry import init_sentry
from app.tasks.signal_handlers import *
from gevent.pywsgi import WSGIServer
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app
from os import getenv
from pathlib import Path
import os
from app.metrics.metrics import worker_registry
from celery.bootsteps import RUN

logging.basicConfig(level=CONF.loglevel)


def create_http_server(worker):
    flask_app = Flask('worker_server')
    flask_app.wsgi_app = DispatcherMiddleware(flask_app.wsgi_app, {
        '/metrics': make_wsgi_app(registry=worker_registry),
    })

    @flask_app.route("/status")
    def health_check():
        """
        health check handler for /status endpoints
        :return: json of worker info
        """
        worker_state = worker.blueprint.state
        stats = {}
        if worker_state == RUN:
            stats = worker.stats()
            stats['state'] = "RUNNING"
        else:
            stats = worker.info()
            stats['state'] = "TERMINATED"
        return {'status': stats}, 200 if worker_state == RUN else 503

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    return WSGIServer(('', CONF.server.port), flask_app, log=log)


def create_worker():
    QUEUES.build_celery(env=CONF.env)
    celery_app.config_from_object(WorkerConfig(QUEUES))
    worker = celery_app.Worker(
        name=CONF.worker.name,
        loglevel=CONF.loglevel,
    )
    return worker


def cleanup_prom_tmp_dir():
    prometheus_multiproc_dir = getenv('prometheus_multiproc_dir', './tmp/prometheus_multiproc_dir')
    for f in Path(prometheus_multiproc_dir).glob('*'):
        try:
            os.remove(f)
        except OSError as e:
            logging.info("Error: %s : %s" % (f, e.strerror))


def start(worker, server):
    def stop(signum: int, stack: FrameType):
        """
        wrapper function of WorkerSever.stop(), it needs to match the signal handler function's signature.
        """
        logging.info("caught SIGNUM:{SIGNUM}, stopping...".format(SIGNUM=signum))
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


if __name__ == "__main__":
    celery_worker = create_worker()
    init_sentry(CONF)
    http_server = create_http_server(celery_worker)
    start(celery_worker, http_server)
