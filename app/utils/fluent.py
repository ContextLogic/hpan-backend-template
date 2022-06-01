"""
utils.fluent provides a factory class to get a fluent logger, to enable sending logs to TD
"""

import logging
from typing import Any
from typing import (
    Optional,
)

from fluent.sender import FluentSender as sender

from app.config import CONF


class FluentLogger:
    """
    A fluent logger factory class
    """

    _env: Optional[str] = None
    _host: Optional[str] = None
    _port: Optional[int] = None
    _default_db_name = "tcui_test"
    _table_prefix = CONF.name
    _log_level = logging.WARN  # Default value

    class _FluentLogger:
        def __init__(
            self,
            env: str,
            host: str,
            port: int,
            table_name: str,
            default_db_name: str,
            table_prefix: str,
            log_level: int,
            logger: logging.Logger = None,
        ):
            self.level = log_level
            self._table_name = f"{table_prefix}_{table_name}"
            self._logger = logger

            if env != CONF.env:
                self._table_name = f"{self._table_name}_{env}"

            self._sender = sender(default_db_name, host=host, port=port)

        def debug(self, data: Any) -> None:
            """
            debug
            """
            if self.level <= logging.DEBUG:
                self._sender.emit(self._table_name, data)
            if self._logger:
                self._logger.debug(data)

        def info(self, data: Any) -> None:
            """
            info
            """
            if self.level <= logging.INFO:
                self._sender.emit(self._table_name, data)
            if self._logger:
                self._logger.info(data)

        def warning(self, data: Any) -> None:
            """
            warn
            """
            if self.level <= logging.WARN:
                self._sender.emit(self._table_name, data)
            if self._logger:
                self._logger.warning(data)

        def error(self, data: Any) -> None:
            """
            error
            """
            if self.level <= logging.ERROR:
                self._sender.emit(self._table_name, data)
            if self._logger:
                self._logger.error(data)

        def critical(self, data: Any) -> None:
            """
            critical
            """
            if self.level <= logging.CRITICAL:
                self._sender.emit(self._table_name, data)
            if self._logger:
                self._logger.critical(data)

        def __del__(self) -> None:
            self._sender.close()

    @classmethod
    def init(cls, env: str, host: str, port: int, log_level: str) -> None:
        """
        initialize the factory class
        """
        cls._env = env
        cls._host = host
        cls._port = port
        cls._log_level = logging.getLevelName(log_level)

    @classmethod
    def get_logger(
        cls, table_name: str, logger: logging.Logger = None
    ) -> _FluentLogger:
        """
        create a fluent logger using this factory class
        """
        env: str = ""
        host: str = ""
        port: int = 0

        if cls._env is not None:
            env = cls._env
        if cls._host is not None:
            host = cls._host
        if cls._port is not None:
            port = cls._port

        return cls._FluentLogger(
            env,
            host,
            port,
            table_name,
            cls._default_db_name,
            cls._table_prefix,
            cls._log_level,
            logger,
        )
