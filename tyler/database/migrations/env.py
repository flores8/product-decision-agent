from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from tyler.database.thread_store import Base
import os

# Load our database configuration
def get_url():
    """Get database URL from environment or use default SQLite."""
    # If a URL is already set in the config, use that (for testing)
    if context.config.get_main_option("sqlalchemy.url"):
        return context.config.get_main_option("sqlalchemy.url")
    
    # Otherwise use environment configuration
    db_type = os.getenv("TYLER_DB_TYPE", "sqlite")
    
    if db_type == "postgresql":
        host = os.getenv("TYLER_DB_HOST", "localhost")
        port = os.getenv("TYLER_DB_PORT", "5432")
        database = os.getenv("TYLER_DB_NAME", "tyler")
        user = os.getenv("TYLER_DB_USER", "tyler")
        password = os.getenv("TYLER_DB_PASSWORD", "tyler_dev")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        data_dir = os.path.expanduser("~/.tyler/data")
        os.makedirs(data_dir, exist_ok=True)
        return f"sqlite:///{data_dir}/tyler.db"

config = context.config

# Set the database URL in the config if not already set
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_url())

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # For testing, we want to use NullPool to ensure we get a fresh connection
    # each time and don't reuse connections between tests
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 