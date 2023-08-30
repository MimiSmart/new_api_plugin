import time
from functools import wraps


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        diff = end - start
        if diff > 0.2:
            print(f'{func.__name__} took {diff:.6f} seconds to complete')
        return result

    return wrapper
