from time import time


_cache = {}


def get(key):
    item = _cache.get(key)
    if not item or item[0] < time():
        _cache.pop(key, None)
        return None
    return item[1]


def set(key, value, seconds=30):
    _cache[key] = (time() + seconds, value)


def delete(key):
    _cache.pop(key, None)