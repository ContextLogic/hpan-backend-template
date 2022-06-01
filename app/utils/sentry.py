"""
provides a sentry init method to initialize sentry integration in celery
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration


def init_sentry(dsn: str = None, env: str = None) -> None:
    """
    Initialized the sentry with given the sentry_dsn and env
    """
    if dsn:
        sentry_sdk.init(dsn, integrations=[CeleryIntegration()], environment=env)
    else:
        logging.warning("missing sentry_dsn, sentry is disabled")
