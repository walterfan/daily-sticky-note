
import re
import io
import json
import time
import requests
from datetime import datetime
from loguru import logger
import pandas as pd
from cachetools import TTLCache
from functools import wraps

class LazyLlmError(Exception):
    def __init__(self, reason, original_exception):
        self.reason = reason
        self.original_exception = original_exception
        super().__init__(f"LLM Error: {original_exception}")

    def get_reason(self):
        return self.reason
        
def cache_non_empty(maxsize=100, ttl=300):
    # Initialize the cache with the specified maxsize and TTL
    cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key based on function arguments
            cache_key = (args, frozenset(kwargs.items()))
            
            # Check if the result is already cached
            if cache_key in cache:
                return cache[cache_key]
            
            # Compute the result if not in cache
            result = func(*args, **kwargs)
            
            # Only store non-empty results in the cache
            if result not in (None, '', [], {}, set()):
                cache[cache_key] = result
            
            return result
        return wrapper
    return decorator



def str2bool(arg):
    if not arg:
        return False
    if isinstance(arg, bool):
        return arg
    if arg.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    else:
        return False
    
def metrics_recorder(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"[metrics] {{\"name\": \"'{func.__name__}'\", \"duration\": {elapsed_time:.4f} }}")
        return result
    return wrapper

def diagnose_dict2list(diagnose_dict: dict[str, dict]) ->list[tuple[str, str, str]]:
    results = []
    for k, v in diagnose_dict.items():
        results.append((k, v["uuid"], v["category"]))
    return results

def measurements_dict2list(measurements_dict: dict[str, dict]):
    results = []
    for k, v in measurements_dict.items():
        results.append((k,  v["uuid"], v["desc"], v["defaultUnit"]))
    return results

def extract_numbers(text):
    numbers = re.findall(r'\d+\.\d+|\d+', text)
    return [float(num) for num in numbers]
