#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

from __future__ import annotations

#############################################################################
#    Copyright 2013 by Antonio Gomez and Miguel Cardenas                    #
#                                                                           #
#    Licensed under the Apache License, Version 2.0 (the "License");        #
#    you may not use this file except in compliance with the License.       #
#    You may obtain a copy of the License at                                #
#                                                                           #
#        http://www.apache.org/licenses/LICENSE-2.0                         #
#                                                                           #
#    Unless required by applicable law or agreed to in writing, software    #
#    distributed under the License is distributed on an "AS IS" BASIS,      #
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied#
#    See the License for the specific language governing permissions and    #
#    limitations under the License.                                         #
#############################################################################

"""Application logging configuration and management."""

__author__ = "Antonio Gomez"
__version__ = "2.0"

import logging

class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
        100: "\033[1;37;44m"            # White text on blue background
    }

    RESET = "\033[0m"

    def format(self, record):
        original = record.levelname

        color = self.COLORS.get(record.levelno)
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

    @staticmethod
    def create_logger(
        name: str = "dabmpi",
        log_file: str | None = None,
        console_level: int = logging.WARNING,
        file_level: int = logging.DEBUG,
    ) -> logging.Logger:

        logger = logging.getLogger(name)

        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(file_level)
            fh.setFormatter(formatter)  # plain text
            logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(console_level)
        ch.setFormatter(console_formatter)  # colored
        logger.addHandler(ch)

        logging.addLevelName(LoggerConfig.CUSTOM_LEVEL, "BEST")

        return logger


def get_logger(name: str = "dabmpi") -> logging.Logger:
    """Get or create logger by name."""
    return logging.getLogger(name)