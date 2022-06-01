from flask import Flask
from flask_restful import Api
from app.metrics.prom_handler import MetricsHandler
from signal import signal, SIGKILL, SIGINT, SIGTERM
from sys import exit, stdout
from types import FrameType
from multiprocessing import Process
import logging
from app.tasks.tasks import celery_app
from app.config.config import CONF
from app.config.worker_config import WorkerConfig
from app.queues import QUEUES
from app.sentry.sentry import init_sentry


class Server:
    """
    defines the worker server consists of a flask application as the foundation and a celery worker thread.
    flask app exposes status of health check and metrics. While celery worker running in background.
    """
    flask_app = Flask('worker_server')

    def __init__(self, worker, config):
        # create a restful server
        self.server_api = Api(self.flask_app)
        self.server_api.add_resource(MetricsHandler, '/metrics')
        self.server_port = config.server.port
        self.worker = worker

    def stop(self):
        """
        stop the worker process gracefully and exit the main process, because flask app does not have a graceful way of
        shutting down
        """
        self.worker.stop(exitcode=0)
        self._worker_process.join()
        exit(0)


init_sentry(CONF)
QUEUES.build_celery(env=CONF.env)
celery_app.config_from_object(WorkerConfig(QUEUES, ))
logging.basicConfig(level=CONF.loglevel)
worker = celery_app.Worker(
    name=CONF.worker.name,
    loglevel=CONF.loglevel,
)
worker_server = Server(worker, CONF)


@worker_server.flask_app.route("/status")
def health_check():
    """
    health check handler for /status endpoints
    :return: json of worker info
    """
    return {"status": worker_server.worker.info()}


def start_worker_server():
    worker_server.flask_app.run(host='0.0.0.0', port=worker_server.server_port)


def start():
    logging.info("starting server...")
    server_process = Process(name="server", target=start_worker_server)
    server_process.start()

    logging.info("starting celery worker...")
    worker_server.worker.start()
    server_process.join()


def stop(signum: int, stack: FrameType):
    """
    wrapper function of WorkerSever.stop(), it needs to match the signal handler function's signature.
    """
    logging.info("caught SIGNUM:{SIGNUM}, stopping...".format(SIGNUM=signum))
    worker_server.stop()


if __name__ == "__main__":
    signal(SIGTERM, stop)
    signal(SIGINT, stop)
    start()
