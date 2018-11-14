#
# DESCRIPTION
# Measures time of function execution

import functools
import time 

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} min'.format(
            func.__name__, int(elapsedTime / 60)))
    return newfunc