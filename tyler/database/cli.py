"""Command line interface for database management"""
import os
import click
from dotenv import load_dotenv
from pathlib import Path
import logging
import asyncio

logger = logging.getLogger(__name__)

def load_env(env_file: str = None):
    """Load environment variables from .env file"""
    if env_file:
        # Use provided env file
        env_path = Path(env_file)
        if not env_path.exists():
            raise click.BadParameter(f"Environment file not found: {env_file}")
        load_dotenv(env_path)
    else:
        # Try to find .env file
        env_paths = [
            Path.cwd() / '.env',
            Path.home() / '.tyler' / '.env'
        ]
        for path in env_paths:
            if path.exists():
                load_dotenv(path)
                break

def get_db_url(db_type: str = None, **kwargs):
    """Get database URL from environment or arguments"""
    if not db_type:
        db_type = os.getenv('TYLER_DB_TYPE', 'sqlite')
        
    if db_type == 'postgresql':
        host = kwargs.get('db_host') or os.getenv('TYLER_DB_HOST', 'localhost')
        port = kwargs.get('db_port') or os.getenv('TYLER_DB_PORT', '5432')
        name = kwargs.get('db_name') or os.getenv('TYLER_DB_NAME', 'tyler')
        user = kwargs.get('db_user') or os.getenv('TYLER_DB_USER', 'tyler')
        password = kwargs.get('db_password') or os.getenv('TYLER_DB_PASSWORD', 'tyler_dev')
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    elif db_type == 'sqlite':
        # Use provided path or default to ~/.tyler/data/tyler.db
        if 'sqlite_path' in kwargs and kwargs['sqlite_path']:
            db_path = Path(kwargs['sqlite_path'])
        else:
            db_path = Path.home() / '.tyler' / 'data' / 'tyler.db'
            
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"
    else:
        raise click.BadParameter(f"Unsupported database type: {db_type}")

@click.group()
def cli():
    """Tyler database management CLI"""
    pass

@cli.command()
@click.option('--env-file', help='Path to .env file')
@click.option('--db-type', help='Database type (postgresql or sqlite)')
@click.option('--db-host', help='Database host')
@click.option('--db-port', help='Database port')
@click.option('--db-name', help='Database name')
@click.option('--db-user', help='Database user')
@click.option('--db-password', help='Database password')
@click.option('--sqlite-path', help='SQLite database path')
@click.option('--verbose/--no-verbose', default=False, help='Enable verbose output')
def init(env_file, db_type, db_host, db_port, db_name, db_user, db_password, sqlite_path, verbose):
    """Initialize the database"""
    if verbose:
        # If verbose is enabled, temporarily set log level to DEBUG for this command
        os.environ['LOG_LEVEL'] = 'DEBUG'
        from tyler.utils.logging import configure_logging
        configure_logging()
        
    try:
        # Import dependencies here to avoid circular imports
        from sqlalchemy.ext.asyncio import create_async_engine
        from .models import Base
        
        # Load environment variables
        load_env(env_file)
        
        # Get database URL
        db_url = get_db_url(
            db_type=db_type,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            sqlite_path=sqlite_path
        )
        
        if verbose:
            click.echo(f"Using database URL: {db_url}")
        
        # Create async engine
        engine = create_async_engine(db_url)
        
        # Create tables
        async def init_db():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
        asyncio.run(init_db())
        click.echo("Database initialized successfully")
        
    except Exception as e:
        click.echo(f"Error initializing database: {str(e)}", err=True)
        raise click.Abort()

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