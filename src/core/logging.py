#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

from __future__ import annotations

"""Application logging configuration and management."""


import logging


class ColoredFormatter(logging.Formatter):
    """Formatter that colors only the log level name."""

    COLORS = {
        "DEBUG": "\033[36m",       # Cyan
        "INFO": "\033[32m",        # Green
        "WARNING": "\033[33m",     # Yellow
        "ERROR": "\033[31m",       # Red
        "CRITICAL": "\033[35m",    # Magenta
        "BEST": "\033[1;37;44m",   # White on blue background
    }

    RESET = "\033[0m"

    def format(self, record):
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

    LOG_FILE = "dabmpi.log"

    LOG_LEVEL_FILE = logging.DEBUG
    LOG_LEVEL_CONSOLE = logging.WARNING

    CUSTOM_LEVEL = 100
    CUSTOM_LEVEL_NAME = "BEST"

    @staticmethod
    def create_logger(
        name: str = "dabmpi",
        log_file: str | None = None,
        console_level: int = logging.WARNING,
        file_level: int = logging.DEBUG,
    ) -> logging.Logger:

        logging.addLevelName(
            LoggerConfig.CUSTOM_LEVEL,
            LoggerConfig.CUSTOM_LEVEL_NAME,
        )

        def best(self, message, *args, **kwargs):
            self.log(
                LoggerConfig.CUSTOM_LEVEL,
                message,
                *args,
                **kwargs,
            )

        if not hasattr(logging.Logger, "best"):
            logging.Logger.best = best

        logger = logging.getLogger(name)

        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        log_format = (
            "%(asctime)s.%(msecs)03d - "
            "%(name)s - "
            "%(levelname)s - "
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
            fh = logging.FileHandler(
                log_file,
                encoding="utf-8",
            )
            fh.setLevel(file_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(console_level)
        ch.setFormatter(console_formatter)
        logger.addHandler(ch)

        return logger


def get_logger(name: str = "dabmpi") -> logging.Logger:
    """Get an existing logger by name."""
    return logging.getLogger(name)