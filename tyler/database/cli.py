"""CLI tool for Tyler database management."""

import click
from alembic.config import Config
from alembic import command
import os
from pathlib import Path

@click.group()
def cli():
    """Tyler database management CLI."""
    pass

@cli.command()
@click.option('--database-url', required=True, help='Database URL (e.g., postgresql://user:pass@localhost/dbname)')
def init(database_url):
    """Initialize the database with required tables."""
    # Create alembic.ini with the provided database URL
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parent / 'migrations'))
    config.set_main_option('sqlalchemy.url', database_url)
    
    # Run migrations
    command.upgrade(config, 'head')
    click.echo(f"Database initialized at {database_url}")

@cli.command()
@click.option('--database-url', required=True, help='Database URL (e.g., postgresql://user:pass@localhost/dbname)')
def reset(database_url):
    """Reset the database (drop all tables and recreate)."""
    config = Config()
    config.set_main_option('script_location', str(Path(__file__).parent / 'migrations'))
    config.set_main_option('sqlalchemy.url', database_url)
    
    # Drop all tables and rerun migrations
    command.downgrade(config, 'base')
    command.upgrade(config, 'head')
    click.echo(f"Database reset at {database_url}")

def main():
    cli() 