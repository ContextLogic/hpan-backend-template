""" Python Logger Example for Fluentd """
import time
from app.utils.fluent import FluentLogger
import logging

logging.basicConfig(level="DEBUG")

FluentLogger.init(env="local", host="localhost", port=24224, log_level="INFO")

logger = FluentLogger.get_logger("example", logger=logging.getLogger("test"))

if __name__ == "__main__":
    logger.debug({"level": "debug", "message": "this is debug"})
    logger.info({"level": "debug", "message": "this is info"})
    logger.warning({"level": "debug", "message": "this is warning"})
    logger.error({"level": "debug", "message": "this is error"})
    logger.critical({"level": "debug", "message": "this is critical"})

    # wait for sometime for flushing messages.
    time.sleep(5)
