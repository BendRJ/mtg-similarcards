"""Centralized logging configuration for the application."""

import logging
import sys
from pathlib import Path


def setup_logging(
    log_level: int = logging.INFO, #means "show INFO and above" per default
    log_file: str = "app.log",
    log_to_console: bool = True,
    log_to_file: bool = True
) -> None:
    """
    Configure application-wide logging.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Path to the log file
        log_to_console: Whether to output logs to console
        log_to_file: Whether to output logs to file

    Example:
        from src.app.config.logging_config import setup_logging
        setup_logging(log_level=logging.DEBUG)
    """
    # Create root logger
    root_logger = logging.getLogger()
    #other loggers will inherit this configuration when set up with logging.getLogger(__name__) in their respective modules
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Define log format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Ensure the log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
