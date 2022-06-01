from flask import Flask
from signal import signal, SIGKILL, SIGINT, SIGTERM
from types import FrameType
from threading import Thread
from app.tasks.tasks import celery_app
from app.config.config import CONF
from app.config.worker_config import WorkerConfig
from app.queues import QUEUES
from app.sentry.sentry import init_sentry
from app.tasks.signal_handlers import *
from gevent.pywsgi import WSGIServer
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app
from os import getenv
from pathlib import Path
import os
from app.metrics.metrics import worker_registry
from celery.bootsteps import RUN, CLOSE, TERMINATE


flask_app = Flask('worker_server')
flask_app.wsgi_app = DispatcherMiddleware(flask_app.wsgi_app, {
    '/metrics': make_wsgi_app(registry=worker_registry),
})
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
http_server = WSGIServer(('', 8080), flask_app, log=log)

init_sentry(CONF)
logging.basicConfig(level=CONF.loglevel)
QUEUES.build_celery(env=CONF.env)
celery_app.config_from_object(WorkerConfig(QUEUES, ))
worker = celery_app.Worker(
    name=CONF.worker.name,
    loglevel=CONF.loglevel,
)

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


# def start_http_server():
#     http_server.start()

def start_worker():
    worker.start()


def start():
    logging.info("starting celery worker...")
    worker_process = Thread(name="worker", target=start_worker)
    worker_process.start()

    logging.info("starting server...")
    http_server.serve_forever()

    worker_process.join()


def cleanup_prom_tmp_dir():
    prometheus_multiproc_dir = getenv('prometheus_multiproc_dir', './tmp/prometheus_multiproc_dir')
    for f in Path(prometheus_multiproc_dir).glob('*'):
        try:
            os.remove(f)
        except OSError as e:
            logging.info("Error: %s : %s" % (f, e.strerror))


def stop(signum: int, stack: FrameType):
    """
    wrapper function of WorkerSever.stop(), it needs to match the signal handler function's signature.
    """
    logging.info("caught SIGNUM:{SIGNUM}, stopping...".format(SIGNUM=signum))
    worker.stop()
    http_server.stop()
    cleanup_prom_tmp_dir()


if __name__ == "__main__":
    signal(SIGTERM, stop)
    signal(SIGINT, stop)
    start()