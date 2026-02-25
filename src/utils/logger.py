"""Structured logging utilities.

Provides a factory function that returns a pre-configured ``logging.Logger``
with a consistent format across the entire application.
"""

import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create and return a logger with a console handler.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.
        level: Minimum severity level to emit.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
