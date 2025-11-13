"""
Logger Utility Module
Provides centralized logging configuration using loguru
"""

import sys
from pathlib import Path
from loguru import logger
from config.config import LOGGING_CONFIG, BASE_DIR


def setup_logger():
    """
    Configure and initialize the logger with file and console output.
    
    Features:
    - Colored console output for better readability
    - File rotation to manage log file sizes
    - Retention policy for automatic cleanup
    - Structured logging format with timestamps
    
    Returns:
        logger: Configured loguru logger instance
    """
    # Remove default logger
    logger.remove()
    
    # Add console handler with color
    logger.add(
        sys.stdout,
        format=LOGGING_CONFIG["format"],
        level=LOGGING_CONFIG["level"],
        colorize=True,
    )
    
    # Ensure log directory exists
    log_dir = Path(LOGGING_CONFIG["log_file"]).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Add file handler with rotation and retention
    logger.add(
        LOGGING_CONFIG["log_file"],
        format=LOGGING_CONFIG["format"],
        level=LOGGING_CONFIG["level"],
        rotation=LOGGING_CONFIG["rotation"],
        retention=LOGGING_CONFIG["retention"],
        compression="zip",  # Compress rotated logs
    )
    
    logger.info("Logger initialized successfully")
    return logger


# Initialize logger on module import
log = setup_logger()
