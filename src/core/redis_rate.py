import os
from redis.asyncio import Redis
RATE_REDIS_URL = os.getenv("RATE_LIMIT_REDIS_URL", "redis://redis:6379/1")
_redis: Redis | None = None

async def get_rate_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(RATE_REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis

async def close_rate_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
