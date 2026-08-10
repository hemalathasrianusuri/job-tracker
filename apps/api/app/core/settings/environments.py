from pydantic import model_validator

from app.core.settings.base import BaseAppSettings


class DevelopmentSettings(BaseAppSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


class TestingSettings(BaseAppSettings):
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_tracker_test"
    # Short-lived tokens make auth expiry easy to exercise in tests
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1


class ProductionSettings(BaseAppSettings):
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    # In production these MUST come from the real environment / secrets manager —
    # the defaults in BaseAppSettings are intentionally unsafe so a misconfigured
    # prod deploy fails loudly (empty SECRET_KEY, etc.) rather than silently.

    @model_validator(mode="after")
    def _forbid_dev_defaults(self) -> "ProductionSettings":
        if self.SECRET_KEY == "CHANGE_ME_IN_ENV":
            raise ValueError("SECRET_KEY must be set via environment in production")
        if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials must be set in production")
        return self
