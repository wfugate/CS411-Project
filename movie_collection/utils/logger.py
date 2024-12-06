import logging
from logging.handlers import RotatingFileHandler
import os

def configure_logger(logger, log_level=logging.INFO):
    """
    Configure logger with file and console handlers.

    Args:
        logger: Logger instance to configure
        log_level: Logging level (default: INFO)
    """
    logger.setLevel(log_level)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File Handler - rotates log files when they reach 1MB
    file_handler = RotatingFileHandler(
        'logs/auth.log', 
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)