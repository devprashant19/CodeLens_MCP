import time
import json
import os
import functools
from datetime import datetime
from typing import Any, Callable

LOG_FILE = "logs/tool_calls.jsonl"

def log_tool_call(tool_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result_count = 0
            error_msg = None
            
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, list):
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
                
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
                    
        return wrapper
    return decorator
