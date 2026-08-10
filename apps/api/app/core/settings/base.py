from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Shared settings. Environment-specific classes override individual fields."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    APP_NAME: str = "AI Job Tracker"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_tracker"

    # Redis (cache, rate limiting, Celery broker)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Frontend origin (CORS + post-OAuth redirect target)
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate limiting (requests per window, per IP, via Redis)
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # AI providers (used from Phase 5 onward, declared here so config is centralized)
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    # Model IDs are configurable rather than hardcoded — check your provider's
    # current docs before deploying; these are placeholders, not guarantees.
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_MODEL: str = "gemini-2.5-flash"  # free tier as of mid-2026 — verify current quotas/name
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # free tier as of mid-2026 — verify current quotas/name
    # "claude" | "openai" | "gemini" | "groq". Defaults to a fully free stack
    # (Gemini primary, Groq fallback) — set to "claude"/"openai" and add the
    # matching API key if you'd rather use a paid provider.
    AI_PRIMARY_PROVIDER: str = "gemini"
    AI_FALLBACK_PROVIDER: str = "groq"
    AI_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 7  # 7 days — JD analysis is idempotent per posting
    AI_MAX_OUTPUT_TOKENS: int = 4000

    # If true, resume text extraction + AI skill extraction run as a Celery
    # chain (requires a running worker — see docker-compose's `worker`
    # profile) instead of synchronously in the upload request. Defaults off
    # so local dev works with zero extra services; flip on once you're
    # running the worker.
    ENABLE_ASYNC_RESUME_PROCESSING: bool = False

    # File storage — if Supabase credentials are unset, storage falls back to
    # local disk so Phase 3+ is fully runnable without a live Supabase project.
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_BUCKET: str = "resumes"
    LOCAL_STORAGE_DIR: str = "./local_storage"
    LOCAL_STORAGE_PUBLIC_BASE_URL: str = "http://localhost:8000/local-files"
