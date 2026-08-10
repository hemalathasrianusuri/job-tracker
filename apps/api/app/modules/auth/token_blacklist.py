"""
Refresh tokens are stateless JWTs but we still need to be able to revoke one
before its natural expiry — that's what a blacklist buys us. Rather than
tracking every valid token (defeats the point of JWTs), we only ever store
REVOKED jti values, with a TTL equal to the token's remaining lifetime so the
Redis key expires on its own and the blacklist never grows unbounded.
"""

from datetime import datetime, timezone

import redis.asyncio as redis

from app.core.settings import settings

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

_KEY_PREFIX = "revoked_jti:"


async def revoke(jti: str, expires_at: datetime) -> None:
    ttl_seconds = max(int((expires_at - datetime.now(timezone.utc)).total_seconds()), 0)
    if ttl_seconds > 0:
        await _redis.set(f"{_KEY_PREFIX}{jti}", "1", ex=ttl_seconds)


async def is_revoked(jti: str) -> bool:
    return bool(await _redis.exists(f"{_KEY_PREFIX}{jti}"))
