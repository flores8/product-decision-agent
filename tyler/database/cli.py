"""CLI tool for Tyler database management."""

import click
from alembic import command
from alembic.config import Config
import os
from pathlib import Path
import asyncio
from dotenv import load_dotenv, find_dotenv
from tyler.database.thread_store import ThreadStore

def get_alembic_config():
    """Get Alembic config from package location."""
    package_dir = Path(__file__).parent
    alembic_ini = package_dir / "migrations" / "alembic.ini"
    return Config(alembic_ini)

@click.group()
def cli():
    """Tyler database management commands."""
    pass

@cli.command()
@click.option('--db-type', type=click.Choice(['postgresql', 'sqlite']), help='Database type')
@click.option('--db-host', help='Database host (PostgreSQL only)')
@click.option('--db-port', help='Database port (PostgreSQL only)')
@click.option('--db-name', help='Database name (PostgreSQL only)')
@click.option('--db-user', help='Database user (PostgreSQL only)')
@click.option('--db-password', help='Database password (PostgreSQL only)')
@click.option('--sqlite-path', help='SQLite database path (SQLite only)')
@click.option('--env-file', help='Path to .env file', type=click.Path(exists=True))
@click.option('--verbose', is_flag=True, help='Show debug information')
def init(db_type, db_host, db_port, db_name, db_user, db_password, sqlite_path, env_file, verbose):
    """Initialize the database tables.
    
    Uses environment variables from .env if options not provided.
    Will look for .env in current directory, or use DOTENV_PATH environment variable,
    or use --env-file option.
    
    Environment variables used:
    TYLER_DB_TYPE, TYLER_DB_HOST, TYLER_DB_PORT, TYLER_DB_NAME, TYLER_DB_USER, TYLER_DB_PASSWORD
    
    For SQLite, defaults to ~/.tyler/data/tyler.db if path not specified.
    """
    if verbose:
        click.echo(f"Current working directory: {os.getcwd()}")
    
    # Load .env but allow CLI options to override
    if env_file:
        if verbose:
            click.echo(f"Loading .env from specified path: {env_file}")
        load_dotenv(env_file)
    elif os.getenv("DOTENV_PATH"):
        env_path = os.getenv("DOTENV_PATH")
        if verbose:
            click.echo(f"Loading .env from DOTENV_PATH: {env_path}")
        load_dotenv(env_path)
    else:
        env_path = find_dotenv(usecwd=True)
        if env_path:
            if verbose:
                click.echo(f"Found .env at: {env_path}")
            load_dotenv(env_path)
        else:
            if verbose:
                click.echo("No .env file found")
    
    if verbose:
        click.echo("\nEnvironment variables after loading:")
        for var in ["TYLER_DB_TYPE", "TYLER_DB_HOST", "TYLER_DB_PORT", "TYLER_DB_NAME", "TYLER_DB_USER"]:
            click.echo(f"{var}={os.getenv(var, 'not set')}")
    
    # Use CLI options if provided, otherwise fall back to env vars
    db_type = db_type or os.getenv("TYLER_DB_TYPE", "sqlite")
    
    if db_type == "postgresql":
        db_host = db_host or os.getenv("TYLER_DB_HOST")
        db_port = db_port or os.getenv("TYLER_DB_PORT")
        db_name = db_name or os.getenv("TYLER_DB_NAME")
        db_user = db_user or os.getenv("TYLER_DB_USER")
        db_password = db_password or os.getenv("TYLER_DB_PASSWORD")
        
        if not all([db_host, db_port, db_name, db_user, db_password]):
            missing = [var for var, val in {
                "host": db_host,
                "port": db_port,
                "name": db_name,
                "user": db_user,
                "password": db_password
            }.items() if not val]
            raise click.UsageError(
                f"Missing required PostgreSQL settings: {', '.join(missing)}. "
                "Provide them via CLI options or environment variables in .env file"
            )
        
        db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
    else:  # sqlite
        if sqlite_path:
            db_path = Path(sqlite_path)
        else:
            data_dir = Path(os.path.expanduser("~/.tyler/data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "tyler.db"
            
        db_url = f"sqlite+aiosqlite:///{db_path}"
    
    if verbose:
        click.echo(f"\nUsing database URL: {db_url}")
    
    async def init_db():
        store = ThreadStore(db_url)
        await store.initialize()
        click.echo(f"Initialized database at {db_url}")
    
    asyncio.run(init_db())

@cli.command()
def migrate():
    """Generate a new migration based on model changes."""
    alembic_cfg = get_alembic_config()
    message = click.prompt("Migration message", type=str)
    command.revision(alembic_cfg, message=message, autogenerate=True)
    click.echo("Migration created successfully")

@cli.command()
def upgrade():
    """Upgrade database to latest version."""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    click.echo("Database upgraded successfully")

@cli.command()
def downgrade():
    """Downgrade database by one version."""
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, "-1")
    click.echo("Database downgraded successfully")

@cli.command()
def history():
    """Show migration history."""
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)

@cli.command()
def current():
    """Show current database version."""
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)

def main():
    cli() 