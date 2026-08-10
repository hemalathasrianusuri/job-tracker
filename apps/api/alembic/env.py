from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.settings import settings
from app.db.base import Base

# Import every module's models here so Base.metadata is fully populated for
# autogenerate. As new modules land (jobs, resume, ...) add their import here.
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.companies import models as companies_models  # noqa: F401
from app.modules.resume import models as resume_models  # noqa: F401
from app.modules.jobs import models as jobs_models  # noqa: F401
from app.modules.skills import models as skills_models  # noqa: F401
from app.modules.ai import models as ai_models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_db_url() -> str:
    """Alembic migrations run synchronously — swap the asyncpg driver for
    psycopg2 regardless of what's configured for the running app."""
    return settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _sync_db_url()

    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
