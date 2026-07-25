import functools
import json
import logging
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler

from codelens.config import config

logger = logging.getLogger("codelens_tool_calls")
logger.setLevel(logging.INFO)
_handler_setup_done = False

def _setup_handler():
    global _handler_setup_done
    if _handler_setup_done:
        return
        
    os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
    handler = RotatingFileHandler(
        config.log_file, 
        maxBytes=config.log_max_bytes, 
        backupCount=config.log_backup_count, 
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    _handler_setup_done = True

def log_tool_call(tool_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _setup_handler()
            start_time = time.time()
            success = True
            result_count = 0
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    result_count = 1
                elif isinstance(result, list) or hasattr(result, "__len__"):
                    result_count = len(result)
                else:
                    result_count = 1 if result else 0
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Filter out 'self' from kwargs if present, for cleaner logging
                logged_kwargs = {k: v for k, v in kwargs.items() if k != 'self'}
                
                log_entry = {
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "tool_name": tool_name,
                    "input_args": logged_kwargs,
                    "latency_ms": latency_ms,
                    "success": success,
                    "result_count": result_count,
                    "error": error_msg
                }
                
                logger.info(json.dumps(log_entry))
                    
        return wrapper
    return decorator
