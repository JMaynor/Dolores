"""
This module contains logger config for the project.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Create a custom logger
logger = logging.getLogger("ezosync")

# Set the default log level
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.setLevel(log_level)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(
    "dolores.log", maxBytes=5 * 1024 * 1024, backupCount=3
)  # 5 MB per file, keep 3 backups

# Set log level for handlers
console_handler.setLevel(log_level)
file_handler.setLevel(log_level)

# Create formatters and add them to handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Prevent the custom logger from propagating messages to the root logger
logger.propagate = False

# Configure the root logger to use the same handlers
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
