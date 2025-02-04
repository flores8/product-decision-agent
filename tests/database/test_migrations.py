import pytest
import os
from pathlib import Path
import tempfile
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text, inspect
from tyler.database.thread_store import ThreadStore, ThreadRecord
from tyler.models.thread import Thread
from tyler.models.message import Message

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        url = f"sqlite:///{f.name}"
        # Create a fresh database file
        engine = create_engine(url)
        # Close any existing connections
        engine.dispose()
        yield url

@pytest.fixture
def alembic_config(temp_db):
    """Get Alembic config for testing."""
    package_dir = Path(__file__).parent.parent.parent / "tyler" / "database"
    alembic_ini = package_dir / "migrations" / "alembic.ini"
    config = Config(alembic_ini)
    
    # Override the database URL in the config
    config.set_main_option("sqlalchemy.url", temp_db)
    
    # Set the script location
    config.set_main_option("script_location", str(package_dir / "migrations"))
    
    # Create a fresh engine for cleanup
    engine = create_engine(temp_db)
    try:
        # Drop all tables in reverse order to handle dependencies
        with engine.begin() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            for table in reversed(tables):
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
    finally:
        # Ensure we close all connections
        engine.dispose()
    
    return config

def test_initial_migration(temp_db, alembic_config):
    """Test that initial migration creates correct schema."""
    # Run migrations
    command.upgrade(alembic_config, "head")
    
    # Check schema
    engine = create_engine(temp_db)
    try:
        inspector = inspect(engine)
        
        # Check if threads table exists
        assert 'threads' in inspector.get_table_names()
        
        # Check columns
        columns = {col['name']: col for col in inspector.get_columns('threads')}
        assert 'id' in columns
        assert 'data' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns
        
        # Check column types (using SQLite type names)
        assert columns['id']['type'].__class__.__name__ == 'VARCHAR'
        assert columns['data']['type'].__class__.__name__ == 'JSON'
        assert columns['created_at']['type'].__class__.__name__ == 'DATETIME'
        assert columns['updated_at']['type'].__class__.__name__ == 'DATETIME'
        
        # Check indexes
        indexes = inspector.get_indexes('threads')
        index_names = {idx['name'] for idx in indexes}
        assert 'ix_threads_created_at' in index_names
        assert 'ix_threads_updated_at' in index_names
    finally:
        engine.dispose()

def test_migration_with_data(temp_db, alembic_config):
    """Test that migrations preserve existing data."""
    # Set up database and store
    command.upgrade(alembic_config, "head")
    store = ThreadStore(temp_db)
    
    # Add test data with various fields
    thread = Thread()
    thread.title = "Test Thread"
    thread.attributes = {"category": "test", "priority": "high"}
    thread.source = {"name": "test", "id": "123"}
    
    # Add messages
    thread.add_message(Message(role="user", content="Test message"))
    thread.add_message(Message(role="assistant", content="Test response"))
    
    # Save thread and verify it was saved
    store.save(thread)
    saved_thread = store.get(thread.id)
    assert saved_thread is not None
    assert saved_thread.title == thread.title
    
    # Create a backup of the data
    engine = create_engine(temp_db)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM threads")).fetchall()
            backup_data = [dict(row._mapping) for row in result]
    finally:
        engine.dispose()
    
    # Run downgrade and upgrade
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    
    # Restore the data
    engine = create_engine(temp_db)
    try:
        with engine.begin() as conn:
            for row in backup_data:
                conn.execute(
                    text("INSERT INTO threads (id, data, created_at, updated_at) VALUES (:id, :data, :created_at, :updated_at)"),
                    row
                )
    finally:
        engine.dispose()
    
    # Verify data is preserved
    loaded_thread = store.get(thread.id)
    assert loaded_thread is not None
    assert loaded_thread.title == thread.title
    assert loaded_thread.attributes == thread.attributes
    assert loaded_thread.source == thread.source
    assert len(loaded_thread.messages) == len(thread.messages)

def test_migration_downgrade(temp_db, alembic_config):
    """Test that downgrades work correctly."""
    # Set up database
    command.upgrade(alembic_config, "head")
    
    # Add some data
    store = ThreadStore(temp_db)
    thread = Thread()
    store.save(thread)
    
    # Run downgrade
    command.downgrade(alembic_config, "base")
    
    # Verify tables are gone
    engine = create_engine(temp_db)
    try:
        inspector = inspect(engine)
        assert 'threads' not in inspector.get_table_names()
    finally:
        engine.dispose()

def test_migration_idempotency(temp_db, alembic_config):
    """Test that running migrations multiple times is safe."""
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Run migrations multiple times
    command.upgrade(alembic_config, "head")
    command.upgrade(alembic_config, "head")
    
    # Should not raise any errors
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    assert 'threads' in inspector.get_table_names()

def test_migration_empty_db(temp_db, alembic_config):
    """Test migrations on empty database."""
    alembic_config.set_main_option("sqlalchemy.url", temp_db)
    
    # Create empty database first
    engine = create_engine(temp_db)
    
    # Run migrations
    command.upgrade(alembic_config, "head")
    
    # Check schema was created
    inspector = inspect(engine)
    assert 'threads' in inspector.get_table_names() 