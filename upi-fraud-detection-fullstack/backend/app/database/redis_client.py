import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(REDIS_URL)
    return _redis
