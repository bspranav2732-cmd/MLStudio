"""
Logging Configuration
=====================

Sets up a dual-output logger for the Solvosys desktop launcher:
- Console output (INFO level, concise format)
- File output   (DEBUG level, detailed format, logs/launcher.log)

Usage:
    from desktop.logger import get_logger
    log = get_logger()
    log.info("Server started on port %d", port)
"""

import logging
from desktop.resources import get_logs_dir


_LOG_FORMAT_CONSOLE = "%(asctime)s  %(levelname)-8s  %(message)s"
_LOG_FORMAT_FILE = "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger = None


def get_logger(name: str = "solvosys") -> logging.Logger:
    """
    Return the application logger, creating it on first call.

    The logger writes to both the console and to logs/launcher.log.
    Subsequent calls return the same logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        _logger = logger
        return _logger

    # ── Console Handler (INFO) ────────────────────────────
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(
        logging.Formatter(_LOG_FORMAT_CONSOLE, datefmt=_DATE_FORMAT)
    )
    logger.addHandler(console)

    # ── File Handler (DEBUG) ──────────────────────────────
    log_file = get_logs_dir() / "launcher.log"
    file_handler = logging.FileHandler(
        log_file, mode="a", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT_FILE, datefmt=_DATE_FORMAT)
    )
    logger.addHandler(file_handler)

    _logger = logger
    return _logger
