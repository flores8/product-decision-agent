"""Logging configuration for tyler package."""
import os
import logging

def configure_logging():
    """Configure logging for the tyler package based on environment variables.
    
    This will set up logging for all tyler modules based on the LOG_LEVEL environment variable.
    If LOG_LEVEL is not set, defaults to INFO.
    
    This also configures some third-party loggers to appropriate levels to reduce noise.
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Configure the root logger with our format
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Set log level for all tyler loggers
    tyler_logger = logging.getLogger('tyler')
    tyler_logger.setLevel(log_level)
    
    # Ensure child loggers inherit the level
    tyler_logger.propagate = True
    
    # Configure third-party loggers to reduce noise
    third_party_loggers = {
        'PyPDF2': logging.ERROR,  # PyPDF2 is very verbose at INFO level
        'urllib3': logging.INFO,  # Network requests
        'sqlalchemy': logging.WARNING,  # Database operations
    }
    
    for logger_name, level in third_party_loggers.items():
        logging.getLogger(logger_name).setLevel(level) 