import asyncio
from functools import wraps


def run_async(f):
    @wraps(f)
    def _run_async(*args, **kwargs):
        result = f(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        else:
            return result
    return _run_async
