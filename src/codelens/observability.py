import time
import json
import os
import functools
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Any, Callable

from codelens.config import config

os.makedirs(os.path.dirname(config.log_file), exist_ok=True)

logger = logging.getLogger("codelens_tool_calls")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    config.log_file, 
    maxBytes=config.log_max_bytes, 
    backupCount=config.log_backup_count, 
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(message)s"))
if not logger.handlers:
    logger.addHandler(handler)

def log_tool_call(tool_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result_count = 0
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    result_count = 1
                elif isinstance(result, list):
                    result_count = len(result)
                elif hasattr(result, "__len__"):
                    result_count = len(result)
                else:
                    result_count = 1 if result else 0
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise e
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Filter out 'self' from kwargs if present, for cleaner logging
                logged_kwargs = {k: v for k, v in kwargs.items() if k != 'self'}
                
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
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
