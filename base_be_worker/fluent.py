"""
fluent provides a factory class to get a fluent_logger logger, to enable sending logs to TD
"""

import logging
from typing import Any

from fluent.sender import FluentSender as sender


class FluentLogger:
    """
    A fluent logger factory class
    """

    _env: str = "local"
    _host: str = "localhost"
    _port: int = 24224
    _default_db = "python-be"
    _table_prefix = "default"
    _log_level = logging.WARN  # Default value

    class _FluentLogger:
        # pylint: disable=too-many-arguments
        def __init__(
            self,
            env: str,
            host: str,
            port: int,
            table: str,
            database: str,
            table_prefix: str,
            log_level: int,
            logger: logging.Logger = None,
        ):
            self.level = log_level
            self._table_name = f"{table_prefix}_{table}"
            self._logger = logger

            if env.capitalize() not in ["PROD", "PRODUCTION"]:
                self._table_name = f"{self._table_name}_{env}"

            self._sender = sender(database, host=host, port=port)

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
    def init(cls, **kwargs: dict) -> None:
        """
        initialize the factory class
        """
        cls._env = kwargs.get("env", cls._env)  # type: ignore[assignment]
        cls._host = kwargs.get("host", cls._host)  # type: ignore[assignment]
        cls._port = kwargs.get("port", cls._port)  # type: ignore[assignment]
        cls._log_level = kwargs.get("log_level", cls._log_level)  # type: ignore[assignment]
        cls._default_db = kwargs.get("default_db", cls._default_db)  # type: ignore[assignment]
        cls._table_prefix = kwargs.get(
            "table_prefix", cls._table_prefix  # type: ignore[assignment]
        )

    @classmethod
    def get_logger(cls, table: str, logger: logging.Logger = None) -> _FluentLogger:
        """
        create a fluent_logger logger using this factory class
        """
        return cls._FluentLogger(
            cls._env,
            cls._host,
            cls._port,
            table,
            cls._default_db,
            cls._table_prefix,
            cls._log_level,
            logger,
        )
