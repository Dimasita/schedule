import time


def benchmark(text):
    def decor(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            return_value = func(*args, **kwargs)
            result = time.time() - start
            with open('timings.txt', 'a') as the_file:
                the_file.write(f'{text}: {result} seconds.\n')
            return return_value
        return wrapper
    return decor
