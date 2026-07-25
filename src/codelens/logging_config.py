import logging
import sys


def setup_logging():
    """Configure basic structured logging for the application."""
    logger = logging.getLogger("codelens")
    if logger.handlers:
        return logger
        
    import os
    log_level_str = os.environ.get("CODELENS_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    logger.setLevel(log_level)
    
    # Console handler for operational logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_logger(name: str):
    return logging.getLogger(f"codelens.{name}")
