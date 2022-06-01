import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
import logging

logger = logging.getLogger(__name__)


def init_sentry(conf):
    if hasattr(conf, 'sentry_dsn'):
        sentry_sdk.init(conf.sentry_dsn, integrations=[CeleryIntegration()], environment=conf.env)
    else:
        logger.warning('missing sentry_dsn in the config file, sentry is disabled')