import logging
import sys

def setup_logging():
    """Configure basic structured logging for the application."""
    logger = logging.getLogger("codelens")
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Console handler for operational logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_logger(name: str):
    return logging.getLogger(f"codelens.{name}")
