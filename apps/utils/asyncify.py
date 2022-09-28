import time
from functools import wraps, partial
import asyncio

# Timer utilities
times = dict()


def timer_start(key):
    times[key] = time.time()


def timer_end(key):
    try:
        print(f"Time elapsed for task {key}: {time.time()-times[key]}")
        del times[key]
    except Exception as e:
        print(e)
        pass


def timer(key):
    if key in times:
        timer_end(key)
    else:
        timer_start(key)

# asyncify decorator


def asyncify(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run
