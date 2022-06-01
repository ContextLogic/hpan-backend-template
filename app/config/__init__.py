"""
contains a method to read args from cli and overwrite the default configurations.
It also generates a global CONF, CELERY_WORKER_CONFIG configuration objects, which can be accessed from other modules.
"""

from argparse import ArgumentParser, SUPPRESS
from importlib import import_module

from app.config.configuration.configuration import Config, WorkerConfig
from app.config.queues import QUEUES


def init_configs() -> tuple[Config, WorkerConfig]:
    """
    calls at app startup phase, loads the configuration file,
    parse the cli arguments and overwrite the config if specified.
    return app config and celery config.
    """
    parser = ArgumentParser(description="python-backend-worker-template")
    parser.add_argument(
        "-l", "--log_level", type=str, default=SUPPRESS, help="log level"
    )
    parser.add_argument("-e", "--env", type=str, default=SUPPRESS, help="environment")
    parser.add_argument(
        "-p", "--server_port", type=int, default=SUPPRESS, help="server port"
    )
    parser.add_argument(
        "-c",
        "--config_module",
        type=str,
        default="app.config.configuration.configuration",
        help="configuration file path in python module format",
    )
    args = parser.parse_args()

    config_module = import_module(args.config_module)

    conf = config_module.Config()  # type: ignore[attr-defined]
    # override the default configuration using the value passed from cli arguments
    for key in args.__dict__:
        setattr(conf, key, args.__dict__.get("key"))

    QUEUES.build_celery(env=conf.env)
    celery_worker_config = config_module.WorkerConfig(QUEUES)  # type: ignore[attr-defined]

    return conf, celery_worker_config


# app-wide config and celery worker config
CONF, CELERY_WORKER_CONFIG = init_configs()
