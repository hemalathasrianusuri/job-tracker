from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP-baseline security headers. CSP is deliberately permissive on
    connect-src/img-src (the API serves a SPA-style frontend that talks to
    itself and Supabase Storage) — tighten this if you add third-party
    embeds. HSTS only sends in production: it's a browser-cached instruction
    to always use HTTPS, which would break local http://localhost dev."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https://*.supabase.co; "
            f"connect-src 'self' {settings.FRONTEND_URL}; "
            "frame-ancestors 'none'"
        )

        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        return response
