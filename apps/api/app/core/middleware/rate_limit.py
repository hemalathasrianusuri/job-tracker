import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.settings import settings

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window limiter keyed by client IP + path prefix. Simple and adequate
    for portfolio scale; swap for a token-bucket / sliding-window-log if this
    ever needs to be precise under real adversarial traffic.

    Auth endpoints get a tighter budget than general API traffic — brute-force
    and credential-stuffing risk lives there, not on GET /jobs."""

    AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(settings.API_V1_PREFIX):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        is_auth_route = request.url.path.startswith(self.AUTH_PREFIX)
        limit = settings.RATE_LIMIT_REQUESTS // 5 if is_auth_route else settings.RATE_LIMIT_REQUESTS
        key = f"rate_limit:{client_ip}:{'auth' if is_auth_route else 'api'}"

        count = await _redis.incr(key)
        if count == 1:
            await _redis.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests, please slow down."},
            )

        return await call_next(request)
