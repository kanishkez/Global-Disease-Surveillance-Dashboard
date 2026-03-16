from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
import redis.asyncio as aioredis
from app.config import get_settings
import json
from typing import Optional

settings = get_settings()


async def get_redis():
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close()


class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Optional[dict]:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: dict, ttl: int = None):
        await self.redis.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or self.default_ttl
        )

    async def invalidate(self, pattern: str):
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)
