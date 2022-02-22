# Copyright 2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module provides methods that perform the logging operations.
"""

import enum
import logging
import sys


def setup_custom_logger(name: str):
    """Set the logger class for the library

    Args:
        name: Name of the Logger
    """
    formatter = logging.Formatter(fmt='%(asctime)s AppConfiguration %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(screen_handler)
    return logger


class Logger:
    """Logger for the library"""
    __is_debug = False

    __AppLogger = setup_custom_logger("appconfig_logger")

    class LoggerColors:
        """Logger Colors"""
        INFO = '\033[99m'
        ERROR = '\033[91m'
        SUCCESS = '\033[92m'
        WARNING = '\033[93m'
        DEBUG = '\033[99m'
        END = '\033[0m'

    class LEVEL(enum.Enum):
        """Logger Levels"""
        SUCCESS = 'SUCCESS'
        ERROR = 'ERROR'
        WARN = 'WARNING'
        INFO = 'INFO'
        DEBUG = 'DEBUG'

    @classmethod
    def set_debug(cls, value: bool):
        """Enable or disable the debug mode in Logger"""
        cls.__is_debug = value

    @classmethod
    def is_debug(cls):
        """Check whether the logger is in debug mode"""
        return cls.__is_debug

    @classmethod
    def info(cls, message):
        """Log info message"""
        message = str(message)
        cls.__AppLogger.info(cls.LoggerColors.INFO + message + cls.LoggerColors.END)

    @classmethod
    def error(cls, message):
        """Log error message"""
        message = str(message)
        cls.__AppLogger.error(cls.LoggerColors.ERROR + message + cls.LoggerColors.END)

    @classmethod
    def warning(cls, message):
        """Log warning message"""
        message = str(message)
        if cls.__is_debug:
            cls.__AppLogger.warning(cls.LoggerColors.WARNING + message + cls.LoggerColors.END)

    @classmethod
    def success(cls, message):
        """Log success message"""
        message = str(message)
        if cls.__is_debug:
            cls.__AppLogger.info(cls.LoggerColors.SUCCESS + message + cls.LoggerColors.END)

    @classmethod
    def debug(cls, message):
        """Log debug message"""
        message = str(message)
        if cls.__is_debug:
            cls.__AppLogger.debug(cls.LoggerColors.DEBUG + message + cls.LoggerColors.END)
