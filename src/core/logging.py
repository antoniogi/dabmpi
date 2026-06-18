#!/usr/bin/env python3

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


#
# Custom BEST level
#
BEST_LEVEL = 25
BEST_LEVEL_NAME = "BEST"


def rotate_on_startup(
    log_path: Path,
    backup_count: int,
) -> None:
    """Rotate existing logs before starting a new run."""

    if not log_path.exists():
        return

    #
    # Remove oldest backup
    #
    oldest = Path(f"{log_path}.{backup_count}")

    if oldest.exists():
        oldest.unlink()

    #
    # Shift backups
    #
    for i in range(backup_count - 1, 0, -1):
        src = Path(f"{log_path}.{i}")

        if src.exists():
            src.rename(f"{log_path}.{i + 1}")

    #
    # Move current log -> .1
    #
    log_path.rename(f"{log_path}.1")


def _register_custom_levels() -> None:
    """Register custom logging levels."""

    logging.addLevelName(
        BEST_LEVEL,
        BEST_LEVEL_NAME,
    )

    if not hasattr(logging.Logger, "best"):

        def best(
            self: logging.Logger,
            message: str,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            if self.isEnabledFor(BEST_LEVEL):
                self._log(
                    BEST_LEVEL,
                    message,
                    args,
                    **kwargs,
                )

        setattr(logging.Logger, "best", best)


class ColoredFormatter(logging.Formatter):
    """Formatter that colors only the log level name."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "BEST": "\033[1;37;44m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }

    RESET = "\033[0m"

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        original = record.levelname

        color = self.COLORS.get(original)

        if color:
            record.levelname = f"{color}{original}{self.RESET}"

        try:
            return super().format(record)
        finally:
            record.levelname = original


class LoggerConfig:
    """Logger configuration with sensible defaults."""

    DEFAULT_LOG_FILE = "dabmpi.log"

    LOG_LEVEL_CONSOLE = logging.WARNING
    LOG_LEVEL_FILE = logging.INFO

    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_LOG_FILES = 3

    @classmethod
    def create_logger(
        cls,
        name: str = "dabmpi",
        log_file: str | None = None,
        console_level: int | None = None,
        file_level: int | None = None,
        rank: int = 0,
    ) -> logging.Logger:
        """Create and configure a logger."""

        _register_custom_levels()

        logger = logging.getLogger(name)

        #
        # Already configured
        #
        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addFilter(MPIRankFilter(rank))

        console_level = (
            cls.LOG_LEVEL_CONSOLE if console_level is None else console_level
        )

        file_level = cls.LOG_LEVEL_FILE if file_level is None else file_level

        log_format = (
            "%(asctime)s.%(msecs)03d "
            "[pid=%(process)d rank=%(rank)d] "
            "%(name)s "
            "%(levelname)s "
            "%(message)s"
        )

        formatter = logging.Formatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = ColoredFormatter(
            log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if log_file:
            log_path = Path(log_file)

            log_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            if rank == 0:  # Only do this on rank 0 to avoid conflicts
                rotate_on_startup(
                    log_path,
                    cls.MAX_LOG_FILES,
                )

            file_handler = RotatingFileHandler(
                filename=log_path,
                maxBytes=cls.MAX_LOG_SIZE,
                backupCount=cls.MAX_LOG_FILES,
                encoding="utf-8",
                delay=True,
            )

            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        #
        # Console handler
        #
        console_handler = logging.StreamHandler()

        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)

        return logger


def get_logger(
    name: str = "dabmpi",
) -> logging.Logger:
    """Get an existing logger."""

    _register_custom_levels()

    return logging.getLogger(name)


class MPIRankFilter(logging.Filter):
    """Inject MPI rank into log records."""

    def __init__(
        self,
        rank: int | None = None,
    ) -> None:
        super().__init__()
        self.rank = rank

    def filter(
        self,
        record: logging.LogRecord,
    ) -> bool:
        record.rank = self.rank if self.rank is not None else -1
        return True
