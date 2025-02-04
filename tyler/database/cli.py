"""CLI tool for Tyler database management."""

import click
from alembic import command
from alembic.config import Config
import os
from pathlib import Path

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
def init():
    """Initialize the database with latest schema."""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    click.echo("Database initialized successfully")

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