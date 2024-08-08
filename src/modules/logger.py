"""
This module contains logger config for the project.
"""

import logging
import os

# Create a custom logger
logger = logging.getLogger("dolores")

# Set the default log level
log_level = os.getenv("LOG_LEVEL", "ERROR").upper()
logger.setLevel(log_level)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("dolores.log")

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
