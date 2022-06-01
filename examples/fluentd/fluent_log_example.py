""" Python Logger Example for Fluentd """
import time
from fluent import sender


def log_periodically() -> None:
    while True:
        cur_time = int(time.time())
        logger.emit_with_time(
            "follow", cur_time, {"from": "test", "to": "this is the an example event"}
        )
        time.sleep(60)


def time_delay(sec: int) -> None:
    time.sleep(sec)


if __name__ == "__main__":
    logger = sender.FluentSender("example.event", host="localhost", port=24224)
    log_periodically()
