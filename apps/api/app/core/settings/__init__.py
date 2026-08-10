import os
from functools import lru_cache

from app.core.settings.base import BaseAppSettings
from app.core.settings.environments import (
    DevelopmentSettings,
    ProductionSettings,
    TestingSettings,
)

_ENV_MAP = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}


@lru_cache
def get_settings() -> BaseAppSettings:
    """Cached settings instance. Reads ENVIRONMENT once per process."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    settings_cls = _ENV_MAP.get(env, DevelopmentSettings)
    return settings_cls()


settings = get_settings()
