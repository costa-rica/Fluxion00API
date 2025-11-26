"""
Logging configuration for Fluxion00API.

Provides structured logging for agent progress tracking with time-only timestamps.
"""

import logging
import sys


def setup_logger(name: str = "fluxion") -> logging.Logger:
    """
    Set up logger with custom formatting.

    Args:
        name: Logger name (default: "fluxion")

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Time-only format (no date)
        # Format: HH:MM:SS [LEVEL] message
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def truncate_text(text: str, max_length: int = 30) -> str:
    """
    Truncate text to specified length for logging.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 30)

    Returns:
        str: Truncated text with ellipsis if needed
    """
    if not text:
        return ""

    # Remove newlines and extra whitespace for cleaner logs
    clean_text = " ".join(text.split())

    if len(clean_text) <= max_length:
        return clean_text

    return clean_text[:max_length] + "..."


# Global logger instance
logger = setup_logger()
