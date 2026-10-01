import json
import os
from time import time

from dotenv import load_dotenv

try:
    from redis.asyncio import Redis
except ModuleNotFoundError:
    Redis = None

_cache = {}
load_dotenv()
_redis = (
    Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    if Redis is not None
    else None
)


async def _redis_available():
    if _redis is None:
        return False
    try:
        await _redis.ping()
        return True
    except Exception:
        return False


async def get(key):
    if await _redis_available():
        value = await _redis.get(key)
        return json.loads(value) if value is not None else None

    item = _cache.get(key)
    if not item or item[0] < time():
        _cache.pop(key, None)
        return None
    return item[1]


async def set(key, value, seconds=30):
    if await _redis_available():
        await _redis.set(key, json.dumps(value), ex=seconds)
        return

    _cache[key] = (time() + seconds, value)


async def delete(key):
    if await _redis_available():
        await _redis.delete(key)
        return

    _cache.pop(key, None)